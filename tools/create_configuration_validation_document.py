"""Create the Step 50 configuration-boundary remediation document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUTPUT = Path("docs/36-configuration-validation.docx")
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
    set_font(title.add_run("ContentFlow AI 配置边界修复"), size=21, bold=True, color=RGBColor(0, 0, 0))
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(16)
    set_font(subtitle.add_run("代码 Review 整改  环境变量到用户提示的可验证链路"), size=10.5, color=RGBColor(89, 89, 89))

    body(doc, "本次整改只处理 Code Review 的第一项 P2：超时环境变量解析。修复后的系统只接受有限且大于 0 的秒数；非法值会变为领域配置错误，并由现有错误映射显示为模型配置不可用。这样既保留开发日志定位信息，也不会把原始 ValueError 暴露给用户。")

    heading(doc, "1 输入 输出与职责")
    table(doc, ["层次", "输入", "输出或职责"], [
        ("环境变量", "LLM_TIMEOUT_SECONDS 字符串", "提供本机可配置超时"),
        ("Settings", "字符串", "有限且大于 0 的 float 或 SettingsConfigurationError"),
        ("错误映射", "领域配置错误", "模型配置不可用的稳定中文提示"),
        ("测试", "非数字 零 负数 nan inf", "验证非法边界与 UI 分类"),
    ], [1.1, 2.2, 3.4])

    heading(doc, "2 最小实现方案")
    bullets(doc, [
        "新增 SettingsConfigurationError，表达环境设置无法形成安全配置。",
        "新增 timeout 读取函数：先转换 float，再检查 finite 和大于 0。",
        "Settings from env 只负责组装已验证的值，不再直接执行裸 float 转换。",
        "将新错误加入 present failure 的配置错误集合，复用已有产品提示。",
    ])
    body(doc, "该改动没有改变 API Key、模型名称、工作流或 Prompt 的输入输出，只收紧配置边界。因此适合用小范围单元测试验证，而不需要重构整个配置系统。")

    # Keep the verification table and the learning summary together on page two.
    doc.add_page_break()
    heading(doc, "3 Debug 与测试结果")
    table(doc, ["步骤", "结果", "结论"], [
        ("复现", "not a number 原先触发 ValueError", "确认 Review 发现真实存在"),
        ("定向测试", "16 passed", "非法 timeout 与错误映射均通过"),
        ("全量回归", "94 passed", "新增 6 条边界测试且无回归"),
        ("静态检查", "Ruff passed", "修复新增 import 的排序问题后通过"),
    ], [1.2, 2.0, 3.5])
    body(doc, "实现后第一次 Ruff 报告 import 顺序错误。该问题不影响行为，但静态检查能防止风格漂移；调整 import 顺序后重新执行全量回归和 Ruff，全部通过。")

    heading(doc, "4 学到什么")
    body(doc, "环境变量是外部输入，不应因为来自部署环境就默认可信。配置解析要把字符串、数值合法性和产品错误提示分层处理。领域异常让底层保持准确，错误映射让用户获得可行动的说明，测试则保证这条边界在后续重构中不被破坏。")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)


if __name__ == "__main__":
    build()
