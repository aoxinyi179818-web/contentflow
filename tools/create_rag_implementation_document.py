"""Create the Step 35 local RAG implementation document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/21-rag-local-implementation.docx")


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


def table(document: Document, headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
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
        for index, value in enumerate(row):
            cell = output.add_row().cells[index] if index == 0 else output.rows[-1].cells[index]
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
    set_font(title.add_run("ContentFlow AI 最小 RAG 实现"), 21, bold=True)
    metadata = document.add_paragraph()
    metadata.paragraph_format.space_after = Pt(13)
    set_font(
        metadata.add_run("阶段：Step 35  范围：本地可测试检索链路  日期：2026年9月10日"),
        10,
        color="595959",
    )

    heading(document, "阶段结论")
    body(
        document,
        "ContentFlow 已完成从 ResearchSource 到 Writer Context 的最小 RAG 链路。它包含清洗、分块、确定性向量化、内存索引、余弦相似度检索和带来源标识的上下文格式化。"
        "实现不调用外部 Embedding API，也没有接入 LangGraph；目的是先获得可重复、可测试的数据链路。",
    )

    heading(document, "数据流")
    numbered(
        document,
        [
            "Research Agent 返回 ResearchSource，其中含 source_id、标题、URL 和资料摘要。",
            "Retriever 清洗空白字符并转换为 DocumentRecord，空资料会被拒绝。",
            "ChunkingConfig 按 chunk_size 和 overlap 生成可追溯的 ChunkRecord。",
            "HashingEmbedding 把片段和查询编码为固定长度向量；InMemoryRetriever 保存它们。",
            "search 返回按余弦相似度排序的 EvidenceChunk，format_writer_context 输出带 [source_id] 的上下文。",
        ],
    )

    heading(document, "模块职责")
    table(
        document,
        ["对象", "关键字段或方法", "职责"],
        [
            ["ChunkingConfig", "chunk_size、overlap", "验证分块参数，保证 overlap 小于 chunk_size。"],
            ["DocumentRecord", "source_id、text", "清洗后的可索引资料。"],
            ["ChunkRecord", "chunk_id、位置、来源", "索引最小单元，保留可追溯关系。"],
            ["HashingEmbedding", "embed(text)", "本地确定性向量化，可被真实模型实现替换。"],
            ["InMemoryRetriever", "search(query, top_k)", "计算余弦相似度并返回 EvidenceChunk。"],
            ["format_writer_context", "EvidenceChunk 列表", "把证据格式化为 Writer 可消费的带来源上下文。"],
        ],
        [1.4, 2.35, 2.45],
    )

    heading(document, "输入输出和失败边界")
    table(
        document,
        ["输入或情况", "输出或行为", "产品意义"],
        [
            ["有效资料和查询", "Top K EvidenceChunk，含 score 和 source_id。", "Writer 可引用具体资料。"],
            ["空查询", "RetrievalInputError。", "避免无意义检索和不确定结果。"],
            ["Top K 小于 1 或大于 10", "RetrievalInputError。", "限制上下文膨胀。"],
            ["overlap 大于等于 chunk_size", "Pydantic ValidationError。", "避免步长为零导致死循环。"],
            ["无相关证据", "Writer 提示资料不足。", "防止把模型记忆伪装成检索事实。"],
        ],
        [1.65, 2.35, 2.2],
    )

    heading(document, "验证结果")
    table(
        document,
        ["项目", "结果", "说明"],
        [
            ["专项单元测试", "4 passed", "覆盖分块重叠、相关性排序、来源上下文和参数校验。"],
            ["无网络检索示例", "成功", "主动回忆资料排在第一位，并生成带来源的 Writer Context。"],
            ["项目回归", "待本阶段末尾执行", "确保新增模块不破坏已有 Planner、Graph 和 Agent。"],
        ],
        [1.65, 1.35, 3.2],
    )

    heading(document, "当前实现的局限")
    body(
        document,
        "HashingEmbedding 根据字符和英文词的哈希特征计算相似度，不理解真正语义。它可能把共享常见字符的弱相关资料排进 Top K。"
        "内存索引也不会持久化。它们是有意保留的教学边界：Step 36 将用固定问题集验证检索质量，再决定真实 Embedding、FAISS 或 Chroma 的选择。",
    )

    heading(document, "学习总结")
    body(
        document,
        "RAG 不只是调用向量数据库。真正需要掌握的是从来源到 Chunk，再到 Evidence 和 Writer Context 的可追溯数据链路。"
        "把 Embedding 定义为接口，使系统未来可以替换模型而不重写分块、检索边界或 Writer 的来源格式。",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
