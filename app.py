"""Chinese-first Streamlit interface for the ContentFlow AI MVP."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import streamlit as st

from contentflow.adapter import adapt_content
from contentflow.agents.visual import create_visual_plan
from contentflow.config import Settings, SettingsConfigurationError, save_deepseek_api_key
from contentflow.database import ProjectRepository
from contentflow.editor import rewrite_with_instruction
from contentflow.error_handling import present_failure
from contentflow.export import (
    default_export_stem,
    render_content_package_markdown,
    sanitize_export_stem,
)
from contentflow.history import format_project_label, result_from_project_record
from contentflow.models import (
    CONTENT_LENGTH_OPTIONS,
    CONTENT_PLATFORM_OPTIONS,
    CONTENT_TONE_OPTIONS,
    FEEDBACK_RATING_OPTIONS,
    TOPIC_STATUS_OPTIONS,
    ContentPreferences,
)
from contentflow.mvp import MvpResult, run_mvp
from contentflow.observability import configure_logging, log_event, new_run_id
from contentflow.packaging import generate_publishing_assets

configure_logging()

st.set_page_config(
    page_title="ContentFlow AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def apply_styles() -> None:
    """Keep the first interface intentional without introducing a component library."""
    st.markdown(
        """
        <style>
        .stApp { background: #eef3f5; color: #17232b; }
        .block-container { max-width: 1240px; padding-top: 3.5rem; padding-bottom: 4rem; }
        .eyebrow { color: #d55e4d; font-size: 0.76rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; }
        .hero-copy { max-width: 46rem; color: #52616a; font-size: 1.05rem; line-height: 1.65; margin: 0.4rem 0 1.8rem; }
        .workflow-card { background: #17232b; border-radius: 20px; color: #f7fafb; padding: 1.25rem 1.3rem; margin-bottom: 1.25rem; }
        .workflow-label { color: #aebcc3; font-size: 0.77rem; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.9rem; }
        .flow-rail { display: flex; gap: 0.4rem; align-items: stretch; }
        .flow-node { flex: 1; border: 1px solid #43515a; border-radius: 12px; padding: 0.8rem 0.7rem; min-height: 88px; }
        .flow-index { color: #f5826d; font-size: 0.72rem; font-weight: 700; }
        .flow-title { display: block; font-size: 1rem; font-weight: 700; margin: 0.32rem 0; }
        .flow-desc { color: #bfcbd0; font-size: 0.79rem; line-height: 1.35; }
        .panel-note { color: #64727a; font-size: 0.88rem; line-height: 1.55; }
        .empty-state { background: #fff; border: 1px dashed #b9c8ce; border-radius: 16px; padding: 2.4rem 1.8rem; text-align: center; color: #64727a; }
        div[data-testid="stForm"] { background: #fff; border: 1px solid #d9e2e5; border-radius: 18px; padding: 1.2rem 1.25rem 1.3rem; }
        div[data-testid="stTabs"] button { font-weight: 650; }
        .stDownloadButton button, .stFormSubmitButton button { border-radius: 10px; font-weight: 700; }
        @media (max-width: 760px) { .flow-rail { flex-direction: column; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_rail() -> None:
    """Render the actual four-stage workflow users are about to run."""
    steps = (
        ("01", "策划", "澄清受众、语气与结构"),
        ("02", "写作", "根据计划生成内容初稿"),
        ("03", "审阅", "按四个维度评估质量"),
        ("04", "修订", "依据建议完成一轮改写"),
    )
    nodes = "".join(
        (
            '<div class="flow-node">'
            f'<span class="flow-index">{index}</span>'
            f'<span class="flow-title">{title}</span>'
            f'<span class="flow-desc">{description}</span>'
            "</div>"
        )
        for index, title, description in steps
    )
    st.markdown(
        f'<section class="workflow-card"><div class="workflow-label">一次运行，四个真实节点</div>'
        f'<div class="flow-rail">{nodes}</div></section>',
        unsafe_allow_html=True,
    )


def render_api_configuration() -> None:
    """Let a local user choose a session key or explicitly save one to local .env."""
    with st.popover("API 配置", use_container_width=True):
        st.caption("仅在本机生效。输入内容不会显示在页面或日志中。")
        with st.form("api_key_configuration", border=False):
            api_key = st.text_input(
                "DeepSeek API Key",
                type="password",
                placeholder="输入你的 Key",
            )
            use_for_session = st.form_submit_button("仅本次会话使用", use_container_width=True)
            save_to_disk = st.form_submit_button("保存到本机 .env", use_container_width=True)

        if use_for_session or save_to_disk:
            try:
                session_settings = Settings().with_deepseek_api_key(api_key)
            except SettingsConfigurationError as error:
                st.error(str(error))
            else:
                st.session_state["deepseek_session_api_key"] = session_settings.deepseek_api_key
                if save_to_disk:
                    save_deepseek_api_key(session_settings.deepseek_api_key)
                    st.success("已保存到本机 .env，并在本次会话生效。")
                else:
                    st.success("已仅为本次会话配置 API Key。")

        if st.session_state.get("deepseek_session_api_key"):
            st.caption("当前会话已配置 API Key。")
            if st.button("移除本次会话 Key", use_container_width=True):
                st.session_state.pop("deepseek_session_api_key", None)
                st.success("已移除本次会话 API Key。")


def active_settings() -> Settings:
    """Load local settings and apply the optional non-persistent session override."""
    settings = Settings.from_env()
    session_key = st.session_state.get("deepseek_session_api_key")
    return settings.with_deepseek_api_key(session_key) if session_key else settings


def render_plan(result: MvpResult) -> None:
    st.caption(
        f"受众：{result.plan.audience}　·　语气：{result.plan.tone}　·　"
        f"平台：{result.plan.platform}　·　篇幅：{result.plan.target_length}"
    )
    if result.plan.scope_note:
        st.info(result.plan.scope_note)
    if result.plan.brand_voice:
        st.caption(f"品牌写作规则：{result.plan.brand_voice}")
    for order, section in enumerate(result.plan.sections, start=1):
        st.markdown(f"**{order:02d}. {section.title}**　{section.objective}")


def render_review(result: MvpResult) -> None:
    report = result.review
    score, structure, clarity, tone, completeness = st.columns(5)
    score.metric("总分", f"{report.score}/100")
    structure.metric("结构", f"{report.structure_score}/25")
    clarity.metric("清晰度", f"{report.clarity_score}/25")
    tone.metric("受众与语气", f"{report.audience_tone_score}/25")
    completeness.metric("完整度", f"{report.completeness_score}/25")
    st.markdown(f"**审阅结论：** {report.summary}")

    if report.problems:
        st.markdown("**待处理问题**")
        st.dataframe(
            [
                {
                    "严重程度": item.severity,
                    "问题类型": item.problem_type,
                    "位置": item.location,
                    "原因": item.reason,
                    "建议": item.suggestion,
                }
                for item in report.problems
            ],
            hide_index=True,
            use_container_width=True,
        )
    if report.priority_suggestions:
        st.markdown("**优先修订建议**")
        for suggestion in report.priority_suggestions:
            st.markdown(f"- {suggestion}")


def render_project_feedback(result: MvpResult) -> None:
    """Collect one editable feedback record for the persisted content package."""
    st.divider()
    st.subheader("这次内容对你有帮助吗？")
    if not result.project_id:
        st.info("本次内容尚未保存为项目，暂时不能记录反馈。")
        return
    try:
        repository = ProjectRepository(active_settings().database_url)
        existing = repository.get_feedback(result.project_id)
    except Exception as error:
        presentation = present_failure(error)
        if presentation.code == "unexpected":
            raise
        st.error(f"{presentation.title}：{presentation.message}")
        return

    initial_index = FEEDBACK_RATING_OPTIONS.index(existing.rating) if existing else 0
    with st.form(f"project_feedback_{result.project_id}", border=False):
        rating = st.radio(
            "反馈结论",
            FEEDBACK_RATING_OPTIONS,
            index=initial_index,
            horizontal=True,
        )
        comment = st.text_area(
            "希望改进什么？（可选）",
            value=existing.comment if existing else "",
            max_chars=500,
            placeholder="例如：请补充真实案例，或把语气调整得更轻松。",
        )
        submitted = st.form_submit_button("保存反馈", use_container_width=True)
    if submitted:
        try:
            repository.save_feedback(result.project_id, rating=rating, comment=comment)
        except ValueError as error:
            st.error(f"反馈未保存：{error}")
        else:
            st.success("反馈已保存。再次提交会更新这条项目反馈。")


def render_platform_adaptations(result: MvpResult) -> None:
    """Create, retain, and download audience-aware versions for publication platforms."""
    st.divider()
    st.subheader("改写为发布模板")
    st.caption("只依据已审阅的修订稿改写，不补充新的事实或来源。每个平台保留一份最新版本。")
    target_platform = st.selectbox(
        "目标发布模板",
        CONTENT_PLATFORM_OPTIONS,
        key=f"adaptation_target_{result.project_id or result.plan.topic}",
    )
    button_key = f"adaptation_generate_{result.project_id or result.plan.topic}"
    if st.button("生成平台版本", use_container_width=True, key=button_key):
        try:
            with st.spinner(f"正在生成{target_platform}版本…"):
                adaptation = adapt_content(
                    result.final_content,
                    platform=target_platform,
                    audience=result.plan.audience,
                    settings=active_settings(),
                )
                if result.project_id:
                    ProjectRepository(active_settings().database_url).save_adaptation(
                        result.project_id, adaptation
                    )
            adaptations = tuple(
                item for item in result.adaptations if item.platform != adaptation.platform
            ) + (adaptation,)
            result = replace(result, adaptations=adaptations)
            st.session_state["mvp_result"] = result
            st.success(f"已生成并保存{adaptation.platform}版本。")
        except Exception as error:
            presentation = present_failure(error)
            if presentation.code == "unexpected":
                raise
            st.error(f"{presentation.title}：{presentation.message}")

    if not result.adaptations:
        st.info("选择一个发布模板后生成。生成的版本会随项目历史保存在本机。")
        return
    st.markdown("**已生成的平台版本**")
    for adaptation in result.adaptations:
        with st.expander(f"{adaptation.platform} · {adaptation.title}"):
            st.markdown(adaptation.content)
            if adaptation.format_notes:
                st.caption(" · ".join(adaptation.format_notes))
            st.download_button(
                f"下载 {adaptation.platform} (.md)",
                data=f"# {adaptation.title}\n\n{adaptation.content}\n",
                file_name=(
                    f"{sanitize_export_stem(result.plan.topic)}-"
                    f"{sanitize_export_stem(adaptation.platform, fallback='平台版本')}.md"
                ),
                mime="text/markdown",
                key=f"adaptation_download_{result.project_id}_{adaptation.platform}",
                use_container_width=True,
            )


def _save_current_content(result: MvpResult, content: str) -> MvpResult:
    """Keep a user-edited current version without discarding the original AI output."""
    normalized_content = content.strip()
    if not normalized_content:
        raise ValueError("内容不能为空")
    if result.project_id:
        ProjectRepository(active_settings().database_url).save_content_override(
            result.project_id, normalized_content
        )
    updated = replace(result, final_content=normalized_content)
    st.session_state["mvp_result"] = updated
    return updated


def render_content_editor(result: MvpResult) -> MvpResult:
    """Offer direct editing plus an explicitly scoped AI rewrite."""
    st.divider()
    st.subheader("内容编辑台")
    st.caption("保存后会覆盖项目的当前展示稿，原始 AI 修订稿仍保留在本机。")
    editor_key = f"editable_content_{result.project_id or result.plan.topic}"
    if editor_key not in st.session_state:
        st.session_state[editor_key] = result.final_content
    if result.original_final_content and result.original_final_content != result.final_content:
        with st.expander("查看原始 AI 修订稿"):
            st.markdown(result.original_final_content)
    with st.form(f"direct_edit_{editor_key}", border=False):
        edited_content = st.text_area("当前发布稿", key=editor_key, height=320, max_chars=20_000)
        saved = st.form_submit_button("保存人工编辑", use_container_width=True)
    if saved:
        try:
            result = _save_current_content(result, edited_content)
        except (ValueError, OSError) as error:
            st.error(f"编辑未保存：{error}")
        else:
            st.success("当前发布稿已保存。")

    with st.expander("AI 定向改写"):
        st.caption("粘贴完整原文片段即可只替换这段；留空则改写整篇。")
        with st.form(f"targeted_rewrite_{editor_key}", border=False):
            selected_text = st.text_area("指定替换片段（可选）", height=110, max_chars=5_000)
            instruction = st.text_area(
                "改写要求",
                placeholder="例如：压缩为三句，保留观点，语气更像经验分享。",
                height=90,
                max_chars=500,
            )
            rewrite_submitted = st.form_submit_button("生成并保存改写", use_container_width=True)
        if rewrite_submitted:
            try:
                with st.spinner("正在按你的要求改写…"):
                    rewritten = rewrite_with_instruction(
                        st.session_state[editor_key],
                        instruction,
                        selected_text=selected_text or None,
                        settings=active_settings(),
                    )
                st.session_state[editor_key] = rewritten
                result = _save_current_content(result, rewritten)
            except Exception as error:
                presentation = present_failure(error)
                if presentation.code == "unexpected":
                    raise
                st.error(f"{presentation.title}：{presentation.message}")
            else:
                st.success("改写已保存到当前发布稿。")
    return result


def render_publishing_assets(result: MvpResult) -> MvpResult:
    """Generate local title, hook, tag, and CTA options without publishing anywhere."""
    st.divider()
    st.subheader("发布包装")
    st.caption("只生成本地内容，不会发布到任何平台。")
    platform = st.selectbox(
        "包装目标平台",
        CONTENT_PLATFORM_OPTIONS,
        index=CONTENT_PLATFORM_OPTIONS.index(result.plan.platform),
        key=f"packaging_platform_{result.project_id or result.plan.topic}",
    )
    if st.button("生成发布包装", use_container_width=True, key=f"packaging_generate_{result.project_id or result.plan.topic}"):
        try:
            with st.spinner("正在生成标题和封面钩子…"):
                assets = generate_publishing_assets(result.final_content, platform=platform, settings=active_settings())
                if result.project_id:
                    ProjectRepository(active_settings().database_url).save_publishing_assets(result.project_id, assets)
            result = replace(
                result,
                publishing_assets=tuple(item for item in result.publishing_assets if item.platform != assets.platform) + (assets,),
            )
            st.session_state["mvp_result"] = result
            st.success(f"已生成{platform}的发布包装。")
        except Exception as error:
            presentation = present_failure(error)
            if presentation.code == "unexpected":
                raise
            st.error(f"{presentation.title}：{presentation.message}")
    for assets in result.publishing_assets:
        with st.expander(f"{assets.platform} · 标题与包装"):
            st.markdown("**标题备选**")
            for index, title in enumerate(assets.titles, start=1):
                st.markdown(f"{index}. {title}")
            st.markdown("**封面 / 开头钩子**")
            for hook in assets.cover_hooks:
                st.markdown(f"- {hook}")
            if assets.tags:
                st.markdown("**建议标签**　" + "　".join(f"#{tag}" for tag in assets.tags))
            st.markdown(f"**互动收尾：** {assets.call_to_action}")
    return result


def render_visual_suggestions(result: MvpResult) -> MvpResult:
    """Plan visuals but deliberately never execute an image search or generation tool."""
    st.divider()
    st.subheader("视觉素材建议")
    st.caption("仅给出插图、照片或图表的使用建议和提示词；不会搜索或生成图片。")
    if st.button("生成视觉建议", use_container_width=True, key=f"visual_generate_{result.project_id or result.plan.topic}"):
        try:
            with st.spinner("正在判断哪些位置值得增加视觉素材…"):
                visual_plan = create_visual_plan(result.final_content, settings=active_settings())
                if result.project_id:
                    ProjectRepository(active_settings().database_url).save_visual_plan(result.project_id, visual_plan)
            result = replace(result, visual_plan=visual_plan)
            st.session_state["mvp_result"] = result
            st.success("视觉建议已保存。")
        except Exception as error:
            presentation = present_failure(error)
            if presentation.code == "unexpected":
                raise
            st.error(f"{presentation.title}：{presentation.message}")
    if not result.visual_plan:
        st.info("生成后会显示有限、可核对的视觉建议。")
        return result
    st.markdown(f"**规划说明：** {result.visual_plan.overview}")
    for asset in result.visual_plan.assets:
        with st.expander(f"{asset.section_anchor} · {asset.purpose}"):
            st.markdown(f"**建议类型：** {asset.asset_type}")
            st.markdown(f"**提示词 / 搜索词：** {asset.query_or_prompt}")
            st.markdown(f"**理由：** {asset.rationale}")
            st.caption("当前仅提供建议；模型标注的工具不会被执行。")
    return result


def render_quality_overview() -> None:
    """Show local evaluation signals without exposing any content to third parties."""
    st.subheader("质量评估")
    st.caption("仅汇总本机项目的最新反馈，并与 AI 审阅分数对照。")
    try:
        overview = ProjectRepository(active_settings().database_url).get_feedback_overview()
    except Exception as error:
        presentation = present_failure(error)
        if presentation.code == "unexpected":
            raise
        st.error(f"{presentation.title}：{presentation.message}")
        return

    total, helpful, rate, score = st.columns(4)
    total.metric("已反馈项目", overview.total_count)
    helpful.metric("有帮助", overview.helpful_count)
    rate.metric("有帮助率", f"{overview.helpful_rate}%" if overview.helpful_rate is not None else "暂无")
    score.metric(
        "平均审阅分",
        f"{overview.average_review_score}/100" if overview.average_review_score is not None else "暂无",
    )
    if not overview.recent_items:
        st.info("还没有反馈。完成创作后，在内容包底部提交你的判断。")
        return
    st.markdown("**最近反馈**")
    st.dataframe(
        [
            {
                "更新时间": item.updated_at.astimezone().strftime("%Y-%m-%d %H:%M"),
                "项目": item.topic,
                "用户反馈": item.rating,
                "审阅分": item.review_score,
                "说明": item.comment or "—",
            }
            for item in overview.recent_items
        ],
        hide_index=True,
        use_container_width=True,
    )


def render_result(result: MvpResult, *, heading: str = "本次内容包") -> None:
    """Present every workflow artifact so users can inspect, not only copy, AI output."""
    st.divider()
    st.subheader(heading)
    st.info(
        "使用提示：AI 生成内容可能有错误，请核查关键事实、引用和适用范围。"
        "当前 Research 使用本地演示资料，不等同于实时网络检索。"
    )
    if result.metrics:
        metrics = result.metrics
        llm, tools, rewrites, duration, tokens = st.columns(5)
        llm.metric("模型调用", metrics.llm_call_count)
        tools.metric("工具调用", metrics.tool_call_count)
        rewrites.metric("改写次数", metrics.rewrite_count)
        duration.metric("工作流耗时", f"{metrics.duration_ms or 0} ms")
        tokens.metric("Token", metrics.total_tokens if metrics.total_tokens is not None else "未采集")
        if metrics.total_tokens is None:
            st.caption("当前模型响应未提供可用 Token usage，因此只展示真实调用次数，不估算成本。")
    plan_tab, draft_tab, review_tab, final_tab = st.tabs(["内容计划", "初稿", "审阅报告", "修订稿"])
    with plan_tab:
        render_plan(result)
    with draft_tab:
        st.markdown(result.draft)
    with review_tab:
        render_review(result)
    with final_tab:
        st.markdown(result.final_content)
        if "mvp_export_stem" not in st.session_state:
            st.session_state["mvp_export_stem"] = default_export_stem(result.plan.topic)
        st.text_input(
            "导出文件名",
            key="mvp_export_stem",
            help="仅修改文件名；不需要填写 .md 后缀。",
        )
        st.download_button(
            "下载内容包 (.md)",
            data=render_content_package_markdown(result),
            file_name=f"{sanitize_export_stem(st.session_state['mvp_export_stem'])}.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.caption("保存位置由浏览器决定。若希望每次选择位置，请在浏览器下载设置中开启“下载前询问每个文件的保存位置”。")
    result = render_content_editor(result)
    result = render_publishing_assets(result)
    result = render_visual_suggestions(result)
    render_platform_adaptations(result)
    render_project_feedback(result)


def render_content_assets() -> None:
    """Manage reusable brand rules and the local topic calendar in one workspace."""
    st.subheader("内容资产")
    st.caption("品牌语气和选题日历都只保存在本机，不连接外部发布平台。")
    try:
        repository = ProjectRepository(active_settings().database_url)
    except Exception as error:
        presentation = present_failure(error)
        if presentation.code == "unexpected":
            raise
        st.error(f"{presentation.title}：{presentation.message}")
        return
    voice_tab, calendar_tab = st.tabs(["品牌语气", "选题与日历"])
    with voice_tab:
        st.caption("同名保存会更新原有规则；规则会在策划和写作阶段同时生效。")
        with st.form("brand_voice_form", border=False):
            name = st.text_input("品牌语气名称", placeholder="例如：理性但不说教")
            instructions = st.text_area(
                "写作规则",
                placeholder="例如：先给结论，再解释原因；短句；避免夸张承诺。",
                max_chars=500,
                height=130,
            )
            submitted = st.form_submit_button("保存品牌语气", use_container_width=True)
        if submitted:
            try:
                repository.save_brand_voice(name=name, instructions=instructions)
            except ValueError as error:
                st.error(f"品牌语气未保存：{error}")
            else:
                st.success("品牌语气已保存，可在“开始创作”中选择。")
        voices = repository.list_brand_voices()
        if voices:
            st.markdown("**已保存规则**")
            for voice in voices:
                with st.expander(voice.name):
                    st.write(voice.instructions)
        else:
            st.info("还没有品牌语气。保存后，新的内容会遵守这组写作规则。")
    with calendar_tab:
        st.caption("发布状态是本地记录，适合管理创作节奏；不会检查或同步真实平台。")
        with st.form("topic_idea_form", border=False):
            title = st.text_input("选题标题", placeholder="例如：给新手的 AI 工具选择清单")
            notes = st.text_area("选题备注（可选）", max_chars=500, height=80)
            platform, status = st.columns(2)
            with platform:
                selected_platform = st.selectbox("计划平台", CONTENT_PLATFORM_OPTIONS)
            with status:
                selected_status = st.selectbox("本地发布状态", TOPIC_STATUS_OPTIONS)
            add_date = st.checkbox("加入日期计划", value=False, key="topic_add_date")
            planned_date = st.date_input("计划日期", key="topic_scheduled_date")
            scheduled_for = planned_date if add_date else None
            submitted = st.form_submit_button("保存选题", use_container_width=True)
        if submitted:
            try:
                repository.create_topic_idea(
                    title=title,
                    notes=notes,
                    platform=selected_platform,
                    status=selected_status,
                    scheduled_for=scheduled_for,
                )
            except ValueError as error:
                st.error(f"选题未保存：{error}")
            else:
                st.success("选题已保存到本地内容日历。")
        ideas = repository.list_topic_ideas()
        if not ideas:
            st.info("还没有选题。先添加一个本地选题即可开始排期。")
            return
        st.markdown("**选题日历**")
        st.dataframe(
            [
                {
                    "计划日期": idea.scheduled_for.isoformat() if idea.scheduled_for else "未安排",
                    "选题": idea.title,
                    "平台": idea.platform,
                    "状态": idea.status,
                    "备注": idea.notes or "—",
                }
                for idea in ideas
            ],
            hide_index=True,
            use_container_width=True,
        )
        selected_idea = st.selectbox("更新一条选题", ideas, format_func=lambda item: item.title)
        with st.form("topic_idea_update_form", border=False):
            updated_status = st.selectbox(
                "更新状态",
                TOPIC_STATUS_OPTIONS,
                index=TOPIC_STATUS_OPTIONS.index(selected_idea.status),
            )
            keep_date = st.checkbox("保留 / 设置计划日期", value=selected_idea.scheduled_for is not None)
            planned_update_date = st.date_input(
                "更新计划日期",
                value=selected_idea.scheduled_for or date.today(),
            )
            updated_date = planned_update_date if keep_date else None
            update_submitted = st.form_submit_button("更新本地状态", use_container_width=True)
        if update_submitted:
            repository.update_topic_idea(selected_idea.id, status=updated_status, scheduled_for=updated_date)
            st.success("本地选题状态已更新。")


def render_project_history() -> None:
    """List recent local projects and load one only when the user chooses it."""
    st.subheader("项目历史")
    st.caption("最近 20 个已保存到本机 SQLite 的内容包。选择项目后可查看与导出。")
    try:
        repository = ProjectRepository(active_settings().database_url)
        summaries = repository.list_recent_projects()
    except Exception as error:
        presentation = present_failure(error)
        if presentation.code == "unexpected":
            raise
        st.error(f"{presentation.title}：{presentation.message}")
        return

    if not summaries:
        st.info("还没有历史项目。完成第一轮创作后，内容包会自动保存在这里。")
        return

    selected_summary = st.selectbox(
        "选择历史项目",
        summaries,
        format_func=format_project_label,
        key="history_project_selection",
    )
    if st.button("打开项目", use_container_width=True):
        record = repository.get_project(selected_summary.id)
        if record is None:
            st.error("该项目已不存在，请刷新后重新选择。")
            return
        st.session_state["mvp_result"] = result_from_project_record(record)
        st.session_state["mvp_export_stem"] = default_export_stem(record.topic)
        st.session_state["history_open_project_id"] = record.id
        st.success("已加载项目。你可以查看全部内容或导出内容包。")

    opened_project_id = st.session_state.get("history_open_project_id")
    if opened_project_id:
        record = repository.get_project(opened_project_id)
        if record is None:
            st.session_state.pop("history_open_project_id", None)
            st.warning("上次打开的项目已不存在。")
        else:
            render_result(result_from_project_record(record), heading="历史项目内容包")


def main() -> None:
    apply_styles()
    title_column, config_column = st.columns((0.78, 0.22), vertical_alignment="top")
    with title_column:
        st.markdown('<div class="eyebrow">ContentFlow AI · MVP</div>', unsafe_allow_html=True)
        st.title("把一个主题，变成可审阅的内容")
    with config_column:
        st.write("")
        render_api_configuration()
    st.markdown(
        '<p class="hero-copy">输入内容主题，依次运行策划、写作、审阅和修订。你可以保留每一环的产物，判断 AI 的结论是否可靠，而不只是拿走一段成稿。</p>',
        unsafe_allow_html=True,
    )
    render_workflow_rail()

    workspace = st.radio(
        "工作区",
        ("开始创作", "历史项目", "内容资产", "质量评估"),
        horizontal=True,
        label_visibility="collapsed",
    )

    if workspace == "历史项目":
        render_project_history()
        return
    if workspace == "质量评估":
        render_quality_overview()
        return
    if workspace == "内容资产":
        render_content_assets()
        return

    try:
        brand_voices = ProjectRepository(active_settings().database_url).list_brand_voices()
    except Exception as error:
        presentation = present_failure(error)
        if presentation.code == "unexpected":
            raise
        st.error(f"{presentation.title}：{presentation.message}")
        return
    brand_voice_options = ("不使用品牌语气",) + tuple(voice.name for voice in brand_voices)
    brand_voice_by_name = {voice.name: voice.instructions for voice in brand_voices}

    left, right = st.columns((1.08, 0.92), gap="large")
    with left:
        st.subheader("开始一轮创作")
        with st.form("创作配置", border=False):
            topic = st.text_area(
                "本次想创作什么？",
                placeholder="例如：面向大学新生，写一篇 800 字的文章，解释如何建立可持续的学习习惯。",
                height=150,
            )
            st.markdown("**内容偏好**")
            audience, tone = st.columns((1.2, 0.8))
            with audience:
                target_audience = st.text_input("目标受众", value="通用读者")
            with tone:
                selected_tone = st.selectbox("语气", CONTENT_TONE_OPTIONS)
            platform, target_length = st.columns(2)
            with platform:
                selected_platform = st.selectbox(
                    "主创作平台",
                    CONTENT_PLATFORM_OPTIONS,
                    help="平台会从策划阶段决定内容结构，而不只是最后改写格式。",
                )
            with target_length:
                selected_length = st.selectbox("目标篇幅", CONTENT_LENGTH_OPTIONS, index=1)
            selected_brand_voice = st.selectbox(
                "品牌语气（可选）",
                brand_voice_options,
                help="保存过的写作规则会同时传入策划和写作节点。",
            )
            submitted = st.form_submit_button("开始生成内容包", use_container_width=True)
        st.markdown(
            '<p class="panel-note">主创作平台会决定内容骨架：小红书使用钩子、分点与互动收尾；PPT 按页面组织；短视频按口播节奏组织。生成后仍可改写为其他平台版本。</p>',
            unsafe_allow_html=True,
        )

    with right:
        st.subheader("你会看到什么")
        st.markdown(
            """
            - 可检查的内容计划，而不是黑箱提示词
            - 初稿与修订稿，便于比较改写是否真的改善
            - 结构、清晰度、受众语气、完整度四项评分
            """
        )

    if submitted:
        if not topic.strip():
            log_event("ui_input_error", error_type="TopicInputError", topic_length=0)
            st.error("请输入内容主题后再开始生成。")
        else:
            run_id = new_run_id()
            normalized_topic = topic.strip()
            log_event("ui_submit", run_id=run_id, topic_length=len(normalized_topic))
            try:
                preferences = ContentPreferences(
                    audience=target_audience.strip(),
                    tone=selected_tone,
                    platform=selected_platform,
                    target_length=selected_length,
                    brand_voice=brand_voice_by_name.get(selected_brand_voice),
                )
                with st.spinner("正在依次完成策划、写作、审阅和修订…"):
                    settings = active_settings()
                    repository = ProjectRepository(settings.database_url)
                    st.session_state["mvp_result"] = run_mvp(
                        normalized_topic,
                        settings=settings,
                        repository=repository,
                        run_id=run_id,
                        preferences=preferences,
                    )
                st.session_state["mvp_export_stem"] = default_export_stem(normalized_topic)
                log_event("ui_complete", run_id=run_id)
                st.success("内容包已保存到本地项目历史。")
            except Exception as error:
                log_event("ui_error", run_id=run_id, error_type=type(error).__name__)
                presentation = present_failure(error)
                if presentation.code == "unexpected":
                    raise
                st.error(f"{presentation.title}：{presentation.message}")

    result = st.session_state.get("mvp_result")
    if result is None:
        st.markdown(
            '<div class="empty-state"><strong>还没有内容包</strong><br>输入主题并开始生成；结果会留在本次页面会话中供你检查。</div>',
            unsafe_allow_html=True,
        )
    else:
        render_result(result)


if __name__ == "__main__":
    main()
