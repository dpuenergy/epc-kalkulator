"""
Parsery pro import dat z PENB (vyhláška 264/2020) a výpočtu Svoboda SW (Energie 2021).

Podporované formáty:
  1. PENB dle vyhl. 264/2020 Sb. – protokol z Energie 2021 / jiného certifikovaného SW
  2. Výpočet Svoboda SW (Energie 2021) – podrobný protokol (.pdf)
  3. Deksoft – strukturou shodný se Svoboda SW, proto sdílí parser

Exportovaná funkce:
    parse_pdf(path) -> PENBData
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union


# ══════════════════════════════════════════════════════════════════════════════
# Datové třídy
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class KonstrukceObaly:
    """Jedna konstrukce obálky budovy."""
    ozn: str                        # kód / zkratka (SV1, SCH_střecha …)
    nazev: str                      # plný název
    typ: str                        # stena / strecha / podlaha_ext / podlaha_zem / otvor
    plocha_m2: float                # m²
    U: float                        # W/(m²·K) skutečná hodnota
    U_ref: Optional[float] = None   # W/(m²·K) požadovaná (UN,20)


@dataclass
class PENBData:
    """Výsledek parsování PENB nebo podrobného výpočtu Svoboda SW / Deksoft."""
    zdroj: str = "unknown"          # "penb_264_2020" | "svoboda_sw"

    # Geometrie
    objem_m3: float = 0.0
    plocha_m2: float = 0.0          # energeticky vztažná plocha
    ochlazovana_plocha_m2: float = 0.0

    # Okrajové podmínky
    theta_e: float = -13.0

    # Konstrukce obálky
    konstrukce: list[KonstrukceObaly] = field(default_factory=list)

    # Dodan á energie (MWh/rok)
    ut_mwh: float = 0.0             # vytápění (EP,H)
    tuv_mwh: float = 0.0            # příprava TUV (EP,W)
    ee_mwh: float = 0.0             # elektrická energie celkem
    zp_mwh: float = 0.0             # zemní plyn celkem (ÚT + TUV)

    # Měsíční průběhy (12 hodnot, MWh) – dodaná energie
    mesice_celkem: list[float] = field(default_factory=lambda: [0.0] * 12)
    mesice_zp: list[float] = field(default_factory=lambda: [0.0] * 12)
    mesice_ee: list[float] = field(default_factory=lambda: [0.0] * 12)

    # Tepelná ztráta
    phi_total_kw: float = 0.0       # přesná (z PDF), nebo 0.0

    # Průměrný součinitel prostupu tepla
    U_em: float = 0.0               # W/(m²·K)

    @property
    def phi_z_obalkoy(self) -> float:
        """Orientační Φ [kW] = Σ(A·U) · ΔT, ΔT = 20 − θe."""
        if not self.konstrukce:
            return 0.0
        return sum(k.plocha_m2 * k.U for k in self.konstrukce) * (20.0 - self.theta_e) / 1000.0


# ══════════════════════════════════════════════════════════════════════════════
# Pomocné funkce
# ══════════════════════════════════════════════════════════════════════════════

def _float(s: str) -> float:
    """Česká desetinná čárka → float, vrátí 0.0 při chybě."""
    try:
        return float(s.replace(",", ".").replace("\xa0", "").replace(" ", "").strip())
    except (ValueError, AttributeError):
        return 0.0


def _grep(pattern: str, text: str, group: int = 1, flags: int = 0) -> str:
    """Vrátí první shodu skupiny nebo prázdný řetězec."""
    m = re.search(pattern, text, flags)
    return m.group(group) if m else ""


_SKIP_WORDS = {
    "vysvětlivky", "poznámka", "průměrný", "celkový", "celková", "součet",
    "faktor", "rozložení", "měrný", "potřeba", "dodaná", "spotřeba",
    "orientační", "název", "přehled", "výsledky",
}


# ══════════════════════════════════════════════════════════════════════════════
# Parser – Nový PENB (264/2020)
# ══════════════════════════════════════════════════════════════════════════════

# Řádek konstrukce:  SV1 20,0 EXT 5883,0 0,220 0,30 0,30 73 %
_RE_PENB_ROW = re.compile(
    r"^([A-Z]{1,4}\d+[a-z]?)\s+"
    r"[\d,]+\s+"                         # θi
    r"(EXT|ZEM|SOUS|NEVYT)\s+"           # prostředí
    r"([\d,]+)\s+"                        # plocha
    r"([\d,]+)\s+"                        # U
    r"([\d,]+)\s+"                        # UN
    r"[\d,]+\s+\d+\s*%",                  # Urec + %
    re.MULTILINE,
)

_SEKCE_PENB: list[tuple[str, str]] = [
    ("STĚNY VNĚJŠÍ",                  "stena"),
    ("STŘECHY",                        "strecha"),
    ("PODLAHY NAD VENKOVNÍM",          "podlaha_ext"),
    ("KONSTRUKCE K ZEMINĚ",            "podlaha_zem"),
    ("VÝPLNĚ OTVORŮ",                  "otvor"),
    ("TEPELNÉ MOSTY",                  "_konec"),
    ("TEPELNÉ VAZBY",                  "_konec"),
]

# Měsíční řádek PENB: "Celkem 385,08 309,68 ..."  nebo "Zemní plyn 350,72 ..."
_RE_MESIC_LINE = re.compile(
    r"([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+"
    r"([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)"
)


def _parse_penb_264(pages: list[str]) -> PENBData:
    data = PENBData(zdroj="penb_264_2020")
    full = "\n".join(pages)

    # Geometrie
    v = _grep(r"Objem budovy.*?m3\s+([\d,]+)", full, flags=re.DOTALL)
    if v:
        data.objem_m3 = _float(v)
    v = _grep(r"Celková plocha hodnocené obálky.*?m2\s+([\d,]+)", full, flags=re.DOTALL)
    if v:
        data.ochlazovana_plocha_m2 = _float(v)
    v = _grep(r"Celková energeticky vztažná plocha.*?m2\s+([\d,]+)", full, flags=re.DOTALL)
    if v:
        data.plocha_m2 = _float(v)

    # Θe
    v = _grep(r"[Nn]ávrhov[aá]\s+venkovn[íi]\s+teplota.*?([-−]?\d+[,\d]*)\s*[°C]", full)
    if v:
        data.theta_e = -abs(_float(v))

    # Energie celkem ze souhrnu energonositelů (strana B):
    # "zemní plyn 1789,616 ..." a "elektřina ze sítě 283,500 ..."
    # Tato část stránky: "Dodan á energie ... MWh/rok ..."
    # Lepší: použij souhrn energonositelů pokud je (PENB ho má na str. B)
    m = re.search(r"Zemní plyn\s+([\d,]+)\s+-\s+-\s+-\s+([\d,]+)\s+-\s+-\s+([\d,]+)", full)
    if m:
        data.zp_mwh = _float(m.group(3))
    m = re.search(r"Elektřina\s+([\d,]+).*?-\s+-\s+([\d,]+)\s+-\s+-\s+([\d,]+)", full)
    if m:
        data.ee_mwh = _float(m.group(3))

    # Vytápění / TUV (MWh/rok) – tabulka v sekci B
    m = re.search(
        r"MWh/rok\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+-\s+([\d,]+)\s+([\d,]+)\s+-\s+([\d,]+)",
        full,
    )
    if m:
        data.ut_mwh  = _float(m.group(1))
        data.tuv_mwh = _float(m.group(4))

    # Měsíční průběhy ze strany D
    lines_with_months = []
    in_monthly = False
    for line in full.splitlines():
        if "Leden" in line and "Únor" in line:
            in_monthly = True
            continue
        if in_monthly:
            m12 = _RE_MESIC_LINE.search(line)
            if m12:
                vals = [_float(m12.group(i)) for i in range(1, 13)]
                if "Celkem" in line or line.strip().startswith("Celkem"):
                    data.mesice_celkem = vals
                elif "Zemní plyn" in line or "Plyn" in line:
                    data.mesice_zp = vals
                elif "Elektřina" in line:
                    data.mesice_ee = vals
            if "BILANCE DLE ÚČELŮ" in line:
                in_monthly = False

    if not data.zp_mwh:
        data.zp_mwh = sum(data.mesice_zp)
    if not data.ee_mwh:
        data.ee_mwh = sum(data.mesice_ee)

    # Konstrukce – sekce F
    aktualni_typ = "stena"
    for page in pages:
        for line in page.splitlines():
            line_s = line.strip()
            for kw, typ in _SEKCE_PENB:
                if kw in line_s:
                    aktualni_typ = typ
                    break
            if aktualni_typ == "_konec":
                continue
            m = _RE_PENB_ROW.match(line_s)
            if m:
                data.konstrukce.append(KonstrukceObaly(
                    ozn=m.group(1), nazev=m.group(1),
                    typ=aktualni_typ,
                    plocha_m2=_float(m.group(3)),
                    U=_float(m.group(4)),
                    U_ref=_float(m.group(5)) or None,
                ))

    # Ochlazovaná plocha = součet ploch všech konstrukcí obálky.
    # Přepočet z konstrukcí je spolehlivější než regex (pdfplumber občas
    # sloučí popisky tabulky na jeden řádek a regex zachytí špatnou hodnotu).
    if data.konstrukce:
        data.ochlazovana_plocha_m2 = sum(k.plocha_m2 for k in data.konstrukce)

    data.phi_total_kw = round(data.phi_z_obalkoy, 1)
    return data


# ══════════════════════════════════════════════════════════════════════════════
# Parser – Svoboda SW / Deksoft
# ══════════════════════════════════════════════════════════════════════════════

# Řádek tabulky konstrukcí (pdfplumber – vše na jednom řádku):
#   SCH_střecha 2662,40 0,160 1,00 425,984 0,240
#   Okna 127,60 (127,6x1,0x1) 1,200 1,00 153,120 1,500
#   Dveře plné 7,40 (7,4x1,0x1) 2,000 1,00 14,800 1,700
_RE_SW_KCE = re.compile(
    r"^([A-Za-z\u00c0-\u017f][A-Za-z0-9_\u00c0-\u017f ]*?)\s+"
    r"([\d,]+)(?:\s*\([^)]+\))?\s+"   # plocha (+ optional rozměry)
    r"([\d,]+)\s+"                     # U [W/m2K]
    r"[\d,]+\s+"                       # b [-]
    r"[\d,]+\s+"                       # H,T [W/K]
    r"([\d,]+)$",                      # U,N,20
    re.MULTILINE,
)

# Měsíční tabulka "Měsíc Q,f,H Q,f,C ... Q,fuel" – řádek dat
# "1 330,928 -------- -------- 0,891 19,796 31,514 1,952 -------- 385,081"
_RE_SW_MONTH = re.compile(
    r"^(\d{1,2})\s+"                            # měsíc
    r"([\d,]+|--------)\s+"                     # Q,f,H
    r"(?:[\d,]+|--------)\s+"                   # Q,f,C
    r"(?:[\d,]+|--------)\s+"                   # Q,f,RH
    r"(?:[\d,]+|--------)\s+"                   # Q,f,F
    r"(?:[\d,]+|--------)\s+"                   # Q,f,W
    r"(?:[\d,]+|--------)\s+"                   # Q,f,L
    r"(?:[\d,]+|--------)\s+"                   # Q,f,A
    r"(?:[\d,]+|--------)\s+"                   # Q,f,K
    r"([\d,]+)$",                               # Q,fuel (celkem)
    re.MULTILINE,
)


def _typ_pro_sw(nazev: str) -> str:
    """Typ konstrukce z názvu Svoboda SW / Deksoft."""
    n = nazev.lower()
    if any(x in n for x in ("okna", "okno", "dveř", "dver", "světlík", "svetlik", "vyplň")):
        return "otvor"
    if any(x in n for x in ("sch_", "střech", "strech")):
        return "strecha"
    if any(x in n for x in ("pdl_ext", "extei", "exteri")):
        return "podlaha_ext"
    if any(x in n for x in ("pdl_zem", "zemina", "suterén", "kz")):
        return "podlaha_zem"
    if re.match(r"(st|sch)\d", n) or "strech" in n:
        return "strecha"
    if re.match(r"vo\d", n):
        return "otvor"
    if re.match(r"(kz|pz)\d", n):
        return "podlaha_zem"
    if re.match(r"po\d", n):
        return "podlaha_ext"
    return "stena"


def _parse_svoboda_sw(pages: list[str]) -> PENBData:
    data = PENBData(zdroj="svoboda_sw")
    full = "\n".join(pages)

    # ── Geometrie ─────────────────────────────────────────────────────────────
    v = _grep(r"Objem budovy stanoven[ý].*?:\s*([\d,]+)\s*m3", full)
    if v:
        data.objem_m3 = _float(v)
    v = _grep(r"Celková energeticky vztažná plocha budovy:\s*([\d,]+)\s*m2", full)
    if v:
        data.plocha_m2 = _float(v)
    v = _grep(r"Plocha obalov[ýé]ch konstrukc[íi] budovy:\s*([\d,]+)\s*m2", full)
    if v:
        data.ochlazovana_plocha_m2 = _float(v)

    # ── Okrajové podmínky ─────────────────────────────────────────────────────
    v = _grep(r"[Nn]ávrhov[aá].*?venkovn[íi].*?teplota.*?(?:Te\s*=\s*)?(?:[-−])?([\d]+[,\d]*)\s*C", full)
    if v:
        data.theta_e = -abs(_float(v))

    # ── Phi a Uem ─────────────────────────────────────────────────────────────
    v = _grep(r"Orienta[čc]n[íi] tepeln[aá] ztráta budovy.*?:\s*([\d,]+)\s*kW", full)
    if v:
        data.phi_total_kw = _float(v)
    v = _grep(r"Průměrný součinitel prostupu tepla budovy\s+U,em:\s*([\d,]+)", full)
    if v:
        data.U_em = _float(v)

    # ── Energie – roční souhrn ────────────────────────────────────────────────
    # Strana 23: "Součty pro jednotlivé energonositele: Q,fuel ... zemní plyn 1789,616 ..."
    # Musíme přeskočit tabulku faktorů transformace (strana 22) kde je "zemní plyn 1,0 0,2..."
    m = re.search(
        r"Součty pro.*?zemní plyn\s+([\d,]+)",
        full, re.DOTALL | re.IGNORECASE,
    )
    if m:
        data.zp_mwh = _float(m.group(1))
    else:
        # Fallback: vezmi číslo >= 100 (MWh rok ≠ faktor 1.0)
        m = re.search(r"^zemní plyn\s+(\d{3,}[,\d]*)", full, re.MULTILINE | re.IGNORECASE)
        if m:
            data.zp_mwh = _float(m.group(1))

    m = re.search(
        r"Součty pro.*?elektřina ze sítě\s+([\d,]+)",
        full, re.DOTALL | re.IGNORECASE,
    )
    if m:
        data.ee_mwh = _float(m.group(1))
    else:
        m = re.search(r"^elektřina ze sítě\s+(\d{3,}[,\d]*)", full, re.MULTILINE | re.IGNORECASE)
        if m:
            data.ee_mwh = _float(m.group(1))

    # EP,H a EP,W z detailní sekce
    v = _grep(r"Dodaná energie na vytápění za rok EP,H:.*?([\d,]+)\s*MWh", full)
    if v:
        data.ut_mwh = _float(v)
    v = _grep(r"Dodaná energie na přípravu TV za rok EP,W:.*?([\d,]+)\s*MWh", full)
    if v:
        data.tuv_mwh = _float(v)
    if not data.ut_mwh and data.zp_mwh and data.tuv_mwh:
        data.ut_mwh = max(0.0, data.zp_mwh - data.tuv_mwh)

    # ── Měsíční průběh celé budovy ─────────────────────────────────────────────
    # Hledáme POSLEDNÍ výskyt tabulky "Měsíc Q,f,H..." (= pro celou budovu, ne pro zónu)
    monthly_blocks: list[str] = []
    for page in pages:
        if "Měsíc Q,f,H" in page and "Q,fuel" in page:
            monthly_blocks.append(page)

    if monthly_blocks:
        last_block = monthly_blocks[-1]
        q_fuel: list[float] = []
        q_h:    list[float] = []
        for m in _RE_SW_MONTH.finditer(last_block):
            q_h.append(_float(m.group(2)) if m.group(2) != "--------" else 0.0)
            q_fuel.append(_float(m.group(3)))
        if len(q_fuel) == 12:
            data.mesice_celkem = q_fuel
        if len(q_h) == 12:
            data.mesice_zp = q_h  # ZP ≈ Q,f,H (předpoklad: plyn = vytápění)

    # ── Konstrukce obálky ─────────────────────────────────────────────────────
    _SKIP = re.compile(
        r"(vysvětlivky|poznámka|průměrný|celkový|celková|součet|faktor|"
        r"rozložení|měrný|potřeba|dodaná|spotřeba|orientační|název|přehled|"
        r"výsledky|parametry|zóna|soustava|zdroj|bilance|podíl|tepelný)",
        re.IGNORECASE,
    )
    seen: dict[str, KonstrukceObaly] = {}

    for page in pages:
        if "Název konstrukce" not in page or "U [W/m2K]" not in page:
            continue
        for m in _RE_SW_KCE.finditer(page):
            nazev = m.group(1).strip()
            if _SKIP.match(nazev):
                continue
            plocha = _float(m.group(2))
            U      = _float(m.group(3))
            U_ref  = _float(m.group(4)) or None
            if plocha <= 0 or not (0.01 <= U <= 15.0):
                continue
            typ = _typ_pro_sw(nazev)
            key = f"{nazev.lower()}|{U:.3f}"
            if key in seen:
                seen[key].plocha_m2 += plocha
            else:
                seen[key] = KonstrukceObaly(
                    ozn=nazev[:30], nazev=nazev, typ=typ,
                    plocha_m2=plocha, U=U, U_ref=U_ref,
                )

    data.konstrukce = list(seen.values())
    if data.konstrukce:
        # Ochlazovaná plocha ze součtu ploch konstrukcí (spolehlivější než regex)
        data.ochlazovana_plocha_m2 = sum(k.plocha_m2 for k in data.konstrukce)
        if data.phi_total_kw == 0:
            data.phi_total_kw = round(data.phi_z_obalkoy, 1)

    return data


# ══════════════════════════════════════════════════════════════════════════════
# Hlavní vstupní bod
# ══════════════════════════════════════════════════════════════════════════════

def parse_pdf(path: Union[str, Path, io.IOBase]) -> PENBData:
    """
    Parsuje PENB nebo výpočet Svoboda SW / Deksoft z PDF.

    Detekuje formát automaticky. Stará skenovaná PENB (bez textové vrstvy)
    vrátí prázdný PENBData se zdroj="neznamý".

    Parametr path může být cesta k souboru (str / Path) nebo file-like objekt (BytesIO).

    :raises ImportError: pokud není nainstalován pdfplumber
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("Nainstalujte pdfplumber: pip install pdfplumber")

    # pdfplumber.open() přijímá jak cestu (str), tak file-like objekt
    _source = path if isinstance(path, (io.IOBase, io.RawIOBase, io.BufferedIOBase)) else str(path)
    pages: list[str] = []
    with pdfplumber.open(_source) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")

    full = "\n".join(pages)

    if "Energie 2021" in full or "VÝPOČET ENERGETICKÉ NÁROČNOSTI BUDOV" in full:
        return _parse_svoboda_sw(pages)
    if ("PRŮKAZ ENERGETICKÉ NÁROČNOSTI" in full
            or "264/2020" in full
            or "406/2000" in full):
        return _parse_penb_264(pages)
    # Fallback: zkus PENB
    if any(_RE_PENB_ROW.search(p) for p in pages):
        return _parse_penb_264(pages)
    return PENBData(zdroj="neznamý")
