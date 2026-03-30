"""
Ekonomická analýza EPC projektů.

Výpočty vyžadované vyhláškami 140/2021 Sb. (EA) a 141/2021 Sb. (EP):
  • NPV  – čistá současná hodnota [Kč]
  • IRR  – vnitřní výnosové procento [%]
  • Tsd  – diskontovaná doba úhrady [roky]

Vzorce pracují s reálnou (nikoliv nominální) diskontní sazbou.
Úspora energie roste s inflací energií (g), servisní náklady jsou konstantní.

Roční cashflow v roce t:
    CF_t = uspora_kc × (1 + g)^t − servisni

NPV:
    NPV = Σ_{t=1}^{n} CF_t / (1 + r)^t − investice

Tsd = nejmenší t takové, že kumulativní diskontované CF ≥ 0

IRR = r* taková, že NPV(r*) = 0  (hledáme bisekci 0–100 %)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class EkonomickeParametry:
    """Parametry ekonomické analýzy společné pro celý projekt."""

    horizont: int = 20              # roky analýzy (typicky 20 dle EP/EA)
    diskontni_sazba: float = 0.04   # reálná diskontní sazba (4 % = standard OPŽP)
    inflace_energie: float = 0.03   # roční zdražování energie (3 %)


@dataclass
class EkonomickeBilance:
    """Výsledky ekonomické analýzy pro jedno opatření nebo celý projekt."""

    npv: float = 0.0                # Kč – čistá současná hodnota
    irr: Optional[float] = None     # 0–1; None pokud IRR neexistuje (NPV < 0 v celém horizontu)
    tsd: Optional[float] = None     # roky; None pokud Tsd > horizont


# ──────────────────────────────────────────────────────────────────────────────
# Interní helper
# ──────────────────────────────────────────────────────────────────────────────

def _rocni_cf(uspora_kc: float, servisni: float, t: int, g: float) -> float:
    """Reálný cashflow v roce t [Kč]."""
    return uspora_kc * ((1.0 + g) ** t) - servisni


# ──────────────────────────────────────────────────────────────────────────────
# Veřejné výpočetní funkce
# ──────────────────────────────────────────────────────────────────────────────

def vypocitej_npv(
    investice: float,
    uspora_kc: float,
    servisni: float,
    par: EkonomickeParametry,
) -> float:
    """Čistá současná hodnota projektu [Kč]."""
    r, g, n = par.diskontni_sazba, par.inflace_energie, par.horizont
    pv = sum(
        _rocni_cf(uspora_kc, servisni, t, g) / (1.0 + r) ** t
        for t in range(1, n + 1)
    )
    return round(pv - investice, 0)


def vypocitej_tsd(
    investice: float,
    uspora_kc: float,
    servisni: float,
    par: EkonomickeParametry,
) -> Optional[float]:
    """
    Diskontovaná doba úhrady [roky].

    Vrátí None pokud projekt nedosáhne splacení v rámci horizontu.
    """
    r, g = par.diskontni_sazba, par.inflace_energie
    cumulative = -investice
    for t in range(1, par.horizont + 1):
        cumulative += _rocni_cf(uspora_kc, servisni, t, g) / (1.0 + r) ** t
        if cumulative >= 0.0:
            return float(t)
    return None


def vypocitej_irr(
    investice: float,
    uspora_kc: float,
    servisni: float,
    par: EkonomickeParametry,
) -> Optional[float]:
    """
    Vnitřní výnosové procento (IRR) bisekční metodou, 50 iterací (přesnost ~0,003 %).

    Hledá r* ∈ (0, 1) takové, že NPV(r*) = 0.
    Vrátí None pokud opatření nemá kladné NPV ani při r=0.
    """
    if investice <= 0.0 or uspora_kc <= servisni:
        return None

    g, n = par.inflace_energie, par.horizont

    def npv_at_r(r: float) -> float:
        return (
            sum(_rocni_cf(uspora_kc, servisni, t, g) / (1.0 + r) ** t
                for t in range(1, n + 1))
            - investice
        )

    if npv_at_r(0.0) < 0.0:
        return None  # projekt nikdy není výnosný

    lo, hi = 0.0, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2.0
        if npv_at_r(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2.0, 4)


def vypocitej_bilanci(
    investice: float,
    uspora_kc: float,
    servisni: float,
    par: EkonomickeParametry,
) -> EkonomickeBilance:
    """Vypočítá NPV, IRR a Tsd najednou a vrátí EkonomickeBilance."""
    return EkonomickeBilance(
        npv=vypocitej_npv(investice, uspora_kc, servisni, par),
        irr=vypocitej_irr(investice, uspora_kc, servisni, par),
        tsd=vypocitej_tsd(investice, uspora_kc, servisni, par),
    )
