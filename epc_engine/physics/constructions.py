"""
Výpočet součinitele prostupu tepla U [W/(m²·K)] pro stavební konstrukce.

Odpovídá listu Tepelná ztráta v šabloně Výpočet ochlazovaných konstrukcí.xltx:
  R_tot = Rsi + Σ(d / λ) + Rse
  U = 1 / R_tot
  H = A × U   [W/K]
  Q = H × ΔT / 1 000   [kW]

Standardní povrchové odpory (ČSN EN ISO 6946):
  Rsi = 0.13 m²·K/W  (vnitřní povrch, horizontální tok)
  Rse = 0.04 m²·K/W  (vnější povrch)

Použití::

    from epc_engine.physics.constructions import Vrstva, Konstrukce
    from epc_engine.physics.materials import lambda_materialu

    k = Konstrukce(
        nazev="Obvodová stěna",
        plocha_m2=350.0,
        vrstvy=[
            Vrstva("Omítka vápenná", d=0.02, lambda_=0.88),
            Vrstva("Zdivo-CP", d=0.45, lambda_=0.80),
            Vrstva("Omítka vápennocementová", d=0.02, lambda_=0.99),
        ],
    )
    print(f"U_stav = {k.U:.3f} W/(m²·K)")

    uspora_kw = k.uspora_tepelna_ztrata_kw(U_po=0.20, delta_T=34)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Povrchové odpory dle ČSN EN ISO 6946
RSI = 0.13   # m²·K/W – vnitřní povrch (horizontální tok tepla)
RSE = 0.04   # m²·K/W – vnější povrch


@dataclass
class Vrstva:
    """Jedna vrstva stavební konstrukce."""
    nazev: str
    d: float          # tloušťka [m]
    lambda_: float    # součinitel tepelné vodivosti [W/(m·K)]

    @property
    def R(self) -> float:
        """Tepelný odpor vrstvy [m²·K/W]."""
        if self.lambda_ <= 0:
            return 0.0
        return self.d / self.lambda_


@dataclass
class Konstrukce:
    """
    Stavební konstrukce s výpočtem U-hodnoty a tepelné ztráty.

    Parametry
    ---------
    nazev       : popis konstrukce (např. „Obvodová stěna – původní")
    plocha_m2   : celková plocha konstrukce [m²]
    vrstvy      : seznam vrstev (Vrstva), od interiéru k exteriéru
    Rsi         : vnitřní povrchový odpor [m²·K/W] (default 0.13)
    Rse         : vnější povrchový odpor [m²·K/W] (default 0.04)
    """
    nazev: str = ""
    plocha_m2: float = 0.0
    vrstvy: list[Vrstva] = field(default_factory=list)
    Rsi: float = RSI
    Rse: float = RSE

    @property
    def R_tot(self) -> float:
        """Celkový tepelný odpor konstrukce [m²·K/W]."""
        return self.Rsi + sum(v.R for v in self.vrstvy) + self.Rse

    @property
    def U(self) -> float:
        """Součinitel prostupu tepla [W/(m²·K)]."""
        if self.R_tot <= 0:
            return 0.0
        return 1.0 / self.R_tot

    def H(self) -> float:
        """Měrná tepelná ztráta prostupem H = A × U [W/K]."""
        return self.plocha_m2 * self.U

    def tepelna_ztrata_kw(self, delta_T: float) -> float:
        """
        Tepelná ztráta prostupem Q = H × ΔT / 1 000 [kW].

        delta_T : teplotní rozdíl θi − θe [K]
        """
        return self.H() * delta_T / 1_000.0

    def uspora_tepelna_ztrata_kw(
        self,
        U_po: float,
        delta_T: float,
    ) -> float:
        """
        Úspora tepelné ztráty po zateplení [kW].

        U_po    : nová U-hodnota po realizaci opatření [W/(m²·K)]
        delta_T : teplotní rozdíl θi − θe [K]
        """
        Q_pred = self.tepelna_ztrata_kw(delta_T)
        Q_po   = self.plocha_m2 * U_po * delta_T / 1_000.0
        return max(0.0, Q_pred - Q_po)


def uspora_tepelne_ztráty(
    plocha_m2: float,
    U_pred: float,
    U_po: float,
    delta_T: float = 34.0,
) -> float:
    """
    Zkrácená verze: úspora tepelné ztráty [kW] bez potřeby vrstev.

    Vhodné, když je U_pred (stávající stav) zadáno přímo – např. z PENB.

    delta_T default = 34 K odpovídá θi=21 °C, θe=−13 °C (Praha).
    """
    return max(0.0, plocha_m2 * (U_pred - U_po) * delta_T / 1_000.0)
