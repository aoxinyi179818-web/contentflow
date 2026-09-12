"""Tests for the local, traceable RAG retrieval pipeline."""

import pytest
from pydantic import ValidationError

from contentflow.rag.retriever import (
    ChunkingConfig,
    DocumentRecord,
    RetrievalInputError,
    build_retriever,
    chunk_document,
    format_writer_context,
)
from contentflow.tools.local_research import ResearchSource

SOURCES = [
    ResearchSource(
        source_id="retrieval-practice",
        title="主动回忆的练习设计",
        url="https://example.invalid/research/retrieval-practice",
        summary="用不看笔记的自测问题检查理解，再根据遗漏内容安排下一轮复习。",
    ),
    ResearchSource(
        source_id="privacy-boundary",
        title="学习工具中的隐私边界",
        url="https://example.invalid/research/privacy-boundary",
        summary="上传课程材料前先确认文件是否包含个人信息、课程限制或不可分享内容。",
    ),
]


def test_chunk_document_keeps_traceability_and_overlap() -> None:
    document = DocumentRecord(
        source_id="source-a",
        title="标题",
        url="https://example.invalid/a",
        text="甲" * 100,
    )

    chunks = chunk_document(document, ChunkingConfig(chunk_size=40, overlap=10))

    assert len(chunks) == 3
    assert chunks[0].source_id == "source-a"
    assert chunks[1].start_char == 30
    assert chunks[0].text[-10:] == chunks[1].text[:10]


def test_retriever_returns_relevant_source_before_unrelated_source() -> None:
    retriever = build_retriever(SOURCES)

    evidence = retriever.search("如何通过主动回忆和自测安排复习？", top_k=2)

    assert evidence[0].source_id == "retrieval-practice"
    assert evidence[0].score > 0
    assert retriever.chunk_count == 2


def test_writer_context_includes_source_identity_and_empty_result_boundary() -> None:
    retriever = build_retriever(SOURCES)
    evidence = retriever.search("个人信息上传", top_k=1)

    context = format_writer_context(evidence)

    assert "[privacy-boundary]" in context
    assert "example.invalid" in context
    assert "未检索到" in format_writer_context([])


def test_invalid_chunk_and_retrieval_arguments_are_rejected() -> None:
    with pytest.raises(ValidationError, match="overlap"):
        ChunkingConfig(chunk_size=40, overlap=40)

    retriever = build_retriever(SOURCES)
    with pytest.raises(RetrievalInputError, match="query"):
        retriever.search("  ")
    with pytest.raises(RetrievalInputError, match="top_k"):
        retriever.search("复习", top_k=11)
