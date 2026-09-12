from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT = Path(r"D:\contextai\docs\09-acceptance-criteria.docx")

# standard_business_brief preset + named Chinese-font override
PAGE_W = Inches(8.5)
PAGE_H = Inches(11)
MARGIN = Inches(1)
CONTENT_DXA = 9360
TABLE_INDENT_DXA = 120
CELL_TOP_BOTTOM = 80
CELL_START_END = 120
BLUE = "2E74B5"
DARK_BLUE = "1F4D78"
INK = "182230"
MUTED = "667085"
LIGHT = "F2F4F7"
CALLOUT = "F4F6F9"
GREEN = "067647"
GREEN_BG = "ECFDF3"
AMBER = "7A5A00"
AMBER_BG = "FFFAEB"
RED = "9B1C1C"
WHITE = "FFFFFF"
BORDER = "D0D5DD"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=CELL_TOP_BOTTOM, start=CELL_START_END,
                     bottom=CELL_TOP_BOTTOM, end=CELL_START_END):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.find(qn("w:tcMar"))
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


def set_table_geometry(table, widths, indent=TABLE_INDENT_DXA):
    assert sum(widths) == CONTENT_DXA
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(CONTENT_DXA))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), str(indent))
    tbl_ind.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(widths[idx]))
            tc_w.set(qn("w:type"), "dxa")
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def set_run(run, size=None, bold=None, color=INK, ascii_font="Calibri", east_asia="Microsoft YaHei"):
    run.font.name = ascii_font
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), ascii_font)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), ascii_font)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), east_asia)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def format_cell(cell, bold=False, color=INK, size=9.2):
    for paragraph in cell.paragraphs:
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.line_spacing = 1.05
        for run in paragraph.runs:
            set_run(run, size=size, bold=bold, color=color)


def add_table(doc, headers, rows, widths, header_fill=LIGHT, font_size=9.2):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for i, header in enumerate(headers):
        table.rows[0].cells[i].text = header
        set_cell_shading(table.rows[0].cells[i], header_fill)
        format_cell(table.rows[0].cells[i], bold=True, color=DARK_BLUE, size=font_size)
    set_repeat_header(table.rows[0])
    for row_data in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row_data):
            cells[i].text = str(value)
            format_cell(cells[i], size=font_size)
    set_table_geometry(table, widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_callout(doc, label, text, fill=CALLOUT, color=DARK_BLUE):
    table = doc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(f"{label}  ")
    set_run(r, size=10.5, bold=True, color=color)
    r = p.add_run(text)
    set_run(r, size=10.5, color=INK)
    set_table_geometry(table, [CONTENT_DXA])
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    p.add_run(text)
    return p


def add_number(doc, text):
    p = doc.add_paragraph(style="List Number")
    p.add_run(text)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.keep_with_next = True
    return p


def add_scenario(doc, scenario):
    sid, title, priority, source, given, when, then = scenario
    p = doc.add_paragraph()
    p.style = "Heading 3"
    p.paragraph_format.keep_with_next = True
    r = p.add_run(f"{sid}  {title}")
    r.bold = True
    meta = doc.add_paragraph()
    meta.paragraph_format.space_after = Pt(3)
    r = meta.add_run(f"[{priority}]  追溯：{source}")
    set_run(r, size=9, bold=True, color=GREEN if priority == "Must" else AMBER)
    for label, value in (("Given", given), ("When", when), ("Then", then)):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.18)
        p.paragraph_format.first_line_indent = Inches(-0.18)
        p.paragraph_format.space_after = Pt(3 if label != "Then" else 8)
        p.paragraph_format.line_spacing = 1.1
        r = p.add_run(f"{label}  ")
        set_run(r, size=10, bold=True, color=DARK_BLUE)
        r = p.add_run(value)
        set_run(r, size=10, color=INK)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("第 ")
    set_run(run, size=9, color=MUTED)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    paragraph._p.append(fld)
    run = paragraph.add_run(" 页")
    set_run(run, size=9, color=MUTED)


doc = Document()
section = doc.sections[0]
section.page_width = PAGE_W
section.page_height = PAGE_H
section.top_margin = MARGIN
section.right_margin = MARGIN
section.bottom_margin = MARGIN
section.left_margin = MARGIN
section.header_distance = Inches(0.492)
section.footer_distance = Inches(0.492)

styles = doc.styles
normal = styles["Normal"]
normal.font.name = "Calibri"
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
normal.font.size = Pt(11)
normal.font.color.rgb = RGBColor.from_string(INK)
normal.paragraph_format.space_before = Pt(0)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.10

