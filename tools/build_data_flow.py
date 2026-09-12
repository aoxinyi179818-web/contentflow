from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT = r"D:\contextai\docs\13-data-flow.docx"

def shade(cell, fill):
    pr = cell._tc.get_or_add_tcPr()
    el = pr.find(qn("w:shd"))
    if el is None:
        el = OxmlElement("w:shd")
        pr.append(el)
    el.set(qn("w:fill"), fill)

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
    r.font.size = Pt(9.2)
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
p.add_run("数据流与状态设计")
sub = doc.add_paragraph()
sub.add_run("ContentFlow AI · MVP Data Flow and State v1.0").italic = True
doc.add_paragraph("本阶段把系统架构中的模块交互具体化为一份可实现的数据流设计。核心结论是：ContentFlow AI 使用一个以任务为边界的共享 State，保存用户输入、阶段结果、版本关系、运行记录、错误和当前状态；每个节点只读取所需字段，并返回明确的状态更新。")

doc.add_heading("1. State 设计目标", 1)
bullets(doc, [
    "让 Workflow 中的每个阶段都能从同一个任务上下文读取数据，避免把结果藏在局部变量中。",
    "让用户刷新、返回或重试时能够恢复最近成功结果，而不是重新开始任务。",
    "让每次模型调用、版本创建和错误都可追溯，便于测试、Debug 和成本分析。",
    "让未来迁移 LangGraph 或接入 Vue 时，仍然沿用相同的数据契约。",
])

doc.add_heading("2. MVP State 总览", 1)
state = doc.add_paragraph()
state.paragraph_format.left_indent = Inches(0.25)
state.add_run("task_id\ninput\nplan\nresearch_context\ndraft_versions\nreview\ncurrent_version_id\nrewrite_count\nstage\nstatus\nruns\nerrors\ncreated_at / updated_at").font.name = "Consolas"
doc.add_paragraph("State 是任务级上下文，不等于数据库中的一张表。实现时可以把它拆成多个实体保存，再在 Workflow 执行时组装成当前任务视图。")

doc.add_heading("3. 字段分组与生命周期", 1)
add_table(doc, ["字段组", "示例字段", "创建时机", "更新规则"], [
    ("用户输入", "topic, audience, content_type, platform, tone, length, constraints", "创建任务", "用户编辑后生成新输入快照，不静默丢弃"),
    ("计划", "plan, confirmed_plan, plan_version_id", "Planner 成功", "用户确认后锁定 Writer 使用的版本"),
    ("资料上下文", "research_results, accepted_sources, research_context", "Research 成功或明确降级", "只允许采纳资料进入 Writer 上下文"),
    ("稿件", "draft_versions, current_version_id, final_content", "Writer/Rewrite 成功", "成功版本追加，不覆盖历史版本"),
    ("评审", "review, issues, issue_decisions", "Reviewer 成功", "与被评审版本绑定"),
    ("控制信息", "stage, status, rewrite_count, retry_count", "任务创建", "只能通过合法状态转换更新"),
    ("运行与错误", "runs, errors, last_error", "每次阶段运行", "追加记录，不能用新错误覆盖历史"),
])

doc.add_heading("4. 主流程数据流", 1)
add_table(doc, ["节点", "读取", "处理", "写入 State"], [
    ("Input Validator", "用户表单", "校验必填、长度、默认值和约束", "input、status=Ready"),
    ("Planner", "input", "调用模型并解析结构化计划", "plan、plan_version、run、stage"),
    ("Plan Confirm", "plan", "用户编辑、确认或要求重规划", "confirmed_plan、plan_version"),
    ("Research", "confirmed_plan", "获取资料；首版可明确降级", "research_results、research_context"),
    ("Writer", "confirmed_plan + context", "生成按章节组织的稿件", "draft_version、current_version_id"),
    ("Reviewer", "current_version", "检查维度、风险和问题", "review、issues"),
    ("Quality Router", "review、rewrite_count", "决定 Rewrite、Accept 或人工处理", "stage、status、route"),
    ("Rewrite", "current_version + selected_issues", "生成独立的新版本", "draft_version、rewrite_count"),
    ("Final", "current_version + review", "编辑、保存、复制和交付", "final_content、status=Completed"),
], [1.1, 2.0, 2.2, 1.5])

