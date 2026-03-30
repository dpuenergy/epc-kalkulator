"""
Testy pro Sprint 2 – EA/EP soulad.

Pokrývá:
  • epc_engine.economics  – NPV, IRR, Tsd
  • epc_engine.emissions  – EmiseBilance, EPS
  • epc_engine.building_class – Uem,N, A–G klasifikace
  • epc_engine.calculator – integrace EA/EP do vypocitej()
"""

from __future__ import annotations

import pytest

from epc_engine.economics import (
    EkonomickeParametry,
    EkonomickeBilance,
    vypocitej_npv,
    vypocitej_tsd,
    vypocitej_irr,
    vypocitej_bilanci,
)
from epc_engine.emissions import (
    EmiseBilance,
    EMISNI_FAKTORY,
    vypocitej_emise,
)
from epc_engine.building_class import (
    KlasifikaceObaly,
    vypocitej_uem_n,
    klasifikuj_uem,
    obalkova_klasifikace,
)
from epc_engine.calculator import Project
from epc_engine.models import EnergyInputs
from epc_engine.measures import OP1a


# ──────────────────────────────────────────────────────────────────────────────
# Ekonomika
# ──────────────────────────────────────────────────────────────────────────────

class TestEkonomika:

    @pytest.fixture
    def par_standard(self) -> EkonomickeParametry:
        return EkonomickeParametry(horizont=20, diskontni_sazba=0.04, inflace_energie=0.03)

    @pytest.fixture
    def par_bez_inflace(self) -> EkonomickeParametry:
        return EkonomickeParametry(horizont=20, diskontni_sazba=0.04, inflace_energie=0.0)

    def test_npv_kladne_pri_kratke_navratnosti(self, par_standard):
        # Investice 100k, úspora 15k/rok, servisní 1k → NPV musí být kladné
        npv = vypocitej_npv(100_000, 15_000, 1_000, par_standard)
        assert npv > 0

    def test_npv_zaporne_pri_dlouhe_navratnosti(self, par_standard):
        # Investice 1M, úspora jen 5k/rok → NPV musí být záporné
        npv = vypocitej_npv(1_000_000, 5_000, 0, par_standard)
        assert npv < 0

    def test_npv_nulova_investice(self, par_standard):
        # Nulová investice → NPV = PV diskontovaných příjmů (kladné)
        npv = vypocitej_npv(0, 10_000, 0, par_standard)
        assert npv > 0

    def test_tsd_existuje_pro_kratkou_navratnost(self, par_bez_inflace):
        # Bez inflace, prostá návratnost ≈ 100k / (15k - 1k) ≈ 7,1 let
        # Diskontovaná Tsd bude o trochu delší
        tsd = vypocitej_tsd(100_000, 15_000, 1_000, par_bez_inflace)
        assert tsd is not None
        assert 7 <= tsd <= 12

    def test_tsd_none_pro_ztratu(self, par_standard):
        # Úspora menší než servisní → projekt nikdy nesplatí
        tsd = vypocitej_tsd(100_000, 500, 1_000, par_standard)
        assert tsd is None

    def test_tsd_none_pri_prilis_dlouhe_navratnosti(self, par_standard):
        # Investice 1M, úspora 10k → prostá návratnost >20 let → Tsd bude None
        tsd = vypocitej_tsd(1_000_000, 10_000, 0, par_standard)
        assert tsd is None

    def test_irr_vetsi_nez_diskont_kdyz_npv_kladne(self, par_standard):
        # NPV > 0 ↔ IRR > diskontní sazba
        irr = vypocitej_irr(100_000, 15_000, 1_000, par_standard)
        assert irr is not None
        assert irr > par_standard.diskontni_sazba

    def test_irr_none_pro_nerentabilni_projekt(self, par_standard):
        # Úspora < servisní → projekt není rentabilní
        irr = vypocitej_irr(100_000, 500, 1_000, par_standard)
        assert irr is None

    def test_irr_none_pro_nulovou_investici_pri_low_uspora(self, par_standard):
        # investice=0 → vrátí None (podmínka investice <= 0)
        irr = vypocitej_irr(0, 15_000, 1_000, par_standard)
        assert irr is None

    def test_vypocitej_bilanci_vraci_vsechna_pole(self, par_standard):
        b = vypocitej_bilanci(100_000, 15_000, 1_000, par_standard)
        assert isinstance(b, EkonomickeBilance)
        assert b.npv > 0
        assert b.irr is not None
        assert b.tsd is not None

    def test_konzistence_npv_irr(self, par_standard):
        """Pokud NPV > 0, pak IRR musí existovat a IRR > diskontní sazba."""
        npv = vypocitej_npv(100_000, 15_000, 1_000, par_standard)
        irr = vypocitej_irr(100_000, 15_000, 1_000, par_standard)
        assert npv > 0
        assert irr is not None
        assert irr > par_standard.diskontni_sazba