for name, size, color, before, after in (
    ("Heading 1", 16, BLUE, 16, 8),
    ("Heading 2", 13, BLUE, 12, 6),
    ("Heading 3", 11.5, DARK_BLUE, 8, 4),
):
    style = styles[name]
    style.font.name = "Calibri"
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    style.font.size = Pt(size)
    style.font.bold = True
    style.font.color.rgb = RGBColor.from_string(color)
    style.paragraph_format.space_before = Pt(before)
    style.paragraph_format.space_after = Pt(after)
    style.paragraph_format.keep_with_next = True

for name in ("List Bullet", "List Number"):
    style = styles[name]
    style.font.name = "Calibri"
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    style.font.size = Pt(11)
    style.paragraph_format.left_indent = Inches(0.5)
    style.paragraph_format.first_line_indent = Inches(-0.25)
    style.paragraph_format.space_after = Pt(8)
    style.paragraph_format.line_spacing = 1.167

header = section.header.paragraphs[0]
header.alignment = WD_ALIGN_PARAGRAPH.LEFT
header.paragraph_format.space_after = Pt(0)
r = header.add_run("CONTENTFLOW AI  /  PRODUCT ACCEPTANCE")
set_run(r, size=8.5, bold=True, color=MUTED)
add_page_number(section.footer.paragraphs[0])

# Memo masthead
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(16)
p.paragraph_format.space_after = Pt(4)
r = p.add_run("产品验收标准")
set_run(r, size=24, bold=True, color=INK)
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(16)
r = p.add_run("ContentFlow AI · MVP Acceptance Criteria v1.0")
set_run(r, size=13, color=MUTED)

metadata = [
    ("生命周期阶段", "第九部分 / Step 13：需求转验收标准"),
    ("验收对象", "Plan → Research → Write → Review → Rewrite → Final 的 MVP 闭环"),
    ("依据", "PRD、功能清单、MVP 定义、User Flow、Figma 原型"),
    ("目标读者", "产品、设计、开发、测试及 AI 应用开发学习者"),
    ("文档状态", "Baseline v1.0 / 开发前验收基线"),
]
for label, value in metadata:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(f"{label}：")
    set_run(r, size=10.5, bold=True)
    r = p.add_run(value)
    set_run(r, size=10.5)

add_callout(
    doc,
    "阶段结论",
    "本文件把产品需求转换为可执行、可复现、可追溯的验收条件。开发完成不等于验收通过；只有场景结果满足、阻断缺陷关闭并保留证据，功能才可进入下一阶段。",
    GREEN_BG,
    GREEN,
)

add_heading(doc, "1. 为什么需要验收标准", 1)
doc.add_paragraph(
    "PRD 描述产品需要解决的问题，验收标准描述可观察的完成状态。它让产品、开发和测试使用同一套判断依据，防止“功能做了但无法证明做对”，也避免把模型一次偶然生成的好结果误认为系统稳定。"
)
add_bullet(doc, "把模糊词转换为可观察行为，例如把“结果质量好”拆成结构完整、约束遵循、问题可定位和风险有提示。")
add_bullet(doc, "把主路径、异常路径和边界条件同时纳入开发范围。")
add_bullet(doc, "为后续测试用例、回归测试和缺陷优先级提供直接来源。")
add_bullet(doc, "让生成式 AI 的非确定性通过固定测试集、结构校验和人工评分共同管理。")

add_heading(doc, "2. 验收范围与边界", 1)
add_table(
    doc,
    ["范围", "本阶段验收定义", "发布处理"],
    [
        ("Must Have", "任务输入、Planner、Writer、Reviewer、Rewrite、Final、状态反馈、错误恢复、版本保留", "全部通过才能发布 MVP"),
        ("Should Have", "基础 Research、历史记录、版本差异、阶段级重试", "按开发计划启用；未启用时必须明确标记，不得伪装可用"),
        ("Could Have", "多平台 Adapter、RAG、Visual Agent、自动配图", "不进入本轮发布门槛"),
        ("明确延期", "前端界面中文化", "前端阶段必须以简体中文为主，并执行文字溢出回归"),
        ("明确不包含", "多人协作、复杂权限、自动发布、视频生产", "不得作为 MVP 完成条件"),
    ],
    [1800, 4860, 2700],
)
add_callout(doc, "AI 验收原则", "不验收逐字一致；验收输入输出结构、关键约束、状态行为、失败恢复、事实风险提示和固定样例下的质量下限。")

