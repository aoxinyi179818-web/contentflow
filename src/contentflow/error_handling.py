"""Translate expected technical failures into actionable product messages."""

import sqlite3
from dataclasses import dataclass

from openai import APITimeoutError, AuthenticationError, OpenAIError

from contentflow.adapter import AdapterConfigurationError
from contentflow.agents.research import (
    ResearchConfigurationError,
    ResearchIterationLimitError,
    SearchTimeoutError,
    ToolCallValidationError,
)
from contentflow.agents.visual import VisualPlannerConfigurationError
from contentflow.config import SettingsConfigurationError
from contentflow.database.projects import DatabaseUrlError
from contentflow.deepseek_hello import DeepSeekConfigurationError
from contentflow.editor import EditorConfigurationError
from contentflow.input_validation import TopicInputError
from contentflow.planner import PlannerConfigurationError
from contentflow.packaging import PackagingConfigurationError
from contentflow.reviewer import ReviewerConfigurationError
from contentflow.rewriter import RewriterConfigurationError
from contentflow.structured import StructuredOutputError
from contentflow.writer import WriterConfigurationError


@dataclass(frozen=True)
class FailurePresentation:
    """The user-facing outcome for one expected workflow failure."""

    code: str
    title: str
    message: str
    retryable: bool


_CONFIGURATION_ERRORS = (
    AdapterConfigurationError,
    DeepSeekConfigurationError,
    EditorConfigurationError,
    PackagingConfigurationError,
    PlannerConfigurationError,
    ResearchConfigurationError,
    ReviewerConfigurationError,
    RewriterConfigurationError,
    SettingsConfigurationError,
    VisualPlannerConfigurationError,
    WriterConfigurationError,
)


def present_failure(error: Exception) -> FailurePresentation:
    """Classify known failures without exposing implementation details to users."""
    if isinstance(error, TopicInputError):
        return FailurePresentation(
            "invalid_topic",
            "请输入可用主题",
            "主题不能为空，且最多 500 个字符。",
            False,
        )
    if isinstance(error, _CONFIGURATION_ERRORS + (AuthenticationError,)):
        return FailurePresentation(
            "api_configuration",
            "模型配置不可用",
            "请检查 API Key、模型名称和服务地址后再试。",
            False,
        )
    if isinstance(error, SearchTimeoutError):
        return FailurePresentation(
            "search_timeout",
            "资料检索超时",
            "资料暂时未返回，请稍后重试；系统不会把缺少证据的内容当作事实写入。",
            True,
        )
    if isinstance(error, (APITimeoutError, TimeoutError)):
        return FailurePresentation(
            "llm_timeout",
            "AI 服务响应超时",
            "请稍后重试；若持续出现，请检查网络或适当增加超时设置。",
            True,
        )
    if isinstance(error, StructuredOutputError):
        return FailurePresentation(
            "invalid_structured_output",
            "模型结果格式异常",
            "模型返回的结构化结果不符合约定，请重试；若持续出现，请检查提示词和模型配置。",
            True,
        )
    if isinstance(error, ToolCallValidationError):
        return FailurePresentation(
            "invalid_tool_call",
            "资料检索请求无效",
            "模型发出的检索请求不符合允许的格式，已停止本次生成，请重试。",
            True,
        )
    if isinstance(error, ResearchIterationLimitError):
        return FailurePresentation(
            "research_limit",
            "资料检索已达到上限",
            "系统已停止继续检索，避免无休止调用。请缩小主题范围后重试。",
            True,
        )
    if isinstance(error, (sqlite3.Error, DatabaseUrlError)):
        return FailurePresentation(
            "database_error",
            "本地项目保存失败",
            "内容生成结果未能写入本地数据库。请检查数据目录权限和数据库地址后重试。",
            True,
        )
    if isinstance(error, (OpenAIError, OSError)):
        return FailurePresentation(
            "service_unavailable",
            "AI 服务暂不可用",
            "请检查网络连接和服务状态后重试。",
            True,
        )
    return FailurePresentation(
        "unexpected",
        "生成未完成",
        "发生了未预期的错误。",
        False,
    )