# ──────────────────────────────────────────────────────────────────────────────
# Emise
# ──────────────────────────────────────────────────────────────────────────────

class TestEmise:

    def test_emise_jen_zp(self):
        b = vypocitej_emise(zp_mwh=100, teplo_mwh=0, ee_mwh=0)
        assert b.co2_kg == pytest.approx(100 * EMISNI_FAKTORY["zp"]["co2"])
        assert b.nox_kg == pytest.approx(100 * EMISNI_FAKTORY["zp"]["nox"], rel=1e-3)

    def test_emise_jen_teplo(self):
        b = vypocitej_emise(zp_mwh=0, teplo_mwh=50, ee_mwh=0)
        assert b.co2_kg == pytest.approx(50 * EMISNI_FAKTORY["teplo"]["co2"])

    def test_emise_jen_ee(self):
        b = vypocitej_emise(zp_mwh=0, teplo_mwh=0, ee_mwh=200)
        assert b.co2_kg == pytest.approx(200 * EMISNI_FAKTORY["ee"]["co2"])

    def test_emise_soucet_vice_nosicu(self):
        b = vypocitej_emise(zp_mwh=100, teplo_mwh=0, ee_mwh=100)
        ocekavano_co2 = (100 * EMISNI_FAKTORY["zp"]["co2"]
                         + 100 * EMISNI_FAKTORY["ee"]["co2"])
        assert b.co2_kg == pytest.approx(ocekavano_co2)

    def test_eps_vzorec_ee(self):
        """EPS pro samotnou EE: 1×TZL + 0,88×NOₓ + 0,54×SO₂."""
        b = vypocitej_emise(zp_mwh=0, teplo_mwh=0, ee_mwh=100)
        tzl = 100 * EMISNI_FAKTORY["ee"]["tzl"]
        nox = 100 * EMISNI_FAKTORY["ee"]["nox"]
        so2 = 100 * EMISNI_FAKTORY["ee"]["so2"]
        ocekavany_eps = tzl * 1.0 + nox * 0.88 + so2 * 0.54
        assert b.eps_kg == pytest.approx(ocekavany_eps, rel=1e-3)

    def test_nulove_vstupy_vraci_nuly(self):
        b = vypocitej_emise(0, 0, 0)
        assert b.co2_kg == 0.0
        assert b.eps_kg == 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Klasifikace obálky
# ──────────────────────────────────────────────────────────────────────────────