add_heading(doc, "3. 验收语言与判定规则", 1)
add_heading(doc, "3.1 Given / When / Then", 2)
add_table(
    doc,
    ["关键字", "含义", "写法要求"],
    [
        ("Given", "场景前置条件和已有数据", "必须可建立，不写实现细节"),
        ("When", "用户动作或系统事件", "每个场景只描述一个主要触发动作"),
        ("Then", "用户可观察结果和系统状态", "结果必须可检查，必要时包含数据保留和下一步操作"),
    ],
    [1440, 2880, 5040],
)
add_heading(doc, "3.2 结果状态", 2)
add_bullet(doc, "Pass：场景所有 Then 条件均满足，并保留截图、日志、结构化输出或测试记录。")
add_bullet(doc, "Fail：任一关键结果不满足、结果无法复现，或出现未声明的降级行为。")
add_bullet(doc, "Blocked：依赖环境或服务不可用，暂时无法执行；必须记录原因、责任人和恢复条件。")
add_bullet(doc, "Not Applicable：功能已从当前范围正式移除，并有产品决策记录；不能用它掩盖未完成。")

add_heading(doc, "4. MVP 总体验收门槛", 1)
release_gate = [
    ("AC-G-01", "核心闭环", "一次有效任务可完成输入、规划、写作、评审、必要改写和最终内容交付。"),
    ("AC-G-02", "用户控制", "计划确认、问题处理、最终发布判断均保留用户操作入口。"),
    ("AC-G-03", "失败可恢复", "任何 AI 阶段失败时，最近成功输入和输出仍可访问，用户可重试或返回。"),
    ("AC-G-04", "可追溯", "每次运行至少可关联任务、阶段、时间、状态和输出版本。"),
    ("AC-G-05", "安全底线", "前端、复制内容、日志和版本中不暴露 API Key、系统 Prompt 或内部调试信息。"),
    ("AC-G-06", "质量底线", "固定验收样例中，结构化输出可解析率和人工质量评分达到约定阈值。"),
]
add_table(doc, ["ID", "门槛", "通过条件"], release_gate, [1300, 1800, 6260])

