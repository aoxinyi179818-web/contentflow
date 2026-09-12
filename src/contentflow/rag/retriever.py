"""A small local RAG pipeline with deterministic embeddings.

This module deliberately uses an in-memory index and hashing embeddings.  It
teaches the full data flow without an external vector database or embedding API.
Both can be replaced later through the EmbeddingModel protocol.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from contentflow.tools.local_research import ResearchSource


class RetrievalInputError(ValueError):
    """Raised when a retrieval request cannot be interpreted safely."""


class ChunkingConfig(BaseModel):
    """Explicit, testable controls for turning source text into chunks."""

    model_config = ConfigDict(extra="forbid")

    chunk_size: int = Field(default=180, ge=40, le=2_000)
    overlap: int = Field(default=30, ge=0, le=1_000)

    @model_validator(mode="after")
    def require_overlap_smaller_than_chunk(self) -> ChunkingConfig:
        if self.overlap >= self.chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        return self


class DocumentRecord(BaseModel):
    """A cleaned research source ready to be split and indexed."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    text: str = Field(min_length=1)


class ChunkRecord(BaseModel):
    """One traceable unit stored in the retrieval index."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    text: str = Field(min_length=1)
    chunk_index: int = Field(ge=0)
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)


class EvidenceChunk(ChunkRecord):
    """A retrieved chunk plus the score used for ranking."""

    score: float = Field(ge=0.0, le=1.0)


class EmbeddingModel(Protocol):
    """A replaceable embedding boundary for a future model-backed implementation."""

    def embed(self, text: str) -> list[float]: ...


@dataclass(frozen=True)
class HashingEmbedding:
    """Deterministic character-aware embeddings appropriate for local tests only."""

    dimensions: int = 256

    def __post_init__(self) -> None:
        if self.dimensions < 8:
            raise ValueError("dimensions must be at least 8")

    def embed(self, text: str) -> list[float]:
        tokens = _tokenize(text)
        vector = [0.0] * self.dimensions
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            encoded = int.from_bytes(digest, "big")
            index = encoded % self.dimensions
            vector[index] += 1.0 if encoded & 1 else -1.0
        return _normalize(vector)


@dataclass(frozen=True)
class _IndexedChunk:
    chunk: ChunkRecord
    vector: list[float]

    tokens: frozenset[str]


class InMemoryRetriever:
    """Search an in-memory chunk collection through cosine similarity."""

    def __init__(
        self, indexed_chunks: Sequence[_IndexedChunk], embedding_model: EmbeddingModel
    ) -> None:
        self._indexed_chunks = tuple(indexed_chunks)
        self._embedding_model = embedding_model

    @property
    def chunk_count(self) -> int:
        return len(self._indexed_chunks)

    def search(self, query: str, *, top_k: int = 3) -> list[EvidenceChunk]:
        normalized_query = _clean_text(query)
        if not normalized_query:
            raise RetrievalInputError("query must not be empty")
        if not 1 <= top_k <= 10:
            raise RetrievalInputError("top_k must be between 1 and 10")

        query_tokens = frozenset(_tokenize(normalized_query))
        query_vector = self._embedding_model.embed(normalized_query)
        scored = [
            (
                max(0.0, _dot_product(query_vector, item.vector))
                if _has_meaningful_token_overlap(query_tokens, item.tokens)
                else 0.0,
                item.chunk,
            )
            for item in self._indexed_chunks
        ]
        ranked = sorted(scored, key=lambda item: (-item[0], item[1].source_id, item[1].chunk_index))
        return [
            EvidenceChunk(**chunk.model_dump(), score=round(score, 6))
            for score, chunk in ranked
            if score > 0
        ][:top_k]


def build_retriever(
    sources: Sequence[ResearchSource],
    *,
    chunking: ChunkingConfig | None = None,
    embedding_model: EmbeddingModel | None = None,
) -> InMemoryRetriever:
    """Clean Tool Calling sources, chunk them, and build a local similarity index."""
    active_chunking = chunking or ChunkingConfig()
    active_embedding_model = embedding_model or HashingEmbedding()
    documents = [_source_to_document(source) for source in sources]
    chunks = [
        chunk for document in documents for chunk in chunk_document(document, active_chunking)
    ]
    indexed_chunks = [
        _IndexedChunk(
            chunk=chunk,
            vector=active_embedding_model.embed(chunk.text),
            tokens=frozenset(_tokenize(chunk.text)),
        )
        for chunk in chunks
    ]
    return InMemoryRetriever(indexed_chunks, active_embedding_model)


def chunk_document(document: DocumentRecord, config: ChunkingConfig) -> list[ChunkRecord]:
    """Split a cleaned document into overlapping, source-traceable windows."""
    chunks: list[ChunkRecord] = []
    step = config.chunk_size - config.overlap
    for chunk_index, start_char in enumerate(range(0, len(document.text), step)):
        end_char = min(start_char + config.chunk_size, len(document.text))
        chunk_text = document.text[start_char:end_char].strip()
        if chunk_text:
            chunks.append(
                ChunkRecord(
                    chunk_id=f"{document.source_id}:{chunk_index}",
                    source_id=document.source_id,
                    title=document.title,
                    url=document.url,
                    text=chunk_text,
                    chunk_index=chunk_index,
                    start_char=start_char,
                    end_char=end_char,
                )
            )
        if end_char == len(document.text):
            break
    return chunks


def format_writer_context(evidence: Sequence[EvidenceChunk]) -> str:
    """Format retrieved evidence so the Writer cannot lose source attribution."""
    if not evidence:
        return "未检索到足以支撑写作的资料。请避免把未提供证据的内容写成确定事实。"
    blocks = ["以下资料仅可支持其对应主张，并应保留 [source_id] 标注："]
    for item in evidence:
        blocks.append(
            f"[{item.source_id}] {item.title} | {item.url}\n"
            f"片段 {item.chunk_index + 1}，相关度 {item.score:.3f}\n{item.text}"
        )
    return "\n\n".join(blocks)


def _source_to_document(source: ResearchSource) -> DocumentRecord:
    text = _clean_text(source.summary)
    if not text:
        raise RetrievalInputError(f"source {source.source_id!r} has no indexable text")
    return DocumentRecord(
        source_id=source.source_id,
        title=_require_clean_text(source.title, "title"),
        url=_require_clean_text(source.url, "url"),
        text=text,
    )


def _require_clean_text(value: str, field_name: str) -> str:
    normalized = _clean_text(value)
    if not normalized:
        raise RetrievalInputError(f"{field_name} must not be empty")
    return normalized


def _has_meaningful_token_overlap(
    query_tokens: frozenset[str], chunk_tokens: frozenset[str]
) -> bool:
    shared_tokens = query_tokens & chunk_tokens
    if not shared_tokens:
        return False
    if any(token.isascii() and len(token) > 1 for token in shared_tokens):
        return True

    return len(shared_tokens) >= 2


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _tokenize(text: str) -> list[str]:
    normalized = _clean_text(text).lower()
    latin_words = re.findall(r"[a-z0-9]+", normalized)
    chinese_characters = re.findall(r"[\u4e00-\u9fff]", normalized)
    return latin_words + chinese_characters


def _normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    return [value / magnitude for value in vector] if magnitude else vector


def _dot_product(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(
        left_value * right_value for left_value, right_value in zip(left, right, strict=True)
    )
