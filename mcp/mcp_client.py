import requests
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_plugin import KernelPlugin


class MCPClient:
    def __init__(self, server_url):
        self.server_url = server_url

    def list_tools(self):
        print(f"Server URL: {self.server_url}")
        response = requests.get(f"{self.server_url}/tools")
        print (f"Response: {response.json()}")
        if response.status_code == 200:
            return response.json()["tools"]
        else:
            raise Exception("Failed to retrieve tools")

    def execute_tool(self, tool_name, input_text):
        payload = {"tool": tool_name, "input": input_text}
        response = requests.post(f"{self.server_url}/execute", json=payload)
        if response.status_code == 200:
            return response.json()["result"]
        else:
            raise Exception("Failed to execute tool")

class MCPIntegration:

    functions = {}

    def __init__(self, kernel, mcp_client):
        self.kernel: Kernel = kernel
        self.mcp_client: MCPClient = mcp_client

    def integrate_tools(self) -> KernelPlugin:
        tools = self.mcp_client.list_tools()
        for tool in tools:
            tool_name = tool["name"]
            tool_description = tool["description"]

            @kernel_function(name=tool_name, description=tool_description)
            async def tool_function(input_text):
                return self.mcp_client.execute_tool(tool_name, input_text)
            
            self.functions[tool_name] = tool_function

        return self.kernel.add_functions(plugin_name="MCPPlugin", functions=self.functions)

if __name__ == "__main__":
    import asyncio

    client = MCPClient("http://127.0.0.1:5000")

    # 도구 목록 출력
    tools = client.list_tools()
    print("Available tools:")
    for tool in tools:
        print(f"- {tool['name']}: {tool['description']}")

    # 도구 실행 예시
    result = client.execute_tool("reverse", "Hello World!")
    print(f"Result: {result}")

    kernel = Kernel()
    openai_service = AzureChatCompletion()
    kernel.add_service(openai_service)

    mcp_integration = MCPIntegration(kernel, client)
    kernel_functions = mcp_integration.integrate_tools()

    async def main():
        input_text = "Python is fun!"
        print(f"Trying to reverse: '{input_text}'")

        result = await kernel.invoke(kernel_functions['reverse'], input_text=input_text)
        print(f"Reversed result: '{result}'")

    
    asyncio.run(main())
