"""
Unit testy pro EPC kalkulační engine.

Pokrývají:
  • základní aritmetiku každého opatření
  • tepelný řetěz (chain state se správně propaguje)
  • % výpočty (OP8, OP9, OP16)
  • FVE opatření (OP11, OP12)
  • vodní opatření (OP14, OP15)
  • deaktivace opatření
  • celkovou bilanci (ProjectResult agregace)
  • scénáře (vypocitej_scenar)
"""

import pytest
from ..models import EnergyInputs, ChainState
from ..measures import (
    OP1a, OP1b, OP2, OP3, OP4, OP5, OP6,
    OP7, OP8, OP9,
    OP10, OP11, OP12, OP13,
    OP14, OP15,
    OP16, OP17, OP18, OP19,
    OP20, OP21, OP22,
)
from ..calculator import Project


# ── Pomocné fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def energie_zp() -> EnergyInputs:
    """Typický objekt se zemním plynem pro vytápění."""
    return EnergyInputs(
        zp_ut=450.0,        # MWh/rok
        zp_tuv=30.0,
        ee=95.0,
        voda=800.0,
        srazky=200.0,
        cena_zp=1_800.0,    # Kč/MWh
        cena_ee=4_500.0,
        cena_voda=120.0,
        cena_srazky=50.0,
        cena_ee_vykup=1_200.0,
        pouzit_zp=True,
        pouzit_tuv_zp=True,
    )


@pytest.fixture
def energie_teplo() -> EnergyInputs:
    """Objekt s CZT teplem."""
    return EnergyInputs(
        teplo_ut=400.0,
        teplo_tuv=25.0,
        ee=90.0,
        voda=600.0,
        cena_teplo=2_200.0,
        cena_ee=4_500.0,
        cena_voda=120.0,
        pouzit_teplo=True,
        pouzit_tuv_teplo=True,
    )


# ── Testy: datové modely ──────────────────────────────────────────────────────

class TestEnergyInputs:
    def test_zp_total(self, energie_zp):
        assert energie_zp.zp_total == 480.0

    def test_teplo_total(self, energie_teplo):
        assert energie_teplo.teplo_total == 425.0

    def test_celkove_naklady_zp(self, energie_zp):
        expected = 480 * 1_800 + 95 * 4_500 + 800 * 120 + 200 * 50
        assert energie_zp.celkove_naklady == pytest.approx(expected)

    def test_celkove_naklady_teplo(self, energie_teplo):
        expected = 425 * 2_200 + 90 * 4_500 + 600 * 120
        assert energie_teplo.celkove_naklady == pytest.approx(expected)

    def test_celkove_naklady_bez_aktivnich_nosicu(self):
        e = EnergyInputs(zp_ut=100, ee=50, cena_zp=1800, cena_ee=4500)
        # pouzit_zp = False → ZP se nezapočítává
        assert e.celkove_naklady == pytest.approx(50 * 4500)


class TestChainState:
    def test_from_inputs_zp(self, energie_zp):
        chain = ChainState.from_inputs(energie_zp)
        assert chain.zbyvajici_zp == pytest.approx(480.0)
        assert chain.zbyvajici_teplo == pytest.approx(0.0)  # není CZT
        assert chain.zbyvajici_ee == pytest.approx(95.0)
        assert chain.ref_zp_tuv == pytest.approx(30.0)

    def test_zbyvajici_ut(self, energie_zp):
        chain = ChainState.from_inputs(energie_zp)
        assert chain.zbyvajici_zp_ut() == pytest.approx(450.0)  # 480 − 30

    def test_zbyvajici_ut_po_usporach(self, energie_zp):
        chain = ChainState.from_inputs(energie_zp)
        chain.zbyvajici_zp -= 100.0  # OP1a ušetřila 100 MWh
        assert chain.zbyvajici_zp_ut() == pytest.approx(350.0)  # 380 − 30


# ── Testy: tepelný plášť (OP1a–OP6) ─────────────────────────────────────────