sections = [
    ("5.1 任务创建与输入校验", [
        ("AC-IN-01", "有效输入可开始任务", "Must", "FR-01 / F-01~F-03", "用户已填写非空主题，并选择或填写目标受众、内容类型和输出形式。", "用户点击“开始创作”。", "系统通过校验、创建唯一任务并进入 Planner；页面显示任务摘要和运行状态，且不会重复创建任务。"),
        ("AC-IN-02", "主题为空时阻止提交", "Must", "FR-01 / User Flow 02", "主题为空、仅包含空格或换行，其他字段任意。", "用户点击“开始创作”。", "系统不启动 Planner；主题字段显示明确错误并获得焦点，用户已填写的其他内容保持不变。"),
        ("AC-IN-03", "缺少可补全的约束", "Must", "FR-01 / PRD 7.1", "主题有效，但受众、语气或篇幅缺失。", "用户提交任务。", "系统逐项提示缺失信息；若产品提供默认值，必须显示默认假设并允许用户确认或修改后继续。"),
        ("AC-IN-04", "超长输入得到可执行反馈", "Must", "NFR / 边界场景", "任一输入超过前端或服务端约定上限。", "用户提交任务。", "系统阻止提交或安全截断前给出字数上限和当前字数；不得静默丢弃内容。"),
        ("AC-IN-05", "重复点击只产生一次运行", "Must", "FR-02 / Prototype", "有效输入已经提交，Planner 状态为 Running。", "用户连续点击主按钮或重复提交请求。", "主按钮进入禁用/加载状态；同一任务阶段只保留一个有效运行记录。"),
        ("AC-IN-06", "用户输入被完整保留", "Must", "FR-03", "用户填写了主题、受众、平台、语气、篇幅和禁用内容。", "页面刷新、阶段失败或用户返回输入页。", "最近保存的输入能够恢复；任何字段变化均可被用户再次编辑。"),
    ]),
    ("5.2 Planner 内容规划", [
        ("AC-PL-01", "计划输出结构完整", "Must", "FR-04 / F-04~F-05", "任务输入有效且 Planner 服务可用。", "Planner 完成一次运行。", "输出至少包含内容目标、目标受众假设、语气、章节顺序及每章写作意图；不能只返回标题列表或一段未分段文本。"),
        ("AC-PL-02", "计划遵循用户约束", "Must", "FR-04", "任务包含明确受众、内容类型、平台、语气和篇幅约束。", "Planner 生成计划。", "计划显式反映这些约束；若存在冲突，系统指出冲突并请求用户决策，不得静默忽略。"),
        ("AC-PL-03", "计划确认是写作前置条件", "Must", "FR-05 / User Flow 04", "Planner 已成功，但计划尚未被用户确认。", "用户尝试直接生成最终稿或进入 Writer。", "系统阻止进入 Writer，并引导用户确认、编辑或重新生成计划。"),
        ("AC-PL-04", "计划可编辑并保存", "Must", "FR-05 / F-06", "用户正在查看 Planner 输出。", "用户修改章节标题、顺序或写作意图并点击确认。", "系统保存修改后的完整计划；Writer 接收到的是确认版本而非原始版本。"),
        ("AC-PL-05", "重新规划不覆盖历史结果", "Must", "FR-03 / Version", "任务已有一次 Planner 成功结果。", "用户修改输入并重新运行 Planner。", "系统创建新的计划运行记录，并保留上一版本的时间、状态和可查看结果。"),
        ("AC-PL-06", "Planner 失败可恢复", "Must", "PRD 7.2 / User Flow 失败路径", "Planner 返回超时、服务错误或不可解析结果。", "系统判定本次运行失败。", "页面显示失败原因和“重试/修改输入/保存退出”操作；任务输入不丢失，失败不被显示成空计划。"),
    ]),
    ("5.3 基础 Research", [
        ("AC-RS-01", "研究结果区分来源与推断", "Should", "FR-06 / F-07~F-10", "计划已确认，Research 能获得至少一条资料。", "Research 完成。", "每条结果包含摘要和来源标识；模型推断、无来源信息和待核实内容使用不同状态清晰标记。"),
        ("AC-RS-02", "资料与内容计划有关联", "Should", "FR-06 / F-09", "Research 返回多条资料，计划包含多个章节。", "用户查看研究结果。", "用户能判断每条资料支持哪个主题或章节；无关资料不会自动进入 Writer 上下文。"),
        ("AC-RS-03", "来源失败不伪造内容", "Should", "PRD 失败场景", "搜索服务失败、网页无法访问或没有结果。", "Research 结束。", "系统明确显示失败或资料不足，不生成虚构来源；用户可以重试、导入资料或跳过该步骤。"),
        ("AC-RS-04", "用户可以排除资料", "Should", "PRD 4.1", "研究结果中存在用户不信任或不相关的资料。", "用户将该资料标记为不采用。", "Writer 的输入上下文不包含被排除资料，资料状态和用户选择被保留。"),
        ("AC-RS-05", "Research 延期时有明确降级", "Should", "MVP 范围决策", "当前构建未启用外部 Research。", "用户开始任务。", "界面明确说明将基于用户输入和模型知识生成，并提示事实需人工核实；不得展示虚假的来源覆盖率。"),
    ]),
    ("5.4 Writer 初稿生成", [
        ("AC-WR-01", "基于确认计划生成初稿", "Must", "FR-07 / F-11", "存在用户确认的计划和可用资料上下文。", "Writer 完成运行。", "初稿按确认章节顺序生成，主要观点与写作意图一致，并与当前任务和计划版本建立关联。"),
        ("AC-WR-02", "遵循内容约束", "Must", "FR-07", "任务设置了目标受众、语气、平台、篇幅和禁用内容。", "Writer 生成初稿。", "初稿满足可自动检查的格式和篇幅约束；主观语气通过人工抽检，禁用内容不得出现。"),
        ("AC-WR-03", "初稿可阅读和编辑", "Must", "PRD 目标 / Prototype Result", "Writer 已成功输出初稿。", "用户打开 Draft。", "系统展示标题、章节和正文，不混入 JSON、系统指令、调试日志或不可见控制字符；用户可以编辑并保存。"),
        ("AC-WR-04", "事实风险得到标记", "Must", "PRD 7.1", "初稿包含无法从已采纳资料确认的具体事实、数字或强结论。", "Writer 输出内容。", "相关位置带有待核实提示或低置信标记；不得把模型推断伪装为已验证事实。"),
        ("AC-WR-05", "Writer 失败保留计划", "Must", "User Flow 失败路径", "计划已确认，Writer 超时或返回空内容。", "系统判定运行失败。", "计划和资料仍可访问，页面显示失败原因并提供重试、修改计划和保存退出；不得创建“成功”的空稿件版本。"),
    ]),
    ("5.5 Reviewer 质量评审", [
        ("AC-RV-01", "评审维度完整", "Must", "FR-08 / F-14", "存在可评审的稿件版本。", "Reviewer 完成评审。", "结果至少覆盖结构、清晰度、事实风险、受众/语气匹配和内容完整性；每个维度有明确状态或分数。"),
        ("AC-RV-02", "问题可定位且可执行", "Must", "FR-08 / F-15~F-16", "Reviewer 发现质量问题。", "用户查看问题列表。", "每个问题包含问题类型、严重级别、对应段落或文本片段、原因和修改建议；不能只有泛化评价。"),
        ("AC-RV-03", "高风险事实问题突出显示", "Must", "PRD 7.1", "稿件存在缺乏来源的事实、数字或可能误导的表述。", "Reviewer 输出结果。", "该问题被标记为高风险或待核实，并与普通措辞建议区分；用户可返回原文位置。"),
        ("AC-RV-04", "用户可独立处理建议", "Must", "User Flow 06", "评审包含多条建议。", "用户选择采纳、忽略或手动修复单条建议。", "每条建议拥有独立状态；处理一条不会自动改变其他建议。"),
        ("AC-RV-05", "评审分数与问题一致", "Must", "FR-08", "Reviewer 返回总分、维度分和问题列表。", "系统展示评审结果。", "分数范围合法，低分维度能在问题列表中找到对应依据；若无有效评分，不显示误导性的默认高分。"),
        ("AC-RV-06", "Reviewer 失败不阻塞稿件", "Must", "PRD 失败场景", "初稿存在，但 Reviewer 超时、服务错误或输出无效。", "用户打开结果。", "初稿仍可阅读、编辑和保存；系统说明暂无评分并提供重试或暂时完成操作。"),
    ]),
    ("5.6 Rewrite 改写与版本", [
        ("AC-RW-01", "按选中建议改写", "Must", "FR-09 / F-17", "用户选择一条或多条评审建议，并保留其他建议未选中。", "用户启动 Rewrite。", "新版本针对选中问题进行修改；未选中建议不会被静默应用或删除。"),
        ("AC-RW-02", "改写保持核心约束", "Must", "FR-09", "原稿满足主题、受众和平台约束。", "Rewrite 生成新版本。", "核心主题、已确认结构和禁用内容约束仍成立；若用户修改约束，系统记录变化。"),
        ("AC-RW-03", "生成独立新版本", "Must", "FR-09 / Version", "任务已有 Draft v1。", "Rewrite 成功。", "系统创建 Draft v2，并保留 v1；当前版本、来源版本、生成时间和触发建议可追溯。"),
        ("AC-RW-04", "变化说明可理解", "Must", "FR-09", "Rewrite 已创建新版本。", "用户查看新版本。", "系统说明主要修改位置和原因；不得只显示“优化完成”。"),
        ("AC-RW-05", "用户可以回退", "Should", "FR-10", "至少存在两个稿件版本。", "用户选择上一版本并确认回退。", "上一版本成为新的当前版本或被复制为新版本；已有版本历史不被删除。"),
        ("AC-RW-06", "失败不产生伪版本", "Must", "异常处理", "Rewrite 超时、输出为空或违反关键约束。", "系统判定失败。", "当前成功版本保持不变；失败运行有记录，用户可以重试、修改指令或继续使用原稿。"),
    ]),
    ("5.7 Final 最终内容交付", [
        ("AC-FN-01", "最终内容清晰可读", "Must", "FR-11 / F-19", "用户完成评审或明确接受风险。", "系统进入 Final。", "页面显示当前版本的标题、正文、完成状态和必要来源信息；用户无需理解内部 Workflow 即可阅读。"),
        ("AC-FN-02", "最终内容仍可编辑", "Must", "产品目标", "Final 已生成。", "用户修改标题或正文并保存。", "修改被保存为当前版本或新版本，刷新后可恢复，且原生成版本仍可追溯。"),
        ("AC-FN-03", "复制结果保持内容结构", "Must", "FR-11", "Final 包含标题、段落、列表和必要来源。", "用户点击复制。", "剪贴板内容保留可读结构；不包含按钮文案、状态、Prompt、密钥、日志或内部 JSON。"),
        ("AC-FN-04", "复制成功有反馈", "Must", "Prototype Result", "浏览器允许访问剪贴板。", "用户点击复制。", "系统给出明确成功反馈，且不会修改当前稿件内容。"),
        ("AC-FN-05", "复制失败可恢复", "Must", "异常场景", "浏览器拒绝剪贴板权限。", "用户点击复制。", "系统说明失败原因并提供手动选择内容的替代方式；最终稿仍可访问。"),
        ("AC-FN-06", "质量信息辅助而非强制阻塞", "Must", "Prototype Result 底线", "Final 仍存在低风险建议或用户已接受的风险。", "用户复制或保存内容。", "系统保留风险提示，但不以单一评分阻止用户导出；高风险事实需再次确认。"),
    ]),
    ("5.8 Workflow 状态与错误恢复", [
        ("AC-ST-01", "当前阶段可见", "Must", "FR-02 / F-23", "任务处于任意阶段。", "用户打开 Workflow。", "页面显示当前阶段、已完成阶段、待执行阶段和当前状态，不以泛化“处理中”替代阶段名称。"),
        ("AC-ST-02", "状态转换合法", "Must", "User Flow 状态表", "任务从 Ready 开始运行。", "阶段成功、失败或等待用户确认。", "状态只按 Draft→Ready→Running→Needs Review/Failed→Completed 的合法路径变化，并记录变化时间。"),
        ("AC-ST-03", "刷新后恢复最近状态", "Must", "FR-02", "任务正在运行或等待审核。", "用户刷新页面或重新打开任务。", "系统恢复最近已知状态和成功输出；若后台状态未知，显示“正在确认状态”而不是重启任务。"),
        ("AC-ST-04", "错误信息可行动", "Must", "PRD 7.2", "任一阶段发生可预期错误。", "系统展示错误。", "错误信息包含发生阶段、用户可理解的原因、已保留内容和下一步操作；不直接暴露堆栈或供应商密钥信息。"),
        ("AC-ST-05", "阶段重试不丢失上下文", "Must", "FR-03", "某阶段失败，前序阶段已有成功结果。", "用户点击重试。", "仅重新运行目标阶段及必要后续阶段；前序成功结果保持，新的运行记录与旧失败记录均可区分。"),
        ("AC-ST-06", "离开页面不造成重复运行", "Must", "User Flow 中途离开", "阶段正在运行。", "用户切换页面后返回。", "系统继续展示同一运行，或明确显示已取消；不得无提示创建第二次模型调用。"),
        ("AC-ST-07", "无限循环受到限制", "Must", "AI 安全边界", "Reviewer 持续判定需要改写。", "Rewrite 达到产品配置的最大次数。", "系统停止自动循环，保留最后成功版本并要求用户选择继续修改、接受风险或结束任务。"),
    ]),
    ("5.9 History 与版本恢复", [
        ("AC-HI-01", "历史任务可识别", "Should", "FR-12 / F-24", "账户中存在多个任务。", "用户打开 History。", "列表至少显示主题或标题、更新时间、状态和当前版本，并按最近更新时间排序。"),
        ("AC-HI-02", "打开最近成功节点", "Should", "FR-12 / User Flow", "一个任务在中途失败或未完成。", "用户从 History 打开任务。", "系统进入最近成功阶段或当前可恢复页面，并保留失败提示和重试入口。"),
        ("AC-HI-03", "完成任务打开最终版本", "Should", "FR-12", "任务状态为 Completed。", "用户点击该任务。", "系统打开 Result，并展示当前最终版本及可访问的历史版本。"),
        ("AC-HI-04", "空历史提供下一步", "Should", "Prototype Empty State", "当前没有任何任务。", "用户打开 History。", "系统显示空状态和“新建内容”入口，不显示空白表格或错误。"),
        ("AC-HI-05", "历史数据异常被隔离", "Should", "非功能可靠性", "单个历史记录损坏或缺失某字段。", "用户打开 History。", "其他任务仍可显示；异常任务被标记且不能导致整个列表白屏。"),
    ]),
]

