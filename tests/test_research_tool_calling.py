"""Tests for the bounded standalone Research Tool Calling loop."""

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from contentflow.agents.research import (
    ResearchIterationLimitError,
    ToolCallValidationError,
    run_research_agent,
)
from contentflow.config import Settings
from contentflow.tools.local_research import SearchArguments, search_research_knowledge


@dataclass
class FakeFunction:
    name: str
    arguments: str


@dataclass
class FakeToolCall:
    id: str
    function: FakeFunction
    type: str = "function"


@dataclass
class FakeMessage:
    content: str | None
    tool_calls: list[FakeToolCall] | None = None


class FakeCompletions:
    def __init__(self, messages: list[FakeMessage]) -> None:
        self.messages = messages
        self.requests: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.requests.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=self.messages.pop(0))])


class FakeClient:
    def __init__(self, messages: list[FakeMessage]) -> None:
        self.completions = FakeCompletions(messages)
        self.chat = SimpleNamespace(completions=self.completions)


def test_local_search_returns_only_demonstration_sources() -> None:
    sources = search_research_knowledge(SearchArguments(query="学习计划", max_results=2))

    assert sources
    assert len(sources) <= 2
    assert all(source.source_type == "demo_seed" for source in sources)


def test_agent_executes_tool_and_returns_sources() -> None:
    client = FakeClient(
        [
            FakeMessage(
                content=None,
                tool_calls=[
                    FakeToolCall(
                        id="call_1",
                        function=FakeFunction(
                            name="search_research_knowledge",
                            arguments='{"query":"学习计划","max_results":2}',
                        ),
                    )
                ],
            ),
            FakeMessage(content="可以先拆分任务并安排自测 [study-planning]。"),
        ]
    )

    result = run_research_agent(
        "如何制定复习计划？",
        settings=Settings(llm_model="test-model"),
        client=client,
    )

    assert result.answer.endswith("[study-planning]。")
    assert result.tool_calls[0].arguments.query == "学习计划"
    assert result.sources
    second_request_messages = client.completions.requests[1]["messages"]
    assert any(message["role"] == "tool" for message in second_request_messages)


def test_agent_rejects_invalid_tool_arguments() -> None:
    client = FakeClient(
        [
            FakeMessage(
                content=None,
                tool_calls=[
                    FakeToolCall(
                        id="call_1",
                        function=FakeFunction(
                            name="search_research_knowledge",
                            arguments='{"query":"学习计划","max_results":99}',
                        ),
                    )
                ],
            )
        ]
    )

    with pytest.raises(ToolCallValidationError):
        run_research_agent("测试", settings=Settings(llm_model="test-model"), client=client)


def test_agent_stops_after_iteration_budget() -> None:
    repeated_call = FakeMessage(
        content=None,
        tool_calls=[
            FakeToolCall(
                id="call_1",
                function=FakeFunction(
                    name="search_research_knowledge",
                    arguments='{"query":"学习计划"}',
                ),
            )
        ],
    )
    client = FakeClient([repeated_call])

    with pytest.raises(ResearchIterationLimitError, match="exceeded 1"):
        run_research_agent(
            "测试",
            settings=Settings(llm_model="test-model"),
            client=client,
            max_iterations=1,
        )
