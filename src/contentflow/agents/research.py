"""A bounded Tool Calling loop for the future Research Agent."""

import json
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from contentflow.config import Settings
from contentflow.llm_client import create_deepseek_client
from contentflow.observability import (
    current_run_id,
    log_event,
    new_run_id,
    record_llm_call,
    record_llm_usage,
    run_context,
)
from contentflow.tools.local_research import (
    ResearchSource,
    SearchArguments,
    search_research_knowledge,
)

SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_research_knowledge",
        "description": "在本地演示资料中检索与研究问题相关的来源。返回的是演示语料，不是实时网络搜索结果。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "要检索的具体信息缺口"},
                "max_results": {"type": "integer", "description": "返回条数，范围 1 到 5"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}


class ResearchAgentError(RuntimeError):
    """Base error for a bounded research Tool Calling run."""


class ToolCallValidationError(ResearchAgentError):
    """Raised when the model requests an unknown tool or invalid arguments."""


class ResearchIterationLimitError(ResearchAgentError):
    """Raised when the model keeps requesting tools past the allowed budget."""


class ResearchConfigurationError(ResearchAgentError):
    """Raised when the configured provider cannot run the standalone agent."""


class SearchTimeoutError(ResearchAgentError):
    """Raised when a research tool does not return before its time budget."""


class ToolCallRecord(BaseModel):
    """Auditable record of a single executed tool call."""

    model_config = ConfigDict(extra="forbid")

    tool_call_id: str
    tool_name: str
    arguments: SearchArguments
    source_count: int


class ResearchResult(BaseModel):
    """Output of the standalone Tool Calling exercise."""

    model_config = ConfigDict(extra="forbid")

    answer: str
    sources: list[ResearchSource] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class ChatCompletions(Protocol):
    def create(self, **kwargs: Any) -> Any: ...


class ResearchClient(Protocol):
    class Chat(Protocol):
        completions: ChatCompletions

    chat: Chat


@dataclass(frozen=True)
class ExecutedToolCall:
    record: ToolCallRecord
    sources: list[ResearchSource]


def build_research_messages(question: str) -> list[dict[str, Any]]:
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("question must not be empty")
    return [
        {
            "role": "system",
            "content": (
                "你是 ContentFlow 的研究助手。需要资料时调用工具。"
                "只依据工具结果总结，并用 [source_id] 标注依据。"
                "工具返回的是演示语料，不得声称完成了实时网络搜索。"
            ),
        },
        {"role": "user", "content": normalized_question},
    ]


def _assistant_message(message: Any) -> dict[str, Any]:
    tool_calls = message.tool_calls or []
    payload: dict[str, Any] = {"role": "assistant", "content": message.content or ""}
    if tool_calls:
        payload["tool_calls"] = [
            {
                "id": call.id,
                "type": call.type,
                "function": {"name": call.function.name, "arguments": call.function.arguments},
            }
            for call in tool_calls
        ]
    return payload


def _execute_tool_call(call: Any, *, run_id: str | None = None) -> ExecutedToolCall:
    if call.function.name != "search_research_knowledge":
        raise ToolCallValidationError(f"Unknown tool requested: {call.function.name}")
    try:
        arguments = SearchArguments.model_validate_json(call.function.arguments)
    except (ValidationError, ValueError) as error:
        raise ToolCallValidationError("Tool arguments do not match the allowed schema.") from error

    active_run_id = run_id or new_run_id()
    log_event(
        "tool_call_start",
        run_id=active_run_id,
        tool=call.function.name,
        query_length=len(arguments.query),
    )
    try:
        sources = search_research_knowledge(arguments)
    except TimeoutError as error:
        log_event(
            "tool_call_error",
            run_id=active_run_id,
            tool=call.function.name,
            error_type=type(error).__name__,
        )
        raise SearchTimeoutError("Research search exceeded its time budget.") from error
    log_event(
        "tool_call_end",
        run_id=active_run_id,
        tool=call.function.name,
        source_count=len(sources),
    )
    return ExecutedToolCall(
        record=ToolCallRecord(
            tool_call_id=call.id,
            tool_name=call.function.name,
            arguments=arguments,
            source_count=len(sources),
        ),
        sources=sources,
    )


def run_research_agent(
    question: str,
    *,
    settings: Settings | None = None,
    client: ResearchClient | None = None,
    max_iterations: int = 3,
) -> ResearchResult:
    """Run a validated model-tool loop, bounded by the number of model rounds."""
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")
    messages = build_research_messages(question)
    active_settings = settings or Settings.from_env()
    active_client = client or create_deepseek_client(
        active_settings,
        consumer_name="Research Agent",
        error_type=ResearchConfigurationError,
    )
    run_id = current_run_id() or new_run_id()
    log_event("agent_start", run_id=run_id, agent="research")
    source_by_id: dict[str, ResearchSource] = {}
    records: list[ToolCallRecord] = []

    for _ in range(max_iterations):
        with run_context(run_id):
            record_llm_call(run_id, node="research_agent")
            response = active_client.chat.completions.create(
                model=active_settings.llm_model,
                messages=messages,
                tools=[SEARCH_TOOL_SCHEMA],
                tool_choice="auto",
                max_tokens=1200,
            )
            record_llm_usage(response, node="research_agent")
        message = response.choices[0].message
        tool_calls = message.tool_calls or []
        messages.append(_assistant_message(message))
        if not tool_calls:
            answer = (message.content or "").strip()
            if not answer:
                raise ResearchAgentError("Research Agent returned an empty final answer.")
            result = ResearchResult(
                answer=answer, sources=list(source_by_id.values()), tool_calls=records
            )
            log_event(
                "agent_end",
                run_id=run_id,
                agent="research",
                source_count=len(result.sources),
                tool_call_count=len(result.tool_calls),
            )
            return result

        for call in tool_calls:
            executed = _execute_tool_call(call, run_id=run_id)
            records.append(executed.record)
            for source in executed.sources:
                source_by_id[source.source_id] = source
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(
                        [source.model_dump() for source in executed.sources], ensure_ascii=False
                    ),
                }
            )

    error = ResearchIterationLimitError(f"Research Agent exceeded {max_iterations} tool-call rounds.")
    log_event("agent_error", run_id=run_id, agent="research", error_type=type(error).__name__)
    raise error
