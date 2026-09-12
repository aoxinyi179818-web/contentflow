from contentflow.rewriter import build_rewriter_messages


def test_rewriter_prompt_forbids_unsourced_consequences_and_rules() -> None:
    messages = build_rewriter_messages("# 初稿", "# 审阅报告")
    prompt = messages[0]["content"]

    assert "不得依据常识补充" in prompt
    assert "学术不端" in prompt
    assert "数据处理规则" in prompt
