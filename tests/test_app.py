"""UI smoke tests that never call the live LLM workflow."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_app_renders_chinese_workspace() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()

    assert not app.exception
    assert app.title[0].value == "把一个主题，变成可审阅的内容"
    assert [button.label for button in app.button[:2]] == ["仅本次会话使用", "保存到本机 .env"]
    assert app.radio[0].options == ["开始创作", "历史项目", "内容资产", "质量评估"]
    assert app.text_area[0].label == "本次想创作什么？"
    assert [selectbox.label for selectbox in app.selectbox] == ["语气", "主创作平台", "目标篇幅", "品牌语气（可选）"]
    assert app.text_input[1].label == "目标受众"


def test_app_rejects_empty_topic_before_calling_workflow() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    app.button[2].click().run()

    assert not app.exception
    assert "请输入内容主题" in app.error[0].value


def test_app_renders_empty_project_history() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    app.radio[0].set_value("历史项目").run()

    assert not app.exception
    assert app.subheader[0].value == "项目历史"


def test_app_renders_empty_quality_overview() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    app.radio[0].set_value("质量评估").run()

    assert not app.exception
    assert app.subheader[0].value == "质量评估"


def test_app_renders_local_content_assets_workspace() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    app.radio[0].set_value("内容资产").run()

    assert not app.exception
    assert app.subheader[0].value == "内容资产"
    assert [tab.label for tab in app.tabs] == ["品牌语气", "选题与日历"]
