"""Create the Step 30 LangGraph foundations learning document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/16-langgraph-foundations.docx")


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
    title.paragraph_format.space_after = Pt(6)
    set_run_font(title.add_run("ContentFlow AI LangGraph 基础学习记录"), 21, bold=True)

    metadata = document.add_paragraph()
    metadata.paragraph_format.space_after = Pt(13)
    set_run_font(
        metadata.add_run("阶段：Step 30  范围：State Node Edge  日期：2026年9月10日"),
        10,
        color="595959",
    )

    add_heading(document, "阶段结论")
    add_body(
        document,
        "本阶段已用一个不调用模型的最小图验证 State、Node 和 Edge 的协作关系。"
        "State 是跨节点传递的共享数据快照；Node 是读取当前 State 并返回局部更新的函数；Edge 决定下一个执行节点。"
        "这三个概念足以表达 ContentFlow 的基础线性路径，但尚未接入条件路由或循环。",
    )

    add_heading(document, "概念与 ContentFlow 映射")
    add_table(
        document,
        ["概念", "在 LangGraph 中的含义", "ContentFlow 对应物", "本阶段验证方式"],
        [
            [
                "State",
                "当前流程共享的数据快照",
                "topic、plan、draft、review、状态字段",
                "Planner 写入 plan，Writer 读取同一 State。",
            ],
            [
                "Node",
                "读取 State 并返回更新的 Python 函数",
                "Planner、Writer、Reviewer、Rewrite",
                "两个节点各自只更新自己负责的字段。",
            ],
            [
                "Edge",
                "定义节点之间的固定或条件执行关系",
                "Planner 到 Writer 等流程连接",
                "使用 START 到 Planner 到 Writer 到 END 的固定路径。",
            ],
            [
                "Compile",
                "对图结构做基本检查并生成可调用图",
                "工作流构建完成后的可运行版本",
                "调用 compile 后再 invoke，避免孤立节点。",
            ],
        ],
        [1.1, 2.1, 2.05, 2.2],
    )

    add_heading(document, "最小概念验证设计")
    add_table(
        document,
        ["输入", "节点更新", "输出", "不做什么"],
        [
            [
                "topic 与空 events 列表",
                "Planner 返回 plan 与事件；Writer 返回 draft 与事件",
                "topic、plan、draft、按顺序追加的 events",
                "不调用 LLM，不修改 run_mvp，不含 Router。",
            ],
        ],
        [1.45, 2.35, 1.85, 1.8],
    )

    add_heading(document, "关键实现原则")
    add_body(
        document,
        "节点返回更新，而不是直接修改传入的 State。这样每个节点的输入与输出更容易检查和测试。"
        "示例中的 events 使用追加规则，因此 Planner 和 Writer 分别返回一条新事件，最终 State 保留两个节点的执行记录。"
        "正式项目会在下一阶段使用同样的方式保存 plan、draft、review、rewrite_count、status 和 errors。",
    )

    add_heading(document, "固定边与未来条件边")
    add_body(
        document,
        "本阶段的边是固定的：START 到 Planner，Planner 到 Writer，Writer 到 END。"
        "Step 31 会保留这条骨架，同时加入 Reviewer 和 Quality Router。届时条件边将根据 review.score 与 rewrite_count 选择 Rewrite 或 End。"
        "条件边必须有明确的退出条件，避免改写循环无限执行。",
    )

    add_heading(document, "运行与测试结果")
    add_numbered_steps(
        document,
        [
            "运行演示脚本后，最终 State 同时包含原始 topic、Planner 写入的 plan 和 Writer 写入的 draft。",
            "测试确认 Writer 的 draft 包含上游 plan，证明节点通过 State 传递数据。",
            "测试确认 events 的顺序为 Planner 后 Writer，证明固定 Edge 的执行顺序。",
            "空主题在图启动前被拒绝，不会进入任何节点。",
        ],
    )

    add_heading(document, "下一阶段的边界")
    add_body(
        document,
        "下一阶段只重构现有 Planner、Writer、Reviewer 和 Rewrite 为基础 Graph，并新增 Quality Router。"
        "不在该阶段实现 Research Agent、工具调用、RAG、数据库或 UI 流式展示。先证明条件路由与改写上限正确，再逐项增加能力。",
    )

    add_heading(document, "学习总结")
    add_body(
        document,
        "LangGraph 不替代业务函数。它让业务函数在同一个 State 上协作，并把执行关系从散落的 if 和局部变量中抽离出来。"
        "对 ContentFlow 而言，最直接的收益是下一阶段能将“是否改写”的产品规则写成可观察、可测试、可限制的条件边。",
    )

    add_heading(document, "参考资料")
    add_body(
        document,
        "LangChain LangGraph Graph API overview：https://docs.langchain.com/oss/python/langgraph/graph-api",
    )
    add_body(
        document,
        "LangChain LangGraph Use the graph API：https://docs.langchain.com/oss/python/langgraph/use-graph-api",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
