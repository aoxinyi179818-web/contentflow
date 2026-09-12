"""Create the Step 49 Git workflow learning document."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUTPUT = Path("docs/34-git-workflow.docx")
BLUE = "17365D"
PALE_BLUE = "EAF2F8"
GRID = "D9D9D9"


def set_font(run, *, size: float = 10.5, bold: bool = False, color: RGBColor | None = None) -> None:
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def remove_title_border(paragraph) -> None:
    properties = paragraph._p.get_or_add_pPr()
    borders = properties.find(qn("w:pBdr"))
    if borders is None:
        borders = OxmlElement("w:pBdr")
        properties.append(borders)
    bottom = borders.find(qn("w:bottom"))
    if bottom is None:
        bottom = OxmlElement("w:bottom")
        borders.append(bottom)
    bottom.set(qn("w:val"), "nil")


def style_cell(cell, *, fill: str | None = None) -> None:
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    properties = cell._tc.get_or_add_tcPr()
    margins = OxmlElement("w:tcMar")
    for side in ("top", "start", "bottom", "end"):
        edge = OxmlElement(f"w:{side}")
        edge.set(qn("w:w"), "100")
        edge.set(qn("w:type"), "dxa")
        margins.append(edge)
    properties.append(margins)
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge = OxmlElement(f"w:{side}")
        edge.set(qn("w:val"), "single")
        edge.set(qn("w:sz"), "6")
        edge.set(qn("w:color"), GRID)
        borders.append(edge)
    properties.append(borders)
    if fill:
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), fill)
        properties.append(shading)


def set_width(cell, inches: float) -> None:
    cell.width = Inches(inches)
    properties = cell._tc.get_or_add_tcPr()
    width = OxmlElement("w:tcW")
    width.set(qn("w:w"), str(int(inches * 1440)))
    width.set(qn("w:type"), "dxa")
    properties.append(width)


def add_heading(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph(style="Heading 1")
    paragraph.paragraph_format.space_before = Pt(10)
    paragraph.paragraph_format.space_after = Pt(5)
    set_font(paragraph.add_run(text), size=14, bold=True, color=RGBColor(0, 0, 0))


def add_body(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.22
    paragraph.paragraph_format.space_after = Pt(5)
    set_font(paragraph.add_run(text))


def add_bullets(doc: Document, values: list[str]) -> None:
    for value in values:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.line_spacing = 1.1
        paragraph.paragraph_format.space_after = Pt(1)
        set_font(paragraph.add_run(value))


def add_table(doc: Document, headers: list[str], rows: list[tuple[str, ...]], widths: list[float]) -> None:
    output = doc.add_table(rows=1, cols=len(headers))
    output.style = "Table Grid"
    output.autofit = False
    for index, value in enumerate(headers):
        cell = output.rows[0].cells[index]
        set_width(cell, widths[index])
        style_cell(cell, fill=BLUE)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(paragraph.add_run(value), size=8.5, bold=True, color=RGBColor(255, 255, 255))
    header_props = output.rows[0]._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    header_props.append(header)
    for row_index, values in enumerate(rows):
        cells = output.add_row().cells
        for index, value in enumerate(values):
            cell = cells[index]
            set_width(cell, widths[index])
            style_cell(cell, fill=PALE_BLUE if row_index % 2 else None)
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.line_spacing = 1.05
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if index == 0 else WD_ALIGN_PARAGRAPH.LEFT
            set_font(paragraph.add_run(value), size=8.3)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def build() -> None:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.67)
    section.bottom_margin = Inches(0.67)
    section.left_margin = Inches(0.65)
    section.right_margin = Inches(0.65)
    normal = doc.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(10.5)

    title = doc.add_paragraph(style="Title")
    remove_title_border(title)
    title.paragraph_format.space_after = Pt(8)
    set_font(title.add_run("ContentFlow AI Git 工作流"), size=21, bold=True, color=RGBColor(0, 0, 0))
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(16)
    set_font(subtitle.add_run("项目生命周期 Step 49  可追溯的提交与分支规则"), size=10.5, color=RGBColor(89, 89, 89))

    add_body(
        doc,
        "本阶段的结论是：先让每次提交只表达一个可验证的变化，再考虑分支和远程协作。当前仓库位于 main，已有早期产品文档提交；应用代码、测试、提示词和 Step 9 之后的大部分文档尚未进入历史。因此不能用一次大提交掩盖所有变化，应先建立清晰的基线，再从后续功能开始保持小而完整的提交。",
    )

    add_heading(doc, "1 Git 的四个位置")
    rows = [
        ("工作区", "正在编辑的文件", "先运行测试和检查差异"),
        ("暂存区", "本次准备提交的精确文件", "用 git add 指定文件，不用 git add ."),
        ("本地提交", "可回溯的项目快照", "提交前检查 git diff --cached"),
        ("远程仓库", "GitHub 等协作副本", "当前尚未配置，不会自动上传"),
    ]
    add_table(doc, ["位置", "含义", "本项目的操作原则"], rows, [1.05, 2.1, 3.55])

    add_heading(doc, "2 当前仓库状态与判断")
    add_body(
        doc,
        "检查时 main 已有 5 个提交，作者身份已配置，尚未设置远程仓库。docs 02 user analysis 处于已修改状态，其余应用代码和较新的学习文档主要为未跟踪文件。该修改可能是你已有的内容，本阶段不将它纳入建议提交。docx qa 目录属于文档渲染中间物，也不应提交。",
    )
    add_bullets(
        doc,
        [
            "已验证 .env 被 .gitignore 忽略，.env.example 可被正常追踪。",
            "已验证暂存区为空，git diff --cached --check 没有空白错误。",
            "没有远程地址时，git commit 只写入本机；git push 才会向 GitHub 等远程发送内容。",
        ],
    )

    add_heading(doc, "3 推荐分支和提交策略")
    rows = [
        ("main", "稳定且可运行的基线", "只合入已测试的完整变化"),
        ("feature planner", "单一功能开发", "完成后测试并合入 main"),
        ("feature research agent", "Tool Calling 和研究流程", "独立于普通 Writer 节点"),
        ("feature rag", "检索与评测", "保留评测数据和回归测试"),
        ("feature visual agent", "V2 视觉规划", "不阻塞 V1 交付"),
    ]
    add_table(doc, ["分支", "职责", "合入条件"], rows, [1.55, 2.3, 2.85])
    add_body(
        doc,
        "当前已积累较多未跟踪成果，历史无法按原始开发顺序完全恢复。推荐先建立一次有明确说明的 MVP 基线提交，随后每个新功能在 feature 分支开发。不要为了形式把已完成的历史内容拆成伪造的时间线。",
    )

    add_heading(doc, "4 每次提交的安全操作顺序")
    rows = [
        ("1", "git status --short", "识别修改 未跟踪和不应提交的文件"),
        ("2", "运行相关测试", "确认当前变化可运行"),
        ("3", "git add 指定路径", "只加入本次主题相关文件"),
        ("4", "git diff --cached --check", "检查空白错误和提交范围"),
        ("5", "git diff --cached", "人工确认内容和密钥未进入暂存区"),
        ("6", "git commit -m", "用 feat fix test docs chore 表达变化"),
    ]
    add_table(doc, ["顺序", "命令或动作", "目的"], rows, [0.55, 2.25, 3.9])

    add_heading(doc, "5 当前建议的首批提交")
    rows = [
        ("MVP 基线", "配置 应用代码 提示词 数据 测试", "feat add ContentFlow MVP baseline"),
        ("学习记录", "docs 09 至 docs 34 与对应生成工具", "docs add engineering learning records"),
        ("后续安全改动", "基线后的单一安全变化与测试", "feat add baseline safety controls"),
    ]
    add_table(doc, ["提交主题", "建议包含", "提交信息"], rows, [1.15, 3.0, 2.55])
    add_body(
        doc,
        "当前的 app.py 和 src 都尚未被 Git 跟踪，因此无法将其中的 Step 48 代码从历史功能中可靠分离。应先建立 MVP 基线提交，再对后续新增或修改的安全控制使用独立提交。基线提交前需再次检查内容范围。任何提交都不能包含 .env、docx qa、临时测试目录、个人 IDE 配置或未经你确认的 docs 02 修改。",
    )

    add_heading(doc, "6 常见错误和本阶段学习总结")
    add_bullets(
        doc,
        [
            "git add . 很方便，但会把临时文件和无关修改一起带入提交；本项目优先使用精确路径。",
            "Commit 不等于上传 GitHub。Commit 写本地历史，Push 才需要远程仓库和网络权限。",
            "不要在未运行测试时提交，也不要把多个不相关功能混成一条提交。",
            "提交信息写变化和意图，例如 feat add content planner，而不是 update files。",
            "git add -n 首次受 Windows 沙箱的 index.lock 限制；仓库状态未变，在受控权限下重试成功。这属于环境权限问题，不是项目代码问题。",
        ],
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)


if __name__ == "__main__":
    build()
