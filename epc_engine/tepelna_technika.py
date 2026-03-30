"""
Výpočet tepelně technických vlastností dle ČSN EN ISO 6946:2017.

Normové hodnoty UN dle ČSN 73 0540-2:2011, tabulka 3
(pro budovy s převažující návrhovou vnitřní teplotou 18–22 °C, fr = 1.0).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Vrstva


# ── Povrchové odpory [m²K/W] dle ČSN EN ISO 6946:2017 ────────────────────────
# (tepelný tok horizontální nebo šikmý; podlaha k zemině Rse = 0)

_RSI_RSE: dict[str, tuple[float, float]] = {
    "stena":   (0.13, 0.04),
    "strecha": (0.10, 0.04),
    "podlaha": (0.17, 0.00),
    "okno":    (0.13, 0.04),
    "dvere":   (0.13, 0.04),
}

# ── Normové hodnoty [W/(m²K)] dle ČSN 73 0540-2:2011, tabulka 3 ──────────────
# UN   = požadovaná hodnota pro stávající budovy (fr = 1.0)
# Urec = doporučená hodnota
# Upas = doporučená hodnota pro pasivní budovy

_UN_NORMOVE: dict[str, float] = {
    "stena":   0.30,   # stěna vnější těžká / lehká
    "strecha": 0.24,   # střecha plochá a šikmá se sklonem do 45°
    "podlaha": 0.45,   # podlaha vytápěného prostoru přilehlá k zemině
    "okno":    1.50,   # výplň otvoru (okna, balkónové dveře)
    "dvere":   1.70,   # vstupní dveře
}

_UREC_NORMOVE: dict[str, float] = {
    "stena":   0.25,
    "strecha": 0.16,
    "podlaha": 0.30,
    "okno":    1.20,
    "dvere":   0.90,
}

_UPAS_NORMOVE: dict[str, float] = {
    "stena":   0.18,
    "strecha": 0.15,
    "podlaha": 0.22,
    "okno":    0.80,
    "dvere":   0.60,
}

# Popisy typů pro UI a dokumenty
TYP_POPISY: dict[str, str] = {
    "stena":   "Stěna vnější",
    "strecha": "Střecha / strop pod půdou",
    "podlaha": "Podlaha k zemině",
    "okno":    "Okna / balkónové dveře",
    "dvere":   "Vstupní dveře",
}


# ── Funkce ────────────────────────────────────────────────────────────────────

def vypocitej_u_z_vrstev(vrstvy: list[Vrstva], typ: str = "stena") -> float:
    """
    Výpočet součinitele prostupu tepla U [W/(m²K)] z vrstev konstrukce.

    U = 1 / (Rsi + ΣR_vrstev + Rse)

    kde R_vrstvy = d [m] / λ [W/(m·K)]

    Vrstvy s λ = 0 jsou ignorovány (vzduchová mezera – konzervativní přístup).
    """
    rsi, rse = _RSI_RSE.get(typ, (0.13, 0.04))
    r_vrstvy = sum(
        v.tloustka_m / v.lambda_wm
        for v in vrstvy
        if v.lambda_wm > 0 and v.tloustka_m > 0
    )
    r_total = rsi + r_vrstvy + rse
    if r_total <= 0:
        return 0.0
    return 1.0 / r_total


def un_pozadovana(typ: str) -> float:
    """Normová požadovaná hodnota UN,20 [W/(m²K)] dle ČSN 73 0540-2:2011."""
    return _UN_NORMOVE.get(typ, 0.30)


def urec_doporucena(typ: str) -> float:
    """Doporučená hodnota Urec [W/(m²K)] dle ČSN 73 0540-2:2011."""
    return _UREC_NORMOVE.get(typ, _UN_NORMOVE.get(typ, 0.30) * 0.8)


def upas_pasivni(typ: str) -> float:
    """Doporučená hodnota pro pasivní budovy Upas [W/(m²K)] dle ČSN 73 0540-2:2011."""
    return _UPAS_NORMOVE.get(typ, _UN_NORMOVE.get(typ, 0.30) * 0.6)


def hodnoceni_splneni(u: float, un: float) -> str:
    """Textové hodnocení: 'Vyhovuje' pokud U ≤ UN, jinak 'Nevyhovuje'."""
    if un <= 0:
        return "–"
    return "Vyhovuje" if u <= un else "Nevyhovuje"


def vypocitej_uem_z_konstrukci(konstrukce: list) -> float | None:
    """
    Průměrný součinitel prostupu tepla obálky budovy Uem [W/(m²K)].

    Uem = (ΣAi·Ui·bi + ΔUem·A) / A

    kde bi = 1 (kontakt s exteriérem), ΔUem = 0.02 W/(m²K) (tepelné vazby).
    Vrací None pokud není žádná konstrukce nebo celková plocha = 0.
    """
    DELTA_UEM = 0.02
    celkova_plocha = sum(k.plocha_m2 for k in konstrukce)
    if celkova_plocha <= 0:
        return None
    sum_au = sum(k.plocha_m2 * k.u_effective for k in konstrukce)
    return (sum_au + DELTA_UEM * celkova_plocha) / celkova_plocha