doc.add_heading("5. 状态转换规则", 1)
doc.add_paragraph("状态转换是数据流的护栏。UI 不能直接把任务改成 Completed，必须由 Workflow 根据节点结果完成转换。")
add_table(doc, ["当前状态", "触发事件", "下一状态", "必须保留"], [
    ("Draft", "输入校验通过", "Ready", "原始输入"),
    ("Ready", "开始某阶段", "Running", "任务摘要和 run_id"),
    ("Running", "阶段成功且需用户确认", "Needs Confirmation", "阶段结果"),
    ("Running", "阶段成功且可继续", "Ready / Running", "成功结果和运行记录"),
    ("Running", "超时、服务错误或解析失败", "Failed", "前序成功结果、错误和重试入口"),
    ("Needs Confirmation", "用户确认或接受建议", "Ready", "用户决策和版本关系"),
    ("Ready", "用户完成最终确认", "Completed", "当前版本和交付内容"),
], [1.35, 2.1, 1.55, 1.5])

doc.add_heading("6. 版本关系", 1)
doc.add_paragraph("版本关系解决“这份内容是怎么来的”这个问题。所有由模型生成或用户保存的重要结果都应有版本身份；改写创建新版本，回退不能删除旧版本。")
add_table(doc, ["版本", "父版本", "触发来源", "可追溯信息"], [
    ("Plan v1", "无", "Planner", "输入快照、模型运行 ID、创建时间"),
    ("Confirmed Plan v1", "Plan v1", "用户编辑确认", "用户修改内容和确认时间"),
    ("Draft v1", "Confirmed Plan v1", "Writer", "计划版本、上下文摘要、运行 ID"),
    ("Draft v2", "Draft v1", "Rewrite", "选中的问题、改写指令、运行 ID"),
    ("Manual Edit vN", "任一当前版本", "用户保存", "编辑者、修改时间、变化摘要"),
])

doc.add_heading("7. Research 的数据边界", 1)
doc.add_paragraph("Research 在当前 MVP 中是可降级能力。即使未启用外部搜索，也要让 State 能区分“没有研究”“研究失败”和“研究成功但资料被用户排除”，避免 Writer 把不同情况当成同一份空上下文。")
add_table(doc, ["状态", "research_results", "Writer 行为", "用户提示"], [
    ("Not Enabled", "空，带原因", "基于用户输入和模型知识，标记事实风险", "当前未启用外部资料"),
    ("Failed", "失败记录", "不伪造来源，可由用户重试或跳过", "资料获取失败"),
    ("Succeeded", "带来源和摘要", "只使用已采纳上下文", "资料已加入写作依据"),
    ("Partially Accepted", "包含采纳/排除状态", "过滤排除资料", "部分资料未采用"),
])

doc.add_heading("8. 重试与错误数据流", 1)
add_table(doc, ["情况", "State 更新", "是否重跑前序", "用户下一步"], [
    ("Planner Invalid JSON", "Run=Failed，保留 Input", "否", "重试或修改输入"),
    ("Writer Timeout", "Run=Failed，保留 Confirmed Plan", "否", "重试 Writer 或返回计划"),
    ("Reviewer 失败", "Run=Failed，保留 Draft", "否", "重试评审或直接编辑稿件"),
    ("Rewrite 达到上限", "保留最后成功版本，status=Needs Confirmation", "否", "接受、手动修改或结束"),
    ("页面刷新", "从 Repository 恢复最近 State", "否", "继续等待、重试或查看结果"),
])

doc.add_heading("9. 数据流设计检查点", 1)
bullets(doc, [
    "每个节点是否明确列出读取字段和写入字段？",
    "节点失败时，前序成功结果是否仍可读取？",
    "用户确认、忽略建议和手动编辑是否被记录为数据，而不是只改变页面显示？",
    "每个稿件版本是否能找到父版本、生成原因和对应运行？",
    "Research 未启用、失败和成功是否能被 Writer 区分？",
    "刷新、重试和重复点击是否会产生可解释的 State 变化？",
])

doc.add_heading("10. 阶段结论", 1)
doc.add_paragraph("ContentFlow AI 的 State 以任务为边界，包含输入、计划、资料上下文、稿件版本、评审、控制状态、运行记录和错误。主流程通过明确的数据契约逐节点推进；成功结果追加保存，失败记录追加保存，用户决策和版本关系可追溯。这个设计为下一阶段的项目工程初始化提供了模型、目录和数据库的直接输入。")
doc.add_paragraph("进入下一阶段的条件：能够根据本文件画出一次完整任务的数据流，并解释每个字段何时创建、谁可以修改、失败时如何保留。下一阶段将创建 Git 项目基础结构和开发环境。")

doc.save(OUT)
print(OUT)
