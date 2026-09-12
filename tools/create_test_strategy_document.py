"""Create the Step 44 testing strategy Word document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT = Path("docs/29-test-strategy.docx")
BLUE = "17365D"
PALE_BLUE = "EAF2F8"
GRID = "D9D9D9"


def font(run, *, size: float = 10.5, bold: bool = False, color: RGBColor | None = None) -> None:
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def cell_style(cell, *, fill: str | None = None) -> None:
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    tc_pr = cell._tc.get_or_add_tcPr()
    margins = OxmlElement("w:tcMar")
    for side in ("top", "start", "bottom", "end"):
        element = OxmlElement(f"w:{side}")
        element.set(qn("w:w"), "110")
        element.set(qn("w:type"), "dxa")
        margins.append(element)
    tc_pr.append(margins)
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "6")
        element.set(qn("w:color"), GRID)
        borders.append(element)
    tc_pr.append(borders)
    if fill:
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), fill)
        tc_pr.append(shading)


def width(cell, inches: float) -> None:
    cell.width = Inches(inches)
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = OxmlElement("w:tcW")
    tc_w.set(qn("w:w"), str(int(inches * 1440)))
    tc_w.set(qn("w:type"), "dxa")
    tc_pr.append(tc_w)


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    paragraph = doc.add_paragraph(style=f"Heading {level}")
    paragraph.paragraph_format.space_before = Pt(13 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(6)
    font(
        paragraph.add_run(text), size=14 if level == 1 else 11.5, bold=True, color=RGBColor(0, 0, 0)
    )


def add_text(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.35
    paragraph.paragraph_format.space_after = Pt(7)
    font(paragraph.add_run(text))


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.line_spacing = 1.2
        paragraph.paragraph_format.space_after = Pt(3)
        font(paragraph.add_run(item))


def add_table(
    doc: Document, headers: list[str], rows: list[tuple[str, ...]], widths: list[float]
) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        width(cell, widths[index])
        cell_style(cell, fill=BLUE)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        font(paragraph.add_run(header), size=8.7, bold=True, color=RGBColor(255, 255, 255))
    tr_pr = table.rows[0]._tr.get_or_add_trPr()
    repeated = OxmlElement("w:tblHeader")
    repeated.set(qn("w:val"), "true")
    tr_pr.append(repeated)
    for row_index, values in enumerate(rows):
        cells = table.add_row().cells
        for index, value in enumerate(values):
            cell = cells[index]
            width(cell, widths[index])
            cell_style(cell, fill=PALE_BLUE if row_index % 2 else None)
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.line_spacing = 1.05
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER if index == 0 else WD_ALIGN_PARAGRAPH.LEFT
            )
            font(paragraph.add_run(value), size=8.4)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def build() -> None:
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
    title.paragraph_format.space_after = Pt(8)
    font(title.add_run("ContentFlow AI 测试策略"), size=21, bold=True, color=RGBColor(0, 0, 0))
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(16)
    font(
        subtitle.add_run("项目生命周期 Step 44  验收追溯与回归执行方案"),
        size=10.5,
        color=RGBColor(89, 89, 89),
    )

    add_text(
        doc,
        "本策略的结论是：ContentFlow AI 应以可重复的本地自动化测试作为日常质量门槛，以固定输入和伪造客户端控制大模型的不确定性，再用少量受控的真实服务验证和人工验收补充用户体验。当前基线已有 68 项自动化测试；下一步新增用例必须追溯到产品验收标准，而不是只为代码覆盖率而写。",
    )

    add_heading(doc, "1 测试目标与范围")
    add_text(
        doc,
        "测试的目标不是证明某一次模型生成看起来不错，而是证明输入、结构化输出、工作流路由、失败恢复、数据保存和中文界面在可预期条件下保持一致。测试范围覆盖当前 MVP 的 Plan、Research、RAG、Write、Review、Rewrite、Adapter、Visual Plan、SQLite 和 Streamlit 界面。",
    )
    add_bullets(
        doc,
        [
            "默认回归不请求真实 DeepSeek，不读取真实密钥，也不依赖公网，以保证速度、成本和结果稳定。",
            "真实 LLM 或外部搜索验证属于受控接口检查：仅在手动启用、使用测试密钥、记录模型版本时运行。",
            "每个缺陷修复先新增或更新能复现该问题的测试，再运行关联用例和完整回归。",
        ],
    )

    add_heading(doc, "2 分层测试模型")
    add_table(
        doc,
        ["层级", "验证对象", "方法", "执行频率"],
        [
            ("单元", "校验、Prompt、Pydantic、RAG、错误映射", "固定输入与确定性断言", "每次修改"),
            (
                "集成",
                "LangGraph 节点顺序、Router、SQLite 持久化",
                "Fake 服务与临时数据库",
                "每次修改",
            ),
            ("界面冒烟", "中文工作区、空输入、关键提示", "Streamlit AppTest", "每次修改"),
            (
                "接口合同",
                "LLM 客户端、Search 工具模式与超时",
                "Mock 401、500、Timeout、Invalid JSON",
                "合并前和 Step 45",
            ),
            (
                "人工验收",
                "视觉、焦点、加载、中文文案、真实生成质量",
                "Given When Then 与截图记录",
                "发布前",
            ),
        ],
        [0.75, 1.75, 2.55, 1.25],
    )

    add_heading(doc, "3 验收标准到测试的追溯")
    add_table(
        doc,
        ["验收主题", "代表性验收 ID", "当前自动化证据", "后续补齐"],
        [
            (
                "输入与任务",
                "AC-IN-01 至 04",
                "test_app、test_failure_handling、test_workflow_graph",
                "重复提交、字段恢复与字数计数",
            ),
            (
                "内容计划与写作",
                "AC-PL-01、AC-WR-01 至 05",
                "test_planner、test_writer、test_structured_downstream",
                "计划确认、编辑和版本历史",
            ),
            (
                "研究与 RAG",
                "AC-RS-01 至 03",
                "test_research_tool_calling、test_rag_retriever、test_research_workflow",
                "用户排除资料和外部搜索契约",
            ),
            (
                "评审与改写",
                "AC-RV-01 至 05、AC-RW-02",
                "test_reviewer、test_quality_router、test_rewriter",
                "逐条建议采纳与版本差异",
            ),
            (
                "错误与状态",
                "AC-ST-04、07、AC-NF-04",
                "test_failure_handling、test_research_timeout、Router limit tests",
                "401、500、页面保留最近成功内容",
            ),
            (
                "存储与展示",
                "AC-HI-01、AC-FN-01、AC-NF-06",
                "test_project_repository、test_app",
                "历史列表、复制、全中文前端人工验收",
            ),
        ],
        [1.25, 1.35, 2.3, 1.4],
    )

    add_heading(doc, "4 六类测试策略")
    add_table(
        doc,
        ["类型", "固定测试对象", "判定重点", "实现原则"],
        [
            (
                "功能",
                "Planner、Writer、Reviewer、Adapter、Visual",
                "结构完整、约束保留、输出可读",
                "优先断言结构和边界，不断言模型逐字文本。",
            ),
            (
                "接口",
                "OpenAI 客户端和本地 Search 工具",
                "请求模式、参数、返回合同",
                "使用 Fake Client；真实服务独立手动执行。",
            ),
            (
                "异常",
                "Timeout、401、500、Invalid JSON、SQLite",
                "提示可行动、前序结果不丢失",
                "注入异常，不访问真实网络。",
            ),
            (
                "边界",
                "空输入、501 字主题、非法分数、非法检索参数",
                "提前拦截且不调用下游",
                "覆盖最小值、最大值与越界值。",
            ),
            (
                "工作流",
                "高分、低分、证据不足、上限",
                "节点顺序、合法状态、循环停止",
                "记录调用序列并断言最终 status。",
            ),
            ("回归", "完整 pytest 和 Ruff", "既有能力未被破坏", "修复后先局部，随后全量。"),
        ],
        [0.72, 1.75, 1.95, 1.88],
    )

    add_heading(doc, "5 测试数据与环境")
    add_bullets(
        doc,
        [
            "主题样例固定为中文教育或内容创作主题；超长样例使用 501 个字符，避免与产品上限 500 混淆。",
            "模型输出使用可读的固定 JSON、缺字段 JSON、空内容和异常响应，分别验证正常与失败合同。",
            "SQLite 测试使用 pytest 的 tmp_path 创建临时数据库，不连接用户的 data 目录。",
            "tests/conftest.py 强制清空真实 API Key 并将 LLM_PROVIDER 设为 mock，默认测试不会泄露密钥或产生调用费用。",
            "若执行真实服务检查，单独记录环境、模型版本、Prompt 版本、耗时和失败类型，且不纳入默认 pytest。",
        ],
    )

    add_heading(doc, "6 执行节奏与质量门槛")
    add_table(
        doc,
        ["时机", "命令或动作", "通过标准"],
        [
            ("开发中", "pytest 关联测试文件 -q", "当前改动的正常、异常和边界路径通过。"),
            (
                "提交前",
                "python -m pytest -q；python -m ruff check",
                "全部自动化测试和静态检查通过。",
            ),
            (
                "修复缺陷后",
                "先复现缺陷，再跑关联模块与全量回归",
                "缺陷有固定回归用例，且无相邻功能回归。",
            ),
            (
                "发布前",
                "按验收文档执行 Must 场景与人工界面检查",
                "保留截图、输出、日志或测试记录。",
            ),
        ],
        [0.95, 2.55, 2.8],
    )
    add_text(
        doc,
        "推荐本地命令：.venv\\Scripts\\python.exe -m pytest -q；.venv\\Scripts\\python.exe -m ruff check。发生 Prompt、模型合同或路由改动时，必须额外运行对应模块的局部测试，再执行全量回归。",
    )

    add_heading(doc, "7 当前缺口与 Step 45 任务")
    add_text(
        doc,
        "当前 68 项测试已经覆盖核心工作流、结构化输出、RAG、工具调用、循环上限、SQLite 和基础界面。它们不是完整发布验证。下一阶段应把下面缺口写成有编号的测试用例，并明确哪些属于当前 MVP、哪些依赖后续前端能力。",
    )
    add_bullets(
        doc,
        [
            "补齐 API 401 与 500 的明确模拟测试，并确认不会暴露供应商细节或密钥。",
            "补齐真实主题的正常闭环测试用例编号 TC01，以及超长主题、超时、Invalid JSON、Search 失败和数据库失败的编号化矩阵。",
            "对重复提交、计划确认、用户编辑、版本回退、历史列表和复制功能建立测试；这些功能尚未完全进入当前 Streamlit MVP。",
            "在正式前端阶段补充中文文案、加载态、键盘焦点和布局溢出的人工验收清单。",
        ],
    )

    add_heading(doc, "8 本阶段学习总结")
    add_text(
        doc,
        "测试策略把产品验收、工程测试和发布判断连接起来。对 AI 应用而言，可靠性来自固定数据、结构合同、受控的失败模拟和可追溯的回归，而不是期待模型每次都给出相同文字。完成本阶段后，Step 45 将把策略落为带编号、可执行的测试用例。",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)


if __name__ == "__main__":
    build()