class TestTepelnyPlast:
    def test_op1a_investice(self, energie_zp):
        op = OP1a(uspora_zp_mwh=60.0, plocha_m2=1200, cena_kc_m2=1_800)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert r.investice == pytest.approx(1200 * 1800)

    def test_op1a_uspora_kc(self, energie_zp):
        op = OP1a(uspora_zp_mwh=60.0, plocha_m2=1200, cena_kc_m2=1_800)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert r.uspora_zp == pytest.approx(60.0)
        assert r.uspora_kc == pytest.approx(60.0 * 1_800)

    def test_op1a_chain_aktualizuje(self, energie_zp):
        op = OP1a(uspora_zp_mwh=60.0, plocha_m2=1200, cena_kc_m2=1_800)
        chain = ChainState.from_inputs(energie_zp)
        op.calculate(chain, energie_zp)
        assert chain.zbyvajici_zp == pytest.approx(420.0)  # 480 − 60

    def test_op1a_neaktivni(self, energie_zp):
        op = OP1a(aktivni=False, uspora_zp_mwh=60.0, plocha_m2=1200, cena_kc_m2=1_800)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert not r.aktivni
        assert r.investice == 0.0
        assert chain.zbyvajici_zp == pytest.approx(480.0)  # chain se nezměnil

    def test_op1a_ignoruje_teplo_kdyz_pouzit_zp(self, energie_zp):
        op = OP1a(uspora_teplo_mwh=50.0, uspora_zp_mwh=60.0,
                  plocha_m2=100, cena_kc_m2=1_000)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        # pouzit_teplo=False → uspora_teplo musí být 0
        assert r.uspora_teplo == 0.0
        assert r.uspora_zp == pytest.approx(60.0)

    def test_retezec_op1a_op2(self, energie_zp):
        """OP2 dostane chain po OP1a → base consumption je nižší."""
        op1a = OP1a(uspora_zp_mwh=60.0, plocha_m2=1200, cena_kc_m2=1_800)
        op2 = OP2(uspora_zp_mwh=30.0, plocha_m2=300, cena_kc_m2=8_000)
        chain = ChainState.from_inputs(energie_zp)
        op1a.calculate(chain, energie_zp)
        assert chain.zbyvajici_zp == pytest.approx(420.0)
        op2.calculate(chain, energie_zp)
        assert chain.zbyvajici_zp == pytest.approx(390.0)

    def test_navratnost(self, energie_zp):
        op = OP1a(uspora_zp_mwh=60.0, plocha_m2=1200, cena_kc_m2=1_800)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        # investice = 2_160_000, uspora = 108_000, navratnost ≈ 20
        assert r.prosta_navratnost == pytest.approx(2_160_000 / 108_000)

    def test_navratnost_zaporna_uspora(self, energie_zp):
        op = OP1a(uspora_zp_mwh=0.0, servisni=5_000,
                  plocha_m2=100, cena_kc_m2=1_000)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert r.prosta_navratnost is None  # ∞

    def test_op1a_fyzika_dle_u_hodnot(self, energie_zp):
        """Physics mode: úspora se spočítá z ΔU × A × D."""
        # Brno: d13=232, tes13=4.0 → D = 232 × (21 − 4.0) = 3944 K·den
        op = OP1a(plocha_m2=1000, u_stavajici=0.8, u_nove=0.25,
                  cena_kc_m2=1_800, denostupne=3944.0)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        ocekavano = (0.8 - 0.25) * 1000 * 3944.0 * 24.0 / 1_000_000.0
        assert r.uspora_zp == pytest.approx(ocekavano, rel=1e-6)
        assert r.uspora_teplo == 0.0  # pouzit_teplo=False

    def test_op1a_rucni_override_ma_prednost(self, energie_zp):
        """Pokud je uspora_zp_mwh > 0, fyzikální vstupy se ignorují."""
        op = OP1a(plocha_m2=1000, u_stavajici=0.8, u_nove=0.25,
                  denostupne=3944.0, uspora_zp_mwh=50.0, cena_kc_m2=1_800)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert r.uspora_zp == pytest.approx(50.0)

    def test_op1a_fyzika_nulova_bez_parametru(self, energie_zp):
        """Pokud nejsou u-hodnoty zadány, fyzikální výpočet vrátí 0."""
        op = OP1a(plocha_m2=1000, cena_kc_m2=1_800)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert r.uspora_zp == 0.0
        assert r.uspora_teplo == 0.0


