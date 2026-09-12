"""Create the Step 40 Adapter learning document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/25-content-adapter.docx")


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


def add_platform_table(document: Document) -> None:
    table = document.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    for cell, text in zip(table.rows[0].cells, ["平台", "输出目标", "适配规则"], strict=True):
        set_cell(cell, text, header=True)
    rows = [
        ("长文章", "完整文章", "保留标题层级、论述与段落结构"),
        ("社交媒体文案", "可直接发布的短文案", "短段落、吸引开头、互动收尾"),
        ("PPT 大纲", "逐页提纲", "按页给出标题与要点"),
        ("短视频脚本", "口播脚本", "开场、主体、结尾行动引导"),
    ]
    for values in rows:
        cells = table.add_row().cells
        for cell, text in zip(cells, values, strict=True):
            set_cell(cell, text)
    widths = [Inches(1.25), Inches(2.0), Inches(3.9)]
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
    style_run(title.add_run("ContentFlow AI 多平台内容适配"), 21, True)
    add_paragraph(document, "阶段：Step 40  范围：审核后内容的多平台交付")

    add_paragraph(document, "阶段结论", True)
    add_paragraph(
        document,
        "Adapter 已作为普通 LLM Node 接在 Research Workflow 的 Finalize 之后。它只处理通过质量循环后的 final_content，并返回可验证的 AdaptedContent。由于目标格式明确且不需要自主选择工具，本阶段不将它设计为 Agent。",
    )

    add_paragraph(document, "输入输出设计", True)
    add_paragraph(
        document,
        "输入为 final_content、platform、audience 和 Settings。platform 只允许长文章、社交媒体文案、PPT 大纲、短视频脚本四种值。输出包含 platform、title、content、format_notes；Pydantic 会拒绝未知字段、空标题和空正文。",
    )

    add_paragraph(document, "平台适配规格", True)
    add_platform_table(document)

    add_paragraph(document, "内容安全边界", True)
    add_paragraph(
        document,
        "Adapter Prompt 明确要求只依据最终内容改写，不补充没有依据的新事实、数据、来源或结论，并保留不确定性和待核实提示。这样平台化表达不会覆盖 Research 与 Reviewer 已建立的事实边界。",
    )

    add_paragraph(document, "工作流接入", True)
    add_paragraph(
        document,
        "ResearchWorkflowState 新增 platform 与 adapted_content。ResearchWorkflowServices 通过可选 adapt_content 依赖注入 Adapter，旧的测试和调用不传 Adapter 时仍可以正常结束。Finalize 到 Adapter 到 END 的边保持最终内容和质量状态不变。",
    )

    add_paragraph(document, "调试记录", True)
    add_paragraph(
        document,
        "首次集成测试失败，因为 Prompt 的 JSON 合约包含 format_notes，而 AdaptedContent Schema 漏掉该字段。Pydantic 的 extra forbid 正确阻断了这个不一致。补齐字段后，提示词、模型和测试恢复同一份契约。",
    )

    add_paragraph(document, "验收结果", True)
    add_paragraph(
        document,
        "新增 Adapter 输入校验与 Prompt 测试，以及 Finalize 后适配的 Workflow 集成测试。定向验证 11 passed；完整项目回归 51 passed；Ruff 静态检查、格式检查与编译检查通过。",
    )

    add_paragraph(document, "学习总结", True)
    add_paragraph(
        document,
        "多平台适配的难点不是重新生成内容，而是把格式差异和事实边界同时写进接口契约。普通 LLM Node 适合确定目标的转换任务；当未来需要自己判断视觉素材类型或调用搜索、绘图工具时，才需要使用 Agent。",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
