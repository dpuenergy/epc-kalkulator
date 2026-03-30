"""
Generátory grafů pro EA/EP dokumenty.

Používá matplotlib s Agg backendem (bez GUI), výstup je BytesIO (PNG).
Vložení do dokumentu: doc.add_picture(buf, width=Cm(x)).

Funkce:
  graf_spotreba_rocni      – sloupcový graf roční spotřeby dle energonosiče (3 roky)
  graf_spotreba_mesicni    – sloupcový graf měsíčních spotřeb pro zadaný energonosič
  graf_podily_spotreby     – výsečový graf podílů spotřeby a nákladů dle energonosiče
  graf_cf_kumulativni      – čárový graf kumulativního CF (příl. 7 – per opatření)
  graf_investice_uspory    – skupinový sloupcový graf investice vs. roční úspora
"""
from __future__ import annotations

from io import BytesIO
from itertools import groupby
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from epc_engine.models import BuildingInfo, EnergyInputs, MeasureResult
    from epc_engine.models import EkonomickeParametry

# ── Paleta barev ARBOL (přizpůsobitelná) ──────────────────────────────────────
_COLORS = {
    "Teplo (CZT)":          "#E05C2E",
    "Zemní plyn":           "#4A90D9",
    "Elektrická energie":   "#F5A623",
    "Jiný":                 "#7B68EE",
    "default":              "#888888",
}
_CF_COLOR_ND  = "#4A90D9"   # kumulace nediskontovaná
_CF_COLOR_D   = "#E05C2E"   # kumulace diskontovaná
_CF_ZERO_COLOR = "#888888"  # nulová linie
_BAR_INV  = "#4A90D9"       # investice
_BAR_SAV  = "#5CB85C"       # úspory

_DPI    = 150
_FIGW   = 14.0   # cm – šířka figure → převedeme na palce (1 cm = 0.3937 in)
_FIGH   = 7.0    # cm

_MONTHS_CZ = ["Led", "Úno", "Bře", "Dub", "Kvě", "Čer",
               "Čvc", "Srp", "Zář", "Říj", "Lis", "Pro"]


def _cm_to_in(cm: float) -> float:
    return cm * 0.3937


