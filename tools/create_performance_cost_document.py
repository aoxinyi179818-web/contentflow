"""Create the Step 47 performance and cost learning document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT = Path("docs/32-performance-cost.docx")
BLUE = "17365D"
PALE_BLUE = "EAF2F8"
GRID = "D9D9D9"


def set_font(run, *, size: float = 10.5, bold: bool = False, color: RGBColor | None = None) -> None:
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def clear_paragraph_borders(paragraph) -> None:
    properties = paragraph._p.get_or_add_pPr()
    borders = properties.find(qn("w:pBdr"))
    if borders is None:
        borders = OxmlElement("w:pBdr")
        properties.append(borders)
    bottom = borders.find(qn("w:bottom"))
    if bottom is None:
        bottom = OxmlElement("w:bottom")
        borders.append(bottom)
    bottom.set(qn("w:val"), "nil")


def style_cell(cell, *, fill: str | None = None) -> None:
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    properties = cell._tc.get_or_add_tcPr()
    margins = OxmlElement("w:tcMar")
    for side in ("top", "start", "bottom", "end"):
        edge = OxmlElement(f"w:{side}")
        edge.set(qn("w:w"), "105")
        edge.set(qn("w:type"), "dxa")
        margins.append(edge)
    properties.append(margins)
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge = OxmlElement(f"w:{side}")
        edge.set(qn("w:val"), "single")
        edge.set(qn("w:sz"), "6")
        edge.set(qn("w:color"), GRID)
        borders.append(edge)
    properties.append(borders)
    if fill:
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), fill)
        properties.append(shading)


def set_width(cell, inches: float) -> None:
    cell.width = Inches(inches)
    properties = cell._tc.get_or_add_tcPr()
    width = OxmlElement("w:tcW")
    width.set(qn("w:w"), str(int(inches * 1440)))
    width.set(qn("w:type"), "dxa")
    properties.append(width)


def heading(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph(style="Heading 1")
    paragraph.paragraph_format.space_before = Pt(10)
    paragraph.paragraph_format.space_after = Pt(5)
    set_font(paragraph.add_run(text), size=14, bold=True, color=RGBColor(0, 0, 0))


def body(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.22
    paragraph.paragraph_format.space_after = Pt(5)
    set_font(paragraph.add_run(text))


def bullets(doc: Document, values: list[str]) -> None:
    for value in values:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.line_spacing = 1.1
        paragraph.paragraph_format.space_after = Pt(1)
        set_font(paragraph.add_run(value))


def table(doc: Document, headers: list[str], rows: list[tuple[str, ...]], widths: list[float]) -> None:
    output = doc.add_table(rows=1, cols=len(headers))
    output.style = "Table Grid"
    output.autofit = False
    for index, value in enumerate(headers):
        cell = output.rows[0].cells[index]
        set_width(cell, widths[index])
        style_cell(cell, fill=BLUE)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(paragraph.add_run(value), size=8.4, bold=True, color=RGBColor(255, 255, 255))
    properties = output.rows[0]._tr.get_or_add_trPr()
    repeated = OxmlElement("w:tblHeader")
    repeated.set(qn("w:val"), "true")
    properties.append(repeated)
    for row_index, values in enumerate(rows):
        cells = output.add_row().cells
        for index, value in enumerate(values):
            cell = cells[index]
            set_width(cell, widths[index])
            style_cell(cell, fill=PALE_BLUE if row_index % 2 else None)
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.line_spacing = 1.05
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if index == 0 else WD_ALIGN_PARAGRAPH.LEFT
            set_font(paragraph.add_run(value), size=8.2)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def build() -> None:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.67)
    section.bottom_margin = Inches(0.67)
    section.left_margin = Inches(0.65)
    section.right_margin = Inches(0.65)
    normal = doc.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(10.5)

    title = doc.add_paragraph(style="Title")
    clear_paragraph_borders(title)
    title.paragraph_format.space_after = Pt(8)
    set_font(title.add_run("ContentFlow AI 性能与成本记录"), size=21, bold=True, color=RGBColor(0, 0, 0))
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(16)
    set_font(subtitle.add_run("项目生命周期 Step 47  以真实调用数据指导优化"), size=10.5, color=RGBColor(89, 89, 89))

    body(
        doc,
        "本阶段为每次 ContentFlow 工作流建立 RunMetrics。它记录模型调用次数、工具调用次数、改写次数、工作流耗时和可用的 Token usage。结论是：先建立可验证的基线，再优化；不能仅凭最终内容质量或猜测的 Token 数判断系统成本。",
    )

    heading(doc, "1 需要观察什么")
    rows = [
        ("模型调用", "llm_call", "每次 LLM 请求尝试", "识别无意义重复调用"),
        ("工具调用", "tool_call_start", "每次 Tool 请求尝试", "控制 Agent Loop 成本"),
        ("Token", "llm_usage", "provider response 的 usage", "只累计真实返回数据"),
        ("耗时", "workflow_start 到 workflow_end", "毫秒级工作流时长", "发现慢节点与超时"),
        ("改写", "workflow_end rewrite_count", "质量循环实际次数", "验证 Router 是否节制"),
    ]
    table(doc, ["指标", "事件", "定义", "用于回答的问题"], rows, [0.85, 1.55, 2.0, 2.3])

    heading(doc, "2 指标数据流与边界")
    body(
        doc,
        "workflow_start 创建 run_id 对应的内存指标。Planner、Writer、Reviewer、Rewrite、Adapter、Visual Planner 和 Research Agent 在发起模型请求前记录 llm_call。工具在 tool_call_start 时计数。若模型响应提供 usage，则记录 input_tokens、output_tokens 和 total_tokens；workflow_end 或 workflow_error 固化状态、改写次数与耗时。",
    )
    bullets(
        doc,
        [
            "RunMetrics 仅保存运行标识、次数、耗时、状态和数字型 Token，不保存主题、Prompt、正文、模型回复或 API Key。",
            "内存最多保留 100 个 run，适合单进程本地 MVP 的排查，不替代生产环境的监控系统。",
            "模型未返回 usage 时 Token 显示为未采集。系统仍显示模型调用次数，但不会根据字符数估算成本。",
        ],
    )

    heading(doc, "3 当前产品中的优化规则")
    rows = [
        ("高分内容", "Review 达到阈值", "跳过 Rewrite", "少一次模型调用"),
        ("低分内容", "未到改写上限", "只改写后复审一次", "质量与成本可控"),
        ("研究不足", "Evidence 低且未到上限", "回到 Research", "避免无证据继续写作"),
        ("循环上限", "达到 research 或 rewrite 上限", "停止并返回状态", "防止无限调用"),
        ("RAG 上下文", "按 Top K 检索", "只送相关资料", "限制 Context 长度"),
    ]
    table(doc, ["场景", "判断", "当前行为", "成本收益"], rows, [0.9, 1.65, 2.1, 2.05])

    heading(doc, "4 如何在界面和测试中验证")
    bullets(
        doc,
        [
            "在 Streamlit 生成完成后，结果区展示模型调用、工具调用、改写次数、工作流耗时和 Token。",
            "如果 Token 显示未采集，先检查模型响应是否提供 usage；这表示数据不可用，不是零 Token。",
            "测试覆盖高低分路径：低分经过一次 Rewrite 与复审时，模型调用应为 5 次，rewrite_count 为 1。",
            "完整验证命令：.venv\\Scripts\\python.exe -m pytest -q -p no:cacheprovider --basetemp .\\test_tmp_step47。",
            "静态检查命令：.venv\\Scripts\\python.exe -m ruff check app.py src\\contentflow tests。",
        ],
    )

    heading(doc, "5 后续优化的决策顺序")
    body(
        doc,
        "先观察，再提出假设，再改动一个变量，最后回归测试。比如某类任务的模型调用数异常高，应先按 run_id 确认是 Research 重试、Rewrite 低分路径还是界面重复提交；只有确认原因后，才调整阈值、Top K、超时或缓存策略。不要为了降低调用数直接删除 Reviewer 或 Research，这会损失产品的可验证性。",
    )
    bullets(
        doc,
        [
            "优先级一：删除重复提交和不必要的重试。",
            "优先级二：缩短无关 Context，并用 RAG 检索结果控制输入长度。",
            "优先级三：对可复用的研究结果或计划设计缓存，并用失效规则避免陈旧资料。",
            "优先级四：根据实际质量与成本数据再选择更快或更便宜的模型。",
        ],
    )

    heading(doc, "6 本阶段学习总结")
    body(
        doc,
        "你学会了把性能与成本变成运行数据，而不是经验判断：LLM 调用次数说明流程复杂度，Tool 调用次数反映 Agent 边界，耗时帮助定位慢路径，真实 usage 才能支持 Token 成本分析。当前 MVP 已具备本地基线；下一阶段才处理基础安全与可靠性。",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)


if __name__ == "__main__":
    build()
