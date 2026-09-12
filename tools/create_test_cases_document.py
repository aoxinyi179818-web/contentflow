"""Create the Step 45 acceptance test case document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT = Path("docs/30-test-cases.docx")
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


def style_cell(cell, *, fill: str | None = None) -> None:
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    tc_pr = cell._tc.get_or_add_tcPr()
    margins = OxmlElement("w:tcMar")
    for side in ("top", "start", "bottom", "end"):
        edge = OxmlElement(f"w:{side}")
        edge.set(qn("w:w"), "105")
        edge.set(qn("w:type"), "dxa")
        margins.append(edge)
    tc_pr.append(margins)
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge = OxmlElement(f"w:{side}")
        edge.set(qn("w:val"), "single")
        edge.set(qn("w:sz"), "6")
        edge.set(qn("w:color"), GRID)
        borders.append(edge)
    tc_pr.append(borders)
    if fill:
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), fill)
        tc_pr.append(shading)


def set_width(cell, inches: float) -> None:
    cell.width = Inches(inches)
    tc_pr = cell._tc.get_or_add_tcPr()
    value = OxmlElement("w:tcW")
    value.set(qn("w:w"), str(int(inches * 1440)))
    value.set(qn("w:type"), "dxa")
    tc_pr.append(value)


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


def heading(doc: Document, text: str, level: int = 1) -> None:
    paragraph = doc.add_paragraph(style=f"Heading {level}")
    paragraph.paragraph_format.space_before = Pt(13 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(6)
    set_font(
        paragraph.add_run(text), size=14 if level == 1 else 11.5, bold=True, color=RGBColor(0, 0, 0)
    )


def body(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.35
    paragraph.paragraph_format.space_after = Pt(7)
    set_font(paragraph.add_run(text))


def bullets(doc: Document, values: list[str]) -> None:
    for value in values:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.line_spacing = 1.2
        paragraph.paragraph_format.space_after = Pt(3)
        set_font(paragraph.add_run(value))


def table(
    doc: Document, headers: list[str], rows: list[tuple[str, ...]], widths: list[float]
) -> None:
    output = doc.add_table(rows=1, cols=len(headers))
    output.style = "Table Grid"
    output.autofit = False
    for index, value in enumerate(headers):
        cell = output.rows[0].cells[index]
        set_width(cell, widths[index])
        style_cell(cell, fill=BLUE)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(paragraph.add_run(value), size=8.5, bold=True, color=RGBColor(255, 255, 255))
    row_properties = output.rows[0]._tr.get_or_add_trPr()
    repeated = OxmlElement("w:tblHeader")
    repeated.set(qn("w:val"), "true")
    row_properties.append(repeated)
    for row_index, values in enumerate(rows):
        cells = output.add_row().cells
        for index, value in enumerate(values):
            cell = cells[index]
            set_width(cell, widths[index])
            style_cell(cell, fill=PALE_BLUE if row_index % 2 else None)
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.line_spacing = 1.05
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER if index in (0, 1, 4) else WD_ALIGN_PARAGRAPH.LEFT
            )
            set_font(paragraph.add_run(value), size=8.1)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def build() -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.68)
    section.bottom_margin = Inches(0.68)
    section.left_margin = Inches(0.65)
    section.right_margin = Inches(0.65)
    normal = doc.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(10.5)

    title = doc.add_paragraph(style="Title")
    clear_paragraph_borders(title)
    title.paragraph_format.space_after = Pt(8)
    set_font(
        title.add_run("ContentFlow AI 验收测试用例"), size=21, bold=True, color=RGBColor(0, 0, 0)
    )
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(16)
    set_font(
        subtitle.add_run("项目生命周期 Step 45  TC01 至 TC10 自动化测试基线"),
        size=10.5,
        color=RGBColor(89, 89, 89),
    )

    body(
        doc,
        "本阶段已将测试策略落为 10 条带编号的自动化验收用例。每条用例都对应当前 MVP 的可观察行为，并连接到产品验收标准、固定测试数据与实际测试函数。TC01 至 TC10 已在本地通过，不依赖真实 API Key、网络或生产数据库。",
    )

    heading(doc, "1 执行范围与判定")
    body(
        doc,
        "本组用例覆盖正常主题、空主题、超长主题、模型错误、结构化输出、质量路由、研究路由、工具超时、改写上限和 SQLite 持久化。通过条件是：测试中的 Given 条件成立后，系统输出与 Then 断言一致，且不产生真实模型调用。",
    )
    bullets(
        doc,
        [
            "执行入口：tests/test_acceptance_cases.py。",
            "隔离方式：Fake 工作流服务、构造的 HTTP 错误、monkeypatch 和 pytest tmp_path。",
            "回归命令：.venv\\Scripts\\python.exe -m pytest tests\\test_acceptance_cases.py -q。",
            "发布前仍需执行完整 pytest、Ruff 与 PRD 中 Must 场景的人工验收。",
        ],
    )

    heading(doc, "2 TC01 至 TC10 用例矩阵")
    cases = [
        (
            "TC01",
            "AC-IN-01 AC-PL-01 AC-FN-01",
            "有效主题",
            "完成 Planner Write Review Final",
            "通过",
        ),
        ("TC02", "AC-IN-02", "空白主题", "工作流前拒绝", "通过"),
        ("TC03", "AC-IN-04", "501 字主题", "提示超长且不进入下游", "通过"),
        ("TC04", "AC-PL-06 AC-ST-04", "Timeout 401 500", "返回安全且可行动的提示", "通过"),
        ("TC05", "AC-PL-06", "缺字段 JSON", "结构化合同拒绝结果", "通过"),
        ("TC06", "AC-RW-01", "Review 分数 70", "执行一次 Rewrite 后复审", "通过"),
        ("TC07", "AC-RS-03 AC-ST-02", "Evidence 分数 10", "回到 Research 并完成第二轮", "通过"),
        ("TC08", "AC-RS-03", "Search Timeout", "转换为 SearchTimeoutError", "通过"),
        ("TC09", "AC-ST-07", "持续低分", "达到上限后停止循环", "通过"),
        ("TC10", "AC-HI-01", "完成的项目工件", "SQLite 保存后可完整读取", "通过"),
    ]
    table(
        doc,
        ["编号", "验收追溯", "Given 输入或事件", "Then 关键断言", "结果"],
        cases,
        [0.52, 1.37, 1.48, 2.55, 0.52],
    )

    heading(doc, "3 用例实现说明")
    details = [
        "TC01 使用固定的高分 ReviewReport 和 Fake 节点服务，验证有效主题按 Planner、Writer、Reviewer 顺序到达 Final。",
        "TC02 与 TC03 直接验证共享输入校验器，确保页面以外的工作流入口也无法绕过边界规则。",
        "TC04 在本地构造 TimeoutError、AuthenticationError 401 和 InternalServerError 500，断言只返回中文恢复分类，不出现密钥或供应商堆栈。",
        "TC05 传入缺少必填字段的 JSON，确认 Pydantic 合同阻止不完整内容成为 ContentPlan。",
        "TC06 与 TC09 分别验证低分触发改写、改写次数到达配置上限时停止，防止质量循环无限运行。",
        "TC07 用两次固定 Evidence 分数模拟资料不足后重新研究，断言调用序列和 research_count 都正确。",
        "TC08 通过 monkeypatch 模拟本地 Search 工具超时，确认工具层异常被翻译为可识别的领域异常。",
        "TC10 使用 tmp_path 下的临时 SQLite 文件，确认完成项目保存后可按 ID 读回完整工件。",
    ]
    bullets(doc, details)

    heading(doc, "4 测试数据与 Debug 记录")
    body(
        doc,
        "首次运行中，TC01、TC07 与 TC10 失败。原因不是应用实现，而是测试工厂为 90 分评审固定分配了前三项各 20 分，从而把完整度算成 30，超过数据合同规定的单项上限 25。修复后，工厂函数按四个维度分配不超过 25 的合法分数，10 条用例全部通过。",
    )
    body(
        doc,
        "这个 Debug 说明测试数据本身也是产品合同的一部分。测试不能只追求总分正确，还要满足每个字段的业务约束；否则测试失败会错误地指向被测功能。",
    )

    heading(doc, "5 本阶段学习总结")
    body(
        doc,
        "测试编号让产品需求、自动化实现和缺陷记录有了共同语言。对 AI 工作流而言，最有价值的断言是状态、结构、边界和调用顺序，而不是模型输出的逐字一致。下一阶段将进入 Step 46，沿 UI 到数据库的数据链路建立系统化 Debug 方法。",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)


if __name__ == "__main__":
    build()
