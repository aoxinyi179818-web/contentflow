"""Create the Step 48 security baseline learning document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT = Path("docs/33-security-baseline.docx")
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
    set_font(title.add_run("ContentFlow AI 基础安全基线"), size=21, bold=True, color=RGBColor(0, 0, 0))
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(16)
    set_font(subtitle.add_run("项目生命周期 Step 48  本地 MVP 的输入 工具 文件与输出边界"), size=10.5, color=RGBColor(89, 89, 89))

    body(
        doc,
        "本阶段为 ContentFlow 建立可验证的基础安全线。目标不是把本地 MVP 包装成生产级平台，而是明确哪些输入、工具、文件和 AI 输出受到约束，哪些风险仍需要在后续版本处理。结论是：密钥不进入仓库，未校验输入不进入工作流，文件只能从允许目录读取，AI 结果必须带有核查边界。",
    )

    heading(doc, "1 已实现的安全控制")
    rows = [
        ("API Key", ".env 与 .gitignore", "密钥不进入代码或提交", "保留本机环境变量"),
        ("用户主题", "validate_topic", "拒绝空值 非字符串 超过 500 字", "工作流前阻断"),
        ("Tool 参数", "Pydantic SearchArguments", "限制 Query 与 max_results", "不执行未知 Tool"),
        ("文件读取", "read_allowed_text", "限定目录和扩展名", "拒绝绝对路径与越界"),
        ("Agent 循环", "max_iterations 与 Router 上限", "达到上限停止", "避免无限调用"),
        ("AI 内容", "结构化输出与界面提示", "提示核查关键事实", "不把生成内容当事实"),
        ("Research", "source_id 与 URL", "保留来源标识", "说明演示资料边界"),
    ]
    table(doc, ["对象", "机制", "控制效果", "当前边界"], rows, [0.82, 1.78, 2.22, 1.88])

    heading(doc, "2 文件路径安全设计")
    body(
        doc,
        "文件路径问题的核心不是“能不能读文件”，而是调用方能否借由路径读到不应读取的文件。新增的 read_allowed_text 会先解析路径，再验证它位于调用场景批准的根目录中，检查后缀是否允许，并且只读取常规文件。Prompt 只能读取 prompts 目录下批准名称对应的 Markdown；RAG 评测只能读取 data 目录下的 JSON。",
    )
    bullets(
        doc,
        [
            "拒绝 ../ 逃逸和根目录外的绝对路径。",
            "拒绝把 Markdown 当作评测 JSON 或把任意扩展名当作 Prompt。",
            "不存在的批准文件只返回通用错误，不在异常文本中披露完整路径。",
            "当前版本没有用户文件上传；若将来加入上传，需要单独设计大小限制、病毒扫描、内容类型校验和隔离存储。",
        ],
    )

    heading(doc, "3 AI 输出和资料的可靠性边界")
    body(
        doc,
        "Structured Output 只保证字段形状正确，不保证模型结论真实。界面明确提示用户核查关键事实、引用和适用范围。Research Agent 的系统指令要求依据工具结果总结并标注 source_id；RAG Context 同时带来源标题、URL 和片段。当前工具返回的是本地演示语料，因此不能宣传为实时网络研究。",
    )

    heading(doc, "4 安全测试与一次 Debug")
    rows = [
        ("路径允许", "批准目录内 JSON", "成功读取 UTF 8 文本"),
        ("路径拒绝", "目录外文件与错误后缀", "抛出安全异常，不读取内容"),
        ("缺失文件", "批准目录内不存在文件", "返回通用不存在错误"),
        ("密钥卫生", ".gitignore", "确认 .env 被忽略"),
        ("Debug", "测试文件名写错", "目录清单确认 test_prompting 后重跑"),
    ]
    table(doc, ["验证点", "输入或现象", "结果"], rows, [1.1, 2.5, 3.1])
    body(
        doc,
        "本阶段第一次定向测试没有运行，因为命令引用了不存在的 test_prompt_loading.py，随后又误用了 test_prompt_files.py。通过列出 tests 目录确认真实入口为 test_prompting.py 后，17 条定向测试通过，最终全量回归 88 passed，Ruff 也通过。这个问题不是产品缺陷，但说明安全验证流程同样需要从实际文件清单或项目配置获得输入。",
    )

    heading(doc, "5 当前未覆盖的风险")
    rows = [
        ("账号与权限", "无登录和多用户隔离", "部署前引入身份认证与授权模型"),
        ("数据保护", "SQLite 未做静态加密", "确认数据分类与备份策略"),
        ("滥用控制", "无公网限流和配额", "接入限流 审计与预算阈值"),
        ("内容治理", "无专业审核系统", "按目标场景设计人工复核与政策"),
        ("外部资料", "当前是本地演示语料", "接入真实搜索前审查来源与许可"),
    ]
    table(doc, ["风险领域", "当前状态", "后续处理"], rows, [1.35, 2.45, 2.9])

    heading(doc, "6 本阶段学习总结")
    body(
        doc,
        "你学会了将安全落实为秘密、输入、Tool、文件、循环、AI 输出和来源的可验证边界。当前本地 MVP 已明确能力限制，下一阶段才进入 Git 工作流。",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)


if __name__ == "__main__":
    build()
