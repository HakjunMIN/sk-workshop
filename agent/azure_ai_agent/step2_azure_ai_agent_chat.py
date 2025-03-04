# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI, a chat completion  #
# agent and have them participate in a group chat to work towards   #
# the user's requirement.                                           #
#####################################################################


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "approved" in history[-1].content.lower()


REVIEWER_NAME = "ArtDirector"
REVIEWER_INSTRUCTIONS = """
귀하는 데이비드 오길비에 대한 애정에서 비롯된 카피라이팅에 대한 의견을 가진 아트 디렉터입니다.
주어진 카피가 인쇄할 수 있는지 여부를 판단하는 것이 목표입니다.
그렇다면 승인되었음을 표시합니다.  승인을 내리지 않는 한 “승인”이라는 단어를 사용하지 마세요.
그렇지 않은 경우에는 예시 없이 제안된 문구를 다듬는 방법에 대한 인사이트를 제공하세요.
"""

COPYWRITER_NAME = "CopyWriter"
COPYWRITER_INSTRUCTIONS = """
당신은 10년 경력의 카피라이터이며 간결하고 건조한 유머를 구사하는 것으로 유명합니다.
목표는 해당 분야의 전문가로서 최고의 카피를 다듬고 결정하는 것입니다.
응답당 하나의 제안만 제공합니다.
당면한 목표에 집중할 수 있습니다.
잡담으로 시간을 낭비하지 마세요.
아이디어를 구체화할 때 제안을 고려하세요.
"""


async def main():
    ai_agent_settings = AzureAIAgentSettings.create(env_file_path="../../.env")

    async with (
        DefaultAzureCredential() as creds,
        AIProjectClient.from_connection_string(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
        # Create the reviewer agent definition
        reviewer_agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=REVIEWER_NAME,
            instructions=REVIEWER_INSTRUCTIONS,
        )
        # Create the reviewer Azure AI Agent
        agent_reviewer = AzureAIAgent(
            client=client,
            definition=reviewer_agent_definition,
        )

        # Create the copy writer agent definition
        copy_writer_agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=COPYWRITER_NAME,
            instructions=COPYWRITER_INSTRUCTIONS,
        )
        # Create the copy writer Azure AI Agent
        agent_writer = AzureAIAgent(
            client=client,
            definition=copy_writer_agent_definition,
        )

        chat = AgentGroupChat(
            agents=[agent_writer, agent_reviewer],
            termination_strategy=ApprovalTerminationStrategy(agents=[agent_reviewer], maximum_iterations=10),
        )

        input = "새로운 전기차 라인의 슬로건"

        try:
            await chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=input))
            print(f"# {AuthorRole.USER}: '{input}'")

            async for content in chat.invoke():
                print(f"# {content.role} - {content.name or '*'}: '{content.content}'")

            print(f"# IS COMPLETE: {chat.is_complete}")

            print("*" * 60)
            print("Chat History (In Descending Order):\n")
            async for message in chat.get_chat_messages(agent=agent_reviewer):
                print(f"# {message.role} - {message.name or '*'}: '{message.content}'")
        finally:
            await chat.reset()
            await client.agents.delete_agent(agent_reviewer.id)
            await client.agents.delete_agent(agent_writer.id)


if __name__ == "__main__":
    asyncio.run(main())
