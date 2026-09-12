from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT = r"D:\contextai\docs\12-architecture.docx"

def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)

def borders(table):
    pr = table._tbl.tblPr
    el = pr.first_child_found_in("w:tblBorders")
    if el is None:
        el = OxmlElement("w:tblBorders")
        pr.append(el)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        n = el.find(qn("w:" + edge))
        if n is None:
            n = OxmlElement("w:" + edge)
            el.append(n)
        n.set(qn("w:val"), "single")
        n.set(qn("w:sz"), "4")
        n.set(qn("w:color"), "D9D9D9")

def set_cell(cell, text, bold=False, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(str(text))
    r.bold = bold
    r.font.size = Pt(9.3)
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

def add_table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    borders(t)
    for i, h in enumerate(headers):
        set_cell(t.rows[0].cells[i], h, True, "FFFFFF")
        shade(t.rows[0].cells[i], "203864")
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(row):
            set_cell(cells[i], value)
            if ri % 2:
                shade(cells[i], "F4F7FA")
    if widths:
        for row in t.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Inches(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def bullets(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(3)
        p.add_run(item)

doc = Document()
s = doc.sections[0]
s.top_margin = Inches(0.65)
s.bottom_margin = Inches(0.65)
s.left_margin = Inches(0.75)
s.right_margin = Inches(0.75)
styles = doc.styles
styles["Normal"].font.name = "Microsoft YaHei"
styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
styles["Normal"].font.size = Pt(10.5)
for name, size in [("Title", 22), ("Heading 1", 15), ("Heading 2", 12)]:
    st = styles[name]
    st.font.name = "Microsoft YaHei"
    st._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.font.size = Pt(size)

p = doc.add_paragraph(style="Title")
p.add_run("系统架构设计")
sub = doc.add_paragraph()
sub.add_run("ContentFlow AI · MVP Architecture v1.0").italic = True
doc.add_paragraph("本架构将 ContentFlow AI 拆分为界面层、应用编排层、AI 能力层、数据层和横向支撑层。MVP 采用单体应用形态，模块内部保持清晰边界；当流程复杂度和并发需求增加时，再演进为 API、队列和独立服务。")

doc.add_heading("1. 架构目标与边界", 1)
add_table(doc, ["目标", "架构回应"], [
    ("先跑通内容创作闭环", "用 Streamlit + Python Coordinator 串起 Topic、Planner、Writer、Reviewer、Rewrite、Final。"),
    ("AI 输出可控", "所有关键输出经过 Pydantic Schema 校验，模型调用通过统一 Client。"),
    ("失败可恢复", "状态和结果持久化，失败保留最近成功版本，重试不重复运行前序阶段。"),
    ("后续可扩展", "Research、RAG、LangGraph 和 Vue 通过模块或适配器接入，不直接侵入核心模型。"),
], [2.2, 4.3])

doc.add_heading("2. MVP 总体架构", 1)
doc.add_paragraph("系统调用关系如下。箭头表示主要依赖方向，不代表每个模块都必须部署为独立服务。")
arch = doc.add_paragraph()
arch.paragraph_format.left_indent = Inches(0.25)
arch.paragraph_format.space_after = Pt(8)
arch.add_run("用户\n  ↓\nStreamlit UI\n  ↓\nWorkflow Coordinator\n  ├── Input Validator\n  ├── Planner Service\n  ├── Writer Service\n  ├── Reviewer Service\n  └── Rewrite Service\n        ↓\n统一 LLM Client ── Pydantic Parser\n        ↓\nRepository ── SQLite\n        ↓\nTask / Run / Version / Error Log").font.name = "Consolas"
doc.add_paragraph("横向支撑：配置与密钥管理、结构化日志、超时与重试、输入安全校验、固定样例测试。")

doc.add_heading("3. 分层设计", 1)
add_table(doc, ["层次", "模块", "主要职责", "不负责什么"], [
    ("界面层", "Streamlit UI", "收集输入、显示状态、展示计划/稿件/评审、触发操作", "不直接拼 Prompt、不直接操作数据库"),
    ("应用层", "Workflow Coordinator", "控制阶段顺序、状态转换、重试、幂等和路由", "不负责具体页面样式和模型细节"),
    ("AI 能力层", "Planner / Writer / Reviewer / Rewrite", "准备输入、调用 LLM、解析结果、返回领域对象", "不决定页面导航和数据库表结构"),
    ("基础设施层", "LLM Client / Repository", "外部模型调用、持久化、日志和配置", "不包含产品流程判断"),
    ("数据模型层", "Pydantic Models", "定义模块之间稳定的数据契约", "不执行模型调用"),
], [1.1, 1.65, 2.8, 1.45])

doc.add_heading("4. 一次任务的数据流", 1)
add_table(doc, ["步骤", "发生什么", "保存什么", "失败时"], [
    ("1 输入", "用户填写主题、受众和约束", "Task + Input", "前端提示，不能调用模型"),
    ("2 规划", "Planner 根据 Input 生成 ContentPlan", "Run + Plan", "保留 Input，允许重试"),
    ("3 确认", "用户编辑并确认计划", "ConfirmedPlan", "停留在确认状态"),
    ("4 写作", "Writer 根据确认计划生成 DraftVersion", "Run + DraftVersion", "计划仍可访问"),
    ("5 评审", "Reviewer 返回 ReviewResult", "Review + Issues", "稿件仍可编辑和保存"),
    ("6 改写", "用户选择问题后生成新版本", "New DraftVersion", "当前成功版本不变"),
    ("7 交付", "用户编辑、复制或保存最终内容", "CurrentVersion + Final", "保留可用稿件并提示原因"),
], [0.8, 2.45, 1.7, 1.55])

doc.add_heading("5. 核心模块职责", 1)
add_table(doc, ["模块", "输入", "输出", "关键约束"], [
    ("Input Validator", "表单字段", "ValidatedInput", "空值、长度、默认值和禁用内容"),
    ("Workflow Coordinator", "Task + 用户动作", "TaskState", "合法状态、幂等、最大重试次数"),
    ("Planner Service", "ValidatedInput", "ContentPlan", "章节顺序、目标、语气和写作意图完整"),
    ("Writer Service", "ConfirmedPlan + Context", "DraftVersion", "遵守计划、受众、平台和篇幅约束"),
    ("Reviewer Service", "DraftVersion", "ReviewResult", "问题可定位、分数有依据、风险可区分"),
    ("Rewrite Service", "Version + SelectedIssues", "NewDraftVersion", "只应用选中建议，保留版本关系"),
    ("Repository", "领域对象", "保存/读取结果", "失败记录和成功版本可区分"),
], [1.45, 2.0, 1.55, 1.5])

doc.add_heading("6. 状态与持久化设计", 1)
doc.add_paragraph("Task 是用户看到的项目，Run 是一次阶段执行，Version 是可被阅读和回退的计划或稿件版本。三者分开，可以避免“重新生成一次”覆盖历史，也能解释某个结果由哪次运行产生。")
add_table(doc, ["实体", "关键字段", "用途"], [
    ("Task", "task_id, input, stage, status, current_version_id", "恢复用户任务和展示总进度"),
    ("Run", "run_id, task_id, stage, started_at, ended_at, result, error", "记录每次调用、失败和重试"),
    ("PlanVersion", "plan_id, task_id, content, confirmed, created_at", "保留原始计划和用户确认计划"),
    ("DraftVersion", "version_id, parent_id, content, source_issues", "保留初稿、改写稿和来源建议"),
    ("Review", "review_id, version_id, score, dimensions, issues", "保存可追溯的评审结果"),
])

doc.add_heading("7. 失败处理与可观测性", 1)
bullets(doc, [
    "每个阶段记录 stage、run_id、开始时间、结束时间、输入摘要、结果状态和错误类型。敏感内容不直接写入普通日志。",
    "模型超时、限流、认证失败、服务错误和 Invalid JSON 分开分类，便于决定重试还是提示用户修改。",
    "重试只重新执行失败阶段及其必要后续阶段，不重复调用已经成功的前置阶段。",
    "UI 显示用户可理解的错误和下一步；开发日志保留足够定位问题的信息，但不暴露密钥和系统 Prompt。",
    "为 Coordinator 设置最大重试次数和最大改写次数，达到上限后停止自动循环。",
])

doc.add_heading("8. 后续演进路线", 1)
add_table(doc, ["阶段", "架构变化", "触发条件"], [
    ("MVP", "单体 Streamlit + Python Coordinator + SQLite", "验证核心用户任务和 AI 输出质量"),
    ("V1", "引入 LangGraph 管理条件路由、人工确认和 Rewrite Loop", "流程分支和共享状态明显增加"),
    ("V1 增强", "Research Adapter + Search Tool + 可选 RAG", "用户需要可追溯外部资料或个人知识库"),
    ("产品化", "Python API + Vue 前端 + 服务型数据库", "需要多用户、复杂交互、并发和权限"),
])

doc.add_heading("9. 架构评审问题", 1)
bullets(doc, [
    "如果 Reviewer 失败，用户还能否查看和编辑初稿？",
    "如果用户刷新页面，系统如何知道是否应该继续等待，而不是重复调用？",
    "一个改写版本能否找到它的父版本和触发它的问题？",
    "界面是否只依赖领域对象，而不是依赖 LLM 返回的原始文本？",
    "未来把 Streamlit 换成 Vue，Workflow 和 AI Service 是否可以不重写？",
    "未来加入 Research 或 RAG，是否只需实现适配器而不用改变 Writer 的核心契约？",
])

doc.add_heading("10. 阶段结论", 1)
doc.add_paragraph("ContentFlow AI 的 MVP 采用模块化单体架构：界面负责交互，Workflow Coordinator 负责流程，AI Service 负责具体能力，LLM Client 和 Repository 负责外部依赖，Pydantic Model 负责数据契约。该架构足以支持首版学习和验证，也为后续 LangGraph、Research、RAG、Vue 和服务化演进保留边界。")
doc.add_paragraph("进入下一阶段的条件：能够解释一次任务从用户输入到最终内容的完整数据流，并说明每个模块为什么存在、失败时如何恢复。下一阶段将进入数据流与 State 设计。")

doc.save(OUT)
print(OUT)
