"""
Hlavní kalkulační engine – třída Project.

Drží referenční energetická data a seznam opatření, spustí celý výpočetní
řetěz a vrátí ProjectResult s kompletní bilancí.

Odpovídá logice listu Celková bilance v Excel šabloně:
  • každé opatření dostane aktuální ChainState (zbývající spotřeby)
  • opatření vrátí MeasureResult a IN-PLACE sníží zbývající hodnoty
  • ProjectResult agreguje výsledky všech aktivních opatření
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Optional

from .models import BuildingInfo, ChainState, EnergyInputs, MeasureResult, ProjectResult
from .measures import BaseMeasure
from .economics import EkonomickeParametry, vypocitej_bilanci
from .emissions import vypocitej_emise
from .building_class import obalkova_klasifikace


@dataclass
class Project:
    """
    EPC projekt = identifikace budovy + referenční data + seznam opatření.

    Použití::

        from epc_engine import EnergyInputs, Project
        from epc_engine.measures import OP1a, OP9, OP10, OP11

        energie = EnergyInputs(
            zp_ut=450.0, zp_tuv=30.0,
            ee=95.0, voda=800.0,
            cena_zp=1_800.0, cena_ee=4_500.0,
            cena_voda=120.0,
            pouzit_zp=True,
        )

        projekt = Project(
            nazev="ZŠ Politických vězňů",
            energie=energie,
            opatreni=[
                OP1a(uspora_zp_mwh=60.0, plocha_m2=1200, cena_kc_m2=1800),
                OP9(pocet_ot=180, procento_uspory=0.10),
                OP10(uspora_ee_mwh=20.0, pocet_svitidel=200),
                OP11(vyroba_mwh=80, self_consumption_mwh=60, export_mwh=20,
                     n_panelu=160, cena_projektovani_kc=50_000),
            ],
        )

        result = projekt.vypocitej()
        print(f"Celková investice: {result.celkova_investice:,.0f} Kč")
        print(f"Prostá návratnost: {result.prosta_navratnost_celkem:.1f} let")
    """

    nazev: str = ""
    budova: BuildingInfo = field(default_factory=BuildingInfo)
    energie: EnergyInputs = field(default_factory=EnergyInputs)
    opatreni: list[BaseMeasure] = field(default_factory=list)

    # EA/EP rozšíření
    ekonomicke_parametry: Optional[EkonomickeParametry] = None
    uem_stav: float = 0.0       # W/m²K – průměrný součinitel prostupu tepla obálky
    faktor_tvaru: float = 0.0   # A/V [m⁻¹] – faktor tvaru budovy

    def vypocitej(self) -> ProjectResult:
        """
        Spustí výpočetní řetěz přes všechna opatření a vrátí ProjectResult.

        Chain state se inicializuje z referenčních spotřeb a průběžně se
        aktualizuje (každé aktivní opatření sníží zbývající spotřebu).
        Neaktivní opatření chain neovlivní.
        """
        chain = ChainState.from_inputs(self.energie)
        vysledky: list[MeasureResult] = []

        for op in self.opatreni:
            result = op.calculate(chain, self.energie)
            # Dopočítat % úspory z celkových nákladů (pokud není 0)
            if result.aktivni and self.energie.celkove_naklady > 0:
                result.uspora_pct = result.uspora_kc / self.energie.celkove_naklady
            vysledky.append(result)

        result = ProjectResult(energie=self.energie, vysledky=vysledky)

        # ── EA/EP rozšíření ──────────────────────────────────────────────────
        par = self.ekonomicke_parametry
        result.ekonomika_parametry = par

        # 1. Ekonomika – per opatření
        if par is not None:
            for r in result.vysledky:
                if r.aktivni and r.investice > 0:
                    r.ekonomika = vypocitej_bilanci(
                        r.investice, r.uspora_kc, r.servisni_naklady, par
                    )

        # 2. Ekonomika – projekt celkem
        if par is not None and result.celkova_investice > 0:
            result.ekonomika_projekt = vypocitej_bilanci(
                result.celkova_investice,
                result.celkova_uspora_kc,
                result.celkove_servisni_naklady,
                par,
            )

        # 3. Emisní bilance před a po opatřeních
        e = self.energie
        result.emise_pred = vypocitej_emise(
            zp_mwh=e.zp_total,
            teplo_mwh=e.teplo_total,
            ee_mwh=e.ee,
        )
        result.emise_po = vypocitej_emise(
            zp_mwh=max(0.0, e.zp_total - result.celkova_uspora_zp),
            teplo_mwh=max(0.0, e.teplo_total - result.celkova_uspora_teplo),
            ee_mwh=max(0.0, e.ee - result.celkova_uspora_ee),
        )

        # 4. Klasifikace obálky budovy (jen pokud jsou k dispozici vstupy)
        if self.uem_stav > 0.0 and self.faktor_tvaru > 0.0:
            result.klasifikace_pred = obalkova_klasifikace(
                self.uem_stav, self.faktor_tvaru
            )

        return result

    def vypocitej_scenar(
        self,
        aktivni_ids: list[str],
    ) -> ProjectResult:
        """
        Vypočítá scénář s jiným výběrem aktivních opatření.

        Parametr aktivni_ids je seznam ID opatření (např. ["OP1a", "OP9", "OP11"]).
        Ostatní opatření jsou pro tento výpočet deaktivována (originální objekt
        se nemění – pracuje se s kopií).

        Příklad::

            # Porovnat scénář bez zateplení vs. plný scénář
            base = projekt.vypocitej()
            bez_zatepleni = projekt.vypocitej_scenar(
                ["OP7", "OP9", "OP10", "OP11"]
            )
        """
        projekt_kopia = copy.deepcopy(self)
        for op in projekt_kopia.opatreni:
            op.aktivni = op.id in aktivni_ids
        return projekt_kopia.vypocitej()

    def tabulka_opatreni(self) -> list[dict]:
        """
        Vrátí výsledky jako seznam slovníků vhodný pro pandas DataFrame
        nebo přímé zobrazení v Streamlit tabulce.

        Klíče odpovídají sloupcům listu Celková bilance v Excel šabloně.
        """
        result = self.vypocitej()
        rows = []
        for r in result.vysledky:
            rows.append({
                "ID": r.id,
                "Název": r.nazev,
                "Aktivní": r.aktivni,
                "Investice [Kč]": r.investice if r.aktivni else 0,
                "Úspora tepla [MWh/rok]": r.uspora_teplo,
                "Úspora ZP [MWh/rok]": r.uspora_zp,
                "Úspora EE [MWh/rok]": r.uspora_ee,
                "Výnos přetoky [Kč/rok]": r.vynos_pretoky,
                "Úspora voda [m3/rok]": r.uspora_voda,
                "Úspora srážky [m3/rok]": r.uspora_srazky,
                "Úspora celkem [Kč/rok]": r.uspora_kc,
                "Úspora [%]": round(r.uspora_pct * 100, 1),
                "Servisní náklady [Kč/rok]": r.servisni_naklady,
                "Prostá návratnost [let]": (
                    r.prosta_navratnost
                    if r.prosta_navratnost is not None
                    else float("inf")
                ),
            })
        return rows

    def souhrn(self) -> dict:
        """
        Vrátí souhrnné výsledky projektu jako slovník (pro Streamlit karty).
        """
        result = self.vypocitej()
        return {
            "Název projektu": self.nazev,
            "Celková investice [Kč]": result.celkova_investice,
            "Úspora tepla [MWh/rok]": result.celkova_uspora_teplo,
            "Úspora ZP [MWh/rok]": result.celkova_uspora_zp,
            "Úspora EE [MWh/rok]": result.celkova_uspora_ee,
            "Výnos přetoky FVE [Kč/rok]": result.celkove_vynos_pretoky,
            "Úspora voda [m3/rok]": result.celkova_uspora_voda,
            "Úspora srážky [m3/rok]": result.celkova_uspora_srazky,
            "Úspora celkem [Kč/rok]": result.celkova_uspora_kc,
            "Úspora z celkových nákladů [%]": round(result.celkova_uspora_pct * 100, 1),
            "Servisní náklady [Kč/rok]": result.celkove_servisni_naklady,
            "Prostá návratnost [let]": (
                result.prosta_navratnost_celkem
                if result.prosta_navratnost_celkem is not None
                else float("inf")
            ),
        }