# ── Testy: % opatření (OP8, OP9, OP16) ───────────────────────────────────────

class TestProcentualni:
    def test_op9_uspori_z_ut(self, energie_zp):
        """OP9 uspořuje jen z ÚT části (ne TUV)."""
        chain = ChainState.from_inputs(energie_zp)
        op = OP9(pocet_ot=180, procento_uspory=0.10)
        r = op.calculate(chain, energie_zp)
        # zbývající ÚT = 480 − 30 = 450 MWh; 10 % = 45 MWh
        assert r.uspora_zp == pytest.approx(45.0)

    def test_op9_po_op1a(self, energie_zp):
        """OP9 počítá z chain po OP1a."""
        chain = ChainState.from_inputs(energie_zp)
        OP1a(uspora_zp_mwh=60.0, plocha_m2=100, cena_kc_m2=1).calculate(chain, energie_zp)
        op = OP9(pocet_ot=180, procento_uspory=0.10)
        r = op.calculate(chain, energie_zp)
        # zbývající = 480 − 60 = 420; ÚT = 420 − 30 = 390; 10 % = 39 MWh
        assert r.uspora_zp == pytest.approx(39.0)

    def test_op16_tri_procenta(self, energie_zp):
        chain = ChainState.from_inputs(energie_zp)
        op = OP16(pocet_ot=180)
        r = op.calculate(chain, energie_zp)
        # ÚT = 450; 3 % = 13.5
        assert r.uspora_zp == pytest.approx(450.0 * 0.03)

    def test_op8_investice(self, energie_zp):
        op = OP8(pocet_vetvi=3, cena_kc_vetev=180_000)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert r.investice == pytest.approx(3 * 180_000)


# ── Testy: EE / FVE (OP10–OP12) ──────────────────────────────────────────────

class TestElektrina:
    def test_op10_uspora_ee(self, energie_zp):
        op = OP10(uspora_ee_mwh=20.0, pocet_svitidel=200)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert r.uspora_ee == pytest.approx(20.0)
        assert r.uspora_kc == pytest.approx(20.0 * 4_500)

    def test_op10_chain_ee(self, energie_zp):
        op = OP10(uspora_ee_mwh=20.0, pocet_svitidel=200)
        chain = ChainState.from_inputs(energie_zp)
        op.calculate(chain, energie_zp)
        assert chain.zbyvajici_ee == pytest.approx(75.0)  # 95 − 20

    def test_op11_vlastni_spotreba_a_pretoky(self, energie_zp):
        op = OP11(
            vyroba_mwh=80, self_consumption_mwh=60, export_mwh=20,
            n_panelu=160,
        )
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert r.uspora_ee == pytest.approx(60.0)
        assert r.vynos_pretoky == pytest.approx(20.0 * 1_200)
        assert r.uspora_kc == pytest.approx(60.0 * 4_500 + 20.0 * 1_200)

    def test_op11_servis(self, energie_zp):
        op = OP11(vyroba_mwh=80, self_consumption_mwh=60, export_mwh=20, n_panelu=160)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert r.servisni_naklady == pytest.approx(80 * 110)

    def test_op12_diferencial_cena(self, energie_zp):
        """Úspora baterie = navíc_MWh × (cena_ee − cena_vykup)."""
        op = OP12(velikost_mwh=0.1, cena_kc_mwh=500_000, navice_vyuzito_mwh=15)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        expected_kc = 15 * (4_500 - 1_200)
        assert r.uspora_kc == pytest.approx(expected_kc)


# ── Testy: voda (OP14–OP15) ──────────────────────────────────────────────────

