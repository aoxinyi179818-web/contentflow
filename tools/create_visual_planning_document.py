"""Create the Step 41 Visual Planner learning document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/26-visual-planning.docx")


def style_run(run, size: float, bold: bool = False, color: str = "000000") -> None:
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def add_paragraph(document: Document, text: str, heading: bool = False) -> None:
    paragraph = document.add_paragraph(style="Heading 1" if heading else None)
    paragraph.paragraph_format.space_before = Pt(12 if heading else 0)
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.line_spacing = 1.35
    style_run(paragraph.add_run(text), 14 if heading else 11, heading)


def shade(cell, color: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    properties.append(shading)


def set_cell(cell, text: str, header: bool = False) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if header else WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_after = Pt(2)
    style_run(paragraph.add_run(text), 10, header, "FFFFFF" if header else "000000")
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    if header:
        shade(cell, "1F4E79")


def add_decision_table(document: Document) -> None:
    table = document.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    headers = ["内容特征", "推荐工具", "不可违反的约束"]
    for cell, text in zip(table.rows[0].cells, headers, strict=True):
        set_cell(cell, text, header=True)
    rows = [
        ("真实人物 产品 地点 历史事件", "image_search", "使用可核验图片，不把生成图当作事实照片"),
        ("抽象概念 流程 示意场景", "image_generation", "提示词不能补充原文没有依据的事实"),
        ("明确数值 趋势 对比数据", "chart", "只使用原文已有数据，不能编造数据点"),
    ]
    for values in rows:
        cells = table.add_row().cells
        for cell, text in zip(cells, values, strict=True):
            set_cell(cell, text)
    widths = [Inches(2.0), Inches(1.35), Inches(3.8)]
    for row in table.rows:
        for cell, width in zip(row.cells, widths, strict=True):
            cell.width = width


def build_document() -> None:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    title = document.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    style_run(title.add_run("ContentFlow AI 视觉规划"), 21, True)
    add_paragraph(document, "阶段：Step 41  范围：视觉素材选择与工具路由规划")

    add_paragraph(document, "阶段结论", True)
    add_paragraph(
        document,
        "Visual Planner 已接在 Adapter 之后，负责判断内容中哪些位置值得增加视觉素材，并输出可执行的素材计划。本阶段只选择未来应该调用的工具，不执行图片搜索、图像生成或图表生成，因此不会产生外部素材成本。",
    )

    add_paragraph(document, "输入输出设计", True)
    add_paragraph(
        document,
        "输入为审核后的 final_content，若已完成 Adapter 则优先使用 adapted_content，并传入 max_visual_assets。输出为 VisualPlan：每项素材计划包含 section_anchor、purpose、asset_type、tool、query_or_prompt、rationale。默认最多规划 3 项，允许范围为 1 到 5。",
    )

    add_paragraph(document, "工具选择决策表", True)
    add_decision_table(document)

    add_paragraph(document, "数据与质量约束", True)
    add_paragraph(
        document,
        "VisualAssetPlan 只允许 image_search、image_generation、chart 三种工具。模型校验工具与素材类型必须匹配，VisualPlan 校验 section_anchor 不可重复。运行时还验证每个 anchor 必须真实出现在输入内容中，防止模型为不存在的段落规划素材。",
    )

    add_paragraph(document, "工作流接入", True)
    add_paragraph(
        document,
        "ResearchWorkflowState 新增 max_visual_assets 和 visual_plan。Visual Planner 以可选依赖注入，不提供服务时返回空更新，旧工作流仍保持可用。当前节点顺序为 Finalize 到 Adapter 到 Visual Planner 到 END，质量循环的状态不会被视觉规划覆盖。",
    )

    add_paragraph(document, "调试记录", True)
    add_paragraph(
        document,
        "首次定向测试在导入 models.py 时出现 IndentationError。原因是写入 VisualPlan 验证器时，重复 anchor 的异常与返回语句没有完整落盘。补齐两行后重新格式化，模型、Prompt 和工作流测试全部恢复通过。",
    )

    add_paragraph(document, "验收结果", True)
    add_paragraph(
        document,
        "新增 Visual Planner 输入校验、工具规则、锚点可追溯性和 Workflow 接入测试。定向验证 15 passed；完整项目回归 55 passed；Ruff 静态检查、格式检查和编译检查通过。",
    )

    add_paragraph(document, "学习总结", True)
    add_paragraph(
        document,
        "视觉能力的第一步应是可解释的规划，而不是立即生成图片。规划层把素材价值、事实边界、工具选择和数量预算拆开，使下一阶段接入真实图片搜索、图像生成或图表服务时可以独立计费、审核和失败重试。",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
