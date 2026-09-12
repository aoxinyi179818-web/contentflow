"""Create the Step 31 base LangGraph workflow design document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/17-langgraph-base-workflow.docx")


def set_cell_shading(cell, color: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    properties.append(shading)


def set_cell_border(cell) -> None:
    properties = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:color"), "D9D9D9")
        borders.append(element)
    properties.append(borders)


def set_run_font(run, size: float, bold: bool = False, color: str = "000000") -> None:
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def add_body(document: Document, text: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(7)
    paragraph.paragraph_format.line_spacing = 1.35
    set_run_font(paragraph.add_run(text), 11)


def add_heading(document: Document, text: str, level: int = 1) -> None:
    paragraph = document.add_paragraph(style=f"Heading {level}")
    paragraph.paragraph_format.space_before = Pt(13 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(5)
    set_run_font(paragraph.add_run(text), 14 if level == 1 else 12, bold=True)


def add_table(
    document: Document, headers: list[str], rows: list[list[str]], widths: list[float]
) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.width = Inches(widths[index])
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_shading(cell, "1F4E78")
        set_cell_border(cell)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(paragraph.add_run(header), 9.5, bold=True, color="FFFFFF")
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cell = cells[index]
            cell.width = Inches(widths[index])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_border(cell)
            if row_index % 2 == 1:
                set_cell_shading(cell, "F3F6F9")
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(2)
            set_run_font(paragraph.add_run(value), 9.5)
    document.add_paragraph().paragraph_format.space_after = Pt(4)


def add_numbered_steps(document: Document, items: list[str]) -> None:
    for item in items:
        paragraph = document.add_paragraph(style="List Number")
        paragraph.paragraph_format.space_after = Pt(4)
        set_run_font(paragraph.add_run(item), 11)


def build_document() -> None:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    title = document.add_paragraph(style="Title")
    title.paragraph_format.space_after = Pt(6)
    set_run_font(title.add_run("ContentFlow AI LangGraph 基础工作流设计"), 21, bold=True)

    metadata = document.add_paragraph()
    metadata.paragraph_format.space_after = Pt(13)
    set_run_font(
        metadata.add_run("阶段：Step 31  范围：基础 Graph 与质量路由  日期：2026年9月10日"),
        10,
        color="595959",
    )

    add_heading(document, "阶段结论")
    add_body(
        document,
        "ContentFlow 的 Planner、Writer、Reviewer 和 Rewrite 已从串行函数调用重构为基础 LangGraph。"
        "新工作流只在审阅分数低于 80 且尚未达到改写上限时进入 Rewrite。"
        "高分内容直接完成，低分内容最多改写一次并复审一次；即使仍不达标，流程也会正常结束，不会无限循环。",
    )

    add_heading(document, "工作流路径")
    add_body(
        document, "START → Planner → Writer → Reviewer → Quality Router → Rewrite 或 Finalize → END"
    )
    add_body(
        document,
        "Router 的规则为：review.score 小于 quality_threshold，并且 rewrite_count 小于 max_rewrite_count 时进入 Rewrite；其他情况进入 Finalize。"
        "Rewrite 完成后回到 Reviewer，因此最后一次 review 始终对应最终输出前的当前内容。",
    )

    add_heading(document, "共享 State 设计")
    add_table(
        document,
        ["字段", "来源或更新节点", "用途", "保留原因"],
        [
            ["topic 与 settings", "输入", "主题和运行配置", "保证所有节点使用同一轮任务配置。"],
            ["plan", "Planner", "Writer 的结构化输入", "沿用 Pydantic ContentPlan。"],
            ["draft", "Writer", "原始初稿", "始终保留，供 UI 展示和比较。"],
            [
                "current_content",
                "Writer 与 Rewrite",
                "当前待审内容",
                "循环中可更新，不覆盖原始初稿。",
            ],
            ["review", "Reviewer", "最后一次质量报告", "Router 与最终结果共用。"],
            [
                "rewrite_count 与 max_rewrite_count",
                "输入与 Rewrite",
                "限制循环",
                "防止低分内容无限改写。",
            ],
            ["final_content 与 status", "Finalize", "统一结束输出", "使 UI 保持稳定接口。"],
        ],
        [1.35, 1.7, 1.65, 2.6],
    )

    add_heading(document, "节点职责")
    add_table(
        document,
        ["节点", "读取", "写入", "职责边界"],
        [
            ["Planner", "topic", "plan、status", "只负责生成内容计划。"],
            ["Writer", "plan", "draft、current_content、status", "只负责根据计划产生初稿。"],
            ["Reviewer", "current_content", "review、status", "只负责评估当前内容。"],
            [
                "Rewrite",
                "current_content、review",
                "current_content、rewrite_count、status",
                "只负责按审阅建议改写。",
            ],
            [
                "Finalize",
                "current_content、review、计数",
                "final_content、status",
                "只统一结束状态，不生成内容。",
            ],
        ],
        [1.15, 1.65, 2.2, 2.3],
    )

    add_heading(document, "对原有 MVP 的兼容策略")
    add_body(
        document,
        "Streamlit 仍调用 run_mvp，并继续接收 MvpResult。"
        "run_mvp 现在把既有的 Planner、Writer、Reviewer 和 Rewrite 函数注入 Graph，再把最终 State 映射回 MvpResult。"
        "因此 UI 无需因编排层重构而改动，业务节点也不需要知道 LangGraph 的存在。",
    )

    add_heading(document, "验收路径")
    add_numbered_steps(
        document,
        [
            "审阅分数等于 80：不调用 Rewrite，初稿直接成为最终稿。",
            "首次审阅为 70，改写后审阅为 85：调用一次 Rewrite 和两次 Reviewer，修订稿成为最终稿。",
            "两次审阅均为 70：只调用一次 Rewrite，状态为 completed_at_rewrite_limit。",
            "MVP 入口仍返回 plan、draft、review 和 final_content，供现有界面使用。",
        ],
    )

    add_heading(document, "本阶段不做什么")
    add_body(
        document,
        "本阶段不处理 API 超时、无效 JSON、Research、工具调用、RAG、数据库持久化或前端流式进度。"
        "这些能力会在后续阶段逐步接入；基础 Graph 的目标仅是让已有内容链路具备明确状态、条件路由和受限循环。",
    )

    add_heading(document, "学习总结")
    add_body(
        document,
        "Graph 的价值在于把业务节点和流程决策分开。Planner、Writer、Reviewer、Rewrite 仍是普通 Python 函数；"
        "质量阈值、改写上限和下一步去向由 State 与 Edge 管理。这样每条产品规则都能被单独测试，并能在未来安全扩展 Research 或更多路由。",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
