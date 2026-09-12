from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/14-prompt-evaluation.docx")


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
    paragraph.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(5)
    set_run_font(paragraph.add_run(text), 14 if level == 1 else 12, bold=True)


def add_table(document: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    widths = [Inches(0.65), Inches(1.0), Inches(1.0), Inches(3.55)]

    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.width = widths[index]
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_shading(cell, "1F4E78")
        set_cell_border(cell)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(paragraph.add_run(header), 10, bold=True, color="FFFFFF")

    for row_index, row in enumerate(rows):
        for index, value in enumerate(row):
            cell = table.add_row().cells[index]
            cell.width = widths[index]
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_border(cell)
            if row_index % 2 == 1:
                set_cell_shading(cell, "F3F6F9")
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(2)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if index < 3 else WD_ALIGN_PARAGRAPH.LEFT
            set_run_font(paragraph.add_run(value), 10)

    document.add_paragraph().paragraph_format.space_after = Pt(4)


def build_document() -> None:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    title = document.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title.paragraph_format.space_after = Pt(6)
    set_run_font(title.add_run("ContentFlow AI Prompt 评测记录"), 22, bold=True)

    metadata = document.add_paragraph()
    metadata.paragraph_format.space_after = Pt(13)
    set_run_font(metadata.add_run("范围：Writer 节点  日期：2026年9月6日  当前生效版本：V3"), 10, color="595959")

    add_heading(document, "评测结论")
    add_body(
        document,
        "Writer Prompt V3 已稳定满足首个非空行为一级 Markdown 标题的格式要求。"
        "但在没有 Research 来源的情况下，模型仍会补充关于 AI 能力、数据处理和课程规则的概括性结论。"
        "因此，V3 仅作为格式改进保留；事实正确性不能由 Prompt 单独保证，后续必须由 Research 和结构化 Reviewer 承担。",
    )

    add_heading(document, "评测目的与固定样例")
    add_body(
        document,
        "本次针对面向大学生的 AI 辅助学习指南进行迭代。固定计划包含四个章节：学习辅助边界、隐私与数据、课程与作业、低风险行动清单。"
        "其中隐私和课程规则被故意设置为高风险主题，用来检验模型是否会把未提供来源的内容写成确定事实。",
    )

    add_heading(document, "评测指标")
    add_table(
        document,
        ["指标", "判定方式", "本轮用途", "说明"],
        [
            ["格式", "首个非空行", "V3 主指标", "必须以 # 开头，避免结果页标题层级混乱。"],
            ["指令遵循", "人工检查", "V1 至 V3", "是否只输出正文并保持计划结构。"],
            ["事实边界", "人工检查", "V1 至 V3", "无 Research 时不得补充可验证的产品、政策、数据处理或课程结论。"],
            ["内容质量", "人工检查", "V1 至 V3", "是否清晰、面向大学生且有可执行建议。"],
        ],
    )

    add_heading(document, "版本结果对比")
    add_table(
        document,
        ["版本", "格式", "事实边界", "结论"],
        [
            ["V1", "可读 Markdown", "失败", "完整 MVP 运行中补充了具体工具、免费政策等无来源信息。"],
            ["V2", "失败", "失败", "高风险样例首行使用 ##；仍出现数据留存和课程差异类结论。"],
            ["V3", "通过", "失败", "首行以 # 开头；仍出现 AI 能力、数据处理和课程规则的概括性结论。"],
        ],
    )

    add_heading(document, "迭代记录")
    add_heading(document, "V1 观察", level=2)
    add_body(
        document,
        "V1 已要求避免编造事实，但约束较抽象。完整 MVP 输出显示，模型会主动给出具体工具名称和免费可用性等可验证信息。"
        "这说明模型会把常识性补充当作帮助内容，而不是把它识别为需要来源的外部事实。",
    )
    add_heading(document, "V2 修改与结果", level=2)
    add_body(
        document,
        "V2 禁止具体产品、平台、学校或课程名称，并禁止免费政策、数据处理和课程后果等结论。"
        "实际输出仍出现输入内容可能保存、不同课程规定不同等概括性说法，且首行没有一级标题。"
        "因此 V2 未通过事实边界和格式两项检查。",
    )
    add_heading(document, "V3 修改与结果", level=2)
    add_body(
        document,
        "V3 新增首个非空行必须是一级 Markdown 标题的规则。真实输出的首行符合要求，格式指标通过。"
        "不过正文仍补充了模型概率性、数据可能保存和课程使用边界等无来源说明。V3 不能被视为事实安全方案。",
    )

    add_heading(document, "产品与工程决策")
    add_body(
        document,
        "当前保留 Writer Prompt V3 的标题格式规则，并保留 V2 的显式事实边界提示。"
        "在 Research 接入前，系统结果应定位为待编辑初稿，不能向用户承诺事实正确。"
        "下一轮不再仅通过增加措辞来解决事实问题，而是在后续阶段引入来源上下文、结构化评分字段和可测试的路由规则。",
    )

    add_heading(document, "可重复评测步骤")
    for index, text in enumerate(
        [
            "使用固定高风险内容计划调用 Writer。",
            "记录首个非空行、输出格式、是否出现无来源结论和内容质量观察。",
            "一次只修改一个 Prompt 目标，并标记版本。",
            "运行单元测试、风格检查和真实调用后，再更新本记录。",
        ],
        start=1,
    ):
        paragraph = document.add_paragraph(style="List Number")
        paragraph.paragraph_format.space_after = Pt(4)
        set_run_font(paragraph.add_run(text), 11)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
