"""Professional booking PDF (Latin + Amharic) built with reportlab platypus."""
from __future__ import annotations
import re
from functools import lru_cache
from io import BytesIO
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import catalog, config

GOLD = colors.HexColor("#B8892E")
DARK = colors.HexColor("#1C1C1C")
GREY = colors.HexColor("#6B6B6B")
CREAM = colors.HexColor("#FBF5EC")
LINE = colors.HexColor("#E6D9C3")
AMBER_BG = colors.HexColor("#FFF3D6")
AMBER_FG = colors.HexColor("#8A5A00")

_ETH = re.compile(r"[\u1200-\u139F\u2D80-\u2DDF\uAB00-\uAB2F]+")
# keep Latin, Ethiopic, general punctuation and currency; drop emoji and other glyphs the fonts lack
_DROP = re.compile(r"[^\u0020-\u024F\u1200-\u139F\u2D80-\u2DDF\uAB00-\uAB2F\u2010-\u2027\u2030-\u205E\u20A0-\u20CF\n]")


@lru_cache
def _fonts() -> None:
    for name, f in [("Noto", "NotoSans-Regular.ttf"), ("Noto-B", "NotoSans-Bold.ttf"),
                    ("Eth", "NotoSansEthiopic-Regular.ttf"), ("Eth-B", "NotoSansEthiopic-Bold.ttf")]:
        pdfmetrics.registerFont(TTFont(name, str(config.FONT_DIR / f)))


def rich(text, bold: bool = False) -> str:
    """Escape text and switch to the Ethiopic font for Amharic runs."""
    t = escape(_DROP.sub("", str(text)))
    font = "Eth-B" if bold else "Eth"
    t = _ETH.sub(lambda m: f'<font name="{font}">{m.group(0)}</font>', t)
    return t.replace("\n", "<br/>")


@lru_cache
def _logo():
    if not config.LOGO_PATH.exists():
        return None
    im = Image.open(config.LOGO_PATH).convert("RGBA")
    buf = BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue(), im.size


def _st():
    def ps(name, **kw):
        kw.setdefault("fontName", "Noto")
        kw.setdefault("leading", 13)
        kw.setdefault("textColor", DARK)
        return ParagraphStyle(name, **kw)
    return {
        "label": ps("label", fontSize=9, textColor=GREY), "value": ps("value", fontSize=10),
        "valueb": ps("valueb", fontSize=10, fontName="Noto-B"),
        "h": ps("h", fontSize=11, fontName="Noto-B", textColor=colors.white),
        "title": ps("title", fontSize=20, leading=24, fontName="Noto-B"),
        "sub": ps("sub", fontSize=9.5, textColor=GREY),
        "term": ps("term", fontSize=9, leftIndent=10),
        "pill": ps("pill", fontSize=8.5, fontName="Noto-B", textColor=AMBER_FG, leading=11),
        "th": ps("th", fontSize=10.5, fontName="Noto-B", textColor=GOLD, spaceAfter=4),
    }


def _section(title, rows, st, width, bold_last=False):
    head = Table([[Paragraph(rich(title, True), st["h"])]], colWidths=[width])
    head.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), DARK), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                              ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                              ("LINEBELOW", (0, 0), (-1, -1), 2, GOLD)]))
    data = []
    for i, (k, v) in enumerate(rows):
        bold = bold_last and i == len(rows) - 1
        data.append([Paragraph(rich(k), st["label"]),
                     Paragraph(rich(v if v not in (None, "") else "-", bold), st["valueb"] if bold else st["value"])])
    body = Table(data, colWidths=[width * 0.34, width * 0.66])
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, CREAM]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]))
    return KeepTogether([head, body, Spacer(1, 7)])


