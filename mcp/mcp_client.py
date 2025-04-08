import asyncio
from contextlib import AsyncExitStack
from typing import Optional

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments

from mcp import ClientSession
from mcp.client.sse import sse_client
class MCPClient:
    def __init__(self, kernel: Kernel):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.kernel = kernel

    async def connect_to_sse_server(self, server_url: str):
        """Connect to an MCP server running with SSE transport"""
        self._streams_context = sse_client(url=server_url)
        streams = await self._streams_context.__aenter__()

        self._session_context = ClientSession(*streams)
        self.session: ClientSession = await self._session_context.__aenter__()

        await self.session.initialize()

    async def cleanup(self):
        """Properly clean up the session and streams"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)

    async def integrate_tools(self) -> KernelPlugin:
        """Integrate tools into the kernel"""
        functions = {}
        print("Initialized SSE client...")
        print("Listing tools...")
        response = await self.session.list_tools()
        tools = response.tools
        print("Tools:", tools)

        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        for tool in available_tools:
            tool_name = tool["name"]
            tool_description = tool["description"]
            tool_input_schema = tool["input_schema"]

            prop_names = list(tool_input_schema.get("properties", {}).keys())
            params_str = ", ".join(prop_names)  # e.g., "input" or "param1, param2"
            input_data_mapping = ", ".join([f"'{name}': {name}" for name in prop_names])
            func_code = (
                f"async def dynamic_tool_function({params_str}):\n"
                f"    input_data = {{{input_data_mapping}}}\n"
                f"    return await self.session.call_tool(tool_name, input_data)"
            )
            local_vars = {}
            exec(func_code, {"self": self, "tool_name": tool_name}, local_vars)
            dynamic_tool_function = local_vars["dynamic_tool_function"]

            tool_function = kernel_function(name=tool_name, description=tool_description)(dynamic_tool_function)

            # @kernel_function(name=tool_name, description=tool_description)
            # async def tool_function(input_text: str):
            #     #TODO: Handle input schema
            #     input_data = {"input": input_text}
            #     return await self.session.call_tool(tool_name, input_data)
                        
            functions[tool_name] = tool_function
        return self.kernel.add_functions(plugin_name="MCPPlugin", functions=functions)

async def main():
    MCE_SERVER_URL = "http://localhost:8080/sse"
    
    kernel = Kernel()
    client = MCPClient(kernel)    
    openai_service = AzureChatCompletion()
    kernel.add_service(openai_service)    
        
    try:
        await client.connect_to_sse_server(server_url=MCE_SERVER_URL)
        input_text = "Python is fun!"
        print(f"Trying to reverse: '{input_text}'")

        kernel_functions = await client.integrate_tools()

        result = await kernel.invoke(kernel_functions['reverse'], KernelArguments(input=input_text))
        print(f"Reversed result: '{result}'")

        result = await kernel.invoke(kernel_functions['add'], KernelArguments(a=123, b=456))
        print(f"Added result: '{result}'")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())