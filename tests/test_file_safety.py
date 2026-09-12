"""Tests for allow-listed repository asset reads and baseline secret hygiene."""

from pathlib import Path

import pytest

from contentflow.safe_files import (
    ApprovedFileNotFoundError,
    UnsafeFilePathError,
    read_allowed_text,
)


def test_read_allowed_text_reads_only_files_under_the_approved_root(tmp_path) -> None:
    allowed_root = tmp_path / "data"
    allowed_root.mkdir()
    dataset = allowed_root / "cases.json"
    dataset.write_text('{"cases": []}', encoding="utf-8")

    assert read_allowed_text(dataset, allowed_root=allowed_root, allowed_suffixes={".json"}) == '{"cases": []}'


def test_read_allowed_text_rejects_path_escape_and_unapproved_suffix(tmp_path) -> None:
    allowed_root = tmp_path / "data"
    allowed_root.mkdir()
    outside_file = tmp_path / "secret.json"
    outside_file.write_text("secret", encoding="utf-8")
    markdown_file = allowed_root / "notes.md"
    markdown_file.write_text("notes", encoding="utf-8")

    with pytest.raises(UnsafeFilePathError, match="approved directory"):
        read_allowed_text(outside_file, allowed_root=allowed_root, allowed_suffixes={".json"})
    with pytest.raises(UnsafeFilePathError, match="File type"):
        read_allowed_text(markdown_file, allowed_root=allowed_root, allowed_suffixes={".json"})


def test_read_allowed_text_reports_missing_file_without_exposing_a_path(tmp_path) -> None:
    allowed_root = tmp_path / "data"
    allowed_root.mkdir()

    with pytest.raises(ApprovedFileNotFoundError, match="Approved file"):
        read_allowed_text(
            allowed_root / "missing.json", allowed_root=allowed_root, allowed_suffixes={".json"}
        )


def test_gitignore_excludes_local_environment_secrets() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8").splitlines()

    assert ".env" in gitignore
