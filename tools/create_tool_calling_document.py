"""Create the Step 33 Tool Calling design document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/19-tool-calling-design.docx")


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
    set_font(title.add_run("ContentFlow AI Tool Calling 设计说明"), 21, bold=True)
    metadata = document.add_paragraph()
    metadata.paragraph_format.space_after = Pt(13)
    set_font(
        metadata.add_run("阶段：Step 33  范围：Research Agent 工具调用  日期：2026年9月10日"),
        10,
        color="595959",
    )

    heading(document, "阶段结论")
    body(
        document,
        "Research Agent 已实现一条受限的工具调用闭环：模型提出函数调用请求，应用验证函数名和参数，执行本地资料检索，再把结构化结果回传给模型。"
        "真实模型验证得到 2 次工具调用和 3 条来源记录。当前工具语料是内置演示资料，用于学习协议和安全边界，不等同于联网搜索。",
    )

    heading(document, "为什么需要 Tool Calling")
    body(
        document,
        "语言模型擅长判断需要什么信息，却不能直接安全地访问应用能力。Tool Calling 把能力定义为受控函数：模型只能提出意图，应用代码仍掌握参数校验、权限、执行和结果格式。"
        "这使 Research Agent 能从模型记忆转向可追溯资料，同时避免让模型任意执行命令或访问未授权资源。",
    )

    heading(document, "输入 输出 与方案")
    table(
        document,
        ["对象", "字段", "设计用途"],
        [
            ["Agent 输入", "question、settings、max_iterations", "限定研究问题、模型配置和最大循环次数。"],
            ["工具请求", "name、arguments JSON", "模型只能请求白名单中的 search_research_knowledge。"],
            ["工具输入", "query、max_results", "Pydantic 校验 query 长度和结果数范围 1 到 5。"],
            ["工具结果", "source_id、title、url、summary", "为下一轮推理和最终来源列表提供结构化证据。"],
            ["Agent 输出", "answer、sources、tool_calls", "同时交付回答、可追溯来源和调试记录。"],
        ],
        [1.25, 2.25, 3.1],
    )

    heading(document, "调用协议")
    numbered(
        document,
        [
            "应用向模型发送研究问题、函数 Schema 和工具使用规则。",
            "模型返回普通回答，或返回一个或多个工具调用请求。",
            "应用仅接受白名单函数，并用 SearchArguments 解析 JSON 参数。",
            "应用执行本地检索，将来源列表序列化为 tool 消息回传给模型。",
            "模型基于工具结果生成最终回答，并以 source_id 标注依据；达到最大迭代次数则报错结束。",
        ],
    )

    heading(document, "安全边界和失败处理")
    table(
        document,
        ["风险", "代码中的控制", "预期行为"],
        [
            ["虚构工具名", "只允许固定函数名", "抛出 ToolCallValidationError，不执行任何操作。"],
            ["参数越界", "Pydantic strict schema 和范围限制", "拒绝例如 max_results 等于 99 的请求。"],
            ["无限调用", "max_iterations 默认 3", "达到上限抛出 ResearchIterationLimitError。"],
            ["来源误导", "source_type 标记为 demo_seed", "明确资料是演示语料，不声称是实时网页。"],
            ["模型不可用", "配置与客户端异常向上抛出", "调用方可显示错误，不伪造研究结论。"],
        ],
        [1.35, 2.55, 2.7],
    )

    heading(document, "测试与真实验证")
    table(
        document,
        ["验证项", "结果", "说明"],
        [
            ["本地单元测试", "4 passed", "覆盖正常回传、参数越界和迭代上限。"],
            ["静态检查", "Ruff passed", "导入顺序和格式符合项目约束。"],
            ["真实模型请求", "成功", "DeepSeek 产生 2 次工具调用。"],
            ["来源结果", "3 条", "返回 study planning、retrieval practice、privacy boundary。"],
        ],
        [1.55, 1.25, 3.8],
    )

    heading(document, "本阶段范围与下一步边界")
    body(
        document,
        "本阶段新增的 Research Agent 保持独立，尚未插入现有 LangGraph 主流程，也未接入网页搜索、数据库或向量检索。"
        "这样可以先验证工具协议、结构化输出和失败路径。后续阶段应先设计 Web Search 的来源策略与评测，再决定是否把 Research 节点接入工作流。",
    )

    heading(document, "学习总结")
    body(
        document,
        "Tool Calling 的关键不是让模型拥有更多权限，而是把模型的决策和程序的执行分开。"
        "模型负责提出要查什么，应用负责验证、执行和记录；因此测试必须覆盖正常路径，也必须覆盖无效参数、未知工具和停止条件。",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
