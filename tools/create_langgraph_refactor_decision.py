"""Create the Step 29 LangGraph refactor decision record."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/15-langgraph-refactor-decision.docx")


def set_cell_shading(cell, color: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    properties.append(shading)


def set_cell_border(cell) -> None:
    properties = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:color"), "D9D9D9")
        borders.append(element)
    properties.append(borders)


def set_run_font(run, size: float, bold: bool = False, color: str = "000000") -> None:
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def add_body(document: Document, text: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(7)
    paragraph.paragraph_format.line_spacing = 1.35
    set_run_font(paragraph.add_run(text), 11)


def add_heading(document: Document, text: str, level: int = 1) -> None:
    paragraph = document.add_paragraph(style=f"Heading {level}")
    paragraph.paragraph_format.space_before = Pt(13 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(5)
    set_run_font(paragraph.add_run(text), 14 if level == 1 else 12, bold=True)


def add_table(
    document: Document, headers: list[str], rows: list[list[str]], widths: list[float]
) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.width = Inches(widths[index])
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_shading(cell, "1F4E78")
        set_cell_border(cell)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(paragraph.add_run(header), 9.5, bold=True, color="FFFFFF")
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cell = cells[index]
            cell.width = Inches(widths[index])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_border(cell)
            if row_index % 2 == 1:
                set_cell_shading(cell, "F3F6F9")
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(2)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            set_run_font(paragraph.add_run(value), 9.5)
    document.add_paragraph().paragraph_format.space_after = Pt(4)


def add_numbered_steps(document: Document, items: list[str]) -> None:
    for item in items:
        paragraph = document.add_paragraph(style="List Number")
        paragraph.paragraph_format.space_after = Pt(4)
        set_run_font(paragraph.add_run(item), 11)


def build_document() -> None:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    title = document.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title.paragraph_format.space_after = Pt(6)
    set_run_font(title.add_run("ContentFlow AI LangGraph 重构决策记录"), 21, bold=True)

    metadata = document.add_paragraph()
    metadata.paragraph_format.space_after = Pt(13)
    set_run_font(
        metadata.add_run(
            "阶段：Step 29  范围：纯 Python MVP 到状态化工作流的重构判断  日期：2026年9月6日"
        ),
        10,
        color="595959",
    )

    add_heading(document, "结论")
    add_body(
        document,
        "当前 MVP 的四个节点可以稳定线性执行，但它已经不适合继续靠串行函数调用来承载下一版需求。"
        "原因不是节点数量，而是即将出现的条件路由、可控循环、共享状态和运行状态展示。"
        "因此下一阶段应学习 LangGraph 的 State、Node 和 Edge，并在随后阶段把现有四个节点重构为基础 Graph；本阶段不接入 Research Agent、RAG 或数据库。",
    )

    add_heading(document, "当前实现与证据")
    add_body(
        document,
        "当前 run_mvp 按固定顺序调用 Planner、Writer、Reviewer 和 Rewrite，并在 Reviewer 之后无条件执行 Rewrite。"
        "MvpResult 只在流程结束时一次性返回 plan、draft、review 和 final_content。"
        "现有单元测试也验证了这条固定顺序，因此当前版本适合演示最小闭环，但无法表达不同审阅结果的不同路径。",
    )

    add_heading(document, "纯 Python 工作流的边界")
    add_table(
        document,
        ["即将出现的需求", "当前线性实现的表现", "风险", "重构后应具备的能力"],
        [
            [
                "按审阅分数决定是否改写",
                "Reviewer 后总是调用 Rewrite",
                "高分内容仍消耗一次模型调用",
                "条件边：低分进入 Rewrite，高分结束",
            ],
            [
                "多轮改写",
                "需要手写嵌套循环和变量",
                "次数与退出条件容易遗漏",
                "在 State 中记录 rewrite_count 和上限",
            ],
            [
                "Research 和失败恢复",
                "函数参数和返回值会持续增加",
                "中间数据与错误状态分散",
                "所有节点读写同一份明确 State",
            ],
            [
                "界面展示运行进度",
                "只有最终 MvpResult",
                "无法告诉用户当前节点和路由原因",
                "节点状态和路由决策可观察",
            ],
            [
                "按路径测试",
                "只能测试固定链路",
                "分支增多后回归成本升高",
                "可分别测试节点和条件路由",
            ],
        ],
        [1.35, 1.75, 1.55, 2.45],
    )

    add_heading(document, "为什么现在引入 LangGraph")
    add_body(
        document,
        "LangGraph 不是替换模型调用代码，也不是为了增加一个技术名词。它提供图结构来表达节点、共享状态、连接关系和条件分支。"
        "对 ContentFlow 而言，Planner、Writer 和 Reviewer 仍然是已有的普通 Python 函数；改变的是编排层。"
        "这可以在不提前实现 Agent 的情况下，先把质量路由和改写循环做成可读、可测、可限制的流程。",
    )

    add_heading(document, "下一阶段的输入输出设计")
    add_table(
        document,
        ["类别", "设计内容", "说明"],
        [
            ["输入 State", "topic、settings", "用户主题和运行配置在图开始时进入 State。"],
            ["中间 State", "plan、draft、review", "沿用已验证的 Pydantic 结构化产物。"],
            [
                "控制 State",
                "rewrite_count、max_rewrite_count、status、errors",
                "用于限制循环、展示进度和记录失败。",
            ],
            [
                "输出 State",
                "final_content、status、errors",
                "流程结束后由 UI 读取，不再只依赖局部变量。",
            ],
            [
                "条件规则",
                "review.score < 80 且未超过上限",
                "仅在确有质量问题时改写；达到上限时结束并保留审阅信息。",
            ],
        ],
        [1.25, 2.65, 3.2],
    )

    add_heading(document, "下一阶段不做什么")
    add_body(
        document,
        "不在基础 Graph 中加入 Web 搜索、工具调用、Research Agent、RAG、数据库或多平台适配。"
        "这些能力会增加新的失败模式和状态字段，应该在基础图和条件路由被独立验证后再加入。"
        "当前 Streamlit 界面仍可调用旧版 run_mvp，等基础 Graph 测试通过后再替换接入点。",
    )

    add_heading(document, "进入 Step 30 的验收条件")
    add_numbered_steps(
        document,
        [
            "能说明 State 是跨节点共享的数据，而不是全局变量。",
            "能说明 Node 是一个完成单一职责的函数，Edge 是节点之间的执行关系。",
            "能说明条件边将依据 review.score 与 rewrite_count 决定下一步。",
            "能说明 max_rewrite_count 用于防止质量循环无限执行。",
            "能绘制并解释 Planner 到 Writer 到 Reviewer 到 Router 到 Rewrite 或 End 的基础路径。",
        ],
    )

    add_heading(document, "本阶段学习总结")
    add_body(
        document,
        "是否采用工作流框架应由流程复杂度决定。线性且无分支的任务使用普通 Python 最简单；当系统需要共享状态、条件选择、循环上限和可观察运行过程时，图编排能降低维护和测试成本。"
        "ContentFlow 现在正处于这个转折点，因此下一步先学习概念，再实施最小重构。",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
