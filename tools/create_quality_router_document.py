"""Create the Step 39 quality-router learning document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/24-quality-router.docx")


def set_run_style(run, size: float, bold: bool = False, color: str = "000000") -> None:
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
    set_run_style(paragraph.add_run(text), 14 if heading else 11, heading)


def shade(cell, color: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    properties.append(shading)


def set_cell_text(cell, text: str, *, header: bool = False) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if header else WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_after = Pt(2)
    set_run_style(paragraph.add_run(text), 10, header, "FFFFFF" if header else "000000")
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    if header:
        shade(cell, "1F4E79")


def add_table(document: Document) -> None:
    table = document.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    headers = ["优先条件", "是否还有额度", "下一跳", "原因"]
    for cell, text in zip(table.rows[0].cells, headers, strict=True):
        set_cell_text(cell, text, header=True)
    rows = [
        ("证据分低于 15", "research_count 小于 2", "Research", "资料不足，先补充可追溯证据"),
        ("证据分低于 15", "research_count 已等于 2", "Finalize", "停止循环并标记研究上限"),
        ("证据分至少 15 且总分低于 80", "rewrite_count 小于 1", "Rewrite", "证据已够，改进表达和结构"),
        ("其余情况", "不适用", "Finalize", "内容达到门槛或对应预算已用尽"),
    ]
    for values in rows:
        cells = table.add_row().cells
        for cell, text in zip(cells, values, strict=True):
            set_cell_text(cell, text)
    widths = [Inches(1.45), Inches(1.4), Inches(0.85), Inches(3.5)]
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
    set_run_style(title.add_run("ContentFlow AI 质量路由器设计"), 21, True)
    add_paragraph(document, "阶段：Step 39  范围：Research Workflow 的质量决策与循环控制")

    add_paragraph(document, "阶段结论", True)
    add_paragraph(
        document,
        "工作流现在根据审阅结果选择补研、改写或结束。证据分是第一道门槛：资料不足时优先返回 Research；只有证据达到要求后，才根据总分决定是否 Rewrite。研究与改写都有明确上限，避免 Agent 无限循环。",
    )

    add_paragraph(document, "输入输出设计", True)
    add_paragraph(
        document,
        "输入包括 ReviewReport 的 score 和 evidence_score，以及 quality_threshold、evidence_threshold、research_count、max_research_count、rewrite_count 与 max_rewrite_count。输出是 research、rewrite 或 finalize；完成状态额外说明是正常完成、研究上限完成或改写上限完成，便于界面展示和日志排查。",
    )

    add_paragraph(document, "路由决策表", True)
    add_table(document)

    add_paragraph(document, "关键实现", True)
    add_paragraph(
        document,
        "ResearchWorkflowState 显式保存质量门槛和计数器。Research 节点每执行一次就递增 research_count，Rewrite 节点递增 rewrite_count。路由函数先判断证据：低于门槛且仍有研究额度时回到 Research；额度耗尽时直接 Finalize。这个顺序保证不会用文字润色掩盖证据不足。",
    )

    add_paragraph(document, "调试发现与修复", True)
    add_paragraph(
        document,
        "边界测试发现一个风险：当证据仍不足、研究次数已达上限且文章总分也低时，旧条件会进入 Rewrite。修复后，研究上限优先结束，并返回 completed_at_research_limit。这样既保留问题信号，也避免无效改写。",
    )

    add_paragraph(document, "验收结果", True)
    add_paragraph(
        document,
        "本阶段新增三类测试：证据不足时再次补研、证据合格但总分不足时改写、研究额度耗尽时停止且不改写。定向测试 3 passed；完整项目回归 47 passed；本阶段文件的 Ruff 静态与格式检查通过。全仓另有 15 个早期文件存在既有格式债务，本阶段未顺手修改。",
    )

    add_paragraph(document, "学习总结", True)
    add_paragraph(
        document,
        "质量路由器把抽象的 AI 质量要求变成可执行的状态机规则。产品上，它让用户知道系统为何继续工作或为何停止；工程上，它通过门槛、计数器和状态码控制成本、延迟和可维护性。下一次扩展时，可以把固定门槛改为用户可配置策略，并记录每次路由的原因用于评测。",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