add_heading(doc, "5. 核心功能验收场景", 1)
doc.add_paragraph("以下场景是开发和测试的共同基线。Must 场景属于 MVP 发布门槛；Should 场景按启用范围执行，但不能以半成品入口误导用户。")
for section_title, scenarios in sections:
    add_heading(doc, section_title, 2)
    for scenario in scenarios:
        add_scenario(doc, scenario)

add_heading(doc, "6. AI 输出质量验收", 1)
quality_rows = [
    ("结构正确率", "Planner、Reviewer 等结构化输出可解析且包含必需字段", "固定样例连续运行，每次记录解析结果", "≥ 95%"),
    ("约束遵循", "主题、受众、内容类型、语气、篇幅和禁用内容满足率", "自动规则 + 人工抽检", "关键约束 100%；综合 ≥ 90%"),
    ("内容完整性", "确认计划中的核心章节在初稿中得到覆盖", "章节映射检查", "核心章节覆盖率 100%"),
    ("问题可执行性", "Reviewer 问题包含位置、类型、等级、原因和建议", "字段校验 + 人工抽检", "必需字段完整率 100%"),
    ("事实风险处理", "无来源的数字、具体事实或强结论被标记", "固定风险样例人工核查", "高风险漏标为 0"),
    ("改写相关性", "Rewrite 主要处理用户选中的问题且不破坏核心含义", "版本差异 + 人工评分", "平均 ≥ 4/5"),
]
add_table(doc, ["维度", "定义", "验证方法", "MVP 建议阈值"], quality_rows, [1700, 3300, 2760, 1600], font_size=8.7)
add_callout(doc, "阈值说明", "这些阈值是开发前基线，首轮测试后可以依据真实表现调整，但调整必须有样本、原因和版本记录，不能为了让失败测试变绿而降低标准。", AMBER_BG, AMBER)

