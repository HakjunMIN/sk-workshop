# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory

###################################################################
# The following sample demonstrates how to create a simple,       #
# non-group agent that repeats the user message in the voice      #
# of a pirate and then ends with a parrot sound.                  #
###################################################################

# Create the instance of the Kernel
kernel = Kernel()

# Add the OpenAIChatCompletion AI Service to the Kernel
kernel.add_service(AzureChatCompletion(service_id="agent", env_file_path="../../.env"))

# Define the agent with name and instructions
AGENT_NAME = "Parrot"
AGENT_INSTRUCTIONS = "You are a helpful parrot that repeats the user message in a emperor's voice."
agent = ChatCompletionAgent(service_id="agent", kernel=kernel, name=AGENT_NAME)


async def main():
    # Define the chat history
    chat_history = ChatHistory()
    chat_history.add_system_message(AGENT_INSTRUCTIONS)

    user_inputs = [
        "행운은 대담한 자에게 유리합니다.",
        "연습이 완벽을 만듭니다.",
    ]
    for user_input in user_inputs:
        # Add the user input to the chat history
        chat_history.add_user_message(user_input)
        print(f"# User: '{user_input}'")
        # Invoke the agent to get a response
        async for content in agent.invoke(chat_history):
            # Add the response to the chat history
            chat_history.add_message(content)
            print(f"# Agent - {content.name or '*'}: '{content.content}'")


if __name__ == "__main__":
    asyncio.run(main())
