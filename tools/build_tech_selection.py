from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT = r"D:\contextai\docs\11-tech-selection.docx"

def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)

def borders(table):
    tbl_pr = table._tbl.tblPr
    el = tbl_pr.first_child_found_in("w:tblBorders")
    if el is None:
        el = OxmlElement("w:tblBorders")
        tbl_pr.append(el)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = el.find(qn("w:" + edge))
        if node is None:
            node = OxmlElement("w:" + edge)
            el.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "4")
        node.set(qn("w:color"), "D9D9D9")

def cell_text(cell, text, bold=False, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(str(text))
    r.bold = bold
    r.font.size = Pt(9.3)
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

def table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    borders(t)
    for i, h in enumerate(headers):
        cell_text(t.rows[0].cells[i], h, True, "FFFFFF")
        shade(t.rows[0].cells[i], "203864")
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(row):
            cell_text(cells[i], value)
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
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
p.add_run("技术选型")
sub = doc.add_paragraph()
sub.add_run("ContentFlow AI · MVP Technology Selection v1.0").italic = True
doc.add_paragraph("本阶段根据技术需求文档，为 ContentFlow AI 的 MVP 选择简单、可验证、可替换的技术方案。推荐先用 Python + Streamlit + Pydantic + LLM API + SQLite 完成闭环，再根据真实复杂度引入 LangGraph、Research Agent 和 RAG。")

doc.add_heading("1. 选型原则", 1)
bullets(doc, [
    "先满足用户闭环，再增加工程复杂度。技术必须服务于 Topic → Planner → Writer → Reviewer → Rewrite → Final。",
    "优先选择学习成本低、社区成熟、便于本地运行和调试的方案。",
    "把模型调用、工作流、存储和界面分层，保证未来可以替换单个组件。",
    "首版关注稳定性、可测试性和错误恢复，不以堆叠 Agent 或 RAG 作为目标。",
    "所有外部服务都保留降级路径，不能因为某个增强能力不可用而阻塞 MVP。",
])

doc.add_heading("2. 推荐技术栈总览", 1)
table(doc, ["层次", "推荐方案", "首版职责", "后续演进"], [
    ("语言", "Python", "业务逻辑、数据模型、测试", "保持不变"),
    ("界面", "Streamlit", "快速完成输入、状态、结果和历史页面", "需要复杂交互时评估前后端分离"),
    ("模型接入", "统一 LLM Client", "封装认证、超时、重试和响应记录", "模型路由、成本统计、供应商切换"),
    ("结构化输出", "Pydantic", "校验 Planner、Reviewer 等结果", "Schema 版本化和更细的自动修复"),
    ("工作流", "Python Coordinator", "先跑通固定 MVP 流程", "复杂分支和循环出现后迁移 LangGraph"),
    ("存储", "SQLite", "保存任务、版本、运行和错误", "多用户或并发增加后迁移服务型数据库"),
    ("测试", "pytest + 固定样例", "单元、流程、异常和回归测试", "增加评测集和质量指标"),
], [1.0, 1.65, 3.0, 1.35])

doc.add_heading("3. 关键技术决策", 1)
table(doc, ["问题", "候选方案", "推荐", "原因"], [
    ("如何快速做 UI", "Streamlit / React", "Streamlit", "MVP 页面以表单、状态和文本结果为主；可快速验证产品闭环。"),
    ("如何保证 AI 字段稳定", "自然语言 / JSON / Pydantic", "Pydantic", "模型输出可以被校验，错误能被捕获，便于测试和下游调用。"),
    ("如何编排首版流程", "if/else / LangGraph", "Python Coordinator", "主流程短且固定，先理解状态和边界，再引入图编排。"),
    ("如何保存历史", "文件 / SQLite / 云数据库", "SQLite", "单机 MVP 足够，支持查询和版本关系，部署成本低。"),
    ("如何接入研究资料", "固定搜索 / Research Agent / RAG", "先定义 Adapter", "Research 是 Should，不阻塞首版；先隔离接口和降级逻辑。"),
    ("如何生成视觉内容", "手动 / Visual Agent / 图像服务", "暂不选", "价值尚未通过 MVP 验证，且增加版权、成本和验收复杂度。"),
], [1.25, 1.55, 1.35, 2.55])

doc.add_heading("4. 为什么不是一开始就使用 LangGraph", 1)
doc.add_paragraph("LangGraph 适合有共享状态、条件路由、循环、人工确认和可观察执行过程的复杂工作流。ContentFlow AI 后续确实可能需要这些能力，但在首版固定链路中直接引入，会让学习重点从需求验证转向框架配置。")
bullets(doc, [
    "MVP 阶段先用明确的 Coordinator 表达状态、调用顺序和错误处理。",
    "当 Research、Rewrite Loop、Quality Router 和人工确认同时存在，if/else 开始分散状态和路由逻辑时，再迁移 LangGraph。",
    "迁移前必须保留同一组输入输出模型和测试用例，确保重构不是重新定义产品行为。",
])

doc.add_heading("5. 为什么首版不强行加入 RAG 和 Agent", 1)
table(doc, ["能力", "真正解决的问题", "当前判断", "进入条件"], [
    ("Research Agent", "根据主题自主规划查询并获取资料", "Should，先预留接口", "用户需要外部资料且固定搜索步骤不够用"),
    ("RAG", "基于用户资料或知识库生成，降低脱离资料的风险", "暂不阻塞 MVP", "出现个人资料、内部知识或可重复检索需求"),
    ("Visual Agent", "判断内容需要何种视觉素材并调用工具", "V2", "文字闭环稳定且视觉需求被验证"),
])

doc.add_heading("6. 成本、风险与替代路径", 1)
table(doc, ["组件", "主要成本", "主要风险", "替代或控制措施"], [
    ("LLM API", "按调用和 Token 计费，受延迟影响", "超时、限流、输出不稳定", "统一 Client、超时、有限重试、固定测试集和调用记录"),
    ("Streamlit", "复杂交互能力有限", "页面状态和长任务管理变复杂", "MVP 先使用；复杂后拆分 API 与前端"),
    ("SQLite", "单机和并发能力有限", "多用户写入冲突或数据增长", "Repository 抽象；需要时迁移 PostgreSQL"),
    ("Pydantic", "需要维护 Schema", "模型返回字段不匹配", "校验、错误提示、有限修复和 Schema 版本"),
    ("LangGraph", "增加框架学习和调试成本", "过早抽象导致流程难懂", "等出现明确的循环、分支和共享状态问题再引入"),
])

doc.add_heading("7. MVP 工程结构建议", 1)
doc.add_paragraph("本阶段只确定职责，不创建所有目录和代码。建议后续按以下边界实现：")
table(doc, ["目录或模块", "职责", "依赖方向"], [
    ("src/models", "Pydantic 数据模型和枚举", "不依赖 UI"),
    ("src/llm", "LLM Client、超时、错误分类", "依赖配置和模型 SDK"),
    ("src/services", "Planner、Writer、Reviewer、Rewrite", "依赖 models 和 llm"),
    ("src/workflow", "阶段顺序、状态和路由", "依赖 services 和 repository"),
    ("src/repository", "任务、运行、版本的保存和读取", "依赖 models"),
    ("app.py", "Streamlit 页面和用户交互", "调用 workflow，不承载模型细节"),
    ("tests", "模型、服务、流程和异常测试", "验证公开行为"),
])

doc.add_heading("8. 本阶段决策清单", 1)
bullets(doc, [
    "首版语言确定为 Python。",
    "首版界面确定为 Streamlit。",
    "AI 输出使用 Pydantic 结构化校验。",
    "首版使用统一 LLM Client，不把供应商 SDK 直接散落在业务模块中。",
    "首版使用 Python Coordinator；LangGraph 延后到出现真实流程复杂度后。",
    "首版使用 SQLite，并通过 Repository 隔离存储实现。",
    "Research、RAG、Visual Agent 作为后续能力，首版提供明确降级边界。",
])

doc.add_heading("9. 阶段结论", 1)
doc.add_paragraph("推荐方案不是技术数量最多的方案，而是能最快验证 ContentFlow AI 核心闭环、同时保留演进空间的方案。下一阶段进入系统架构设计：把这些选型放入模块边界、调用关系和数据流中，并明确一次任务从输入到最终内容如何经过系统。")

doc.save(OUT)
print(OUT)
