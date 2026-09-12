"""Create the Step 37 Research workflow document."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

OUTPUT_PATH = Path("docs/23-research-workflow-integration.docx")


def style(run, size: float, bold: bool = False) -> None:
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.font.bold = bold


def paragraph(document: Document, text: str, heading: bool = False) -> None:
    item = document.add_paragraph(style="Heading 1" if heading else None)
    item.paragraph_format.space_before = Pt(12 if heading else 0)
    item.paragraph_format.space_after = Pt(6)
    item.paragraph_format.line_spacing = 1.35
    style(item.add_run(text), 14 if heading else 11, heading)


def build_document() -> None:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)
    title = document.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    style(title.add_run("ContentFlow AI Research 工作流接入"), 21, True)
    paragraph(document, "阶段：Step 37  范围：Planner 到 Research 到 Writer 的 LangGraph 编排", False)
    paragraph(document, "阶段结论", True)
    paragraph(document, "新增 Research Graph，将 Planner、Research Agent、RAG Context、Writer、Reviewer 和 Rewrite 质量循环串成一条可测试流程。Research 的输出不直接覆盖文章，而是先转为带 source_id 的证据上下文交给 Writer。")
    paragraph(document, "输入输出设计", True)
    paragraph(document, "输入为 topic、Settings 和注入的服务实现。Planner 输出 ContentPlan；Research 输出 ResearchResult；RAG 将来源转为 research_context；Writer 输出 draft；Reviewer 和 Rewrite 延续原有质量循环。最终状态保留 plan、research、research_context、draft、review 和 final_content。")
    paragraph(document, "关键实现", True)
    paragraph(document, "ResearchWorkflowState 使用 TypedDict 显式声明跨节点共享字段。LangGraph 不会自动把普通 dict 中未声明的字段长期保留，因此 State Schema 是流程正确性的组成部分。服务通过依赖注入传入，测试不需要真实 API。")
    paragraph(document, "Bug 与修复", True)
    paragraph(document, "首次集成测试在 Research 节点出现 KeyError topic。原因是 StateGraph(dict) 在 Planner 更新后没有保存 topic 和 settings。改为 StateGraph(ResearchWorkflowState) 后，主题、计划和配置可以跨节点传递，集成测试通过。")
    paragraph(document, "验收结果", True)
    paragraph(document, "测试验证了调用顺序 Planner 到 Research 到 Writer 到 Reviewer，并验证 Writer 收到带 [source_id] 的上下文。全项目回归结果为 42 passed，Ruff 和编译检查通过。基础 Graph 暂时保留，便于对照和回归。")
    paragraph(document, "学习总结", True)
    paragraph(document, "把 Agent 接入 Workflow 的关键不是多加一个节点，而是定义共享状态、证据接口和失败边界。Research 负责资料获取，RAG 负责选证据，Writer 负责写作；这种边界使每个环节都可单独测试。")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
