"""UI smoke tests that never call the live LLM workflow."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_app_renders_chinese_workspace() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()

    assert not app.exception
    assert app.title[0].value == "把一个主题，变成可审阅的内容"
    assert [button.label for button in app.button[:2]] == ["仅本次会话使用", "保存到本机 .env"]
    assert app.text_area[0].label == "本次想创作什么？"


def test_app_rejects_empty_topic_before_calling_workflow() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    app.button[2].click().run()

    assert not app.exception
    assert "请输入内容主题" in app.error[0].value