class TestKlasifikace:

    def test_uem_n_vzorec(self):
        # A/V = 0,5 → Uem,N = 0,30 + 0,15/0,5 = 0,60
        assert vypocitej_uem_n(0.5) == pytest.approx(0.60)

    def test_uem_n_typicky_panelak(self):
        # A/V ≈ 0,35 → Uem,N ≈ 0,729
        assert vypocitej_uem_n(0.35) == pytest.approx(0.30 + 0.15 / 0.35, rel=1e-6)

    def test_klasifikace_trida_a(self):
        # Uem = 0,25, Uem,N = 0,60 → poměr 0,417 → třída A
        assert klasifikuj_uem(0.25, 0.60) == "A"

    def test_klasifikace_trida_b(self):
        # Uem = 0,42, Uem,N = 0,60 → poměr 0,70 → třída B
        assert klasifikuj_uem(0.42, 0.60) == "B"

    def test_klasifikace_trida_c(self):
        # Uem = 0,60, Uem,N = 0,60 → poměr 1,00 → třída C
        assert klasifikuj_uem(0.60, 0.60) == "C"

    def test_klasifikace_trida_d(self):
        # poměr 1,30 → třída D
        assert klasifikuj_uem(0.78, 0.60) == "D"

    def test_klasifikace_trida_e(self):
        # Uem = 1,20, Uem,N = 0,675 → poměr 1,78 → třída E
        assert klasifikuj_uem(1.20, 0.675) == "E"

    def test_klasifikace_trida_g(self):
        # poměr 3,0 → třída G
        assert klasifikuj_uem(1.80, 0.60) == "G"

    def test_obalkova_klasifikace_nova_budova(self):
        # A/V = 0,5 → Uem,N = 0,60 ; Uem = 0,42 → třída B
        k = obalkova_klasifikace(uem=0.42, faktor_tvaru=0.5)
        assert k.trida == "B"
        assert k.uem_n == pytest.approx(0.60)
        assert k.pomer == pytest.approx(0.42 / 0.60, rel=1e-3)

    def test_obalkova_klasifikace_stara_budova(self):
        # A/V = 0,4 → Uem,N = 0,675 ; Uem = 1,20 → poměr 1,78 → třída E
        k = obalkova_klasifikace(uem=1.20, faktor_tvaru=0.4)
        assert k.trida == "E"

    def test_obalkova_klasifikace_nulovy_faktor_tvaru(self):
        # faktor tvaru = 0 → bezpečný fallback (faktor nahrazen 0,01)
        k = obalkova_klasifikace(uem=1.0, faktor_tvaru=0.0)
        assert k.trida in list("ABCDEFG")  # nesmí vyvolat výjimku


# ──────────────────────────────────────────────────────────────────────────────
# Integrace – vypocitej() doplní EA/EP pole do ProjectResult
# ──────────────────────────────────────────────────────────────────────────────

class TestKalkulatorIntegrace:

    @pytest.fixture
    def energie_zp(self) -> EnergyInputs:
        return EnergyInputs(
            zp_ut=450.0, zp_tuv=30.0,
            ee=100.0,
            cena_zp=1_800.0, cena_ee=4_500.0,
            pouzit_zp=True,
        )

    def test_emise_pred_se_vypocitaji_vzdy(self, energie_zp):
        projekt = Project(energie=energie_zp)
        result = projekt.vypocitej()
        assert result.emise_pred is not None
        from epc_engine.emissions import EMISNI_FAKTORY
        assert result.emise_pred.co2_kg == pytest.approx(
            (450 + 30) * EMISNI_FAKTORY["zp"]["co2"] + 100 * EMISNI_FAKTORY["ee"]["co2"]
        )

    def test_emise_po_nejsou_vetsi_nez_pred(self, energie_zp):
        projekt = Project(
            energie=energie_zp,
            opatreni=[OP1a(aktivni=True, plocha_m2=500,
                           u_stavajici=0.8, u_nove=0.25,
                           denostupne=3944.0, cena_kc_m2=1800)],
        )
        result = projekt.vypocitej()
        assert result.emise_po is not None
        assert result.emise_po.co2_kg <= result.emise_pred.co2_kg

    def test_ekonomika_se_vypocita_kdyz_je_parametry(self, energie_zp):
        par = EkonomickeParametry()
        projekt = Project(
            energie=energie_zp,
            opatreni=[OP1a(aktivni=True, plocha_m2=500,
                           u_stavajici=0.8, u_nove=0.25,
                           denostupne=3944.0, cena_kc_m2=1800)],
            ekonomicke_parametry=par,
        )
        result = projekt.vypocitej()
        assert result.ekonomika_projekt is not None

    def test_ekonomika_chybi_bez_parametru(self, energie_zp):
        projekt = Project(energie=energie_zp)
        result = projekt.vypocitej()
        assert result.ekonomika_projekt is None

    def test_klasifikace_se_vypocita_kdyz_jsou_vstupy(self, energie_zp):
        # A/V = 500/1500 ≈ 0,333 → Uem,N ≈ 0,75
        projekt = Project(
            energie=energie_zp,
            uem_stav=1.2,
            faktor_tvaru=500.0 / 1500.0,
        )
        result = projekt.vypocitej()
        assert result.klasifikace_pred is not None
        assert result.klasifikace_pred.trida in list("ABCDEFG")

    def test_klasifikace_chybi_bez_vstupu(self, energie_zp):
        projekt = Project(energie=energie_zp)
        result = projekt.vypocitej()
        assert result.klasifikace_pred is None
