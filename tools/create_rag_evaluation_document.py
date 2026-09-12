"""Create the Step 36 RAG evaluation document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/22-rag-evaluation.docx")


def font(run, size: float, bold: bool = False, color: str = "000000") -> None:
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def heading(document: Document, text: str) -> None:
    paragraph = document.add_paragraph(style="Heading 1")
    paragraph.paragraph_format.space_before = Pt(12)
    paragraph.paragraph_format.space_after = Pt(5)
    font(paragraph.add_run(text), 14, True)


def body(document: Document, text: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(7)
    paragraph.paragraph_format.line_spacing = 1.35
    font(paragraph.add_run(text), 11)


def shade(cell, color: str) -> None:
    element = OxmlElement("w:shd")
    element.set(qn("w:fill"), color)
    cell._tc.get_or_add_tcPr().append(element)


def table(document: Document, headers: list[str], rows: list[list[str]]) -> None:
    output = document.add_table(rows=1, cols=len(headers))
    output.style = "Table Grid"
    for index, value in enumerate(headers):
        cell = output.rows[0].cells[index]
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shade(cell, "1F4E78")
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        font(paragraph.add_run(value), 9.5, True, "FFFFFF")
    for row_index, values in enumerate(rows):
        cells = output.add_row().cells
        for index, value in enumerate(values):
            if row_index % 2:
                shade(cells[index], "F3F6F9")
            cells[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            font(cells[index].paragraphs[0].add_run(value), 9.5)
    document.add_paragraph().paragraph_format.space_after = Pt(4)


def build_document() -> None:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)
    title = document.add_paragraph(style="Title")
    font(title.add_run("ContentFlow AI RAG 评测结果"), 21, True)
    metadata = document.add_paragraph()
    metadata.paragraph_format.space_after = Pt(12)
    font(metadata.add_run("阶段：Step 36  范围：固定问题集与检索指标  日期：2026年9月10日"), 10, color="595959")

    heading(document, "阶段结论")
    body(document, "本阶段建立了可版本化的 5 题固定评测集和来源级指标。RAG 配置在 4 个有目标来源的问题上全部命中，域外问题正确返回空证据。该结果只说明小型演示语料上的证据检索有效，不能代表真实业务语料上的语义质量。")
    heading(document, "评测设计")
    table(document, ["项目", "设计"], [["数据集", "4 条演示资料、4 个有目标来源的问题、1 个域外无证据问题。"], ["基线", "无 RAG：Writer 没有可引用检索证据，Source Hit 和 MRR 均为 0。"], ["指标", "Source Hit@K、MRR、No Evidence Accuracy。"], ["变体", "small Top 1、default Top 1、default Top 3、wide Top 3。"]])
    heading(document, "结果")
    table(document, ["配置", "Hit@K", "MRR", "无证据正确率"], [["无 RAG", "0.00", "0.00", "1.00"], ["small Top 1", "1.00", "1.00", "1.00"], ["default Top 1", "1.00", "1.00", "1.00"], ["default Top 3", "1.00", "1.00", "1.00"], ["wide Top 3", "1.00", "1.00", "1.00"]])
    heading(document, "发现的 Bug 和修复")
    body(document, "第一次评测中，所有中文查询都没有结果。定位发现：为过滤 Hashing Embedding 碰撞而新增的词项门槛函数漏写返回语句，Python 将其返回为 None，导致所有片段被过滤。补上返回值后，6 个 RAG 相关测试全部通过。该案例说明评测集不仅验证模型效果，也能发现普通控制流 Bug。")
    heading(document, "结果解读")
    body(document, "不同 Chunk Size 和 Top K 得到相同分数，是因为语料很小、主题区分明显，每条资料只有少量片段。不能因此得出参数无关紧要的结论。下一轮评测应加入更长资料、近义问题、相似主题和干扰来源，并观察延迟、上下文长度与错误引用。")
    heading(document, "学习总结")
    body(document, "RAG Evaluation 的最低要求是固定输入、明确正确来源和可重复指标。无 RAG 对比说明的是证据可用性差异，不是自动证明最终文章质量。检索质量、引用正确性和最终回答质量需要分别度量。")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
