# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import (
    KernelFunctionSelectionStrategy,
    KernelFunctionTerminationStrategy,
)
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.functions import KernelFunctionFromPrompt
from semantic_kernel.agents.strategies.selection.sequential_selection_strategy import SequentialSelectionStrategy

###################################################################
# The following sample demonstrates how to create a simple,       #
# agent group chat that utilizes An Art Director Chat Completion  #
# Agent along with a Copy Writer Chat Completion Agent to         #
# complete a task. The sample also shows how to specify a Kernel  #
# Function termination and selection strategy to determine when   #
# to end the chat or how to select the next agent to take a turn  #
# in the conversation.                                            #
###################################################################


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id, env_file_path="../../.env",))
    return kernel


async def main():
    REVIEWER_NAME = "ArtDirector"
    REVIEWER_INSTRUCTIONS = """
    귀하는 데이비드 오길비에 대한 애정에서 비롯된 카피라이팅에 대한 의견을 가진 아트 디렉터입니다.
    주어진 카피가 인쇄할 수 있는지 여부를 판단하는 것이 목표입니다.
    그렇다면 승인되었음을 명시하세요.
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

    termination_function = KernelFunctionFromPrompt(
        function_name="termination",
        prompt="""
        Determine if the copy has been approved.  If so, respond with a single word: yes

        History:
        {{$history}}
        """,
    )

    selection_function = KernelFunctionFromPrompt(
        function_name="selection",
        prompt=f"""
        가장 최근 참가자를 기준으로 대화에서 다음 차례를 맡을 참가자를 결정합니다.
        다음 차례를 맡을 참가자의 이름만 기재합니다.
        한 참가자가 연속으로 두 번 이상 차례를 가져갈 수 없습니다.
        
        이 참가자 중에서만 선택하세요:
        - {REVIEWER_NAME}
        - {COPYWRITER_NAME}
        
        다음 참가자를 선정할 때는 항상 다음 규칙을 따르세요:
        - After user input, it is {COPYWRITER_NAME}'s turn.
        - After {COPYWRITER_NAME} replies, it is {REVIEWER_NAME}'s turn.
        - After {REVIEWER_NAME} provides feedback, it is {COPYWRITER_NAME}'s turn.

        History:
        {{{{$history}}}}
        """,
    )

    chat = AgentGroupChat(
        agents=[agent_writer, agent_reviewer],
        termination_strategy=
        KernelFunctionTerminationStrategy(
            agents=[agent_reviewer],
            function=termination_function,
            kernel=_create_kernel_with_chat_completion("termination"),
            result_parser=lambda result: str(result.value[0]).lower() == "yes",
            history_variable_name="history",
            maximum_iterations=10,
        ),
        selection_strategy=SequentialSelectionStrategy()
        
        # KernelFunctionSelectionStrategy(
        #     function=selection_function,
        #     kernel=_create_kernel_with_chat_completion("selection"),
        #     result_parser=lambda result: str(result.value[0]) if result.value is not None else COPYWRITER_NAME,
        #     agent_variable_name="agents",
        #     history_variable_name="history",
        # ),
    )

    input = "새로운 전기차 라인의 슬로건."

    await chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=input))
    print(f"# User: '{input}'")

    async for content in chat.invoke():
        print(f"# Agent - {content.name or '*'}: '{content.content}'")

    print(f"# IS COMPLETE: {chat.is_complete}")


if __name__ == "__main__":
    asyncio.run(main())
