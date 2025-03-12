# Copyright (c) Microsoft. All rights reserved.

import asyncio

from pydantic import BaseModel, ValidationError

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.functions import KernelArguments

###################################################################
# The following sample demonstrates how to configure an Agent     #
# Group Chat, and invoke an agent with only a single turn.        #
# A custom termination strategy is provided where the model is    #
# to rate the user input on creativity and expressiveness         #
# and end the chat when a score of 70 or higher is provided.      #
###################################################################


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id, env_file_path="../../.env",))
    return kernel


class InputScore(BaseModel):
    """A model for the input score."""

    score: int
    notes: str


class ThresholdTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    threshold: int = 70

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        try:
            result = InputScore.model_validate_json(history[-1].content or "")
            return result.score >= self.threshold
        except ValidationError:
            return False


async def main():
    kernel = _create_kernel_with_chat_completion(service_id="tutor")

    TUTOR_NAME = "Tutor"
    TUTOR_INSTRUCTIONS = """단계별로 생각하고 창의성과 표현력에 대한 사용자 의견을 1~100점까지 평가하고 개선 방법에 대한 몇 가지 메모를 남깁니다."""  # noqa: E501

    settings = kernel.get_prompt_execution_settings_from_service_id(service_id="tutor")
    settings.response_format = InputScore

    agent = ChatCompletionAgent(
        service_id="tutor",
        kernel=kernel,
        name=TUTOR_NAME,
        instructions=TUTOR_INSTRUCTIONS,
        arguments=KernelArguments(settings=settings),
       
    )

    # Here a TerminationStrategy subclass is used that will terminate when
    # the response includes a score that is greater than or equal to 70.
    termination_strategy = ThresholdTerminationStrategy(maximum_iterations=10)

    group_chat = AgentGroupChat(termination_strategy=termination_strategy)

    user_inputs = {
        "석양은 매우 화려합니다.",
        "일몰이 산 너머로 지고 있습니다.",
        "일몰이 산 너머로 지고 하늘을 짙은 붉은 불꽃으로 가득 채우고 구름을 불태우고 있습니다.",
    }
    for user_input in user_inputs:
        await group_chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=user_input))
        print(f"# User: '{user_input}'")

        async for content in group_chat.invoke_single_turn(agent):
            print(f"# Agent - {content.name or '*'}: '{content.content}'")
            print(f"# IS COMPLETE: {group_chat.is_complete}")


if __name__ == "__main__":
    asyncio.run(main())
