# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import CodeInterpreterTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

###################################################################
# The following sample demonstrates how to create a simple,       #
# Azure AI agent that uses the code interpreter tool to answer    #
# a coding question.                                              #
###################################################################


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings.create(env_file_path="../../.env")

    async with (
        DefaultAzureCredential() as creds,
        AIProjectClient.from_connection_string(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
        code_interpreter = CodeInterpreterTool()

        # Create agent definition
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources,
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # Create a new thread
        thread = await client.agents.create_thread()

        user_inputs = [
            "yfinace를 이용하여 microsoft 주식정보를 가져온후 1개월간 주가 추이를 차트로 보여주세요. 코드를 실행하고 결과를 로컬에 chart.png로 저장하세요. 그 파일을 다운로드 받을 수 있게 링크를 제공해줘"
        ]

        try:
            for user_input in user_inputs:
                # Add the user input as a chat message
                await agent.add_chat_message(
                    thread_id=thread.id, message=ChatMessageContent(role=AuthorRole.USER, content=user_input)
                )
                print(f"# User: '{user_input}'")
                # Invoke the agent for the specified thread
                async for content in agent.invoke(thread_id=thread.id):
                    if content.role != AuthorRole.TOOL:
                        print(f"# Agent: {content.content}")
        finally:
            await client.agents.delete_thread(thread.id)
            await client.agents.delete_agent(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