def _get_mpl():
    """Lazy import matplotlib s Agg backendem."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    return plt, mticker


def _finish(fig, plt) -> BytesIO:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _color(energonosic: str) -> str:
    for key, col in _COLORS.items():
        if key.lower() in energonosic.lower():
            return col
    return _COLORS["default"]


# ── Veřejné funkce ─────────────────────────────────────────────────────────────

def graf_spotreba_rocni(budova: "BuildingInfo") -> BytesIO | None:
    """
    Sloupcový graf roční spotřeby dle energonosiče za dostupné roky.

    Vrátí None pokud není dostatek dat.
    Vzor: Obr. 13 'Roční spotřeba el. energie v letech 2014-2016 [MWh]'
    """
    if not budova.historie_spotreby:
        return None

    plt, mticker = _get_mpl()

    # Seskup záznamy podle energonosiče
    from collections import defaultdict
    data: dict[str, dict[int, float]] = defaultdict(dict)
    for h in budova.historie_spotreby:
        data[h.energonosic][h.rok] = h.spotreba_mwh

    roky = sorted({h.rok for h in budova.historie_spotreby})
    energonosice = [e for e in sorted(data.keys())
                    if any(v > 0 for v in data[e].values())]
    if not roky or not energonosice:
        return None

    fig, ax = plt.subplots(figsize=(_cm_to_in(_FIGW), _cm_to_in(_FIGH)))

    n = len(energonosice)
    bar_width = 0.7 / max(n, 1)
    x = list(range(len(roky)))

    for i, en in enumerate(energonosice):
        values = [data[en].get(r, 0.0) for r in roky]
        offset = (i - n / 2 + 0.5) * bar_width
        bars = ax.bar(
            [xi + offset for xi in x], values,
            width=bar_width, label=en, color=_color(en), edgecolor="white"
        )
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(values) * 0.01,
                    f"{val:,.0f}".replace(",", "\u00a0"),
                    ha="center", va="bottom", fontsize=7
                )

    ax.set_xticks(x)
    ax.set_xticklabels([str(r) for r in roky])
    ax.set_ylabel("MWh/rok")
    ax.set_title("Roční spotřeba energie dle energonosiče [MWh]", fontsize=10)
    ax.legend(fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"{v:,.0f}".replace(",", "\u00a0")))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()

    return _finish(fig, plt)


def graf_spotreba_mesicni(budova: "BuildingInfo", energonosic: str) -> BytesIO | None:
    """
    Sloupcový graf měsíčních spotřeb daného energonosiče za dostupné roky.

    Vzor: Obr. 14 'Vývoj měsíčních spotřeb el. energie v letech 2014-2016'
    """
    zaznamy = [h for h in budova.historie_spotreby
               if h.energonosic == energonosic
               and len(h.mesicni_mwh) == 12
               and sum(h.mesicni_mwh) > 0]
    if not zaznamy:
        return None

    plt, mticker = _get_mpl()
    roky = sorted({h.rok for h in zaznamy})

    fig, ax = plt.subplots(figsize=(_cm_to_in(_FIGW), _cm_to_in(_FIGH)))

    n = len(roky)
    bar_width = 0.7 / max(n, 1)
    x = list(range(12))

    rok_colors = ["#4A90D9", "#E05C2E", "#5CB85C", "#F5A623", "#7B68EE"]
    for i, h in enumerate(sorted(zaznamy, key=lambda z: z.rok)):
        offset = (i - n / 2 + 0.5) * bar_width
        ax.bar(
            [xi + offset for xi in x], h.mesicni_mwh,
            width=bar_width,
            label=str(h.rok),
            color=rok_colors[i % len(rok_colors)],
            edgecolor="white"
        )

    ax.set_xticks(x)
    ax.set_xticklabels(_MONTHS_CZ, fontsize=8)
    ax.set_ylabel("MWh")
    ax.set_title(f"Měsíční spotřeba – {energonosic} [MWh]", fontsize=10)
    ax.legend(title="Rok", fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"{v:,.1f}".replace(",", "\u00a0")))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()

    return _finish(fig, plt)


def graf_podily_spotreby(budova: "BuildingInfo") -> BytesIO | None:
    """
    Dva výsečové grafy vedle sebe: podíly spotřeby [MWh] a nákladů [tis. Kč]
    dle energonosiče (průměr dostupných let).

    Vzor: Obr. 47 'Procentní podíly na spotřebě a platbách za energie'
    """
    if not budova.historie_spotreby:
        return None

    from collections import defaultdict
    sum_mwh: dict[str, float] = defaultdict(float)
    sum_kc: dict[str, float] = defaultdict(float)
    count: dict[str, int] = defaultdict(int)

    for h in budova.historie_spotreby:
        sum_mwh[h.energonosic] += h.spotreba_mwh
        sum_kc[h.energonosic] += h.naklady_kc
        count[h.energonosic] += 1

    # Průměrné hodnoty
    avg_mwh = {k: sum_mwh[k] / count[k] for k in sum_mwh}
    avg_kc  = {k: sum_kc[k] / count[k]  for k in sum_kc}

    energonosice = [k for k in avg_mwh if avg_mwh[k] > 0 and avg_kc.get(k, 0) >= 0]
    if not energonosice:
        return None
    # Ensure there are actually non-zero values to plot
    if sum(avg_mwh[k] for k in energonosice) == 0:
        return None

    plt, _ = _get_mpl()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(_cm_to_in(_FIGW), _cm_to_in(_FIGH)))

    colors = [_color(en) for en in energonosice]

    def _autopct(pct):
        return f"{pct:.1f}\u00a0%" if pct > 3 else ""

    for ax, data_dict, title, unit in [
        (ax1, avg_mwh, "Spotřeba energie [MWh/rok]", "MWh"),
        (ax2, avg_kc,  "Náklady na energie [tis. Kč/rok]", "tis. Kč"),
    ]:
        values = [data_dict.get(en, 0) for en in energonosice]
        total = sum(values)
        if total <= 0:
            ax.text(0.5, 0.5, "Data\nnedostupná", ha="center", va="center",
                    transform=ax.transAxes, fontsize=9, color="grey")
            ax.set_title(title, fontsize=9)
            ax.axis("off")
            continue
        wedges, texts, autotexts = ax.pie(
            values, labels=None, colors=colors,
            autopct=_autopct, startangle=90,
            pctdistance=0.75,
            wedgeprops={"edgecolor": "white", "linewidth": 1.5},
        )
        for at in autotexts:
            at.set_fontsize(8)
        ax.set_title(title, fontsize=9)

    # Sdílená legenda
    from matplotlib.patches import Patch
    legend_handles = [Patch(facecolor=c, label=en)
                      for c, en in zip(colors, energonosice)]
    fig.legend(handles=legend_handles, loc="lower center",
               ncol=len(energonosice), fontsize=8,
               bbox_to_anchor=(0.5, -0.02))

    fig.tight_layout()
    return _finish(fig, plt)


def graf_cf_kumulativni(
    r: "MeasureResult",
    parametry: "EkonomickeParametry | None" = None,
    horizont: int = 20,
) -> BytesIO | None:
    """
    Čárový graf kumulativního cash flow (nediskontovaný a diskontovaný).

    Osa X: rok 0 … horizont; Osa Y: tis. Kč kumulativně.
    Zvýrazní rok, kdy kumulace nediskontovaná přechází do kladných hodnot (prostá návratnost).
    Vzor: Tabulka 69 'Ekonomické vyhodnocení opatření E' + čárový průběh.
    """
    if r.investice <= 0 or r.uspora_kc <= 0:
        return None

    import math
    discount = parametry.diskontni_sazba if parametry else 0.04
    inflace  = parametry.inflace_energie  if parametry else 0.03

    roky = list(range(horizont + 1))
    kum_nd = [0.0] * (horizont + 1)
    kum_d  = [0.0] * (horizont + 1)

    kum_nd[0] = -r.investice / 1000  # tis. Kč
    kum_d[0]  = -r.investice / 1000

    for t in range(1, horizont + 1):
        uspora_nd = r.uspora_kc * ((1 + inflace) ** t) / 1000
        uspora_d  = r.uspora_kc * ((1 + inflace) ** t) / ((1 + discount) ** t) / 1000
        kum_nd[t] = kum_nd[t - 1] + uspora_nd
        kum_d[t]  = kum_d[t - 1]  + uspora_d

    plt, _ = _get_mpl()
    fig, ax = plt.subplots(figsize=(_cm_to_in(_FIGW), _cm_to_in(_FIGH)))

    ax.plot(roky, kum_nd, color=_CF_COLOR_ND, linewidth=2,
            label="Kumulace nediskontovaná", marker="o", markersize=3)
    ax.plot(roky, kum_d,  color=_CF_COLOR_D,  linewidth=2,
            label="Kumulace diskontovaná",   marker="s", markersize=3)
    ax.axhline(0, color=_CF_ZERO_COLOR, linewidth=1, linestyle="--")

    # Zvýrazni prostou návratnost
    for t in range(1, horizont + 1):
        if kum_nd[t] >= 0 and kum_nd[t - 1] < 0:
            ax.axvline(t, color=_CF_COLOR_ND, linewidth=1, linestyle=":",
                       label=f"Prostá návratnost ≈ {t}\u00a0let")
            break

    ax.set_xlabel("Rok")
    ax.set_ylabel("Kumulativní CF [tis. Kč]")
    ax.set_title(f"Kumulativní cash flow – {r.id} {r.nazev}", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(linestyle="--", alpha=0.4)
    fig.tight_layout()

    return _finish(fig, plt)


def graf_investice_uspory(aktivni: "list[MeasureResult]") -> BytesIO | None:
    """
    Skupinový sloupcový graf: investice [tis. Kč] vs. roční úspora nákladů [tis. Kč/rok].

    Vzor: Obr. 54–55 'Poměr investičních nákladů a úspor jednotlivých opatření'
    """
    if not aktivni:
        return None

    plt, _ = _get_mpl()

    labels = [r.id for r in aktivni]
    investice = [r.investice / 1000 for r in aktivni]
    uspory    = [r.uspora_kc / 1000 for r in aktivni]

    x = list(range(len(aktivni)))
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(_cm_to_in(_FIGW), _cm_to_in(_FIGH)))

    bars_inv = ax.bar([xi - bar_width / 2 for xi in x], investice,
                      bar_width, label="Investice [tis. Kč]",
                      color=_BAR_INV, edgecolor="white")
    bars_sav = ax.bar([xi + bar_width / 2 for xi in x], uspory,
                      bar_width, label="Roční úspora [tis. Kč/rok]",
                      color=_BAR_SAV, edgecolor="white")

    for bars in (bars_inv, bars_sav):
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    h + max(max(investice), max(uspory)) * 0.01,
                    f"{h:,.0f}".replace(",", "\u00a0"),
                    ha="center", va="bottom", fontsize=7
                )

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("tis. Kč")
    ax.set_title("Investiční náklady vs. roční úspora na energiích", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()

    return _finish(fig, plt)
