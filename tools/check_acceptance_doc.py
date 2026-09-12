from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from PIL import Image
from pypdf import PdfReader

DOCX = Path(r"D:\contextai\docs\09-acceptance-criteria.docx")
PDF = Path(r"D:\contextai\docx_qa\09-acceptance-criteria\09-acceptance-criteria.pdf")
PNG_DIR = PDF.parent
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

errors = []

reader = PdfReader(str(PDF))
if len(reader.pages) != 17:
    errors.append(f"unexpected page count: {len(reader.pages)}")

pdf_text = []
for index, page in enumerate(reader.pages, start=1):
    text = page.extract_text() or ""
    pdf_text.append(text)
    if len(text.strip()) < 120:
        errors.append(f"page {index} may be blank: {len(text.strip())} chars")
    print(f"PAGE {index:02d}: {len(text.strip()):4d} chars | {text.strip()[:70].replace(chr(10), ' / ')}")

all_text = "\n".join(pdf_text)
required = [
    "产品验收标准",
    "MVP 总体验收门槛",
    "核心功能验收场景",
    "AI 输出质量验收",
    "非功能与界面验收",
    "异常与边界测试矩阵",
    "需求追溯矩阵",
    "固定验收样例",
    "发布判定与签字清单",
    "阶段结论",
    "AC-IN-01",
    "AC-PL-01",
    "AC-WR-01",
    "AC-RV-01",
    "AC-RW-01",
    "AC-FN-01",
    "AC-ST-01",
    "AC-HI-01",
    "AC-NF-06",
]
for text in required:
    if text not in all_text:
        errors.append(f"missing rendered text: {text}")

pngs = sorted(PNG_DIR.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[1]))
if len(pngs) != len(reader.pages):
    errors.append(f"png count {len(pngs)} != pdf pages {len(reader.pages)}")
for png in pngs:
    with Image.open(png) as image:
        if image.width < 1000 or image.height < 1000:
            errors.append(f"unexpected PNG dimensions: {png.name} {image.size}")

with ZipFile(DOCX) as archive:
    document_xml = etree.fromstring(archive.read("word/document.xml"))
    tables = document_xml.xpath("//w:tbl", namespaces=NS)
    if len(tables) < 10:
        errors.append(f"too few tables: {len(tables)}")
    for index, table in enumerate(tables, start=1):
        tbl_w = table.xpath("./w:tblPr/w:tblW/@w:w", namespaces=NS)
        grid = [int(v) for v in table.xpath("./w:tblGrid/w:gridCol/@w:w", namespaces=NS)]
        if not tbl_w or int(tbl_w[0]) != 9360:
            errors.append(f"table {index} width is not 9360 DXA")
        if not grid or sum(grid) != 9360:
            errors.append(f"table {index} grid sum is {sum(grid) if grid else 'missing'}")
        fixed_heights = table.xpath(".//w:trHeight[@w:hRule='exact']", namespaces=NS)
        if fixed_heights:
            errors.append(f"table {index} has fixed row heights")

print(f"PAGES={len(reader.pages)} PNGS={len(pngs)} TABLES={len(tables)}")
if errors:
    print("QA_FAIL")
    for error in errors:
        print("-", error)
    raise SystemExit(1)
print("QA_PASS")
