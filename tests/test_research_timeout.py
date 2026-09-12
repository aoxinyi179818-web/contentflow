"""Regression test for the Research Agent search timeout boundary."""

from types import SimpleNamespace

import pytest

from contentflow.agents import research


def test_search_timeout_becomes_a_domain_error(monkeypatch: pytest.MonkeyPatch) -> None:
    call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(
            name="search_research_knowledge",
            arguments='{"query":"学习计划"}',
        ),
    )

    def slow_search(arguments: object) -> None:
        raise TimeoutError("simulated search timeout")

    monkeypatch.setattr(research, "search_research_knowledge", slow_search)

    with pytest.raises(research.SearchTimeoutError, match="time budget"):
        research._execute_tool_call(call)
