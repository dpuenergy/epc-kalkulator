"""
Klasifikace obálky budovy dle průměrného součinitele prostupu tepla Uem.

Normy a předpisy:
  ČSN 73 0540-2:2011 – Tepelná ochrana budov, část 2: Požadavky
  Vyhláška 264/2020 Sb. – o energetické náročnosti budov

Průměrný součinitel prostupu tepla obálky budovy:
    Uem = HT / A  [W/m²K]

  kde HT = měrná tepelná ztráta prostupem = Σ(Ui × Ai) [W/K]
       A  = celková plocha ochlazovaných konstrukcí [m²]

Referenční (normová) hodnota:
    Uem,N = 0,30 + 0,15 / (A/V)  [W/m²K]

  kde A/V je faktor tvaru budovy [m⁻¹]

Klasifikace A–G je dána poměrem Uem / Uem,N:
  A  ≤ 0,50  (mimořádně úsporná)
  B  ≤ 0,75  (velmi úsporná)
  C  ≤ 1,00  (úsporná – referenční nová budova)
  D  ≤ 1,50  (méně úsporná)
  E  ≤ 2,00  (nehospodárná)
  F  ≤ 2,50  (velmi nehospodárná)
  G  > 2,50  (mimořádně nehospodárná)
"""

from __future__ import annotations

from dataclasses import dataclass


# Meze poměru Uem/Uem,N pro třídy A–G (dle ČSN 73 0540-2)
_TRIDY: list[tuple[str, float]] = [
    ("A", 0.50),
    ("B", 0.75),
    ("C", 1.00),
    ("D", 1.50),
    ("E", 2.00),
    ("F", 2.50),
]


@dataclass
class KlasifikaceObaly:
    """Výsledek klasifikace obálky budovy dle Uem."""

    uem: float      # W/m²K – průměrný součinitel prostupu tepla obálky
    uem_n: float    # W/m²K – normový referenční Uem,N
    pomer: float    # Uem / Uem,N (bezrozměrné)
    trida: str      # A–G


def vypocitej_uem_n(faktor_tvaru: float) -> float:
    """
    Referenční (normová) hodnota průměrného součinitele prostupu tepla obálky.

        Uem,N = 0,30 + 0,15 / (A/V)  [W/m²K]

    Parametr:
        faktor_tvaru – A/V [m⁻¹] (plocha obálky / obestavěný objem)
    """
    return 0.30 + 0.15 / max(faktor_tvaru, 0.01)


def klasifikuj_uem(uem: float, uem_n: float) -> str:
    """Vrátí třídu A–G pro dané Uem a Uem,N."""
    if uem_n <= 0.0:
        return "G"
    pomer = uem / uem_n
    for trida, limit in _TRIDY:
        if pomer <= limit:
            return trida
    return "G"


def obalkova_klasifikace(uem: float, faktor_tvaru: float) -> KlasifikaceObaly:
    """
    Kompletní klasifikace obálky budovy.

    Parametry:
        uem          – průměrný součinitel prostupu tepla obálky [W/m²K]
        faktor_tvaru – A/V [m⁻¹]

    Vrátí KlasifikaceObaly s Uem, Uem,N, poměrem a třídou A–G.
    """
    uem_n = vypocitej_uem_n(faktor_tvaru)
    pomer = round(uem / uem_n, 3) if uem_n > 0.0 else 0.0
    return KlasifikaceObaly(
        uem=round(uem, 3),
        uem_n=round(uem_n, 3),
        pomer=pomer,
        trida=klasifikuj_uem(uem, uem_n),
    )
