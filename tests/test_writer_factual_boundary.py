from contentflow.writer import build_writer_messages


def test_writer_prompt_forbids_unverified_claim_categories() -> None:
    messages = build_writer_messages("# 内容计划\n\n## 第一章\n介绍 AI 使用边界。")
    prompt = messages[0]["content"]

    assert "严禁断言模型能力" in prompt
    assert "平台数据处理方式" in prompt
    assert "只能给出中性行动建议" in prompt
