"""Fixed, source-level evaluation for the local RAG retriever."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from contentflow.rag.retriever import ChunkingConfig, build_retriever
from contentflow.safe_files import read_allowed_text
from contentflow.tools.local_research import ResearchSource


class EvaluationCase(BaseModel):
    """One query with a known expected source, or an expected no-evidence result."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    expected_source_id: str | None = None


class RetrievalVariant(BaseModel):
    """A reproducible retrieval configuration under comparison."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    chunking: ChunkingConfig
    top_k: int = Field(ge=1, le=10)


class CaseEvaluation(BaseModel):
    """Observable retrieval outcome for one fixed case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    expected_source_id: str | None
    retrieved_source_ids: list[str]
    reciprocal_rank: float = Field(ge=0.0, le=1.0)
    passed: bool


class EvaluationReport(BaseModel):
    """Aggregate evidence metrics for a baseline or one retrieval configuration."""

    model_config = ConfigDict(extra="forbid")

    variant_name: str
    mode: Literal["no_rag", "rag"]
    source_hit_at_k: float = Field(ge=0.0, le=1.0)
    mean_reciprocal_rank: float = Field(ge=0.0, le=1.0)
    no_evidence_accuracy: float = Field(ge=0.0, le=1.0)
    cases: list[CaseEvaluation]


def load_evaluation_dataset(path: Path) -> tuple[list[ResearchSource], list[EvaluationCase]]:
    """Load versioned demonstration sources and queries from JSON."""
    data_directory = Path(__file__).resolve().parents[3] / "data"
    payload = json.loads(
        read_allowed_text(path, allowed_root=data_directory, allowed_suffixes={".json"})
    )
    sources = [ResearchSource.model_validate(item) for item in payload["sources"]]
    cases = [EvaluationCase.model_validate(item) for item in payload["cases"]]
    if not sources or not cases:
        raise ValueError("evaluation dataset must contain at least one source and one case")
    return sources, cases


def evaluate_no_rag(cases: list[EvaluationCase]) -> EvaluationReport:
    """Record the evidence baseline when the Writer receives no retrieved context."""
    return _aggregate_report(
        "no_rag_baseline", "no_rag", [_evaluate_case(case, []) for case in cases]
    )


def evaluate_variant(
    sources: list[ResearchSource], cases: list[EvaluationCase], variant: RetrievalVariant
) -> EvaluationReport:
    """Evaluate one chunking and Top-K configuration against fixed source targets."""
    retriever = build_retriever(sources, chunking=variant.chunking)
    outcomes = []
    for case in cases:
        evidence = retriever.search(case.query, top_k=variant.top_k)
        outcomes.append(
            _evaluate_case(case, list(dict.fromkeys(item.source_id for item in evidence)))
        )
    return _aggregate_report(variant.name, "rag", outcomes)


def _evaluate_case(case: EvaluationCase, source_ids: list[str]) -> CaseEvaluation:
    if case.expected_source_id is None:
        return CaseEvaluation(
            case_id=case.case_id,
            expected_source_id=None,
            retrieved_source_ids=source_ids,
            reciprocal_rank=1.0 if not source_ids else 0.0,
            passed=not source_ids,
        )
    rank = (
        source_ids.index(case.expected_source_id) + 1
        if case.expected_source_id in source_ids
        else 0
    )
    return CaseEvaluation(
        case_id=case.case_id,
        expected_source_id=case.expected_source_id,
        retrieved_source_ids=source_ids,
        reciprocal_rank=1.0 / rank if rank else 0.0,
        passed=rank > 0,
    )


def _aggregate_report(
    variant_name: str, mode: Literal["no_rag", "rag"], outcomes: list[CaseEvaluation]
) -> EvaluationReport:
    evidence_cases = [outcome for outcome in outcomes if outcome.expected_source_id is not None]
    no_evidence_cases = [outcome for outcome in outcomes if outcome.expected_source_id is None]
    return EvaluationReport(
        variant_name=variant_name,
        mode=mode,
        source_hit_at_k=_average([float(outcome.passed) for outcome in evidence_cases]),
        mean_reciprocal_rank=_average([outcome.reciprocal_rank for outcome in evidence_cases]),
        no_evidence_accuracy=_average([float(outcome.passed) for outcome in no_evidence_cases]),
        cases=outcomes,
    )


def _average(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 1.0
