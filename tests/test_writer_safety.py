from contentflow.writer import build_writer_messages


def test_writer_prompt_requires_official_verification_without_research() -> None:
    messages = build_writer_messages("# 内容计划\n\n## 第一章\n说明 AI 使用边界。")

    assert "当前没有 Research 上下文" in messages[0]["content"]
    assert "查阅所用工具的官方隐私说明" in messages[0]["content"]
    assert "当前 Prompt 版本为 V2" in messages[0]["content"]
    assert "具体产品、平台、学校或课程名称" in messages[0]["content"]
    assert "当前 Prompt 版本为 V3" in messages[0]["content"]
    assert "第一个非空行必须是一级 Markdown 标题" in messages[0]["content"]
