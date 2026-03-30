"""
Stylovací konstanty a formátovací funkce pro Word výstupy.

Všechny fmt_* funkce jsou sdíleny s app.py (UI používá své vlastní verze,
ale tady jsou kanonické hodnoty pro dokumenty).
"""
from __future__ import annotations

from docx.oxml import parse_xml
from docx.oxml.ns import nsmap
from docx.shared import Cm, Pt, RGBColor

# ── Fonty a barvy ─────────────────────────────────────────────────────────────

FONT_BODY = "Calibri"

COLOR_H1 = RGBColor(0x1B, 0x4F, 0x72)
COLOR_H2 = RGBColor(0x2E, 0x86, 0xAB)
COLOR_TBL_HEAD_HEX = "D5E8F0"   # světle modrá záhlaví tabulek
COLOR_TBL_TOTAL_HEX = "EBF5FB"  # ještě světlejší pro řádek CELKEM

# ── Šířky sloupců (pro tabulku opatření) ─────────────────────────────────────

COL_ID = Cm(1.2)
COL_NAZEV = Cm(5.5)
COL_INVESTICE = Cm(2.6)
COL_USPORA_KW = Cm(2.2)
COL_USPORA_KC = Cm(2.6)
COL_NAV = Cm(2.0)
COL_NPV = Cm(2.6)
COL_IRR = Cm(1.6)
COL_TSD = Cm(1.6)


# ── Formátovací funkce ────────────────────────────────────────────────────────

def fmt_kc(v: float) -> str:
    """1 234 567 Kč; záporné hodnoty se znaménkem."""
    s = f"{abs(v):,.0f}".replace(",", "\u00a0")
    return f"{'-' if v < 0 else ''}{s}\u00a0Kč"


def fmt_mwh(v: float) -> str:
    return f"{v:,.1f}\u00a0MWh".replace(",", "\u00a0")


def fmt_m3(v: float) -> str:
    return f"{v:,.0f}\u00a0m³".replace(",", "\u00a0")


def fmt_pct(v: float) -> str:
    """0–1 jako procenta, např. 0.123 → '12,3 %'."""
    return f"{v * 100:.1f}\u00a0%"


def fmt_nav(v: float | None) -> str:
    """Prostá nebo diskontovaná návratnost v letech."""
    return f"{v:.1f}\u00a0let" if v is not None else "\u221e"


def fmt_irr(v: float | None) -> str:
    """IRR v procentech, None jako pomlčka."""
    return f"{v * 100:.1f}\u00a0%" if v is not None else "\u2013"


def fmt_tsd(v: float | None, horizont: int = 20) -> str:
    """Tsd v letech, None = 'nad horizont'."""
    return f"{v:.0f}\u00a0let" if v is not None else f">{horizont}\u00a0let"


# ── Helpers pro python-docx ───────────────────────────────────────────────────

def set_cell_bg(cell, hex6: str) -> None:
    """Nastaví barvu pozadí buňky tabulky (hex bez #)."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = parse_xml(
        f'<w:shd xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        f'w:val="clear" w:color="auto" w:fill="{hex6}"/>'
    )
    # Odstraň existující shd pokud je
    for old in tcPr.findall(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd"
    ):
        tcPr.remove(old)
    tcPr.append(shd)


def set_col_width(cell, width) -> None:
    """Nastaví šířku buňky (Cm nebo Pt)."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcW = parse_xml(
        f'<w:tcW xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        f'w:w="{int(width.twips)}" w:type="dxa"/>'
    )
    for old in tcPr.findall(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcW"
    ):
        tcPr.remove(old)
    tcPr.append(tcW)


def cell_text(cell, text: str, bold: bool = False,
              font_size: int = 9, align=None) -> None:
    """Nastaví text buňky s volitelným formátováním."""
    cell.text = text
    para = cell.paragraphs[0]
    if align:
        para.alignment = align
    for run in para.runs:
        run.font.name = FONT_BODY
        run.font.size = Pt(font_size)
        run.bold = bold
