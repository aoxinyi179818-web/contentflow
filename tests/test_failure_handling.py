"""Tests for user-facing handling of expected ContentFlow failures."""

import sqlite3

import pytest

from contentflow.agents.research import ResearchIterationLimitError, SearchTimeoutError
from contentflow.config import SettingsConfigurationError
from contentflow.error_handling import present_failure
from contentflow.input_validation import MAX_TOPIC_LENGTH, TopicInputError, validate_topic
from contentflow.structured import StructuredOutputError
from contentflow.writer import WriterConfigurationError


def test_topic_validation_normalizes_and_rejects_empty_or_oversized_topics() -> None:
    assert validate_topic("  AI 学习计划  ") == "AI 学习计划"

    with pytest.raises(TopicInputError, match="empty"):
        validate_topic("   ")
    with pytest.raises(TopicInputError, match="exceed"):
        validate_topic("a" * (MAX_TOPIC_LENGTH + 1))


@pytest.mark.parametrize(
    ("error", "code", "title"),
    [
        (TopicInputError("empty"), "invalid_topic", "请输入可用主题"),
        (WriterConfigurationError("missing API key"), "api_configuration", "模型配置不可用"),
        (SettingsConfigurationError("invalid timeout"), "api_configuration", "模型配置不可用"),
        (TimeoutError(), "llm_timeout", "AI 服务响应超时"),
        (SearchTimeoutError("slow search"), "search_timeout", "资料检索超时"),
        (StructuredOutputError("invalid JSON"), "invalid_structured_output", "模型结果格式异常"),
        (ResearchIterationLimitError("limit"), "research_limit", "资料检索已达到上限"),
        (sqlite3.OperationalError("locked"), "database_error", "本地项目保存失败"),
    ],
)
def test_expected_failures_have_stable_user_facing_presentations(
    error: Exception, code: str, title: str
) -> None:
    presentation = present_failure(error)

    assert presentation.code == code
    assert presentation.title == title
    assert presentation.message


def test_unexpected_failures_remain_visible_to_developers() -> None:
    assert present_failure(KeyError("unexpected")).code == "unexpected"
