"""Fixed-corpus evaluation tests for local RAG configurations."""

from pathlib import Path

from contentflow.rag.evaluation import (
    RetrievalVariant,
    evaluate_no_rag,
    evaluate_variant,
    load_evaluation_dataset,
)
from contentflow.rag.retriever import ChunkingConfig

DATASET_PATH = Path("data/rag_evaluation_cases.json")


def test_fixed_dataset_comparison_shows_retrieval_evidence_coverage() -> None:
    sources, cases = load_evaluation_dataset(DATASET_PATH)

    no_rag = evaluate_no_rag(cases)
    report = evaluate_variant(
        sources,
        cases,
        RetrievalVariant(name="default_top_1", chunking=ChunkingConfig(), top_k=1),
    )

    assert no_rag.source_hit_at_k == 0.0
    assert report.source_hit_at_k == 1.0
    assert report.mean_reciprocal_rank == 1.0
    assert report.no_evidence_accuracy == 1.0


def test_chunk_size_and_top_k_variants_keep_case_results_traceable() -> None:
    sources, cases = load_evaluation_dataset(DATASET_PATH)
    variants = [
        RetrievalVariant(
            name="small_top_1", chunking=ChunkingConfig(chunk_size=80, overlap=20), top_k=1
        ),
        RetrievalVariant(
            name="wide_top_3", chunking=ChunkingConfig(chunk_size=240, overlap=40), top_k=3
        ),
    ]

    reports = [evaluate_variant(sources, cases, variant) for variant in variants]

    assert all(len(report.cases) == 5 for report in reports)
    assert all(report.source_hit_at_k == 1.0 for report in reports)
    assert all(report.cases[-1].retrieved_source_ids == [] for report in reports)
