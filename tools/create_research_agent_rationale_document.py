"""Create the Step 32 Research Agent rationale document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/18-research-agent-rationale.docx")


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


def heading(document: Document, text: str, level: int = 1) -> None:
    paragraph = document.add_paragraph(style=f"Heading {level}")
    paragraph.paragraph_format.space_before = Pt(13 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(5)
    set_font(paragraph.add_run(text), 14 if level == 1 else 12, bold=True)


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


def numbered(document: Document, texts: list[str]) -> None:
    for text in texts:
        paragraph = document.add_paragraph(style="List Number")
        paragraph.paragraph_format.space_after = Pt(4)
        set_font(paragraph.add_run(text), 11)


def build_document() -> None:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    title = document.add_paragraph(style="Title")
    title.paragraph_format.space_after = Pt(6)
    set_font(title.add_run("ContentFlow AI Research Agent 设计决策"), 21, bold=True)
    metadata = document.add_paragraph()
    metadata.paragraph_format.space_after = Pt(13)
    set_font(
        metadata.add_run("阶段：Step 32  范围：Research 为什么需要 Agent  日期：2026年9月10日"),
        10,
        color="595959",
    )

    heading(document, "阶段结论")
    body(
        document,
        "ContentFlow 需要 Research，但当前不应把它实现为一条固定搜索语句。不同主题的信息缺口、可靠来源和停止条件都不同。"
        "因此 Research 应由受限 Agent 决定查询与工具调用顺序，并输出可追溯的资料上下文给 Writer。"
        "Agent 的范围只覆盖资料发现和充分性判断，不负责写作、质量评分或最终发布。",
    )

    heading(document, "Writer 为什么不能只依赖模型记忆")
    table(
        document,
        ["问题", "只依赖模型记忆的风险", "Research 的补充"],
        [
            ["时效信息", "信息可能过期，无法说明更新时间。", "查询近期可信来源并保留日期。"],
            ["可验证事实", "容易把概括性说法写成确定结论。", "将主张与来源摘要一起传给 Writer。"],
            [
                "长尾主题",
                "模型知识覆盖和细节完整度不稳定。",
                "按主题动态补足缺失概念、数据或规则。",
            ],
            ["用户信任", "结果无法解释依据从何而来。", "输出来源清单与研究边界。"],
        ],
        [1.35, 2.65, 2.6],
    )

    heading(document, "为什么不是固定搜索流程")
    body(
        document,
        "固定流程适合每次都查询同一种资料的任务，例如查一个固定数据库。ContentFlow 的主题跨度大：学习建议需要教育与行为方法资料，产品比较需要规格与价格来源，政策类主题需要原始规则。"
        "同一主题的计划也会改变检索重点。Research 必须先理解计划，再确定缺什么、查什么、是否继续。",
    )

    heading(document, "Research Agent 的输入输出")
    table(
        document,
        ["类别", "字段", "用途"],
        [
            ["输入", "topic、plan、research_budget", "明确任务范围和可用工具次数。"],
            [
                "中间状态",
                "queries、sources、evidence_gaps、tool_calls",
                "记录决策过程，支持调试与评测。",
            ],
            [
                "输出",
                "research_context、citations、coverage_note",
                "给 Writer 的可引用上下文和覆盖说明。",
            ],
            ["控制", "max_iterations、timeout、allowed_domains", "限制成本、循环和不可信来源。"],
        ],
        [1.25, 2.55, 2.8],
    )

    heading(document, "受限 Agent 循环")
    numbered(
        document,
        [
            "读取 topic 与 Content Plan，列出需要外部证据的主张和信息缺口。",
            "根据缺口生成一个具体查询，并选择允许的 Search 或 Reader 工具。",
            "保存来源、摘要、发布时间和与计划的关联，不把网页正文直接当作结论。",
            "判断关键缺口是否被覆盖；若未覆盖且预算允许，继续下一次查询。",
            "达到覆盖要求、迭代上限或超时后结束，返回研究上下文和未覆盖说明。",
        ],
    )

    heading(document, "职责边界")
    table(
        document,
        ["Research Agent 负责", "Research Agent 不负责"],
        [
            [
                "发现资料缺口、生成查询、调用资料工具、评估资料覆盖度、返回来源和上下文。",
                "直接写最终文章、替代 Reviewer、判断所有事实绝对正确、绕过工具预算、访问未授权数据。",
            ],
        ],
        [3.35, 3.25],
    )

    heading(document, "进入 Step 33 的验收条件")
    numbered(
        document,
        [
            "能用结构化参数描述 Search Tool 的输入和输出。",
            "能区分工具调用请求、工具结果和最终 Agent 输出。",
            "能说明 max_iterations、timeout 与来源限制分别防止什么问题。",
            "能设计一个可测试的停止条件，而不是让 Agent 自由无限循环。",
            "能说明 Writer 只消费 Research Context，不直接把未核验搜索片段写成事实。",
        ],
    )

    heading(document, "本阶段不做什么")
    body(
        document,
        "本阶段没有安装搜索服务、没有接入 Tool Calling、没有执行网页搜索，也没有改动现有基础 Graph。"
        "下一阶段才会定义 Tool Schema、调用协议、最大迭代次数和错误处理；RAG 会在资料获取流程稳定后单独设计。",
    )

    heading(document, "学习总结")
    body(
        document,
        "Agent 适合需要根据中间结果决定下一步的任务。ContentFlow 的 Research 具有这种不确定性：查询不能预先写死，资料是否足够也需要判断。"
        "但 Agent 必须被状态、工具白名单、次数上限和停止条件约束；它不是更自由的 Writer。",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
