"""Create the Step 43 learning record as a polished Word document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/28-failure-handling.docx")
BLUE = "17365D"
LIGHT_BLUE = "EAF2F8"
LIGHT_GRAY = "F7F7F7"
GRID = "D9D9D9"


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    tc_pr.append(shading)


def set_cell_border(cell, color: str = GRID) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = qn(f"w:{edge}")
        element = borders.find(tag)
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "6")
        element.set(qn("w:color"), color)


def set_cell_margins(
    cell, top: int = 100, start: int = 110, bottom: int = 100, end: int = 110
) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_column_width(cell, width_inches: float) -> None:
    cell.width = Inches(width_inches)
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.first_child_found_in("w:tcW")
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(int(width_inches * 1440)))
    tc_w.set(qn("w:type"), "dxa")


def style_run(
    run, *, bold: bool = False, color: RGBColor | None = None, size: float = 10.5
) -> None:
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def add_body(doc: Document, text: str, *, bold_lead: str | None = None) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(7)
    paragraph.paragraph_format.line_spacing = 1.35
    if bold_lead and text.startswith(bold_lead):
        lead = paragraph.add_run(bold_lead)
        style_run(lead, bold=True)
        remainder = paragraph.add_run(text[len(bold_lead) :])
        style_run(remainder)
    else:
        style_run(paragraph.add_run(text))


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    paragraph = doc.add_paragraph(style=f"Heading {level}")
    paragraph.paragraph_format.space_before = Pt(14 if level == 1 else 9)
    paragraph.paragraph_format.space_after = Pt(6)
    run = paragraph.add_run(text)
    style_run(run, bold=True, color=RGBColor(0, 0, 0), size=14 if level == 1 else 11.5)


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(4)
        paragraph.paragraph_format.line_spacing = 1.25
        style_run(paragraph.add_run(item))


def add_matrix(doc: Document) -> None:
    rows = [
        (
            "API Key 错误",
            "配置校验或认证失败",
            "模型配置不可用",
            "检查 API Key、模型名和服务地址。",
        ),
        ("LLM Timeout", "模型调用超过超时设置", "AI 服务响应超时", "稍后重试；必要时增加超时。"),
        ("Search Timeout", "研究工具未在预算内返回", "资料检索超时", "停止本轮，避免无证据写作。"),
        (
            "Invalid JSON",
            "模型输出不符合 Pydantic 合同",
            "模型结果格式异常",
            "重试；持续发生时检查提示词。",
        ),
        ("RAG 无结果", "检索不到相关证据片段", "非异常，进入谨慎写作", "明确提示缺少可支撑资料。"),
        ("Agent 超限", "超过最大工具调用轮数", "资料检索已达到上限", "缩小主题范围后重试。"),
        (
            "Rewrite 循环",
            "低分但达到改写次数上限",
            "完成并标记上限状态",
            "保留结果，避免无限循环。",
        ),
        ("空输入", "清理空白后无主题", "请输入可用主题", "在调用模型前拦截。"),
        ("超长输入", "主题超过 500 个字符", "请输入可用主题", "缩短主题后再提交。"),
        ("数据库异常", "SQLite 操作或地址不合法", "本地项目保存失败", "检查目录权限和数据库地址。"),
    ]
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    table.autofit = False
    widths = [1.05, 1.65, 1.25, 2.55]
    headers = ["场景", "触发边界", "产品反馈", "恢复策略"]
    for index, (header, width) in enumerate(zip(headers, widths, strict=True)):
        cell = table.rows[0].cells[index]
        set_column_width(cell, width)
        set_cell_shading(cell, BLUE)
        set_cell_border(cell)
        set_cell_margins(cell)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        style_run(paragraph.add_run(header), bold=True, color=RGBColor(255, 255, 255), size=9)
    set_repeat_table_header(table.rows[0])

    for row_index, values in enumerate(rows):
        cells = table.add_row().cells
        for index, (value, width) in enumerate(zip(values, widths, strict=True)):
            cell = cells[index]
            set_column_width(cell, width)
            set_cell_border(cell)
            set_cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if row_index % 2 == 1:
                set_cell_shading(cell, LIGHT_BLUE)
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.05
            paragraph.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER if index in (0, 2) else WD_ALIGN_PARAGRAPH.LEFT
            )
            style_run(paragraph.add_run(value), size=8.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def build_document() -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.68)
    section.bottom_margin = Inches(0.68)
    section.left_margin = Inches(0.72)
    section.right_margin = Inches(0.72)

    normal = doc.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(10.5)

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title.paragraph_format.space_after = Pt(8)
    style_run(
        title.add_run("ContentFlow AI 异常处理与失败场景设计"),
        bold=True,
        color=RGBColor(0, 0, 0),
        size=21,
    )
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(16)
    style_run(
        subtitle.add_run("项目生命周期 Step 43  学习记录与实现验证"),
        color=RGBColor(89, 89, 89),
        size=10.5,
    )

    add_body(
        doc,
        "本阶段的结论是：ContentFlow AI 已把常见失败从零散技术报错收敛为可识别、可测试、可恢复的产品行为。用户不会看到 API Key、SQLite 或模型协议的原始细节，而会获得下一步可执行的中文建议；未知程序错误仍会保留给开发阶段排查。",
    )

    add_heading(doc, "1 本阶段目标与产品价值")
    add_body(
        doc,
        "AI 应用的失败不是少数情况，而是正常交互的一部分。模型服务、工具调用、检索、数据库和用户输入都可能中断。如果没有预先设计，系统会把技术栈细节直接暴露给用户，用户也无法判断是否应该重试、修改主题还是检查配置。",
    )
    add_body(
        doc,
        "本阶段采用最小可行策略：把业务层异常和技术层异常翻译为统一的产品提示，同时让工作流保留严格边界。这样既降低用户困惑，也不通过笼统捕获异常掩盖真正的程序缺陷。",
    )

    add_heading(doc, "2 输入输出与职责设计")
    add_body(
        doc,
        "输入包含用户主题，以及 Planner、Research Agent、RAG、SQLite 和模型 SDK 抛出的已知异常。输出为 FailurePresentation，其字段为 code、title、message 和 retryable。页面仅展示标题和恢复建议；工作流与 Agent 不直接依赖 Streamlit。",
    )
    add_bullets(
        doc,
        [
            "输入校验层：validate_topic 统一去除空白，拒绝空主题和超过 500 个字符的主题。",
            "Research Agent：捕获工具的 TimeoutError 并转换为 SearchTimeoutError，保留原始错误链用于调试。",
            "错误呈现层：present_failure 根据异常类型返回稳定的中文文案，不返回 API Key 或底层路径等敏感实现信息。",
            "界面层：只处理已知失败；若分类结果为 unexpected，继续抛出异常，避免隐藏代码缺陷。",
        ],
    )

    add_heading(doc, "3 失败场景覆盖矩阵")
    add_body(
        doc,
        "以下矩阵覆盖 Skill 要求的十类场景。RAG 无结果和两类循环上限属于受控降级，不应该简单视为系统崩溃。",
    )
    add_matrix(doc)

    add_heading(doc, "4 实现落点")
    add_bullets(
        doc,
        [
            "新增 input_validation.py：把主题限制从页面逻辑提升到工作流入口，基础工作流与研究工作流共享同一规则。",
            "新增 error_handling.py：集中维护异常到产品提示的映射，避免每个页面重复判断。",
            "更新 agents/research.py：为搜索超时定义领域异常，调用方可以区分模型超时与检索超时。",
            "更新 app.py：通过统一提示层展示错误，但不吞掉未知异常。",
            "保留原有保护：format_writer_context 在 RAG 无结果时要求谨慎写作；质量路由和研究路由分别以最大改写次数、最大研究次数停止循环。",
        ],
    )

    add_heading(doc, "5 测试与 Debug 记录")
    add_body(
        doc,
        "新增测试覆盖了主题标准化、空输入、超长输入、API 配置、LLM 超时、搜索超时、无效结构化输出、Agent 超限和 SQLite 异常的稳定提示。Research Agent 的超时测试通过 monkeypatch 模拟慢检索，确认 TimeoutError 会被转换为 SearchTimeoutError。",
    )
    add_body(
        doc,
        "首次定向测试暴露了一个真实问题：补丁接线时 except 块缺少抛出语句，造成 Research Agent 模块导入失败。通过定位 IndentationError、补齐异常转换并重新格式化后，定向回归 21 项通过；随后全量测试 68 项通过，Ruff 静态检查和补丁检查均通过。",
    )

    add_heading(doc, "6 本阶段学习总结")
    add_bullets(
        doc,
        [
            "异常设计从用户恢复路径开始，而不是从 try except 开始。",
            "领域异常能让调用方区分超时来源，例如模型超时与资料检索超时的恢复动作不同。",
            "输入限制应在业务入口统一执行，不能只依赖前端页面。",
            "有边界的 Agent 循环和改写循环是可靠性设计的一部分。",
            "回归测试不仅证明功能正确，也帮助快速定位补丁和集成阶段的错误。",
        ],
    )
    add_body(
        doc,
        "下一阶段将进入 Step 44 测试策略：在已有用例基础上，按功能、接口、异常、边界、工作流和回归六类组织完整测试计划。",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
