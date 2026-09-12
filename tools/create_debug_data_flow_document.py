"""Create the Step 46 data-chain debugging learning document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT = Path("docs/31-debug-data-flow.docx")
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


def heading(doc: Document, text: str, level: int = 1) -> None:
    paragraph = doc.add_paragraph(style=f"Heading {level}")
    paragraph.paragraph_format.space_before = Pt(10 if level == 1 else 7)
    paragraph.paragraph_format.space_after = Pt(5)
    set_font(paragraph.add_run(text), size=14 if level == 1 else 11.5, bold=True, color=RGBColor(0, 0, 0))


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
    set_font(title.add_run("ContentFlow AI 数据链路调试"), size=21, bold=True, color=RGBColor(0, 0, 0))
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(16)
    set_font(subtitle.add_run("项目生命周期 Step 46  从用户提交到项目保存的可定位链路"), size=10.5, color=RGBColor(89, 89, 89))

    body(
        doc,
        "本阶段的结论是：调试 AI 工作流不能只看最终报错。每次运行都应有一个 run_id，并在界面、MVP、工作流节点、Router、Tool 和 SQLite 保存事件中复用。这样当用户说“生成失败”时，开发者可以按同一标识还原运行路径，而不记录主题正文、提示词、模型原始回复或 API Key。",
    )

    heading(doc, "1 为什么按数据链路排查")
    body(
        doc,
        "ContentFlow 的一次请求会跨越多个职责边界。错误可能来自输入校验、节点服务、模型解析、路由判断、工具调用或数据库写入。只在最外层捕获异常只能知道“失败了”，无法回答“失败发生在哪一段、是否重试、是否影响数据保存”。因此追踪的对象是事件和关联标识，而不是内容载荷。",
    )
    bullets(
        doc,
        [
            "输入：主题文本、配置、用户提交事件和已知异常。",
            "输出：按 run_id 关联的安全事件，可定位节点、路由、工具与保存结果。",
            "边界：日志只保留长度、状态、分数、计数、类型和不透明 ID，不保存主题、Prompt、正文或密钥。",
        ],
    )

    heading(doc, "2 当前运行链路与事件")
    rows = [
        ("UI", "ui_submit ui_complete ui_error", "topic_length run_id", "界面提交与展示错误"),
        ("MVP", "mvp_start mvp_end mvp_error", "run_id status", "连接产品入口与工作流"),
        ("Graph", "workflow_start workflow_end workflow_error", "run_id workflow status", "识别整条流程边界"),
        ("Node", "node_start node_end node_error", "run_id node status", "定位 Planner Writer Reviewer Rewrite Finalize"),
        ("Router", "router_decision", "destination score count", "解释为何改写或结束"),
        ("Tool", "tool_call_start tool_call_end tool_call_error", "tool query_length source_count", "定位研究工具失败"),
        ("SQLite", "database_save_start database_save_end database_save_error", "topic_length project_id", "确认项目是否落库"),
    ]
    table(doc, ["层级", "事件", "安全字段", "诊断问题"], rows, [0.66, 2.08, 1.52, 2.44])

    heading(doc, "3 如何阅读一次失败")
    body(
        doc,
        "从 run_id 开始按时间查看事件。若最后一条是 node_error，先查看 node 字段，再检查该节点的输入合同和服务异常类型；若出现 router_decision，则先判断目的地是否符合分数和次数阈值；若 workflow_end 已出现而没有 database_save_end，问题通常在 MVP 保存阶段。异常日志只存 error_type，详情仍应在本地受控调试环境中查看。",
    )

    heading(doc, "4 本次 Bug 记录")
    bug_rows = [
        ("现象", "全量回归得到 81 通过、1 失败，失败测试是工具完成事件断言。"),
        ("复现", "运行 pytest -q -p no:cacheprovider --basetemp .\\test_tmp_step46。"),
        ("原因", "测试把 source_count 错误地假定紧跟 run_id；实际日志在两者之间还包含 tool 字段。"),
        ("诊断", "Captured log 显示 tool_call_end 已出现，且 source_count=1，说明产品日志正确，断言顺序过于严格。"),
        ("解决", "改为分别断言事件与 run_id，同时断言 source_count=1，不依赖字段排列顺序。"),
        ("回归", "最终全量 pytest 82 passed，Ruff 静态检查全部通过。"),
    ]
    table(doc, ["记录项", "内容"], bug_rows, [1.05, 5.65])

    heading(doc, "5 运行和验证")
    bullets(
        doc,
        [
            "启动界面：.venv\\Scripts\\streamlit.exe run app.py。提交主题后，在终端按 run_id 查看 INFO 事件。",
            "回归测试：.venv\\Scripts\\python.exe -m pytest -q -p no:cacheprovider --basetemp .\\test_tmp_step46。",
            "静态检查：.venv\\Scripts\\python.exe -m ruff check app.py src\\contentflow tests。",
            "Windows 沙箱若阻止系统临时目录，使用项目内 --basetemp；若环境仍阻止扫描，应以受控权限重跑测试，而非改动业务代码绕过测试。",
        ],
    )

    heading(doc, "6 本阶段学习总结")
    body(
        doc,
        "你学会了把 Debug 从“看报错”变成可重复的数据链路排查：设计稳定的关联 ID，选择不泄露内容的事件字段，记录 Router 与工具边界，并为一次真实失败写清现象、复现、原因、诊断、解决和回归。下一阶段才会进入部署准备；在此之前，这条链路已能为本地 MVP 的问题定位提供证据。",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)


if __name__ == "__main__":
    build()
