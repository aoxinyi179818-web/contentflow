import pytest

from contentflow.editor import EditorInputError, build_editor_messages, replace_selected_text


def test_editor_builds_a_scoped_rewrite_request() -> None:
    messages = build_editor_messages(
        "# 标题\n\n这是需要替换的段落。",
        "语气更简洁",
        selected_text="这是需要替换的段落。",
    )

    assert messages[0]["role"] == "system"
    assert "指定替换片段" in messages[1]["content"]
    assert "只返回这一片段" in messages[1]["content"]


def test_editor_replaces_only_one_exact_selected_excerpt() -> None:
    assert replace_selected_text("甲。乙。", "乙。", "丙。") == "甲。丙。"
    with pytest.raises(EditorInputError, match="exactly once"):
        replace_selected_text("甲。甲。", "甲。", "乙。")
    with pytest.raises(EditorInputError, match="must appear"):
        build_editor_messages("甲。", "改写", selected_text="乙。")
