"""Create the Step 34 RAG problem definition document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/20-rag-problem-definition.docx")


def set_font(run, size: float, bold: bool = False, color: str = "000000") -> None:
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def shade(cell, color: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    element = OxmlElement("w:shd")
    element.set(qn("w:fill"), color)
    properties.append(element)


def border(cell) -> None:
    properties = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:color"), "D9D9D9")
        borders.append(element)
    properties.append(borders)


def heading(document: Document, text: str) -> None:
    paragraph = document.add_paragraph(style="Heading 1")
    paragraph.paragraph_format.space_before = Pt(13)
    paragraph.paragraph_format.space_after = Pt(5)
    set_font(paragraph.add_run(text), 14, bold=True)


def body(document: Document, text: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(7)
    paragraph.paragraph_format.line_spacing = 1.35
    set_font(paragraph.add_run(text), 11)


def table(
    document: Document, headers: list[str], rows: list[list[str]], widths: list[float]
) -> None:
    output = document.add_table(rows=1, cols=len(headers))
    output.style = "Table Grid"
    output.autofit = False
    for index, value in enumerate(headers):
        cell = output.rows[0].cells[index]
        cell.width = Inches(widths[index])
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shade(cell, "1F4E78")
        border(cell)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(paragraph.add_run(value), 9.5, bold=True, color="FFFFFF")
    for row_index, row in enumerate(rows):
        cells = output.add_row().cells
        for index, value in enumerate(row):
            cell = cells[index]
            cell.width = Inches(widths[index])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            border(cell)
            if row_index % 2 == 1:
                shade(cell, "F3F6F9")
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(2)
            set_font(paragraph.add_run(value), 9.5)
    document.add_paragraph().paragraph_format.space_after = Pt(4)


def numbered(document: Document, items: list[str]) -> None:
    for item in items:
        paragraph = document.add_paragraph(style="List Number")
        paragraph.paragraph_format.space_after = Pt(4)
        set_font(paragraph.add_run(item), 11)


def build_document() -> None:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    title = document.add_paragraph(style="Title")
    title.paragraph_format.space_after = Pt(6)
    set_font(title.add_run("ContentFlow AI RAG 问题定义"), 21, bold=True)
    metadata = document.add_paragraph()
    metadata.paragraph_format.space_after = Pt(13)
    set_font(
        metadata.add_run("阶段：Step 34  范围：RAG 价值和接口定义  日期：2026年9月10日"),
        10,
        color="595959",
    )

    heading(document, "阶段结论")
    body(
        document,
        "ContentFlow 引入 RAG 的唯一目标，是让 Writer 根据已获取且可追溯的资料写作，而不是完全依赖模型记忆。"
        "RAG 不是新的搜索功能：Research Agent 负责发现和保存资料，RAG 负责从这些资料中为当前写作任务挑选最相关的少量证据片段。",
    )

    heading(document, "当前问题")
    table(
        document,
        ["现象", "直接把资料放进 Prompt 的问题", "RAG 要解决的事"],
        [
            ["资料较多", "上下文变长、成本升高，模型容易忽略关键段落。", "按写作问题筛选 Top K 相关片段。"],
            ["资料来自多个来源", "来源与具体主张容易脱钩。", "每个片段保留 source_id 和位置。"],
            ["任务会变化", "同一资料库无法靠固定摘要满足所有问题。", "用当前 query 动态选择上下文。"],
            ["资料不足", "模型可能用自身记忆补出确定结论。", "明确返回无足够证据，交给 Writer 降低断言强度。"],
        ],
        [1.3, 2.8, 2.45],
    )

    heading(document, "RAG 的职责边界")
    table(
        document,
        ["模块", "负责", "不负责"],
        [
            ["Research Agent", "决定查什么、调用工具、保存来源摘要。", "为每一段正文选择最终证据。"],
            ["RAG Retriever", "清洗资料、分块、嵌入、相似度检索并返回证据。", "判断资料绝对真实或替 Writer 写文章。"],
            ["Writer", "基于检索上下文写作并标注来源，表达不确定性。", "把没有证据的片段写成事实。"],
            ["Reviewer", "检查证据是否支持主张和引用是否完整。", "重新实现资料检索。"],
        ],
        [1.35, 2.85, 2.35],
    )

    heading(document, "下一阶段的输入输出设计")
    table(
        document,
        ["阶段", "输入", "输出"],
        [
            ["Ingest", "ResearchSource 列表", "可追溯的 DocumentRecord，含 source_id、标题、URL、正文。"],
            ["Chunk", "DocumentRecord", "ChunkRecord，含 chunk_id、文本、source_id、位置和元数据。"],
            ["Index", "ChunkRecord 列表", "向量索引与原始片段映射。"],
            ["Retrieve", "写作 query、Top K", "按分数排序的 EvidenceChunk 列表，或空结果。"],
            ["Writer Context", "EvidenceChunk 列表", "有限长度的引用上下文和来源清单。"],
        ],
        [1.2, 2.55, 2.8],
    )

    heading(document, "最小数据契约")
    body(
        document,
        "每个 ChunkRecord 至少包含 chunk_id、source_id、text、chunk_index、title 和 url。检索结果还必须包含 score。"
        "Writer 的上下文不得只传裸文本：每条片段必须带 source_id，才能让最终文章将主张和来源对应起来。",
    )

    heading(document, "实现方案与取舍")
    table(
        document,
        ["决策", "推荐最小方案", "原因"],
        [
            ["资料来源", "先复用本地演示 ResearchSource", "不引入新的外部 API、权限或爬取变量。"],
            ["向量库", "先使用内存索引和确定性测试数据", "先理解链路，再评估 FAISS 或 Chroma 的持久化需求。"],
            ["Embedding", "使用一个可替换的 Embedding 接口", "避免业务代码绑定到单一模型或供应商。"],
            ["检索数量", "默认 Top K 为 3，随后用评测集调整", "控制 Prompt 长度，同时保持足够的证据覆盖。"],
            ["失败策略", "空结果返回，不伪造上下文", "让 Writer 和 UI 能诚实提示资料不足。"],
        ],
        [1.25, 2.75, 2.55],
    )

    heading(document, "验收标准")
    numbered(
        document,
        [
            "给定两条以上来源资料和一个查询，系统返回包含 source_id 的 Top K 片段。",
            "相同的输入数据与检索配置在测试中得到稳定排序。",
            "空资料库、空查询和 Top K 越界都有明确异常或空结果行为。",
            "Writer 的上下文包含来源标识，不能只包含无归属的文本。",
            "测试能证明高相关片段排在低相关片段之前，并记录无 RAG 与有 RAG 的差异。",
        ],
    )

    heading(document, "本阶段不做什么")
    body(
        document,
        "本阶段不接入 Web Search，不抓取真实网页，不把 RAG 接入 LangGraph 主流程，也不在没有评测集的情况下选择固定 Chunk Size。"
        "这些实现工作留给 Step 35；效果好坏和参数选择留给 Step 36 的 RAG Evaluation。",
    )

    heading(document, "学习总结")
    body(
        document,
        "RAG 的核心产物不是向量库，而是一个可追溯的证据选择接口。只有当资料规模或任务变化让整份资料无法直接放进 Prompt 时，RAG 才值得增加复杂度。"
        "对 ContentFlow 而言，先把 source_id 和证据缺口传到 Writer，比先选某个向量数据库更关键。",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