def _page(canvas, doc, record):
    w, h = A4
    canvas.saveState()
    logo = _logo()
    if logo:
        data, (lw, lh) = logo
        ph = 17 * mm
        canvas.drawImage(ImageReader(BytesIO(data)), 18 * mm, h - 14 * mm - ph, width=ph * lw / lh, height=ph, mask="auto")
    canvas.setFillColor(DARK)
    canvas.setFont("Noto-B", 15)
    canvas.drawRightString(w - 18 * mm, h - 20 * mm, "AGOS POSTPARTUM CARE")
    canvas.setFont("Noto", 8.5)
    canvas.setFillColor(GREY)
    canvas.drawRightString(w - 18 * mm, h - 25 * mm, config.WEBSITE)
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.6)
    canvas.line(18 * mm, h - 35 * mm, w - 18 * mm, h - 35 * mm)
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    canvas.line(18 * mm, 24 * mm, w - 18 * mm, 24 * mm)
    canvas.setFont("Noto", 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(18 * mm, 19 * mm, "This is an official document generated by the AGOS Postpartum Care booking system.")
    canvas.drawString(18 * mm, 15 * mm, "For any inquiries, please contact: " + " | ".join(config.CONTACT_PHONES))
    canvas.drawString(18 * mm, 11 * mm, f"Website: {config.WEBSITE} | Email: {config.EMAIL}")
    canvas.drawRightString(w - 18 * mm, 11 * mm, f"{record['ref']}  |  Page {doc.page}")
    canvas.restoreState()


def build_pdf(record: dict) -> bytes:
    _fonts()
    st = _st()
    buf = BytesIO()
    width = A4[0] - 36 * mm
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=40 * mm,
                            bottomMargin=28 * mm, author="AGOS Postpartum Care",
                            title=f"AGOS {record['form']['pdf_title']} - {record['ref']}")
    form, c = record["form"], record["created"]
    story = [Paragraph(rich(form["pdf_title"], True), st["title"]),
             Paragraph("Booking summary - provisional until the deposit is verified", st["sub"]), Spacer(1, 8)]

    pill = Table([[Paragraph(rich("PENDING - Awaiting 50% Deposit Confirmation", True), st["pill"])]])
    pill.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), AMBER_BG), ("BOX", (0, 0), (-1, -1), 0.6, GOLD),
                              ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                              ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    meta = Table([[Paragraph(rich("Booking Reference"), st["label"]), Paragraph(rich(record["ref"], True), st["valueb"]), pill],
                  [Paragraph(rich("Date of Issue"), st["label"]), Paragraph(rich(c.strftime("%B %d, %Y")), st["value"]), ""],
                  [Paragraph(rich("Time of Issue"), st["label"]),
                   Paragraph(rich(c.strftime("%H:%M:%S") + " (Addis Ababa)"), st["value"]), ""]],
                 colWidths=[width * 0.24, width * 0.36, width * 0.40])
    meta.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("SPAN", (2, 0), (2, 2)), ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                              ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                              ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story += [meta, Spacer(1, 12)]

    for title, fields in form["pdf_rows"]:
        rows = [(label, record["values"][key]) for label, key in fields
                if not (key in ("alt_phone", "house", "gender") and record["values"][key] == "-")]
        story.append(_section(title, rows, st, width))

    pay = [("Payment Status", "PENDING - Awaiting 50% Deposit Confirmation"), ("Bank", config.BANK_NAME),
           ("Account Name", config.BANK_ACCOUNT_NAME), ("Account Number", config.BANK_ACCOUNT_NUMBER),
           ("Package Price", catalog.money(record["price"])),
           ("Remaining Balance", f"{catalog.money(record['balance'])} - due on the day of service"),
           ("Required Deposit (50%)", catalog.money(record["deposit"]))]
    story.append(_section("3. PAYMENT INFORMATION", pay, st, width, bold_last=True))

    terms = ["This booking is provisional until payment confirmation is received.",
             "The 50% deposit must be paid within 24 hours to secure your booking.",
             "Remaining balance is due on the day of service.",
             "Cancellations made less than 48 hours before the event may incur charges."]
    story.append(KeepTogether([Paragraph(rich("4. TERMS AND CONDITIONS", True), st["th"])]
                              + [Paragraph(rich(t), st["term"], bulletText="•") for t in terms]))
    doc.build(story, onFirstPage=lambda cv, d: _page(cv, d, record), onLaterPages=lambda cv, d: _page(cv, d, record))
    return buf.getvalue()
