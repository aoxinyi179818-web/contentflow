"""Create the Step 50 shared LLM-client remediation document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUTPUT = Path("docs/37-llm-client-factory.docx")
BLUE, PALE_BLUE, GRID = "17365D", "EAF2F8", "D9D9D9"


def set_font(run, *, size: float = 10.5, bold: bool = False, color: RGBColor | None = None) -> None:
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def cell_style(cell, fill: str | None = None) -> None:
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    props = cell._tc.get_or_add_tcPr()
    margins = OxmlElement("w:tcMar")
    for side in ("top", "start", "bottom", "end"):
        edge = OxmlElement(f"w:{side}")
        edge.set(qn("w:w"), "100")
        edge.set(qn("w:type"), "dxa")
        margins.append(edge)
    props.append(margins)
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge = OxmlElement(f"w:{side}")
        edge.set(qn("w:val"), "single")
        edge.set(qn("w:sz"), "6")
        edge.set(qn("w:color"), GRID)
        borders.append(edge)
    props.append(borders)
    if fill:
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), fill)
        props.append(shading)


def width(cell, value: float) -> None:
    props = cell._tc.get_or_add_tcPr()
    item = OxmlElement("w:tcW")
    item.set(qn("w:w"), str(int(value * 1440)))
    item.set(qn("w:type"), "dxa")
    props.append(item)


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
        width(cell, widths[index])
        cell_style(cell, BLUE)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(cell.paragraphs[0].add_run(value), size=8.4, bold=True, color=RGBColor(255, 255, 255))
    for row_number, values in enumerate(rows):
        cells = output.add_row().cells
        for index, value in enumerate(values):
            cell = cells[index]
            width(cell, widths[index])
            cell_style(cell, PALE_BLUE if row_number % 2 else None)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER if index == 0 else WD_ALIGN_PARAGRAPH.LEFT
            cell.paragraphs[0].paragraph_format.line_spacing = 1.05
            set_font(cell.paragraphs[0].add_run(value), size=8.2)
        props = output.rows[-1]._tr.get_or_add_trPr()
        props.append(OxmlElement("w:cantSplit"))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def build() -> None:
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(0.67)
    section.left_margin = section.right_margin = Inches(0.65)
    doc.styles["Normal"].font.name = "Microsoft YaHei"
    doc.styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    doc.styles["Normal"].font.size = Pt(10.5)

    title = doc.add_paragraph(style="Title")
    props = title._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "nil")
    borders.append(bottom)
    props.append(borders)
    title.paragraph_format.space_after = Pt(8)
    set_font(
        title.add_run("ContentFlow AI LLM 客户端工厂整改"),
        size=21,
        bold=True,
        color=RGBColor(0, 0, 0),
    )
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(16)
    set_font(subtitle.add_run("代码 Review 整改  统一连接配置与保留模块职责"), size=10.5, color=RGBColor(89, 89, 89))

    body(doc, "本次整改处理 Code Review 的第二项 P2：多个业务模块重复初始化 LLM 客户端。现在由一个共享工厂集中处理 DeepSeek Provider、API Key、模型名、默认服务地址和超时配置；各模块继续保留自己的配置异常类型，因此用户提示和既有测试契约不变。")

    heading(doc, "1 输入 输出与职责")
    table(doc, ["层次", "输入", "输出或职责"], [
        ("调用模块", "Settings 模块名称 异常类型", "声明业务语义 不再构造连接"),
        ("客户端工厂", "Provider API Key 模型 Base URL timeout", "OpenAI 客户端或调用方指定异常"),
        ("业务调用", "统一客户端与已有 Prompt", "保持原模型参数与结构化输出"),
        ("错误映射", "模块专属配置错误", "复用模型配置不可用中文提示"),
    ], [1.15, 2.25, 3.3])

    heading(doc, "2 最小实现方案")
    bullets(doc, [
        "新增 llm_client 模块，只负责创建 DeepSeek OpenAI 客户端和校验公共配置。",
        "Planner Writer Reviewer Rewriter Adapter Research Visual 全部改为调用该工厂。",
        "调用方传入 consumer name 和既有异常类型，保留模块边界与错误语义。",
        "不引入全局单例或客户端缓存，避免在配置变更和测试替身中产生隐藏状态。",
        "保留 deepseek hello，作为 Step 20 的独立 API 学习示例，不混入产品运行时。",
    ])
    body(doc, "该设计把重复规则集中到一个入口，却不把所有 Agent 和 Node 合并为一个通用模块。共享的是连接配置；Prompt、输入校验、模型参数和结果解析仍属于各自业务模块。")

    doc.add_page_break()
    heading(doc, "3 Debug 与测试结果")
    table(doc, ["步骤", "结果", "结论"], [
        ("环境检查", "文档运行时没有 pytest", "改用项目 .venv 执行测试"),
        ("定向测试", "22 passed", "工厂配置与七个模块相关测试通过"),
        ("第一次全量", "系统 Temp 权限错误", "Windows 沙箱限制 不是业务失败"),
        ("全量回归", "98 passed", "在沙箱外验证无功能回归"),
        ("静态检查", "Ruff passed", "修复新测试 import 顺序后通过"),
    ], [1.15, 2.05, 3.5])
    body(doc, "Debug 的关键不是忽略失败，而是定位失败所在链路。定向测试已经证明本项行为正确；全量错误只发生在 pytest 创建或清理临时目录时。将同一命令在受限沙箱外执行后，98 个测试全部通过，因此可以确认重构没有破坏功能。")

    heading(doc, "4 学到什么")
    body(doc, "工厂模式适合集中管理可变的基础设施配置，而不是替代业务模块。重构时必须先识别稳定契约：这里是每个模块的异常类型和用户提示。把公共校验移入工厂，同时把异常类型作为明确输入，能够减少重复并避免改变产品行为。下一项 Review 整改将处理 Research 工作流中硬编码的策略参数。")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)


if __name__ == "__main__":
    build()