add_heading(doc, "7. 非功能与界面验收", 1)
nfr_scenarios = [
    ("AC-NF-01", "敏感信息不外泄", "Must", "PRD NFR 安全", "系统已配置真实或测试 API Key。", "用户查看页面、复制内容、下载结果或触发错误。", "任何用户可见内容均不出现完整密钥、Authorization 头、系统 Prompt 或内部堆栈。"),
    ("AC-NF-02", "常规任务及时反馈", "Must", "PRD NFR 性能", "用户提交有效任务。", "后端尚未完成 AI 处理。", "前端在 1 秒内显示已接收和具体阶段状态；阶段超出产品超时阈值时显示可理解的超时处理。"),
    ("AC-NF-03", "关键操作有加载与禁用状态", "Must", "Prototype Components", "提交、重试、复制或保存操作正在执行。", "用户再次操作同一控件。", "控件展示进行中状态并阻止重复提交，同时不锁死无关的返回或保存操作。"),
    ("AC-NF-04", "错误不造成整页空白", "Must", "可靠性", "单个 API、解析器或历史记录发生错误。", "页面渲染。", "可用区域和最近成功数据仍显示；错误限定在相关模块并提供恢复动作。"),
    ("AC-NF-05", "键盘和焦点可用", "Must", "Prototype 可用性", "用户仅使用键盘操作。", "用户依次访问输入、按钮、问题列表和复制操作。", "焦点顺序符合阅读顺序，焦点样式可见，关键操作可由键盘触发。"),
    ("AC-NF-06", "前端以简体中文为主", "Must", "用户决策 / 前端阶段", "进入正式前端实现和验收环境。", "用户访问四个核心页面及错误、加载和空状态。", "导航、按钮、字段、状态和错误文案以简体中文为主；ContentFlow、AI 等品牌/通用缩写可保留英文；无方框字、截断或布局溢出。"),
]
for scenario in nfr_scenarios:
    add_scenario(doc, scenario)

