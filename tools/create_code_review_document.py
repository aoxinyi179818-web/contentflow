"""Create the Step 50 code review learning document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUTPUT = Path("docs/35-code-review.docx")
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


def remove_title_border(paragraph) -> None:
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
        edge.set(qn("w:w"), "100")
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


def add_heading(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph(style="Heading 1")
    paragraph.paragraph_format.space_before = Pt(10)
    paragraph.paragraph_format.space_after = Pt(5)
    set_font(paragraph.add_run(text), size=14, bold=True, color=RGBColor(0, 0, 0))


def add_body(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.22
    paragraph.paragraph_format.space_after = Pt(5)
    set_font(paragraph.add_run(text))


def add_bullets(doc: Document, values: list[str]) -> None:
    for value in values:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.line_spacing = 1.1
        paragraph.paragraph_format.space_after = Pt(1)
        set_font(paragraph.add_run(value))


def add_table(doc: Document, headers: list[str], rows: list[tuple[str, ...]], widths: list[float]) -> None:
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
    header_props = output.rows[0]._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    header_props.append(header)
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
            set_font(paragraph.add_run(value), size=8.1)
        row_properties = output.rows[-1]._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        row_properties.append(cant_split)
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
    remove_title_border(title)
    title.paragraph_format.space_after = Pt(8)
    set_font(title.add_run("ContentFlow AI 代码 Review"), size=21, bold=True, color=RGBColor(0, 0, 0))
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(16)
    set_font(subtitle.add_run("项目生命周期 Step 50  模块职责 配置边界与可维护性检查"), size=10.5, color=RGBColor(89, 89, 89))

    add_body(
        doc,
        "本次 Review 的结论是：当前 MVP 没有发现阻塞演示或导致密钥泄露的 P1 问题，且 88 条测试和 Ruff 均通过。代码已经具备明确的 Prompt 外置、Pydantic 数据契约、有限循环、可观察日志和分层存储。部署前仍建议处理 3 个 P2 可维护性问题，并明确 1 个 P3 的本地 CLI 文件边界。",
    )

    add_heading(doc, "1 Review 范围和结果")
    rows = [
        ("范围", "app Python 模块 Prompt 配置 测试", "覆盖主工作流 研究流程 数据库与安全边界"),
        ("P1 阻塞", "0", "无密钥硬编码 无异常静默吞掉 无无限循环"),
        ("P2 优先", "3", "部署前建议修正，降低配置和演进风险"),
        ("P3 改进", "1", "本地 CLI 未来暴露前需要收紧边界"),
        ("验证", "88 passed Ruff passed", "全量回归与静态检查均通过"),
    ]
    add_table(doc, ["维度", "结果", "说明"], rows, [1.1, 1.8, 3.8])

    add_heading(doc, "2 已通过的工程检查")
    add_bullets(
        doc,
        [
            "模块按 UI 工作流 Agent RAG 数据库和工具分层，UI 不直接实现模型调用；Prompt 存在 prompts 目录并按白名单加载。",
            "ContentPlan ReviewReport 和 Tool 参数使用 Pydantic 校验；质量路由与 Research Agent 都有限制循环次数。",
            "API Key 只从环境变量读取，日志过滤敏感字段；异常通常记录后重新抛出，再由 UI 转成稳定中文提示。",
            "没有发现空 catch 或 pass 吞错；全量回归 88 passed，Ruff 通过。",
        ],
    )

    add_heading(doc, "3 需要处理的 Review 发现")
    rows = [
        (
            "P2",
            "配置数值解析",
            "config from env 第 30 行",
            "非法 LLM timeout 会直接抛 ValueError，UI 归类为未预期错误",
            "转换为领域配置错误并加入非法值测试",
        ),
        (
            "P2",
            "LLM 客户端重复",
            "7 处 OpenAI 初始化",
            "模型校验 base url timeout 和 usage 逻辑易逐步不一致",
            "抽取共享 client factory，节点保留自己的业务输入和输出",
        ),
        (
            "P2",
            "Research 图策略硬编码",
            "research graph 93 至 304 行",
            "阈值 上限和平台默认值分散在 invoke 状态中，图构建函数也过长",
            "引入 WorkflowPolicy，将节点工厂与路由策略拆分",
        ),
        (
            "P3",
            "CLI 文件读取边界",
            "writer reviewer rewriter 命令入口",
            "直接 read text 适合本地开发，但未复用 allow list 规则",
            "保持仅本机开发用途；若开放上传或服务接口，改为受控目录和类型校验",
        ),
    ]
    add_table(doc, ["级别", "发现", "证据", "风险", "最小修复"], rows, [0.45, 1.15, 1.45, 2.0, 1.65])

    add_heading(doc, "4 一次可复现的配置 Debug")
    add_body(
        doc,
        "将 LLM_TIMEOUT_SECONDS 设置为 not a number 后调用 Settings from env，会在 float 转换处得到 ValueError。这个异常不属于 present failure 已知分类，因此界面会重新抛出它。问题不是模型调用失败，而是环境配置在解析阶段缺少领域校验。修复后应让用户看到模型配置不可用，并保留原始异常供日志定位。",
    )
    add_bullets(
        doc,
        [
            "输入：LLM_TIMEOUT_SECONDS 等于 not a number。",
            "现象：Settings from env 抛出 ValueError。",
            "定位：环境变量到 float 转换没有捕获和归类。",
            "回归：新增正数 非数字和非正数 timeout 的单元测试。",
        ],
    )

    add_heading(doc, "5 推荐的最小重构顺序")
    rows = [
        ("1", "配置边界", "Settings 输出已校验的 timeout，错误可被 present failure 识别"),
        ("2", "客户端工厂", "输入 Settings，输出已配置 OpenAI client，统一模型前置校验"),
        ("3", "研究策略", "输入 WorkflowPolicy，输出可测试的阈值和循环预算"),
        ("4", "CLI 边界", "明确 local only，未来外部入口使用 safe file reader"),
    ]
    add_table(doc, ["顺序", "模块", "完成标准"], rows, [0.55, 1.5, 4.65])
    add_body(
        doc,
        "这些重构不改变产品流程，也不需要引入新 Agent 或框架；目标是集中可变配置和重复基础设施。",
    )

    add_heading(doc, "6 本阶段学习总结")
    add_body(
        doc,
        "代码 Review 先确认设计能否支撑产品目标，再把影响可维护性、安全边界和故障体验的问题按优先级排队。当前建议先修复 3 个 P2，再进入部署前检查。",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)


if __name__ == "__main__":
    build()