class TestVoda:
    def test_op14_uspora_vody(self, energie_zp):
        op = OP14(procento_uspory=0.15, n_umyvadel=30, n_sprch=10, n_splachovadel=20)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert r.uspora_voda == pytest.approx(800 * 0.15)
        assert r.uspora_kc == pytest.approx(800 * 0.15 * 120)

    def test_op14_chain_voda(self, energie_zp):
        op = OP14(procento_uspory=0.15, n_umyvadel=30, n_sprch=10, n_splachovadel=20)
        chain = ChainState.from_inputs(energie_zp)
        op.calculate(chain, energie_zp)
        assert chain.zbyvajici_voda == pytest.approx(800 * 0.85)

    def test_op15_srazky(self, energie_zp):
        op = OP15(procento_uspory=0.50, velikost_nadrze_l=10_000)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert r.uspora_srazky == pytest.approx(200 * 0.50)
        assert r.investice == pytest.approx(10_000 * 27)


# ── Testy: VZT (OP17) ────────────────────────────────────────────────────────

class TestVZT:
    def test_op17_uspora_tepla_a_navys_ee(self, energie_zp):
        chain = ChainState.from_inputs(energie_zp)
        op = OP17(pocet_jednotek=2)
        r = op.calculate(chain, energie_zp)
        # ÚT = 480 − 30 (TUV) = 450 MWh; 3 % = 13.5 MWh (pouze z ÚT, ne TUV)
        assert r.uspora_zp == pytest.approx(450 * 0.03)
        # EE se navyšuje → uspora_ee záporná
        assert r.uspora_ee < 0
        # Celková finanční úspora = ZP úspora − EE navýšení
        assert r.uspora_kc == pytest.approx(
            450 * 0.03 * 1_800 + (-95 * 0.02 * 4_500)
        )


# ── Testy: Project a celková bilance ─────────────────────────────────────────

class TestProject:
    def test_projekt_celkova_investice(self, energie_zp):
        projekt = Project(
            nazev="Test",
            energie=energie_zp,
            opatreni=[
                OP1a(uspora_zp_mwh=60, plocha_m2=1200, cena_kc_m2=1800),
                OP9(pocet_ot=180, procento_uspory=0.10),
                OP10(uspora_ee_mwh=20, pocet_svitidel=200),
            ],
        )
        result = projekt.vypocitej()
        assert result.celkova_investice == pytest.approx(
            1200 * 1800 + 180 * 13_000 + 200 * 6500
        )

    def test_projekt_navratnost(self, energie_zp):
        projekt = Project(
            energie=energie_zp,
            opatreni=[
                OP1a(uspora_zp_mwh=60, plocha_m2=1200, cena_kc_m2=1800),
            ],
        )
        result = projekt.vypocitej()
        assert result.prosta_navratnost_celkem == pytest.approx(
            (1200 * 1800) / (60 * 1800)
        )

    def test_neaktivni_neovlivni_soucet(self, energie_zp):
        projekt = Project(
            energie=energie_zp,
            opatreni=[
                OP1a(aktivni=False, uspora_zp_mwh=60, plocha_m2=1200, cena_kc_m2=1800),
                OP9(pocet_ot=180, procento_uspory=0.10),
            ],
        )
        result = projekt.vypocitej()
        # Pouze OP9 je aktivní
        aktivni = result.aktivni
        assert len(aktivni) == 1
        assert aktivni[0].id == "OP9"

    def test_scenar(self, energie_zp):
        """vypocitej_scenar nezmění originální projekt."""
        projekt = Project(
            energie=energie_zp,
            opatreni=[
                OP1a(uspora_zp_mwh=60, plocha_m2=1200, cena_kc_m2=1800),
                OP9(pocet_ot=180, procento_uspory=0.10),
            ],
        )
        scenar = projekt.vypocitej_scenar(["OP9"])
        plny = projekt.vypocitej()
        # Scénář bez OP1a má nižší investici
        assert scenar.celkova_investice < plny.celkova_investice
        # Originál nezměněn
        assert projekt.opatreni[0].aktivni is True

    def test_retezec_op9_vidi_op1a_uspot(self, energie_zp):
        """Chain se správně propaguje: OP9 vidí zbývající spotřebu po OP1a."""
        projekt = Project(
            energie=energie_zp,
            opatreni=[
                OP1a(uspora_zp_mwh=60, plocha_m2=1200, cena_kc_m2=1800),
                OP9(pocet_ot=180, procento_uspory=0.10),
            ],
        )
        result = projekt.vypocitej()
        op9_result = next(r for r in result.vysledky if r.id == "OP9")
        # zbývající ZP po OP1a: 480 − 60 = 420; ÚT = 420 − 30 = 390; 10 % = 39
        assert op9_result.uspora_zp == pytest.approx(39.0)

    def test_tabulka_opatreni_obsahuje_vsechna(self, energie_zp):
        projekt = Project(
            energie=energie_zp,
            opatreni=[OP1a(plocha_m2=100, cena_kc_m2=1), OP9(pocet_ot=10)],
        )
        tabulka = projekt.tabulka_opatreni()
        assert len(tabulka) == 2
        assert tabulka[0]["ID"] == "OP1a"

    def test_souhrn_klic_navratnost(self, energie_zp):
        projekt = Project(
            energie=energie_zp,
            opatreni=[OP1a(uspora_zp_mwh=60, plocha_m2=1200, cena_kc_m2=1800)],
        )
        s = projekt.souhrn()
        assert "Prostá návratnost [let]" in s


