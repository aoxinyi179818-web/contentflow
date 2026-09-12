from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT = r"D:\contextai\docs\10-technical-requirements.docx"


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def borders(table, color="D9D9D9"):
    tbl_pr = table._tbl.tblPr
    borders_el = tbl_pr.first_child_found_in("w:tblBorders")
    if borders_el is None:
        borders_el = OxmlElement("w:tblBorders")
        tbl_pr.append(borders_el)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        el = borders_el.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            borders_el.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), color)


def set_cell(cell, text, bold=False, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(9.5)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    borders(table)
    for i, header in enumerate(headers):
        set_cell(table.rows[0].cells[i], header, True, "FFFFFF")
        shade(table.rows[0].cells[i], "203864")
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell(cells[i], str(value))
            if row_index % 2 == 1:
                shade(cells[i], "F4F7FA")
    if widths:
        for row in table.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Inches(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_bullets(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(3)
        p.add_run(item)


def add_numbered(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.space_after = Pt(3)
        p.add_run(item)


doc = Document()
section = doc.sections[0]
section.top_margin = Inches(0.65)
section.bottom_margin = Inches(0.65)
section.left_margin = Inches(0.75)
section.right_margin = Inches(0.75)

styles = doc.styles
styles["Normal"].font.name = "Microsoft YaHei"
styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
styles["Normal"].font.size = Pt(10.5)
for style_name, size in [("Title", 22), ("Heading 1", 15), ("Heading 2", 12), ("Heading 3", 10.5)]:
    style = styles[style_name]
    style.font.name = "Microsoft YaHei"
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.font.size = Pt(size)

title = doc.add_paragraph(style="Title")
title.alignment = WD_ALIGN_PARAGRAPH.LEFT
title.add_run("技术需求拆解")
sub = doc.add_paragraph()
sub.paragraph_format.space_after = Pt(12)
sub.add_run("ContentFlow AI · MVP Technical Requirements v1.0").italic = True

doc.add_paragraph("本阶段把已经确认的产品功能、MVP 范围、用户流程、原型和验收标准，转换为开发可以实现、测试可以验证的技术需求。结论是：首版先实现可恢复的文字内容工作流，采用 Python 业务层、LLM API、结构化数据校验和轻量持久化；Research、RAG、Visual Agent 等增强能力保留接口，但不阻塞 MVP 闭环。")

doc.add_heading("1. 阶段目标与边界", level=1)
doc.add_paragraph("本阶段不写业务代码，也不进行最终技术选型。它要回答的是：每个产品能力需要什么输入、处理、输出、状态和失败处理，以及后续应该由哪个技术模块承担。")
add_table(doc, ["本阶段完成", "本阶段暂不完成"], [
    ("拆解产品功能对应的技术问题", "不实现 Planner、Writer 或 Reviewer"),
    ("定义模块输入输出和数据契约", "不提前引入 LangGraph、RAG 或 Agent"),
    ("定义状态、异常和可观测要求", "不确定云部署、并发和商业化方案"),
    ("建立需求到验收标准的追溯关系", "不扩展 PPT、视频和自动配图范围"),
], [3.25, 3.25])

doc.add_heading("2. MVP 技术主链路", level=1)
doc.add_paragraph("MVP 的技术链路保持短而完整。每个步骤产生可保存的结果，失败时保留最近成功结果，用户可以重试或修改后继续。")
add_table(doc, ["阶段", "输入", "输出", "主要技术问题"], [
    ("Topic", "主题、受众、内容类型、平台、语气、篇幅、限制", "ValidatedInput", "字段校验、长度限制、重复提交控制"),
    ("Planner", "ValidatedInput", "ContentPlan", "如何约束模型输出结构并处理解析失败"),
    ("Confirm", "ContentPlan", "ConfirmedPlan", "如何保存用户修改并锁定写作前置版本"),
    ("Writer", "ConfirmedPlan + 可用上下文", "DraftVersion", "如何遵守计划和内容约束"),
    ("Reviewer", "DraftVersion", "ReviewResult", "如何返回可定位、可执行的问题"),
    ("Rewrite", "DraftVersion + SelectedIssues", "NewDraftVersion", "如何只应用用户选中的建议并保留版本"),
    ("Final", "CurrentVersion", "FinalContent", "如何编辑、保存、复制并显示风险提示"),
], [0.85, 2.15, 1.55, 2.0])

doc.add_heading("3. 功能到技术模块的映射", level=1)
add_table(doc, ["产品能力", "技术模块", "职责", "MVP 优先级"], [
    ("创作配置", "Input Validator", "校验必填项、长度、默认值和用户约束", "Must"),
    ("内容策划", "Planner Service", "调用模型生成可编辑的 ContentPlan", "Must"),
    ("内容生成", "Writer Service", "基于确认计划生成 DraftVersion", "Must"),
    ("质量控制", "Reviewer Service", "输出评分、问题、严重级别和建议", "Must"),
    ("改写", "Rewrite Service", "按选中问题生成新版本", "Must"),
    ("工作流状态", "Workflow Coordinator", "管理阶段、运行状态、重试和幂等", "Must"),
    ("版本与历史", "Repository", "保存任务、运行、计划和稿件版本", "Must / 轻量"),
    ("Research", "Research Adapter", "预留资料来源和上下文接口", "Should / 可降级"),
    ("内容适配", "Adapter Service", "预留不同平台的输出转换", "Could"),
], [1.2, 1.55, 3.0, 1.0])

doc.add_heading("4. 核心数据契约", level=1)
doc.add_paragraph("数据契约是模块之间约定的数据形状。MVP 先用 Python 数据类或 Pydantic 模型表达，避免让下游模块依赖一段无法检查的自然语言。")
add_table(doc, ["对象", "最小字段", "来源", "下游使用"], [
    ("ValidatedInput", "topic, audience, content_type, platform, tone, length, constraints", "用户输入", "Planner、Writer"),
    ("ContentPlan", "goal, audience_assumptions, tone, sections, constraints", "Planner", "用户确认、Writer"),
    ("DraftVersion", "version_id, plan_id, title, sections, body, status", "Writer / Rewrite", "Reviewer、Final"),
    ("ReviewIssue", "issue_id, type, severity, location, reason, suggestion, decision", "Reviewer", "用户选择、Rewrite"),
    ("ReviewResult", "overall_score, dimensions, issues, risk_summary", "Reviewer", "Workflow、Result"),
    ("TaskState", "task_id, stage, status, current_version, error, timestamps", "Workflow", "UI、Repository、恢复"),
], [1.35, 2.9, 1.1, 1.25])

doc.add_heading("5. Workflow 与状态要求", level=1)
doc.add_paragraph("Workflow Coordinator 负责让页面和后续代码看到同一份任务状态。它不是模型本身，而是连接用户操作、AI 调用、持久化和错误恢复的业务层。")
add_table(doc, ["状态", "含义", "允许的下一步", "用户可见反馈"], [
    ("Draft", "任务已创建但尚未运行", "Start", "显示输入摘要"),
    ("Running", "当前阶段正在执行", "Success / Failed / Cancelled", "显示具体阶段和禁用重复提交"),
    ("Needs Confirmation", "等待用户确认计划或评审建议", "Confirm / Edit / Retry", "显示下一步行动"),
    ("Failed", "本次运行失败但上下文仍在", "Retry / Edit / Save", "显示原因和保留内容"),
    ("Completed", "用户确认当前内容可交付", "Edit / Copy / New Version", "显示完成状态"),
], [1.25, 2.15, 1.65, 1.55])
doc.add_paragraph("必须满足：同一任务同一阶段不能并发创建多个有效运行；阶段失败不能覆盖最近成功结果；刷新页面不能自动重新触发模型调用；重试要有新的运行记录。")

doc.add_heading("6. 外部能力与接口边界", level=1)
add_table(doc, ["接口", "当前需要", "失败处理", "后续扩展"], [
    ("LLM Client", "统一模型调用、超时、错误分类和原始响应记录", "重试或显示可行动错误，不暴露密钥", "模型路由、成本统计"),
    ("Structured Parser", "把模型结果解析为约定对象并校验字段", "记录 Invalid JSON，有限次数重试", "Schema 版本和自动修复"),
    ("Repository", "保存 Task、Run、Plan、Draft、Review", "局部读写失败不导致整页空白", "SQLite → 云数据库"),
    ("Research Adapter", "定义 search/query/context 的接口，不强依赖实现", "无资料时明确降级", "Search Tool、RAG、来源追踪"),
    ("Clipboard Adapter", "复制最终内容并反馈成功或失败", "提供手动复制替代路径", "导出 Markdown / 文件"),
], [1.35, 2.45, 2.0, 1.0])

doc.add_heading("7. 异常、边界与安全要求", level=1)
add_bullets(doc, [
    "输入异常：空主题、仅空格、超长文本和缺少约束必须在调用模型前拦截，并保留用户已填写内容。",
    "模型异常：处理超时、401、429、500、空响应和 Invalid JSON；错误信息面向用户，日志保留技术原因。",
    "流程异常：限制重试次数和改写次数，防止重复提交及 Reviewer 与 Rewrite 无限循环。",
    "数据异常：单条历史记录损坏时隔离该记录，不影响其他任务；失败版本不能冒充成功版本。",
    "安全要求：API Key 只从环境变量读取；页面、复制内容和错误提示不得出现密钥、Authorization、系统 Prompt 或完整堆栈。",
    "事实风险：首版若未启用 Research，必须在界面明确提示模型内容需要人工核实，不得伪造来源。",
])

doc.add_heading("8. 非功能技术要求", level=1)
add_table(doc, ["维度", "MVP 要求", "验证方式"], [
    ("可用性", "提交后 1 秒内显示已接收和当前阶段", "浏览器操作计时"),
    ("可靠性", "失败不丢输入，最近成功结果可恢复", "注入超时、刷新、重试测试"),
    ("可维护性", "模型调用、解析、工作流和存储分层", "代码结构检查和单元测试"),
    ("可观测性", "记录阶段开始/结束、运行 ID、错误类型和路由决定", "查看结构化日志"),
    ("安全性", "密钥不进入仓库和用户可见输出", "敏感词扫描与错误场景测试"),
    ("中文体验", "前端阶段统一简体中文，保留必要英文品牌词", "页面逐项检查"),
], [1.2, 3.3, 2.3])

doc.add_heading("9. 需求追溯与开发入口", level=1)
doc.add_paragraph("本阶段的技术需求必须能回到已有验收标准。后续开发先从下列最小切片开始：")
add_numbered(doc, [
    "定义 ValidatedInput、ContentPlan、DraftVersion、ReviewResult 和 TaskState 的 Pydantic 模型。",
    "实现一个不依赖真实模型的假 LLM Client，让 Planner 能返回固定结构，先验证数据链路。",
    "实现 Planner 的最小调用接口和 Invalid JSON 处理，再接入真实 LLM API。",
    "为 AC-IN、AC-PL、AC-WR、AC-RV、AC-RW、AC-ST 中的 Must 场景建立测试映射。",
])
add_table(doc, ["技术需求", "对应验收标准", "后续测试证据"], [
    ("输入校验和幂等提交", "AC-IN-01 ～ AC-IN-06", "校验结果、运行记录、界面截图"),
    ("ContentPlan 契约和确认", "AC-PL-01 ～ AC-PL-06", "结构化对象、版本记录"),
    ("DraftVersion 和约束检查", "AC-WR-01 ～ AC-WR-05", "稿件版本、约束测试"),
    ("ReviewResult 和问题定位", "AC-RV-01 ～ AC-RV-06", "评分、问题列表、失败记录"),
    ("版本化 Rewrite", "AC-RW-01 ～ AC-RW-06", "v1/v2 对比、触发建议记录"),
    ("状态恢复和错误处理", "AC-ST-01 ～ AC-ST-07", "状态流转日志、重试测试"),
])

doc.add_heading("10. 阶段结论", level=1)
doc.add_paragraph("ContentFlow AI 的首版技术边界已经明确：先完成一条有结构、有状态、有版本和可恢复的文字内容工作流。技术实现的第一步不是直接接入复杂 Agent，而是先建立数据契约、Workflow 状态和可替换的 LLM Client。Research、RAG、LangGraph 和前端实现将在后续阶段基于真实工程问题逐步引入。")
doc.add_paragraph("进入下一阶段的条件：本文件完成评审，并能解释每个 Must 功能需要哪些技术模块、输入输出和失败处理。下一阶段将进行技术选型，比较候选方案并给出选择理由。")

doc.save(OUT)
print(OUT)
