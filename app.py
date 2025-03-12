import chainlit as cl
from chainlit import Message, on_message

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory

kernel = Kernel()

kernel.add_service(AzureChatCompletion(service_id="agent"))

AGENT_INSTRUCTIONS = "You are a agent"
agent = ChatCompletionAgent(service_id="agent", kernel=kernel, name="agent")

chat_history = ChatHistory()
chat_history.add_system_message(AGENT_INSTRUCTIONS)

@cl.on_message
async def main(message: cl.Message):
    chat_history.add_user_message(message.content)
    response = agent.invoke_stream(chat_history)
    msg = await Message(content="").send()
    async for chunk in response:
        if chunk and chunk.content:
            await msg.stream_token(str(chunk.content))
    await msg.update()
