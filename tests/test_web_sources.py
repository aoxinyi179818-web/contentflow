import socket

import httpx
import pytest

from contentflow.web_sources import (
    WebReferenceError,
    collect_web_references,
    fetch_web_source,
    format_web_reference_context,
    parse_reference_urls,
    validate_public_url,
)


def _public_resolver(_hostname: str, _port: int | None):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]


def test_parse_reference_urls_enforces_the_small_source_budget() -> None:
    assert parse_reference_urls("https://a.example\nhttps://b.example") == (
        "https://a.example",
        "https://b.example",
    )
    with pytest.raises(WebReferenceError, match="最多"):
        parse_reference_urls("\n".join(f"https://{index}.example" for index in range(4)))


def test_collection_reports_an_over_budget_input_without_breaking_the_draft_flow() -> None:
    result = collect_web_references("\n".join(f"https://{index}.example" for index in range(4)))

    assert not result.sources
    assert "最多" in result.failures[0]


def test_validate_public_url_rejects_local_and_credentialed_urls() -> None:
    with pytest.raises(WebReferenceError, match="本机"):
        validate_public_url("http://localhost:8501")
    with pytest.raises(WebReferenceError, match="账号"):
        validate_public_url("https://user:password@example.com", resolver=_public_resolver)


def test_fetch_web_source_extracts_visible_html_and_preserves_url() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=(
                "<html><head><title>官方指南</title><script>ignore me</script></head>"
                "<body><h1>内容创作</h1><p>这是用于写作的公开正文资料，包含可验证信息。</p></body></html>"
            ),
            request=request,
        )
    )
    with httpx.Client(transport=transport) as client:
        source = fetch_web_source(
            "https://example.com/guide", source_id="user-url-1", client=client, resolver=_public_resolver
        )

    assert source.title == "官方指南"
    assert source.url == "https://example.com/guide"
    assert "内容创作" in source.summary
    assert "ignore me" not in source.summary
    assert source.source_type == "user_url"


def test_fetch_web_source_validates_redirect_destination_before_requesting_it() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            302, headers={"location": "http://127.0.0.1/private"}, request=request
        )
    )
    with httpx.Client(transport=transport) as client, pytest.raises(WebReferenceError, match="本机"):
        fetch_web_source(
            "https://example.com/redirect", source_id="user-url-1", client=client, resolver=_public_resolver
        )


def test_collection_keeps_successful_sources_and_reports_failed_urls() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "ok.example":
            return httpx.Response(
                200,
                headers={"content-type": "text/plain"},
                content="公开网页正文包含足够的信息，用于验证多来源处理。",
                request=request,
            )
        return httpx.Response(500, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = collect_web_references(
            "https://ok.example/a\nhttps://bad.example/b", client=client, resolver=_public_resolver
        )

    assert len(result.sources) == 1
    assert len(result.failures) == 1
    context = format_web_reference_context(result.sources)
    assert "[user-url-1]" in context
    assert "ok.example" in context