# ── Testy: infrastrukturní opatření (bez úspor) ───────────────────────────────

class TestInfrastruktura:
    def test_op20_jen_investice(self, energie_zp):
        op = OP20(plocha_m2=1600, cena_kc_m2=500)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert r.investice == pytest.approx(1600 * 500)
        assert r.uspora_kc == 0.0
        assert r.prosta_navratnost is None

    def test_op19_investice(self, energie_zp):
        op = OP19(pocet_mist=12, cena_kc_misto=32_400, cena_hw_kc=40_000)
        chain = ChainState.from_inputs(energie_zp)
        r = op.calculate(chain, energie_zp)
        assert r.investice == pytest.approx(12 * 32_400 + 40_000)


# ── Test: kompletní projekt podobný ZŠ Politických vězňů ─────────────────────

class TestKompletniProjekt:
    def test_zs_politickych_veznu_scenar(self):
        """
        Orientační test s hodnotami blízkými skutečnému objektu.
        Ověřuje, že celý engine proběhne bez chyb a výsledky jsou v rozumném rozsahu.
        """
        energie = EnergyInputs(
            zp_ut=500.0, zp_tuv=35.0,
            ee=100.0, voda=900.0, srazky=300.0,
            cena_zp=1_800.0, cena_ee=4_500.0,
            cena_voda=120.0, cena_srazky=50.0,
            cena_ee_vykup=1_200.0,
            pouzit_zp=True, pouzit_tuv_zp=True,
        )

        projekt = Project(
            nazev="ZŠ Politických vězňů – orientační scénář",
            energie=energie,
            opatreni=[
                OP1a(uspora_zp_mwh=80, plocha_m2=1_400, cena_kc_m2=1_800),
                OP2(uspora_zp_mwh=25, plocha_m2=280, cena_kc_m2=9_000),
                OP3(uspora_zp_mwh=15, plocha_m2=900, cena_kc_m2=2_500),
                OP9(pocet_ot=200, procento_uspory=0.10),
                OP10(uspora_ee_mwh=22, pocet_svitidel=220),
                OP11(
                    vyroba_mwh=85, self_consumption_mwh=65, export_mwh=20,
                    n_panelu=170, cena_projektovani_kc=50_000,
                    cena_revize_kc=15_000, cena_montaz_kc=80_000,
                ),
                OP14(procento_uspory=0.15, n_umyvadel=40, n_sprch=15, n_splachovadel=30),
                OP16(pocet_ot=200),
                OP19(pocet_mist=12),
            ],
        )

        result = projekt.vypocitej()

        # Investice musí být kladná a v rozumném rozsahu (3–30 mil. Kč)
        assert 3_000_000 < result.celkova_investice < 30_000_000

        # Úspora musí být kladná
        assert result.celkova_uspora_kc > 0

        # Návratnost musí být kladná a < 50 let
        assert result.prosta_navratnost_celkem is not None
        assert result.prosta_navratnost_celkem < 50

        # Sumární úspora ZP nesmí přesáhnout referenční spotřebu
        assert result.celkova_uspora_zp <= energie.zp_total