add_heading(doc, "8. 异常与边界测试矩阵", 1)
edge_rows = [
    ("空主题/仅空格", "输入校验", "阻止提交，定位字段，保留其他输入", "Must"),
    ("超长主题/正文", "输入或 Writer", "显示上限；不静默截断；服务端再次校验", "Must"),
    ("LLM 401/403", "任意 AI 阶段", "提示配置不可用；不暴露密钥；允许保存退出", "Must"),
    ("LLM Timeout/500", "任意 AI 阶段", "保留前序结果；显示重试与返回", "Must"),
    ("Invalid JSON", "Planner/Reviewer", "解析失败可重试；不把原始 JSON 当成功结果", "Must"),
    ("模型返回空文本", "Writer/Rewrite", "标记失败；不创建成功版本", "Must"),
    ("资料无结果", "Research", "标记资料不足；允许导入、重试或降级", "Should"),
    ("复制权限拒绝", "Final", "提示失败并提供手动复制路径", "Must"),
    ("连续点击", "所有主操作", "去重或幂等；只产生一个有效运行", "Must"),
    ("刷新/重新登录", "Workflow", "恢复任务、状态和最近成功输出", "Must"),
    ("改写次数达到上限", "Rewrite Loop", "停止自动循环，要求人工决策", "Must"),
    ("单条历史记录损坏", "History", "隔离异常，不影响其他任务", "Should"),
]
add_table(doc, ["场景", "发生位置", "期望行为", "级别"], edge_rows, [2100, 1800, 4260, 1200], font_size=8.8)

add_heading(doc, "9. 需求追溯矩阵", 1)
trace_rows = [
    ("FR-01", "任务创建与输入", "F-01~F-03", "AC-IN-01~06", "Must"),
    ("FR-02", "阶段状态与错误", "F-23 / 横向能力", "AC-ST-01~06", "Must"),
    ("FR-03", "编辑输入与重跑", "F-06 / F-26", "AC-IN-06, AC-PL-05, AC-ST-05", "Must"),
    ("FR-04", "生成内容计划", "F-04~F-05", "AC-PL-01~02", "Must"),
    ("FR-05", "编辑并确认计划", "F-06", "AC-PL-03~05", "Must"),
    ("FR-06", "研究摘要与来源", "F-07~F-10", "AC-RS-01~05", "Should"),
    ("FR-07", "结构化初稿", "F-11~F-12", "AC-WR-01~05", "Must"),
    ("FR-08", "多维评审", "F-14~F-16", "AC-RV-01~06", "Must"),
    ("FR-09", "按建议改写", "F-17~F-18", "AC-RW-01~04, 06", "Must"),
    ("FR-10", "版本差异与回退", "F-25", "AC-RW-03~05", "Should"),
    ("FR-11", "最终稿编辑与复制", "F-19", "AC-FN-01~06", "Must"),
    ("FR-12", "历史任务与版本", "F-24~F-25", "AC-HI-01~05", "Should"),
    ("FR-13", "平台适配", "内容适配", "本轮不验收；进入 V1/V2 后补充", "Could"),
]
add_table(doc, ["PRD", "需求", "功能来源", "验收场景", "优先级"], trace_rows, [1000, 2200, 1800, 3260, 1100], font_size=8.5)

