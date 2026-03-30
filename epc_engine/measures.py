"""
Výpočtové třídy pro všechna opatření OP1a–OP22.

Každá třída:
  - drží vstupní parametry opatření (plochy, výkony, počty, ceny…)
  - implementuje metodu calculate(chain, energie) → MeasureResult
  - IN-PLACE aktualizuje chain (snižuje zbývající spotřeby)

Logika odpovídá vzorcům listů OP1a–OP22 a Celková bilance Excel šablony.
Pořadí opatření a závislosti jsou zachovány (tepelný řetěz OP1a → OP6 → OP7…).

Zkratky používané v kódu:
  k_t  = příznak aktivního tepla ze CZT  (0 nebo 1)
  k_zp = příznak aktivního zemního plynu (0 nebo 1)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from .models import ChainState, EnergyInputs, MeasureResult


# ── Pomocné funkce ────────────────────────────────────────────────────────────

def _navratnost(investice: float, uspora_kc: float, servisni: float) -> Optional[float]:
    """
    Prostá návratnost investice v letech.
    Vrací None pokud je čistá úspora ≤ 0 (v Excelu zobrazeno jako „∞").
    """
    net = uspora_kc - servisni
    if net <= 0:
        return None
    return investice / net


def _result(
    id: str,
    nazev: str,
    investice: float,
    uspora_teplo: float = 0.0,
    uspora_zp: float = 0.0,
    uspora_ee: float = 0.0,
    vynos_pretoky: float = 0.0,
    uspora_voda: float = 0.0,
    uspora_srazky: float = 0.0,
    servisni: float = 0.0,
    energie: Optional[EnergyInputs] = None,
) -> MeasureResult:
    """Sestaví MeasureResult včetně finanční úspory a návratnosti."""
    uspora_kc = (
        uspora_teplo * (energie.cena_teplo if energie else 0)
        + uspora_zp * (energie.cena_zp if energie else 0)
        + uspora_ee * (energie.cena_ee if energie else 0)
        + vynos_pretoky
        + uspora_voda * (energie.cena_voda if energie else 0)
        + uspora_srazky * (energie.cena_srazky if energie else 0)
    )
    uspora_pct = (
        uspora_kc / energie.celkove_naklady
        if (energie and energie.celkove_naklady > 0)
        else 0.0
    )
    r = MeasureResult(
        id=id,
        nazev=nazev,
        aktivni=True,
        investice=investice,
        uspora_teplo=uspora_teplo,
        uspora_zp=uspora_zp,
        uspora_ee=uspora_ee,
        vynos_pretoky=vynos_pretoky,
        uspora_voda=uspora_voda,
        uspora_srazky=uspora_srazky,
        uspora_kc=uspora_kc,
        uspora_pct=uspora_pct,
        servisni_naklady=servisni,
    )
    r.prosta_navratnost = _navratnost(investice, uspora_kc, servisni)
    return r


def _inactive(id: str, nazev: str) -> MeasureResult:
    return MeasureResult(id=id, nazev=nazev, aktivni=False)


def _uspora_zatepleni_mwh(
    plocha_m2: float,
    u_stavajici: float,
    u_nove: float,
    denostupne: float,
) -> float:
    """
    Roční úspora tepelné energie zateplením [MWh/rok].

    Vzorec: ΔU [W/m²K] × A [m²] × D [K·den] × 24 [h/den] / 1 000 000 [Wh→MWh]

    Pokud jsou vstupní parametry nulové nebo neplatné (u_stavajici ≤ u_nove),
    vrátí 0.0 – fyzikální výpočet nelze provést.
    """
    delta_u = max(0.0, u_stavajici - u_nove)
    return delta_u * plocha_m2 * denostupne * 24.0 / 1_000_000.0


# ── Abstraktní základ ─────────────────────────────────────────────────────────

class BaseMeasure(ABC):
    """Abstraktní základ všech opatření."""

    aktivni: bool = True

    @property
    @abstractmethod
    def id(self) -> str: ...

    @property
    @abstractmethod
    def nazev(self) -> str: ...

    @abstractmethod
    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        """
        Vypočítá výsledky opatření a IN-PLACE aktualizuje chain state.
        Pokud není opatření aktivní, vrátí prázdný MeasureResult s aktivni=False.
        """
        ...


# ══════════════════════════════════════════════════════════════════════════════
# SKUPINA 1 – Tepelný plášť (OP1a–OP6)
# Úspory tepla/ZP zadávány uživatelem přímo v MWh/rok
# (obvykle přebrány z výpočtu PENB nebo detailní simulace).
# Opatření snižují zbývající spotřebu v chain pro následující opatření.
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class OP1a(BaseMeasure):
    """
    OP1a – Zateplení obvodových stěn kontaktním zateplovacím systémem (ETICS).

    Vstupní parametry odpovídají listu OP1a Excel šablony:
      uspora_teplo_mwh / uspora_zp_mwh ← C35 / H35 (ruční override)
      plocha_m2                         ← C51
      cena_kc_m2                        ← C52

    Fyzikální režim (primární): zadej u_stavajici, u_nove, denostupne
    a úspora se vypočítá automaticky. Ruční hodnoty uspora_*_mwh mají přednost,
    pokud jsou nenulové.
    """
    aktivni: bool = True
    uspora_teplo_mwh: float = 0.0   # MWh/rok – ruční override pro CZT variantu
    uspora_zp_mwh: float = 0.0      # MWh/rok – ruční override pro plynovou variantu
    plocha_m2: float = 0.0          # m2 zateplované fasády
    cena_kc_m2: float = 0.0         # Kč/m2 vč. DPH
    servisni: float = 0.0           # Kč/rok
    u_stavajici: float = 0.0        # W/m²K – stávající U-hodnota stěny
    u_nove: float = 0.0             # W/m²K – U-hodnota po zateplení
    denostupne: float = 0.0         # K·den – roční denostupně lokality (z projektu)

    @property
    def id(self) -> str: return "OP1a"

    @property
    def nazev(self) -> str: return "Zateplení obvodových stěn (ETICS)"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        k_t = 1 if energie.pouzit_teplo else 0
        k_zp = 1 if energie.pouzit_zp else 0
        if self.uspora_teplo_mwh == 0.0 and self.uspora_zp_mwh == 0.0:
            uspora_mwh = _uspora_zatepleni_mwh(
                self.plocha_m2, self.u_stavajici, self.u_nove, self.denostupne
            )
            ut = uspora_mwh * k_t
            uzp = uspora_mwh * k_zp
        else:
            ut = self.uspora_teplo_mwh * k_t
            uzp = self.uspora_zp_mwh * k_zp
        chain.zbyvajici_teplo -= ut
        chain.zbyvajici_zp -= uzp
        return _result(
            self.id, self.nazev,
            investice=self.plocha_m2 * self.cena_kc_m2,
            uspora_teplo=ut, uspora_zp=uzp,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP1b(BaseMeasure):
    """
    OP1b – Obnova zateplení termoizolačním omítkovým systémem.

    Alternativa k OP1a pro objekty, kde není možné ETICS (NPÚ, …).
    Vstupní parametry: OP1b Excel šablona (C3/C4 = úspora součinitele U,
    C47=plocha, C48=cena; C31/H31 = výsledná úspora MWh).
    Fyzikální režim: viz OP1a.
    """
    aktivni: bool = True
    uspora_teplo_mwh: float = 0.0
    uspora_zp_mwh: float = 0.0
    plocha_m2: float = 0.0
    cena_kc_m2: float = 0.0
    servisni: float = 0.0
    u_stavajici: float = 0.0        # W/m²K – stávající U-hodnota stěny
    u_nove: float = 0.0             # W/m²K – U-hodnota po zateplení
    denostupne: float = 0.0         # K·den – roční denostupně lokality (z projektu)

    @property
    def id(self) -> str: return "OP1b"

    @property
    def nazev(self) -> str: return "Obnova zateplení stěn (termoizolační omítka)"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        k_t = 1 if energie.pouzit_teplo else 0
        k_zp = 1 if energie.pouzit_zp else 0
        if self.uspora_teplo_mwh == 0.0 and self.uspora_zp_mwh == 0.0:
            uspora_mwh = _uspora_zatepleni_mwh(
                self.plocha_m2, self.u_stavajici, self.u_nove, self.denostupne
            )
            ut = uspora_mwh * k_t
            uzp = uspora_mwh * k_zp
        else:
            ut = self.uspora_teplo_mwh * k_t
            uzp = self.uspora_zp_mwh * k_zp
        chain.zbyvajici_teplo -= ut
        chain.zbyvajici_zp -= uzp
        return _result(
            self.id, self.nazev,
            investice=self.plocha_m2 * self.cena_kc_m2,
            uspora_teplo=ut, uspora_zp=uzp,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP2(BaseMeasure):
    """
    OP2 – Výměna otvorových výplní (okna, dveře).

    Vstupní parametry: OP2 Excel šablona (C51=plocha, C52=cena, C35/H35=úspora).
    Fyzikální režim: viz OP1a.
    """
    aktivni: bool = True
    uspora_teplo_mwh: float = 0.0
    uspora_zp_mwh: float = 0.0
    plocha_m2: float = 0.0          # m2 měněných výplní
    cena_kc_m2: float = 0.0         # Kč/m2 vč. DPH
    servisni: float = 0.0
    u_stavajici: float = 0.0        # W/m²K – stávající U-hodnota výplně
    u_nove: float = 0.0             # W/m²K – U-hodnota po výměně
    denostupne: float = 0.0         # K·den – roční denostupně lokality (z projektu)

    @property
    def id(self) -> str: return "OP2"

    @property
    def nazev(self) -> str: return "Výměna otvorových výplní"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        k_t = 1 if energie.pouzit_teplo else 0
        k_zp = 1 if energie.pouzit_zp else 0
        if self.uspora_teplo_mwh == 0.0 and self.uspora_zp_mwh == 0.0:
            uspora_mwh = _uspora_zatepleni_mwh(
                self.plocha_m2, self.u_stavajici, self.u_nove, self.denostupne
            )
            ut = uspora_mwh * k_t
            uzp = uspora_mwh * k_zp
        else:
            ut = self.uspora_teplo_mwh * k_t
            uzp = self.uspora_zp_mwh * k_zp
        chain.zbyvajici_teplo -= ut
        chain.zbyvajici_zp -= uzp
        return _result(
            self.id, self.nazev,
            investice=self.plocha_m2 * self.cena_kc_m2,
            uspora_teplo=ut, uspora_zp=uzp,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP3(BaseMeasure):
    """OP3 – Rekonstrukce střechy (zateplení). Fyzikální režim: viz OP1a."""
    aktivni: bool = True
    uspora_teplo_mwh: float = 0.0
    uspora_zp_mwh: float = 0.0
    plocha_m2: float = 0.0
    cena_kc_m2: float = 0.0
    servisni: float = 0.0
    u_stavajici: float = 0.0        # W/m²K – stávající U-hodnota střechy
    u_nove: float = 0.0             # W/m²K – U-hodnota po zateplení
    denostupne: float = 0.0         # K·den – roční denostupně lokality (z projektu)

    @property
    def id(self) -> str: return "OP3"

    @property
    def nazev(self) -> str: return "Rekonstrukce střechy"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        k_t = 1 if energie.pouzit_teplo else 0
        k_zp = 1 if energie.pouzit_zp else 0
        if self.uspora_teplo_mwh == 0.0 and self.uspora_zp_mwh == 0.0:
            uspora_mwh = _uspora_zatepleni_mwh(
                self.plocha_m2, self.u_stavajici, self.u_nove, self.denostupne
            )
            ut = uspora_mwh * k_t
            uzp = uspora_mwh * k_zp
        else:
            ut = self.uspora_teplo_mwh * k_t
            uzp = self.uspora_zp_mwh * k_zp
        chain.zbyvajici_teplo -= ut
        chain.zbyvajici_zp -= uzp
        return _result(
            self.id, self.nazev,
            investice=self.plocha_m2 * self.cena_kc_m2,
            uspora_teplo=ut, uspora_zp=uzp,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP4(BaseMeasure):
    """OP4 – Zateplení podlahy půdy. Fyzikální režim: viz OP1a."""
    aktivni: bool = True
    uspora_teplo_mwh: float = 0.0
    uspora_zp_mwh: float = 0.0
    plocha_m2: float = 0.0
    cena_kc_m2: float = 0.0
    servisni: float = 0.0
    u_stavajici: float = 0.0        # W/m²K – stávající U-hodnota podlahy půdy
    u_nove: float = 0.0             # W/m²K – U-hodnota po zateplení
    denostupne: float = 0.0         # K·den – roční denostupně lokality (z projektu)

    @property
    def id(self) -> str: return "OP4"

    @property
    def nazev(self) -> str: return "Zateplení podlahy půdy"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        k_t = 1 if energie.pouzit_teplo else 0
        k_zp = 1 if energie.pouzit_zp else 0
        if self.uspora_teplo_mwh == 0.0 and self.uspora_zp_mwh == 0.0:
            uspora_mwh = _uspora_zatepleni_mwh(
                self.plocha_m2, self.u_stavajici, self.u_nove, self.denostupne
            )
            ut = uspora_mwh * k_t
            uzp = uspora_mwh * k_zp
        else:
            ut = self.uspora_teplo_mwh * k_t
            uzp = self.uspora_zp_mwh * k_zp
        chain.zbyvajici_teplo -= ut
        chain.zbyvajici_zp -= uzp
        return _result(
            self.id, self.nazev,
            investice=self.plocha_m2 * self.cena_kc_m2,
            uspora_teplo=ut, uspora_zp=uzp,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP5(BaseMeasure):
    """OP5 – Zateplení podlahy na terénu. Fyzikální režim: viz OP1a."""
    aktivni: bool = True
    uspora_teplo_mwh: float = 0.0
    uspora_zp_mwh: float = 0.0
    plocha_m2: float = 0.0
    cena_kc_m2: float = 0.0
    servisni: float = 0.0
    u_stavajici: float = 0.0        # W/m²K – stávající U-hodnota podlahy
    u_nove: float = 0.0             # W/m²K – U-hodnota po zateplení
    denostupne: float = 0.0         # K·den – roční denostupně lokality (z projektu)

    @property
    def id(self) -> str: return "OP5"

    @property
    def nazev(self) -> str: return "Zateplení podlahy na terénu"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        k_t = 1 if energie.pouzit_teplo else 0
        k_zp = 1 if energie.pouzit_zp else 0
        if self.uspora_teplo_mwh == 0.0 and self.uspora_zp_mwh == 0.0:
            uspora_mwh = _uspora_zatepleni_mwh(
                self.plocha_m2, self.u_stavajici, self.u_nove, self.denostupne
            )
            ut = uspora_mwh * k_t
            uzp = uspora_mwh * k_zp
        else:
            ut = self.uspora_teplo_mwh * k_t
            uzp = self.uspora_zp_mwh * k_zp
        chain.zbyvajici_teplo -= ut
        chain.zbyvajici_zp -= uzp
        return _result(
            self.id, self.nazev,
            investice=self.plocha_m2 * self.cena_kc_m2,
            uspora_teplo=ut, uspora_zp=uzp,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP6(BaseMeasure):
    """OP6 – Výmalba interiérů termoreflexními nátěry. Fyzikální režim: viz OP1a."""
    aktivni: bool = True
    uspora_teplo_mwh: float = 0.0
    uspora_zp_mwh: float = 0.0
    plocha_m2: float = 0.0
    cena_kc_m2: float = 0.0
    servisni: float = 0.0
    u_stavajici: float = 0.0        # W/m²K – ekvivalentní U-hodnota před nátěrem
    u_nove: float = 0.0             # W/m²K – ekvivalentní U-hodnota po nátěru
    denostupne: float = 0.0         # K·den – roční denostupně lokality (z projektu)

    @property
    def id(self) -> str: return "OP6"

    @property
    def nazev(self) -> str: return "Termoreflexní nátěry interiérů"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        k_t = 1 if energie.pouzit_teplo else 0
        k_zp = 1 if energie.pouzit_zp else 0
        if self.uspora_teplo_mwh == 0.0 and self.uspora_zp_mwh == 0.0:
            uspora_mwh = _uspora_zatepleni_mwh(
                self.plocha_m2, self.u_stavajici, self.u_nove, self.denostupne
            )
            ut = uspora_mwh * k_t
            uzp = uspora_mwh * k_zp
        else:
            ut = self.uspora_teplo_mwh * k_t
            uzp = self.uspora_zp_mwh * k_zp
        chain.zbyvajici_teplo -= ut
        chain.zbyvajici_zp -= uzp
        return _result(
            self.id, self.nazev,
            investice=self.plocha_m2 * self.cena_kc_m2,
            uspora_teplo=ut, uspora_zp=uzp,
            servisni=self.servisni, energie=energie,
        )


# ══════════════════════════════════════════════════════════════════════════════
# SKUPINA 2 – Zdroj tepla a regulace (OP7–OP9)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class OP7(BaseMeasure):
    """
    OP7 – Výměna zdroje tepla (kondenzační kotle, tepelné čerpadlo, …).

    Úspory zadává uživatel přímo v MWh/rok.
    EE může být záporné (= navýšení spotřeby, typicky při instalaci TČ).

    Vstupní parametry: OP7 Excel šablona (C35/H35=teplo, C83=EE změna, C53=inv.).
    """
    aktivni: bool = True
    uspora_teplo_mwh: float = 0.0   # MWh/rok – úspora tepla (CZT)
    uspora_zp_mwh: float = 0.0      # MWh/rok – úspora ZP
    zmena_ee_mwh: float = 0.0       # MWh/rok – záporné = navýšení EE (tepelné čerpadlo)
    investice_kc: float = 0.0       # Kč vč. DPH
    servisni: float = 0.0           # Kč/rok

    @property
    def id(self) -> str: return "OP7"

    @property
    def nazev(self) -> str: return "Výměna zdroje tepla"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        k_t = 1 if energie.pouzit_teplo else 0
        k_zp = 1 if energie.pouzit_zp else 0
        ut = self.uspora_teplo_mwh * k_t
        uzp = self.uspora_zp_mwh * k_zp
        chain.zbyvajici_teplo -= ut
        chain.zbyvajici_zp -= uzp
        chain.zbyvajici_ee -= self.zmena_ee_mwh  # záporné zvyšuje zbývající
        return _result(
            self.id, self.nazev,
            investice=self.investice_kc,
            uspora_teplo=ut, uspora_zp=uzp,
            uspora_ee=self.zmena_ee_mwh,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP8(BaseMeasure):
    """
    OP8 – Instalace nadřazené regulace a nová výzbroj rozdělovače/sběrače.

    Úspora tepla = zbývající spotřeba ÚT × procento_uspory.
    „Zbývající ÚT" = chain.zbyvajici_teplo − ref_teplo_tuv (TUV se neúsporuje).

    Vzorce Excel: C35 = (C33 − Ref!C29) × C4, C53 = C3 × (4_500_000 / 25).
    """
    aktivni: bool = True
    pocet_vetvi: int = 1            # počet větví otopné soustavy (C3)
    procento_uspory: float = 0.05   # typicky 5 % (C4 v Excelu)
    servisni: float = 0.0
    # Orientační cena za větev (Kč/větev); v Excelu: 4 500 000 / 25 = 180 000
    cena_kc_vetev: float = 180_000.0

    @property
    def id(self) -> str: return "OP8"

    @property
    def nazev(self) -> str: return "Nadřazená regulace a výzbroj R/S"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        k_t = 1 if energie.pouzit_teplo else 0
        k_zp = 1 if energie.pouzit_zp else 0
        investice = self.pocet_vetvi * self.cena_kc_vetev
        # Úspora pouze z ÚT části (TUV se neúsporuje)
        ut = chain.zbyvajici_teplo_ut() * self.procento_uspory * k_t
        uzp = chain.zbyvajici_zp_ut() * self.procento_uspory * k_zp
        chain.zbyvajici_teplo -= ut
        chain.zbyvajici_zp -= uzp
        return _result(
            self.id, self.nazev,
            investice=investice,
            uspora_teplo=ut, uspora_zp=uzp,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP9(BaseMeasure):
    """
    OP9 – Zavedení IRC systému (individuální regulace) na otopná tělesa.

    Úspora tepla = zbývající ÚT × procento_uspory (typicky 8–12 %).
    Investice = počet OT × cena_kc_ot.
    Servisní náklady = roční programování a maintenance (C82 v Excelu).

    Vzorce Excel:
      C35  = (C33 − Ref!C29) × C4
      C52  = 13 000 Kč/ot
      C80  = n_ot × 2/3 × 25 + 10 000  (roční servis – programování)
      C81  = 12 000                     (fixní roční maintenance)
    """
    aktivni: bool = True
    pocet_ot: int = 0               # počet otopných těles (C3)
    procento_uspory: float = 0.10   # typicky 10 % (C4 v Excelu)
    cena_kc_ot: float = 13_000.0    # Kč/ot vč. DPH (IRC hlavice + ventil)
    fixni_servis_kc: float = 12_000.0  # roční fixní maintenance (C81)

    @property
    def id(self) -> str: return "OP9"

    @property
    def nazev(self) -> str: return "IRC systém (individuální regulace)"

    @property
    def _servisni(self) -> float:
        # C80 + C81 = roční servisní náklady
        return self.pocet_ot * 2 / 3 * 25 + 10_000 + self.fixni_servis_kc

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        k_t = 1 if energie.pouzit_teplo else 0
        k_zp = 1 if energie.pouzit_zp else 0
        investice = self.pocet_ot * self.cena_kc_ot
        ut = chain.zbyvajici_teplo_ut() * self.procento_uspory * k_t
        uzp = chain.zbyvajici_zp_ut() * self.procento_uspory * k_zp
        chain.zbyvajici_teplo -= ut
        chain.zbyvajici_zp -= uzp
        return _result(
            self.id, self.nazev,
            investice=investice,
            uspora_teplo=ut, uspora_zp=uzp,
            servisni=self._servisni, energie=energie,
        )


# ══════════════════════════════════════════════════════════════════════════════
# SKUPINA 3 – Elektrická energie (OP10–OP13)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class OP10(BaseMeasure):
    """
    OP10 – Instalace LED osvětlení.

    Úspory EE zadává uživatel (z kalkulace LED náhrad, typicky z tabulky OP10).
    Investice = počet svítidel × (cena_svitidlo + montaz).

    Vzorce Excel:
      C34  = C33 − C35   (zbývající EE po OP10)
      C54  = C51 × C52 + C51 × C53  (= n × 5 500 + n × 1 000)
    """
    aktivni: bool = True
    uspora_ee_mwh: float = 0.0      # MWh/rok – úspora EE po výměně na LED (C35)
    pocet_svitidel: int = 0         # celkový počet nahrazovaných svítidel (C51)
    cena_svitidlo_kc: float = 5_500.0  # Kč/ks LED svítidlo (C52)
    cena_montaz_kc: float = 1_000.0    # Kč/ks montáž (C53)
    servisni: float = 0.0

    @property
    def id(self) -> str: return "OP10"

    @property
    def nazev(self) -> str: return "Instalace LED osvětlení"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        investice = self.pocet_svitidel * (self.cena_svitidlo_kc + self.cena_montaz_kc)
        chain.zbyvajici_ee -= self.uspora_ee_mwh
        return _result(
            self.id, self.nazev,
            investice=investice,
            uspora_ee=self.uspora_ee_mwh,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP11(BaseMeasure):
    """
    OP11 – Instalace fotovoltaické elektrárny (FVE).

    Výpočet zahrnuje:
      • vlastní spotřebu (úspora EE = self_consumption_mwh × cena_ee)
      • přetoky do sítě (výnos = export_mwh × cena_ee_vykup)

    Servisní náklady = 110 Kč/MWh × roční_vyroba (C73 = 110 × C23 v Excelu).

    Investice = komponenty FVE (C41–C45 v Excelu):
      panely:        n_panelu × cena_panel
      střídače:      (n_panelu / 2) × cena_stridac
      projektování:  cena_projektovani (paušál)
      revize:        cena_revize (paušál)
      montáž:        cena_montaz (paušál)
    """
    aktivni: bool = True
    # Výroba a spotřeba
    vyroba_mwh: float = 0.0           # MWh/rok – celková roční výroba FVE (C24)
    self_consumption_mwh: float = 0.0  # MWh/rok – vlastní spotřeba (C5 = C27)
    export_mwh: float = 0.0           # MWh/rok – přetoky do sítě (C6)
    # Investice
    n_panelu: int = 0                 # počet panelů (C41)
    cena_panel_kc: float = 3_200.0    # Kč/panel (D41)
    cena_stridac_kc: float = 900.0    # Kč/ks střídač (D42, 1 střídač per 2 panely)
    cena_projektovani_kc: float = 0.0 # Kč paušál (D43)
    cena_revize_kc: float = 0.0       # Kč paušál (D44)
    cena_montaz_kc: float = 0.0       # Kč paušál (D45)

    @property
    def id(self) -> str: return "OP11"

    @property
    def nazev(self) -> str: return "Instalace fotovoltaické elektrárny (FVE)"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        investice = (
            self.n_panelu * self.cena_panel_kc
            + (self.n_panelu / 2) * self.cena_stridac_kc
            + self.cena_projektovani_kc
            + self.cena_revize_kc
            + self.cena_montaz_kc
        )
        vynos_pretoky = self.export_mwh * energie.cena_ee_vykup
        # Servis: 110 Kč/MWh roční výroby
        servisni = 110.0 * self.vyroba_mwh
        chain.zbyvajici_ee -= self.self_consumption_mwh
        return _result(
            self.id, self.nazev,
            investice=investice,
            uspora_ee=self.self_consumption_mwh,
            vynos_pretoky=vynos_pretoky,
            servisni=servisni, energie=energie,
        )


@dataclass
class OP12(BaseMeasure):
    """
    OP12 – Instalace bateriového uložiště.

    Baterie zvyšuje míru vlastní spotřeby FVE – přebytky, které by jinak šly
    do sítě, se nyní spotřebují vlastně. Úspora = rozdíl (cena_ee − cena_vykup).

    Servisní náklady = 70 Kč/MWh × navice_vyuzito_mwh (C61 = 70 × C18 v Excelu).
    """
    aktivni: bool = True
    velikost_mwh: float = 0.0          # kapacita baterie v MWh (C3)
    cena_kc_mwh: float = 0.0           # Kč/MWh instalované kapacity
    navice_vyuzito_mwh: float = 0.0    # MWh/rok navíc oproti bez baterie (C4)

    @property
    def id(self) -> str: return "OP12"

    @property
    def nazev(self) -> str: return "Instalace bateriového uložiště"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        investice = self.velikost_mwh * self.cena_kc_mwh
        # Úspora = neposílám do sítě za výkupní cenu, ale spotřebuji za plnou cenu
        uspora_kc = self.navice_vyuzito_mwh * max(0.0, energie.cena_ee - energie.cena_ee_vykup)
        servisni = 70.0 * self.navice_vyuzito_mwh
        # Baterie jen přesouvá spotřebu – nesnižuje zbývající EE v chain
        r = MeasureResult(
            id=self.id, nazev=self.nazev, aktivni=True,
            investice=investice,
            uspora_ee=self.navice_vyuzito_mwh,
            uspora_kc=uspora_kc,
            servisni_naklady=servisni,
        )
        r.prosta_navratnost = _navratnost(investice, uspora_kc, servisni)
        return r


@dataclass
class OP13(BaseMeasure):
    """
    OP13 – Využití přebytků FVE pro ohřev TUV (diverter + akumulační nádrž).

    Snižuje spotřebu tepla/ZP/EE pro ohřev TUV tím, že přebytky FVE ohřejí vodu.
    Faktory k_tuv (F11–F13 v Ovládání) určují, přes který energonosič úspora plyne.

    Vzorce Excel: C24 = (C21×C23 − C22×C20) × F11 (viz OP13 sheet).
    Zjednodušení: zadejte přímo úspory pro každý energonosič v MWh/rok.
    """
    aktivni: bool = True
    uspora_teplo_tuv_mwh: float = 0.0  # MWh/rok – úspora tepla (CZT) pro TUV
    uspora_zp_tuv_mwh: float = 0.0     # MWh/rok – úspora ZP pro TUV
    uspora_ee_tuv_mwh: float = 0.0     # MWh/rok – úspora EE pro TUV (el. bojler)
    velikost_nadrze_l: float = 0.0     # litrů – akumulační nádrž
    cena_kc_l: float = 70.0            # Kč/litr (D36 v Excelu)
    servisni: float = 0.0

    @property
    def id(self) -> str: return "OP13"

    @property
    def nazev(self) -> str: return "Využití přebytků FVE pro ohřev TUV"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        investice = self.velikost_nadrze_l * self.cena_kc_l
        k_t = 1 if energie.pouzit_teplo else 0
        k_zp = 1 if energie.pouzit_zp else 0
        ut = self.uspora_teplo_tuv_mwh * k_t
        uzp = self.uspora_zp_tuv_mwh * k_zp
        uee = self.uspora_ee_tuv_mwh
        chain.zbyvajici_teplo -= ut
        chain.zbyvajici_zp -= uzp
        chain.zbyvajici_ee -= uee
        servisni = 70.0 * (ut + uzp + uee)  # 70 Kč/MWh dle OP13!C63
        return _result(
            self.id, self.nazev,
            investice=investice,
            uspora_teplo=ut, uspora_zp=uzp, uspora_ee=uee,
            servisni=servisni, energie=energie,
        )


# ══════════════════════════════════════════════════════════════════════════════
# SKUPINA 4 – Voda (OP14–OP15)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class OP14(BaseMeasure):
    """
    OP14 – Instalace spořičů vody.

    Úspora vody = celková spotřeba × procento_uspory.
    Investice = n_umyvadel × cena_baterie + n_sprch × cena_sprcha + n_wc × cena_wc.

    Vzorce Excel: C22 = C20 × C6, C44 = C38×C41 + C39×C42 + C40×C43.
    """
    aktivni: bool = True
    procento_uspory: float = 0.0      # podíl ušetřené vody (C6, např. 0.15 = 15 %)
    n_umyvadel: int = 0               # počet baterií umyvadel (C3)
    n_sprch: int = 0                  # počet sprchových hlavic (C4)
    n_splachovadel: int = 0           # počet splachovadel (C5)
    cena_baterie_kc: float = 400.0    # Kč/ks (C41)
    cena_sprcha_kc: float = 500.0     # Kč/ks (C42)
    cena_splachovadlo_kc: float = 800.0  # Kč/ks (C43)
    servisni: float = 0.0

    @property
    def id(self) -> str: return "OP14"

    @property
    def nazev(self) -> str: return "Instalace spořičů vody"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        investice = (
            self.n_umyvadel * self.cena_baterie_kc
            + self.n_sprch * self.cena_sprcha_kc
            + self.n_splachovadel * self.cena_splachovadlo_kc
        )
        uspora_m3 = chain.zbyvajici_voda * self.procento_uspory
        chain.zbyvajici_voda -= uspora_m3
        return _result(
            self.id, self.nazev,
            investice=investice,
            uspora_voda=uspora_m3,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP15(BaseMeasure):
    """
    OP15 – Instalace retenčních nádrží na dešťovou vodu.

    Úspora srážkového poplatku = spotřeba_srazky × procento_uspory.
    Investice = velikost_nadrze_l × 27 Kč/litr (C37 v Excelu).

    Vzorce Excel: C20 = C18 × C4, C38 = C3 × 27.
    """
    aktivni: bool = True
    procento_uspory: float = 0.0      # podíl snížení srážkového poplatku (C4)
    velikost_nadrze_l: float = 0.0    # litrů (C3)
    cena_kc_l: float = 27.0           # Kč/litr (C37)
    servisni: float = 0.0

    @property
    def id(self) -> str: return "OP15"

    @property
    def nazev(self) -> str: return "Retenční nádrž na dešťovou vodu"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        investice = self.velikost_nadrze_l * self.cena_kc_l
        uspora_m3 = chain.zbyvajici_srazky * self.procento_uspory
        chain.zbyvajici_srazky -= uspora_m3
        return _result(
            self.id, self.nazev,
            investice=investice,
            uspora_srazky=uspora_m3,
            servisni=self.servisni, energie=energie,
        )


# ══════════════════════════════════════════════════════════════════════════════
# SKUPINA 5 – Povinná opatření dle dotačních podmínek (OP16–OP19)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class OP16(BaseMeasure):
    """
    OP16 – Hydraulické vyvážení otopné soustavy.

    Úspora = zbývající ÚT × 3 % (pevná hodnota dle OP16!C4 = 0.03).
    Investice = počet OT × 1 200 Kč/ot (C52 v Excelu).

    Vzorce Excel: C35 = (C33 − Ref!C29) × C4, C52 = 1 200.
    """
    aktivni: bool = True
    pocet_ot: int = 0               # přebrán z OP9 (C3 = OP9!C3)
    procento_uspory: float = 0.03   # 3 % (pevně dle Excel šablony)
    cena_kc_ot: float = 1_200.0     # Kč/ot (C52)
    servisni: float = 0.0

    @property
    def id(self) -> str: return "OP16"

    @property
    def nazev(self) -> str: return "Hydraulické vyvážení otopné soustavy"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        k_t = 1 if energie.pouzit_teplo else 0
        k_zp = 1 if energie.pouzit_zp else 0
        investice = self.pocet_ot * self.cena_kc_ot
        ut = chain.zbyvajici_teplo_ut() * self.procento_uspory * k_t
        uzp = chain.zbyvajici_zp_ut() * self.procento_uspory * k_zp
        chain.zbyvajici_teplo -= ut
        chain.zbyvajici_zp -= uzp
        return _result(
            self.id, self.nazev,
            investice=investice,
            uspora_teplo=ut, uspora_zp=uzp,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP17(BaseMeasure):
    """
    OP17 – Instalace vzduchotechniky se zpětným získáváním tepla (ZZT).

    Úspora tepla = zbývající spotřeba × 3 % (C4 = 0.03).
    Navýšení EE  = zbývající spotřeba × 2 % (C5 = 0.02).
    Investice    = počet_jednotek × 295 000 Kč/ks (C52).

    Servis zahrnuje roční provoz VZT a výměnu filtrů.
    Vzorce Excel: C35=C33×C4, C82=C80×C5, C53=C6×295_000.
    """
    aktivni: bool = True
    pocet_jednotek: int = 0            # počet VZT jednotek (C6)
    procento_uspory_tepla: float = 0.03   # 3 % (C4 pevně)
    procento_navyseni_ee: float = 0.02    # 2 % (C5 pevně)
    cena_kc_jednotka: float = 295_000.0  # Kč/ks (C52)
    cena_filtry_kc: float = 15_000.0     # Kč/rok (C99)

    @property
    def id(self) -> str: return "OP17"

    @property
    def nazev(self) -> str: return "VZT se zpětným získáváním tepla (ZZT)"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        k_t = 1 if energie.pouzit_teplo else 0
        k_zp = 1 if energie.pouzit_zp else 0
        investice = self.pocet_jednotek * self.cena_kc_jednotka
        ut = chain.zbyvajici_teplo_ut() * self.procento_uspory_tepla * k_t
        uzp = chain.zbyvajici_zp_ut()   * self.procento_uspory_tepla * k_zp
        navys_ee = chain.zbyvajici_ee * self.procento_navyseni_ee   # záporná "úspora"
        servisni = self.pocet_jednotek * 4 * 2_000 + self.cena_filtry_kc  # C98 + C99
        chain.zbyvajici_teplo -= ut
        chain.zbyvajici_zp -= uzp
        chain.zbyvajici_ee += navys_ee  # spotřeba EE roste
        return _result(
            self.id, self.nazev,
            investice=investice,
            uspora_teplo=ut, uspora_zp=uzp,
            uspora_ee=-navys_ee,   # záporné = navýšení EE nákladů
            servisni=servisni, energie=energie,
        )


@dataclass
class OP18(BaseMeasure):
    """
    OP18 – Instalace venkovních stínicích prvků.

    Nemá přímé energetické úspory modelované v Excel šabloně.
    Investice = plocha_m2 × 3 000 Kč/m2 (C18 = OP2!C51/2.5, C19 = C17×3000).
    """
    aktivni: bool = True
    plocha_m2: float = 0.0          # m2 osazovaných výplní (= OP2 plocha / 2.5)
    cena_kc_m2: float = 3_000.0     # Kč/m2 (C18)
    servisni: float = 0.0

    @property
    def id(self) -> str: return "OP18"

    @property
    def nazev(self) -> str: return "Venkovní stínicí prvky"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        investice = self.plocha_m2 * self.cena_kc_m2
        return _result(
            self.id, self.nazev,
            investice=investice,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP19(BaseMeasure):
    """
    OP19 – Zavedení energetického managementu (monitoring a měření).

    Nemá přímé energetické úspory – pouze investice a provozní náklady.
    Investice = počet_odbernych_mist × 32 400 + 40 000 (C20 × C19 + C33 v Excelu).
    """
    aktivni: bool = True
    pocet_mist: int = 12            # počet měřených odběrných míst (C3 = 12)
    cena_kc_misto: float = 32_400.0 # Kč/místo (C20)
    cena_hw_kc: float = 40_000.0    # Kč – hardware/platforma (C33)
    servisni: float = 0.0

    @property
    def id(self) -> str: return "OP19"

    @property
    def nazev(self) -> str: return "Energetický management (měření a monitoring)"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        investice = self.pocet_mist * self.cena_kc_misto + self.cena_hw_kc
        return _result(
            self.id, self.nazev,
            investice=investice,
            servisni=self.servisni, energie=energie,
        )


# ══════════════════════════════════════════════════════════════════════════════
# SKUPINA 6 – Infrastruktura / udržení bezpečného provozu (OP20–OP22)
# Žádné energetické úspory – pouze investice a servisní náklady.
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class OP20(BaseMeasure):
    """OP20 – Rekonstrukce otopné soustavy (výměna těles, potrubí)."""
    aktivni: bool = True
    plocha_m2: float = 0.0
    cena_kc_m2: float = 0.0
    servisni: float = 0.0

    @property
    def id(self) -> str: return "OP20"

    @property
    def nazev(self) -> str: return "Rekonstrukce otopné soustavy"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        return _result(
            self.id, self.nazev,
            investice=self.plocha_m2 * self.cena_kc_m2,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP21(BaseMeasure):
    """OP21 – Rekonstrukce elektroinstalace."""
    aktivni: bool = True
    investice_kc: float = 0.0
    servisni: float = 0.0

    @property
    def id(self) -> str: return "OP21"

    @property
    def nazev(self) -> str: return "Rekonstrukce elektroinstalace"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        return _result(
            self.id, self.nazev,
            investice=self.investice_kc,
            servisni=self.servisni, energie=energie,
        )


@dataclass
class OP22(BaseMeasure):
    """OP22 – Rekonstrukce rozvodů teplé a studené vody."""
    aktivni: bool = True
    investice_kc: float = 0.0
    servisni: float = 0.0

    @property
    def id(self) -> str: return "OP22"

    @property
    def nazev(self) -> str: return "Rekonstrukce rozvodů teplé a studené vody"

    def calculate(self, chain: ChainState, energie: EnergyInputs) -> MeasureResult:
        if not self.aktivni:
            return _inactive(self.id, self.nazev)
        return _result(
            self.id, self.nazev,
            investice=self.investice_kc,
            servisni=self.servisni, energie=energie,
        )


# ── Veřejný seznam všech opatření v pořadí výpočtu ───────────────────────────

ALL_MEASURES: list[type[BaseMeasure]] = [
    OP1a, OP1b, OP2, OP3, OP4, OP5, OP6,   # tepelný plášť
    OP7, OP8, OP9,                           # zdroj tepla a regulace
    OP10, OP11, OP12, OP13,                  # elektrická energie / FVE
    OP14, OP15,                              # voda
    OP16, OP17, OP18, OP19,                  # dotační povinnosti
    OP20, OP21, OP22,                        # infrastruktura
]
