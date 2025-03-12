# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent

###################################################################
# The following sample demonstrates how to create a simple,       #
# agent group chat that utilizes An Art Director Chat Completion  #
# Agent along with a Copy Writer Chat Completion Agent to         #
# complete a task.                                                #
###################################################################


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id, env_file_path="../../.env",))
    return kernel


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "##approved##" in history[-1].content.lower()


async def main():
    REVIEWER_NAME = "ArtDirector"
    REVIEWER_INSTRUCTIONS = """
    당신은 데이비드 오길비에 대한 애정에서 비롯된 카피라이팅에 대한 의견을 가진 아트 디렉터입니다.
    주어진 카피가 인쇄할 수 있는지 여부를 결정하는 것이 목표입니다.
    그렇다면 "##approved##" 되었음을 명시하세요.
    그렇지 않은 경우 예시 없이 제안된 카피를 다듬는 방법에 대한 인사이트를 제공하세요.
    """
    agent_reviewer = ChatCompletionAgent(
        service_id="artdirector",
        kernel=_create_kernel_with_chat_completion("artdirector"),
        name=REVIEWER_NAME,
        instructions=REVIEWER_INSTRUCTIONS,
    )

    COPYWRITER_NAME = "CopyWriter"
    COPYWRITER_INSTRUCTIONS = """
    당신은 10년 경력의 카피라이터이며 간결하고 건조한 유머를 구사하는 것으로 유명합니다.
    목표는 해당 분야의 전문가로서 최고의 카피를 다듬고 결정하는 것입니다.
    응답당 하나의 제안만 제공합니다.
    당면한 목표에 집중할 수 있습니다.
    잡담으로 시간을 낭비하지 마세요.
    아이디어를 구체화할 때 제안을 고려하세요.
    """
    agent_writer = ChatCompletionAgent(
        service_id="copywriter",
        kernel=_create_kernel_with_chat_completion("copywriter"),
        name=COPYWRITER_NAME,
        instructions=COPYWRITER_INSTRUCTIONS,
    )

    group_chat = AgentGroupChat(
        agents=[
            agent_writer,
            agent_reviewer,
        ],
        termination_strategy=ApprovalTerminationStrategy(
            agents=[agent_reviewer],
            maximum_iterations=10,
        ),
    )

    input = "새로운 전기차 라인의 슬로건"

    await group_chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=input))
    print(f"# User: '{input}'")

    async for content in group_chat.invoke():
        print(f"# Agent - {content.name or '*'}: '{content.content}'")

    print(f"# IS COMPLETE: {group_chat.is_complete}")


if __name__ == "__main__":
    asyncio.run(main())