add_heading(doc, "10. 固定验收样例", 1)
sample_rows = [
    ("S01 标准产品发布", "为 AI 研究工作空间撰写产品发布文章", "B2B 产品经理", "正常主路径、约束遵循、复制"),
    ("S02 科普内容", "解释生成式 AI 幻觉及降低风险的方法", "大学生", "结构清晰、事实风险、可读性"),
    ("S03 资料不足", "分析一个缺少公开信息的新产品", "行业读者", "Research 无结果、待核实提示"),
    ("S04 冲突约束", "800 字深度文章，同时要求 200 字以内", "内容运营", "冲突提示与人工决策"),
    ("S05 禁用内容", "产品介绍，但不得出现保证收益或绝对化承诺", "潜在客户", "禁用内容、Reviewer 风险识别"),
    ("S06 异常输入", "空值、超长文本、特殊字符和重复提交", "任意", "输入校验、稳定性和幂等"),
]
add_table(doc, ["样例", "主题", "目标受众", "主要验证"], sample_rows, [1800, 3500, 1600, 2460], font_size=8.7)

add_heading(doc, "11. 验收执行流程", 1)
for step in [
    "准备：确认本次构建版本、环境、模型版本、Prompt 版本和启用功能范围。",
    "冒烟：先执行 AC-G-01 核心闭环；失败则停止完整验收并修复阻断问题。",
    "功能：按 Must → Should 顺序执行 Given/When/Then 场景，并保存证据。",
    "AI 质量：对固定样例重复运行，记录解析、约束遵循、评分和失败类型。",
    "异常：注入超时、401、500、Invalid JSON、空结果和重复提交。",
    "回归：修复后重跑相关场景及核心闭环，不只验证单个 Bug。",
    "签字：产品确认范围与体验，开发确认实现和日志，测试确认结果与缺陷状态。",
]:
    add_number(doc, step)

add_heading(doc, "12. 发布判定与签字清单", 1)
release_rows = [
    ("Must 场景", "全部 Pass", "阻断"),
    ("Should 场景", "启用项全部 Pass；未启用项有明确范围说明", "条件阻断"),
    ("P0/P1 缺陷", "0 个未关闭", "阻断"),
    ("固定样例", "完成全套执行并保存结果", "阻断"),
    ("AI 质量阈值", "达到第 6 节基线，或有产品批准的偏差记录", "阻断"),
    ("安全与密钥", "无泄露；.env 与日志检查通过", "阻断"),
    ("中文前端", "前端阶段执行 AC-NF-06", "前端发布前阻断"),
    ("已知限制", "在 README/Demo 中可见且与真实实现一致", "必须记录"),
]
add_table(doc, ["检查项", "通过标准", "处理"], release_rows, [2400, 5160, 1800])
add_callout(doc, "最终判定", "MVP 发布要求所有 Must 场景通过、无未关闭的 P0/P1 缺陷、核心闭环回归通过，并能说明已知限制。Should 和 Could 不得通过隐藏入口或虚假状态冒充完成。", GREEN_BG, GREEN)

add_heading(doc, "13. 本阶段评审清单", 1)
for item in [
    "每个 Must 功能是否至少有正常、异常或边界场景？",
    "每个 Then 是否能通过界面、数据、日志或结构化输出进行检查？",
    "验收标准是否描述产品行为，而不是限定具体代码实现？",
    "AI 输出是否同时覆盖结构正确、质量下限和事实风险？",
    "任何失败是否都保留最近成功结果和用户下一步？",
    "PRD、功能 ID、验收 ID 和后续测试用例能否互相追溯？",
    "中文前端要求是否已作为前端发布前的明确门槛？",
]:
    add_bullet(doc, item)

add_heading(doc, "14. 阶段结论", 1)
doc.add_paragraph(
    "ContentFlow AI 的 MVP 已从功能描述转化为可执行验收基线：用户必须能够完成一条可观察、可修改、可恢复的内容工作流；AI 输出以结构、约束、质量和风险处理进行验证；系统失败不能导致输入或成功结果丢失。下一阶段只有在本验收基线确认后，才从功能反推技术需求。"
)

doc.core_properties.title = "ContentFlow AI 产品验收标准"
doc.core_properties.subject = "Step 13 需求转验收标准"
doc.core_properties.author = "ContentFlow AI Project"
doc.core_properties.keywords = "Acceptance Criteria, Given When Then, MVP, AI Product"

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print(OUT)
