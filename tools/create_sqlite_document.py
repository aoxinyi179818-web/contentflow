"""Create the Step 42 SQLite learning document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUTPUT_PATH = Path("docs/27-sqlite-project-storage.docx")


def style_run(run, size: float, bold: bool = False, color: str = "000000") -> None:
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def paragraph(document: Document, text: str, heading: bool = False) -> None:
    item = document.add_paragraph(style="Heading 1" if heading else None)
    item.paragraph_format.space_before = Pt(12 if heading else 0)
    item.paragraph_format.space_after = Pt(6)
    item.paragraph_format.line_spacing = 1.35
    style_run(item.add_run(text), 14 if heading else 11, heading)


def shade(cell, color: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    properties.append(shading)


def cell_text(cell, text: str, header: bool = False) -> None:
    cell.text = ""
    item = cell.paragraphs[0]
    item.alignment = WD_ALIGN_PARAGRAPH.CENTER if header else WD_ALIGN_PARAGRAPH.LEFT
    item.paragraph_format.space_after = Pt(2)
    style_run(item.add_run(text), 10, header, "FFFFFF" if header else "000000")
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    if header:
        shade(cell, "1F4E79")


def add_schema_table(document: Document) -> None:
    table = document.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    for cell, text in zip(table.rows[0].cells, ["字段", "存储形式", "用途"], strict=True):
        cell_text(cell, text, header=True)
    rows = [
        ("id created_at status", "TEXT", "唯一定位、时间排序和运行状态"),
        ("topic draft final_content", "TEXT", "用户主题与可直接展示的内容"),
        ("plan research review", "JSON TEXT", "恢复 Pydantic 结构化产物"),
        ("adapted_content visual_plan", "JSON TEXT 可空", "为 V1 扩展预留的可选内容包"),
    ]
    for values in rows:
        cells = table.add_row().cells
        for cell, text in zip(cells, values, strict=True):
            cell_text(cell, text)
    widths = [Inches(2.2), Inches(1.5), Inches(3.45)]
    for row in table.rows:
        for cell, width in zip(row.cells, widths, strict=True):
            cell.width = width


def build_document() -> None:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)
    title = document.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    style_run(title.add_run("ContentFlow AI SQLite 项目存储"), 21, True)
    paragraph(document, "阶段：Step 42  范围：本地项目历史与结构化内容持久化")
    paragraph(document, "阶段结论", True)
    paragraph(document, "ContentFlow 现在会在 Streamlit 创作成功后保存本地内容包。SQLite 负责持久化，Repository 负责数据访问，MVP 负责在成功后调用 Repository，UI 不直接编写 SQL。刷新页面或重启程序后，历史项目仍可被读取。")
    paragraph(document, "输入输出设计", True)
    paragraph(document, "输入为主题、计划、Research、初稿、审阅、终稿、状态以及可选的适配内容和视觉计划。输出分为完整 ProjectRecord 和用于历史列表的 ProjectSummary。模型 JSON 被存为 TEXT，读取时通过 Pydantic 恢复为原来的结构化类型。")
    paragraph(document, "项目表结构", True)
    add_schema_table(document)
    paragraph(document, "模块职责", True)
    paragraph(document, "ProjectRepository 初始化表和索引，提供 save_project、get_project、list_recent_projects。MVP 的 repository 参数是可选依赖，便于单元测试传入临时数据库。实际 Streamlit 运行会根据 DATABASE_URL 创建 Repository，并在成功后提示用户内容包已保存。")
    paragraph(document, "质量与边界", True)
    paragraph(document, "数据库只接受 sqlite:/// 文件路径，拒绝其他后端和内存地址。主题、初稿、终稿和状态不能为空；历史列表限制为 1 到 100 条。当前版本不实现编辑、删除、多用户、版本链、Token 用量和错误日志，这些属于后续扩展。")
    paragraph(document, "调试记录", True)
    paragraph(document, "定向测试通过后，Ruff 提示使用 datetime.UTC 替代旧的 timezone.utc 写法。自动修复并格式化后，仓储、MVP、界面测试再次通过。")
    paragraph(document, "验收结果", True)
    paragraph(document, "SQLite 读写往返测试验证了计划、Research、审阅、终稿、Adapter 和 VisualPlan 都可恢复；MVP 持久化测试验证了成功结果可写入历史库；Streamlit 冒烟测试保持通过。定向测试 7 passed，完整项目回归 58 passed。")
    paragraph(document, "学习总结", True)
    paragraph(document, "SQLite 适合单机 MVP，因为它不需要独立数据库服务。Repository 将 SQL 与业务逻辑隔离，JSON 保存能快速保留复杂 AI 产物，但当需要按章节、来源或版本进行复杂查询时，应再拆分为规范化表结构。")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
