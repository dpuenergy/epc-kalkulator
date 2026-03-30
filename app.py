"""
Kalkulátor energeticky úsporných projektů – Streamlit aplikace
===============================================================
Spuštění:
    streamlit run app.py
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Přidáme kořenový adresář na cestu, aby fungoval import epc_engine
sys.path.insert(0, str(Path(__file__).parent))

from epc_engine import BuildingInfo, Budova, Prostor, Podklad, EnergyInputs, Project
from epc_engine.models import (
    Vrstva, Konstrukce, TechnickySytem, TechnickeSystemy,
    BilancePouzitiEnergie, PenbData, HistorieRok, KlimatickaData,
    EnMSOblast, EnMSHodnoceni,
    EnergonositelEA, MKHKriterium, EnPIUkazatel, EAData,
    Fotografie,
)
from epc_engine.tepelna_technika import TYP_POPISY, un_pozadovana
from epc_engine.op_descriptions import OP_INFO, OP_PODKLADY, OP_PODKLADY_OBECNE
from epc_engine.penb_parser import parse_pdf as _parse_penb_pdf
from epc_engine.economics import EkonomickeParametry
from epc_engine.physics import (
    lokalita as _lokalita_fn,
    nazvy_lokalit as _nazvy_lokalit_fn,
    denostupne_rok as _denostupne_rok_fn,
    ROCNI_KOREKCE_D as _ROCNI_KOREKCE_D,
)
from epc_engine.measures import (
    OP1a, OP1b, OP2, OP3, OP4, OP5, OP6,
    OP7, OP8, OP9,
    OP10, OP11, OP12, OP13,
    OP14, OP15,
    OP16, OP17, OP18, OP19,
    OP20, OP21, OP22,
)

# ── Konfigurace stránky ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="Kalkulátor energeticky úsporných projektů",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Výchozí hodnoty session state ─────────────────────────────────────────────

DEFAULTS: dict = {
    # ── Typ dokumentu ─────────────────────────────────────────────────────
    # Obecná studie | Podrobná analýza | Energetický posudek | Energetický audit
    "typ_dokumentu": "Energetický audit",
    # ── Identifikace projektu ──────────────────────────────────────────────
    "nazev_zakazky": "",
    "datum": "",
    "program_efekt": False,
    # Zadavatel
    "zadavatel_nazev": "",
    "zadavatel_adresa": "",
    "zadavatel_ico": "",
    "zadavatel_kontakt": "",
    "zadavatel_telefon": "",
    "zadavatel_email": "",
    # Zpracovatel
    "zpracovatel_zastupce": "Ing. Jakub Hřídel",
    # Objekt
    "objekt_nazev": "",
    "objekt_adresa": "",
    "predmet_analyzy": (
        "Předmětem analýzy je zjištění stavu a potenciálu energetických úspor "
        "a vhodnosti realizace úsporných opatření pomocí EPC metody."
    ),
    # Základní parametry
    "druh_cinnosti": "",
    "pocet_zamestnancu": "",
    "provozni_rezim": "",
    # Budovy (jedna budova jako výchozí – list slovníků)
    "budovy": [{"nazev": "", "objem_m3": 0.0, "plocha_m2": 0.0, "ochlaz_m2": 0.0}],
    # Prostory (list slovníků)
    "prostory": [{"nazev": "", "ucel": "", "provoz": ""}],
    # Podklady (list slovníků)
    "podklady": [
        {"nazev": "Spotřeby a platby za elektrickou energii, teplo, vodu", "ok": True},
        {"nazev": "Původní projektová dokumentace", "ok": False},
        {"nazev": "Energetický audit", "ok": False},
        {"nazev": "Průkaz energetické náročnosti budovy (PENB)", "ok": False},
        {"nazev": "Pasport objektu", "ok": False},
        {"nazev": "Revizní zprávy", "ok": False},
        {"nazev": "Informace od provozovatele", "ok": True},
        {"nazev": "Informace z technické prohlídky objektu", "ok": True},
    ],
    "poznamka_podklady": (
        "Pokud není v analýze uvedeno jinak, jsou všechny ceny a náklady uváděny včetně DPH."
    ),
    # ── Projekt
    "nazev": "Nový projekt",
    # Energonosiče (multi-carrier) – každý nezávisle zapínat
    "nosic_zp": True,              # Zemní plyn (vytápění + TUV)
    "nosic_czt": False,            # Teplo (CZT)
    # legacy – zachováno pro zpětnou kompatibilitu; odvozeno z nosic_zp/nosic_czt
    "nosic": "Zemní plyn",
    "tuv_nosic": "Zemní plyn",     # Zemní plyn / Teplo (CZT) / Elektřina
    # ── Okrajové podmínky projektu (sdílené s fyzikálním kalkulátorem) ──────
    "theta_i": 21.0,               # °C – vnitřní výpočtová teplota
    "theta_e": -13.0,              # °C – venkovní výpočtová teplota
    "phi_total_kw": 0.0,           # kW – celková tepelná ztráta objektu
    "lokalita_projekt": "Praha (Karlov)",
    # Spotřeby – roční
    "zp_ut": 450.0,
    "zp_tuv": 30.0,
    "teplo_ut": 0.0,
    "teplo_tuv": 0.0,
    "ee": 95.0,
    "voda": 800.0,
    "srazky": 200.0,
    # Spotřeby – měsíční (12 hodnot na nosič; 0.0 = nezadáno)
    "zp_ut_mesice": [0.0] * 12,
    "zp_tuv_mesice": [0.0] * 12,
    "teplo_ut_mesice": [0.0] * 12,
    "teplo_tuv_mesice": [0.0] * 12,
    "ee_mesice": [0.0] * 12,
    # Ceny
    "cena_zp": 1_800.0,
    "cena_teplo": 2_200.0,
    "cena_ee": 4_500.0,
    "cena_ee_vykup": 1_200.0,
    "cena_voda": 120.0,
    "cena_srazky": 50.0,
    # ── OP1a
    "op1a_on": True,
    "op1a_uspora": 0.0,     # MWh/rok – ruční override (0 = počítej z fyziky)
    "op1a_phi_kw": 0.0,    # kW – snížení tepelné ztráty (z fyzik. kalkulátoru)
    "op1a_plocha": 1_200.0,
    "op1a_cena_m2": 1_800.0,
    "op1a_u_stavajici": 0.0,  # W/m²K – z PENB
    "op1a_u_nove": 0.0,       # W/m²K – cílová hodnota po zateplení
    # ── OP1b
    "op1b_on": False,
    "op1b_uspora": 0.0,
    "op1b_phi_kw": 0.0,
    "op1b_plocha": 0.0,
    "op1b_cena_m2": 600.0,
    "op1b_u_stavajici": 0.0,
    "op1b_u_nove": 0.0,
    # ── OP2
    "op2_on": True,
    "op2_uspora": 0.0,
    "op2_phi_kw": 0.0,
    "op2_plocha": 280.0,
    "op2_cena_m2": 9_000.0,
    "op2_u_stavajici": 0.0,
    "op2_u_nove": 0.0,
    # ── OP3
    "op3_on": True,
    "op3_uspora": 0.0,
    "op3_phi_kw": 0.0,
    "op3_plocha": 900.0,
    "op3_cena_m2": 2_500.0,
    "op3_u_stavajici": 0.0,
    "op3_u_nove": 0.0,
    # ── OP4
    "op4_on": False,
    "op4_uspora": 0.0,
    "op4_phi_kw": 0.0,
    "op4_plocha": 0.0,
    "op4_cena_m2": 1_200.0,
    "op4_u_stavajici": 0.0,
    "op4_u_nove": 0.0,
    # ── OP5
    "op5_on": False,
    "op5_uspora": 0.0,
    "op5_phi_kw": 0.0,
    "op5_plocha": 0.0,
    "op5_cena_m2": 1_500.0,
    "op5_u_stavajici": 0.0,
    "op5_u_nove": 0.0,
    # ── OP6
    "op6_on": False,
    "op6_uspora": 0.0,
    "op6_phi_kw": 0.0,
    "op6_plocha": 0.0,
    "op6_cena_m2": 200.0,
    "op6_u_stavajici": 0.0,
    "op6_u_nove": 0.0,
    # ── OP7
    "op7_on": False,
    "op7_uspora": 0.0,
    "op7_ee_zmena": 0.0,
    "op7_investice": 0.0,
    # ── OP8
    "op8_on": False,
    "op8_vetvi": 3,
    "op8_pct": 5.0,
    # ── OP9
    "op9_on": True,
    "op9_ot": 180,
    "op9_pct": 10.0,
    # ── OP10
    "op10_on": True,
    "op10_uspora_ee": 22.0,
    "op10_svitidel": 200,
    "op10_ee_cap_pct": 50.0,
    # ── OP11
    "op11_on": True,
    "op11_vyroba": 85.0,
    "op11_vlastni": 65.0,
    "op11_export": 20.0,
    "op11_panelu": 170,
    "op11_projekt": 50_000.0,
    "op11_revize": 15_000.0,
    "op11_montaz": 80_000.0,
    # ── OP12
    "op12_on": False,
    "op12_velikost": 0.1,
    "op12_cena_mwh": 500_000.0,
    "op12_navic": 10.0,
    # ── OP13
    "op13_on": False,
    "op13_uspora": 5.0,
    "op13_nadrz": 1_000.0,
    # ── OP14
    "op14_on": True,
    "op14_pct": 15.0,
    "op14_umyvadel": 40,
    "op14_sprch": 15,
    "op14_splachovadel": 30,
    # ── OP15
    "op15_on": False,
    "op15_pct": 50.0,
    "op15_nadrz": 10_000.0,
    # ── OP16
    "op16_on": True,
    "op16_ot": 180,
    # ── OP17
    "op17_on": False,
    "op17_jednotky": 2,
    # OP17 – kalkulátor větrání škol (metodický pokyn SFŽP)
    "op17_skola_typ": 3,           # 1=MŠ, 2=ZŠ1, 3=ZŠ2, 4=SŠ
    "op17_skola_zaci": 25,
    "op17_skola_ucitele": 1,
    "op17_skola_objem": 175.0,     # m³ – typická učebna 7×9×2,8 m
    "op17_skola_co2_max": 1200,    # ppm – limitní koncentrace CO₂
    "op17_skola_co2_out": 400,     # ppm – venkovní CO₂
    "op17_skola_prestávky_pct": 0, # % dětí ve třídě o přestávkách
    "op17_skola_ucitel_prut": 25.0,# m³/h na vyučujícího
    "op17_skola_zzt": 70.0,        # % – účinnost ZZT rekuperátoru
    # ── OP18
    "op18_on": True,
    "op18_plocha": 112.0,
    # ── OP19
    "op19_on": True,
    "op19_mista": 12,
    # ── OP20
    "op20_on": False,
    "op20_plocha": 0.0,
    "op20_cena_m2": 500.0,
    # ── OP21
    "op21_on": False,
    "op21_investice": 0.0,
    # ── OP22
    "op22_on": False,
    "op22_investice": 0.0,
    # ── POPIS stávajícího stavu technických soustav ───────────────────────────
    "popis_vytapeni": "",
    "popis_tuv": "",
    "popis_chlazeni": "",
    "popis_vzt": "",
    "popis_osvetleni": "",
    "popis_stavba": "",
    "popis_elektro": "",
    "popis_voda_rozv": "",
    # Strukturovaná pole – stav soustav
    # Vytápění – zdroje tepla (dynamický seznam)
    "sys_vyt_zdroje": [
        {"typ": "Plynový kotel", "vykon_kw": 0.0, "pocet": 1,
         "rok": 2000, "stav": "Uspokojivý"},
    ],
    "sys_vyt_vetvi": [
        {"typ": "Dvoutrubková", "popis": "", "pocet_ot": 0,
         "trv": True, "rok": 2000, "stav": "Uspokojivý"},
    ],
    "sys_vyt_regulace": [
        {"typ": "Ekvitermní regulace", "rok": 2000, "stav": "Uspokojivý"},
    ],
    # TUV – zdroje ohřevu (dynamický seznam)
    "sys_tuv_zdroje": [
        {"typ": "Plynový zásobníkový ohřívač", "objem_l": 0.0,
         "rok": 2000, "stav": "Uspokojivý"},
    ],
    "sys_tuv_rozvody_cirkulace": False,
    "sys_tuv_rozvody_rok": 2000,
    "sys_tuv_rozvody_stav": "Uspokojivý",
    # Chlazení
    "sys_chl_instalovano": False,
    "sys_chl_jednotky": [
        {"typ": "Klimatizace split / multi-split", "vykon_kw": 0.0,
         "rok": 2010, "stav": "Uspokojivý"},
    ],
    # VZT – jednotky (dynamický seznam)
    "sys_vzt_jednotky": [
        {"nazev": "", "prut_m3h": 0.0, "zzt": False,
         "zzt_ucinnost_pct": 75.0, "rok": 2000, "stav": "Uspokojivý"},
    ],
    # Osvětlení – zóny
    "sys_osv_zony": [
        {"nazev": "", "typ": "Lineární fluorescenční (T8/T5)",
         "prikon_kw": 0.0, "pocet": 0, "rok": 2000, "hodiny_rok": 2000,
         "rizeni": "Ruční spínání", "stav": "Uspokojivý"},
    ],
    # Stavba (U-hodnoty jsou ve Fyzikálním kalkulátoru)
    "sys_sta_rok_vystavby": 1980,
    "sys_sta_zatepleno": False,
    "sys_sta_rok_zatepleni": 2010,
    "sys_sta_stav_steny": "Uspokojivý",
    "sys_sta_stav_strecha": "Uspokojivý",
    "sys_sta_stav_okna": "Uspokojivý",
    # Elektroinstalace
    "sys_ele_rok_rozvadece": 2000,
    "sys_ele_rok_revize": 2020,
    "sys_ele_mereni_podružne": False,
    "sys_ele_stav_rozvadece": "Uspokojivý",
    "sys_ele_stav_rozvody": "Uspokojivý",
    # Rozvody vody
    "sys_vod_material_sv": "Ocelové",
    "sys_vod_material_tv": "Ocelové",
    "sys_vod_cirkulace_tv": False,
    "sys_vod_rok": 2000,
    "sys_vod_stav": "Uspokojivý",
    # ── Voda – měsíční rozpad (12 hodnot) ────────────────────────────────────
    "voda_mesice": [0.0] * 12,
    # ── EA/EP – Obálka budovy a ekonomika ────────────────────────────────────
    "uem_stav": 0.0,              # W/m²K – průměrný součinitel prostupu tepla obálky
    # Ekonomické parametry jsou per-projekt (klíče v _PROJECT_KEYS)
    "diskontni_sazba": 4.0,       # % – reálná diskontní sazba
    "horizont_let": 20,           # roky analýzy
    "inflace_energie": 3.0,       # % – roční inflace energií
    # ── Vstupní data po rocích (pro normalizaci denostupni) ───────────────────
    # Každý záznam: rok, spotřeby energie, D = skutečné denostupně daného roku.
    # D = 0 znamená nezadáno – normalizace pro daný rok se přeskočí.
    "roky_spotreby": [
        {"rok": 2022, "zp_ut": 0.0, "zp_tuv": 0.0,
         "teplo_ut": 0.0, "teplo_tuv": 0.0, "ee": 0.0, "voda": 0.0, "D": 0.0},
        {"rok": 2023, "zp_ut": 0.0, "zp_tuv": 0.0,
         "teplo_ut": 0.0, "teplo_tuv": 0.0, "ee": 0.0, "voda": 0.0, "D": 0.0},
        {"rok": 2024, "zp_ut": 0.0, "zp_tuv": 0.0,
         "teplo_ut": 0.0, "teplo_tuv": 0.0, "ee": 0.0, "voda": 0.0, "D": 0.0},
    ],
    # ── Sprint 4: doplňující identifikační pole ────────────────────────────
    "objekt_ku": "",
    "objekt_parcelni_cislo": "",
    "evidencni_cislo": "",
    "cislo_opravneni": "",
    "ucel_ep": "",
    "ceny_bez_dph": True,
    # ── Sprint 4: klimatická data (pro sekci B.2) ──────────────────────────
    "klima_lokalita": "",
    "klima_stupnodni_norm": 3600.0,
    "klima_ti": 19.0,
    "klima_te": -12.0,
    # ── Sprint 4: tepelná obálka – seznam konstrukcí ───────────────────────
    # Každý prvek: {nazev, typ, plocha_m2, u_zadane ('' = z vrstev), un_value,
    #               vrstvy: [{nazev, tloustka_mm, lambda_wm}]}
    "konstrukce_obalka": [],
    # ── Sprint 4: technické systémy (B.4) ────────────────────────────────
    "ts_vytapeni_typ": "",
    "ts_vytapeni_vykon": 0.0,
    "ts_vytapeni_ucinnost": 0.0,
    "ts_vytapeni_rok": 0,
    "ts_vytapeni_popis": "",
    "ts_tuv_typ": "",
    "ts_tuv_vykon": 0.0,
    "ts_tuv_ucinnost": 0.0,
    "ts_tuv_rok": 0,
    "ts_tuv_popis": "",
    "ts_vzt_typ": "",
    "ts_vzt_vykon": 0.0,
    "ts_vzt_ucinnost": 0.0,
    "ts_vzt_rok": 0,
    "ts_vzt_popis": "",
    "ts_osvetleni_typ": "",
    "ts_osvetleni_popis": "",
    "ts_mar": "",
    # ── Sprint 4: bilance dle účelu (příloha č. 4 vyhl. 141/2021) ─────────
    "bilance_vytapeni_mwh": 0.0,
    "bilance_chlazeni_mwh": 0.0,
    "bilance_tuv_mwh": 0.0,
    "bilance_vetrání_mwh": 0.0,
    "bilance_osvetleni_mwh": 0.0,
    "bilance_technologie_mwh": 0.0,
    "bilance_phm_mwh": 0.0,
    # ── Sprint 4: PENB data (D.4) ─────────────────────────────────────────
    "penb_trida_stav": "",
    "penb_trida_nav": "",
    "penb_potreba_tepla": 0.0,
    "penb_dodana_energie": 0.0,
    "penb_primarni": 0.0,
    "penb_plocha": 0.0,
    "penb_poznamka": "",
    # ── Sprint 5: EnMS hodnocení (B.5.2, C.3) ────────────────────────────
    "enms_certifikovan": False,
    "enms_komentar": "",
    "enms_0_stav": "", "enms_0_h": 0,   # Energetická politika
    "enms_1_stav": "", "enms_1_h": 0,   # Energetické plánování
    "enms_2_stav": "", "enms_2_h": 0,   # Implementace a provoz
    "enms_3_stav": "", "enms_3_h": 0,   # Kontrola a měření
    "enms_4_stav": "", "enms_4_h": 0,   # Interní audit EnMS
    "enms_5_stav": "", "enms_5_h": 0,   # Přezkoumání vedením
    "enms_6_stav": "", "enms_6_h": 0,   # Neustálé zlepšování
    # ── Sprint 4: okrajové podmínky (E) ──────────────────────────────────
    "okrajove_podminky": (
        "Pro dosažení kalkulovaných úspor je nezbytné dodržet navržené technické "
        "parametry při výběru dodavatele, provádět pravidelnou údržbu a servis "
        "instalovaných zařízení a zachovat stávající způsob užívání objektu."
    ),
    # ── Sprint 7: Plán energetického auditu (příloha č. 2 k vyhl. 140/2021) ──
    "plan_ea_datum": "",
    "plan_ea_zadavatel_zastupce": "",
    "plan_ea_mira_detailu": (
        "Úplný energetický audit dle přílohy A3 normy ČSN ISO 50002 (úroveň 2). "
        "Zahrnuje revizi historické spotřeby, místní šetření, měření a výpočtové "
        "hodnocení úsporných opatření."
    ),
    "plan_ea_predmet": "",
    "plan_ea_lokalizace": "",
    "plan_ea_potreby": "",
    "plan_ea_ekonomicke_ukazatele": "NPV, IRR, prostá a reálná doba návratnosti (Ts, Tsd)",
    # horizont, diskont a inflace jsou sdílené klíče z ekonomiky
    "plan_ea_dotace": False,
    "plan_ea_mkh_popis": (
        "Vícekriteriální hodnocení dle přílohy č. 9 vyhl. 140/2021 Sb. zahrnuje: "
        "NPV, dobu návratnosti, úsporu CO₂ a technickou proveditelnost."
    ),
    "plan_ea_soucinnost": (
        "Zadavatel zajistí přístup do všech částí předmětu auditu, přidělí "
        "kontaktní osobu odpovědnou za součinnost a poskytne podklady dle "
        "přiloženého seznamu požadovaných dokumentů."
    ),
    "plan_ea_harmonogram": "",
    "plan_ea_strategicke_dok": "",
    "plan_ea_format": "Elektronicky ve formátu PDF; 1× tištěný výtisk vázaný",
    "plan_ea_projednani": (
        "Návrh zprávy bude předán zadavateli k připomínkám před finalizací. "
        "Případné změny předmětu nebo harmonogramu budou řešeny písemným "
        "dodatkem k plánu EA dle § 4 odst. 3 vyhl. 140/2021 Sb."
    ),
    "plan_ea_dodatky": [],   # list[str]
    # Dotace
    "dotace_poznamky": "",   # poznámky k dotačnímu titulu pro objekt
    "dotace_zpusobile": 0.0, # způsobilé výdaje [Kč]
    "dotace_max_pct": 68.0,  # max. procento podpory [%]
    "dotace_urok": 6.0,      # úroková sazba dodavatelského úvěru [% p.a.]
    # Plán EA – strukturované vstupy (nahrazují free-text areas)
    "plan_ea_uroven": 2,   # int 1–3 (úroveň dle ČSN ISO 50002, příloha A3)
    "plan_ea_systemy": ["Vytápění", "Teplá užitková voda", "Elektrická energie"],
    "plan_ea_cile_seznam": [],   # list[str] – zaškrtnuté cíle zadavatele
    "plan_ea_cil_uspory_pct": 0,   # float – cílová úspora [%]
    "plan_ea_predmet_poznamka": "",   # volitelný doplněk k předmětu
    "plan_ea_ukazatele_seznam": ["NPV", "IRR", "Ts (prostá)", "Tsd (reálná)"],
    "plan_ea_mkh_seznam": [
        "Ekonomická efektivnost (NPV)",
        "Technická proveditelnost",
        "Úspora CO₂",
    ],
    "plan_ea_soucinnost_seznam": [
        "Zajistit přístup do všech prostor objektu",
        "Přidělit kontaktní osobu odpovědnou za součinnost",
        "Dodat podklady dle přiloženého seznamu",
    ],
    "plan_ea_datum_zahajeni_plan": "",
    "plan_ea_datum_setreni": "",
    "plan_ea_datum_navrhu": "",
    "plan_ea_datum_finalizace": "",
    "plan_ea_strategicke_dok_list": [],   # list[str]
    "plan_ea_format_typ": "Elektronicky (PDF) + 1× tisk vázaný",
    "plan_ea_projednani_typ": "Zaslání návrhu zprávy e-mailem k připomínkám",
    "plan_ea_projednani_poznamka": "",
    # ── Sprint 5: EA přídavný modul ──────────────────────────────────────
    "ea_evidencni_cislo": "",
    "ea_cil": "",
    "ea_datum_zahajeni": "",
    "ea_datum_ukonceni": "",
    "ea_plan_text": "",
    "ea_program_realizace": "",
    # Energonosiče: seznam slovníků {nazev, kategorie, oblast}
    "ea_energonositele": [],
    # MKH kritéria: váhy 0–100 pro 4 předvolená kritéria
    "ea_mkh_0_aktivni": True, "ea_mkh_0_vaha": 30,   # NPV
    "ea_mkh_1_aktivni": True, "ea_mkh_1_vaha": 25,   # Td
    "ea_mkh_2_aktivni": True, "ea_mkh_2_vaha": 25,   # MWh
    "ea_mkh_3_aktivni": True, "ea_mkh_3_vaha": 20,   # Kč
    # EnPI ukazatele: seznam slovníků {nazev, jednotka, stavajici, navrhova}
    "ea_enpi": [],
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Multi-objektová architektura ──────────────────────────────────────────────
# Klíče na úrovni projektu (sdílené všemi objekty) – vše ostatní je objektové.
_PROJECT_KEYS: set[str] = {
    "typ_dokumentu",
    "nazev", "nazev_zakazky", "datum", "program_efekt",
    "zadavatel_nazev", "zadavatel_adresa", "zadavatel_ico",
    "zadavatel_kontakt", "zadavatel_telefon", "zadavatel_email",
    "zpracovatel_zastupce",
    # EA/EP ekonomické parametry jsou sdílené pro celý projekt
    "diskontni_sazba", "horizont_let", "inflace_energie",
    # Plán EA – projektová příloha (příloha č. 2 k vyhl. 140/2021), sdílená pro celý projekt
    "plan_ea_datum", "plan_ea_zadavatel_zastupce", "plan_ea_mira_detailu",
    "plan_ea_predmet", "plan_ea_lokalizace", "plan_ea_potreby",
    "plan_ea_ekonomicke_ukazatele", "plan_ea_dotace", "plan_ea_mkh_popis",
    "plan_ea_soucinnost", "plan_ea_harmonogram", "plan_ea_strategicke_dok",
    "plan_ea_format", "plan_ea_projednani", "plan_ea_dodatky",
    # Strukturované klíče (nová generace)
    "plan_ea_systemy", "plan_ea_cile_seznam", "plan_ea_cil_uspory_pct",
    "plan_ea_predmet_poznamka", "plan_ea_ukazatele_seznam", "plan_ea_mkh_seznam",
    "plan_ea_soucinnost_seznam", "plan_ea_datum_zahajeni_plan", "plan_ea_datum_setreni",
    "plan_ea_datum_navrhu", "plan_ea_datum_finalizace", "plan_ea_strategicke_dok_list",
    "plan_ea_format_typ", "plan_ea_projednani_typ", "plan_ea_projednani_poznamka",
}
OBJECT_KEYS: list[str] = [k for k in DEFAULTS if k not in _PROJECT_KEYS]


def _snapshot_object() -> dict:
    """Zaznamená aktuální stav objektu ze session_state do slovníku."""
    return {k: copy.deepcopy(st.session_state[k]) for k in OBJECT_KEYS if k in st.session_state}


def _load_object(data: dict) -> None:
    """Načte data objektu ze slovníku do session_state."""
    for k in OBJECT_KEYS:
        st.session_state[k] = copy.deepcopy(data[k]) if k in data else copy.deepcopy(DEFAULTS[k])


def _serialize_val(v):
    """Převede hodnotu session state na JSON-serializovatelný typ."""
    try:
        import pandas as pd
        if isinstance(v, pd.DataFrame):
            return {"__df__": v.to_dict("records")}
    except ImportError:
        pass
    try:
        import numpy as np
        if isinstance(v, np.integer):
            return int(v)
        if isinstance(v, np.floating):
            return float(v)
        if isinstance(v, np.ndarray):
            return v.tolist()
    except ImportError:
        pass
    if isinstance(v, list):
        return [_serialize_val(i) for i in v]
    if isinstance(v, dict):
        return {k: _serialize_val(vv) for k, vv in v.items()}
    # bool/int/float/str/None projdou přímo
    return v


def _deserialize_val(v):
    """Zpětná konverze JSON hodnoty (inverse of _serialize_val)."""
    if isinstance(v, dict):
        if "__df__" in v:
            try:
                import pandas as pd
                return pd.DataFrame(v["__df__"])
            except Exception:
                return v["__df__"]
        return {k: _deserialize_val(vv) for k, vv in v.items()}
    if isinstance(v, list):
        return [_deserialize_val(i) for i in v]
    return v


def _uloz_projekt() -> str:
    """Serializuje celý projekt (všechny objekty + projektová data) do JSON."""
    import json
    import datetime

    s = st.session_state
    # Nejdřív snapsnout aktuální objekt
    cur_idx = s.get("aktivni_objekt_idx", 0)
    objekty = list(s.get("objekty", [{}]))
    if cur_idx < len(objekty):
        objekty[cur_idx] = _snapshot_object()

    projekt_data = {k: _serialize_val(s.get(k)) for k in _PROJECT_KEYS if k in s}
    objekty_data = [
        {k: _serialize_val(obj.get(k, DEFAULTS.get(k))) for k in OBJECT_KEYS}
        for obj in objekty
    ]

    payload = {
        "format_version": "1.1",
        "app": "EPC Kalkulátor – DPU ENERGY",
        "datum_ulozeni": datetime.date.today().isoformat(),
        "aktivni_objekt_idx": cur_idx,
        "projekt": projekt_data,
        "objekty": objekty_data,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _nacti_projekt(raw: bytes | str) -> str:
    """
    Načte projekt ze JSON bytu/řetězce do session_state.
    Vrátí prázdný řetězec při úspěchu nebo chybovou zprávu.
    """
    import json

    try:
        data = json.loads(raw)
    except Exception as e:
        return f"Nelze načíst soubor: {e}"

    ver = data.get("format_version", "")
    if not ver.startswith("1."):
        return f"Nepodporovaná verze formátu: {ver}"

    # Projektová data
    for k, v in data.get("projekt", {}).items():
        if k in _PROJECT_KEYS:
            st.session_state[k] = _deserialize_val(v)

    # Objekty
    objekty_raw = data.get("objekty", [])
    objekty: list[dict] = []
    for obj_raw in objekty_raw:
        obj: dict = {}
        for k in OBJECT_KEYS:
            if k in obj_raw:
                obj[k] = _deserialize_val(obj_raw[k])
            else:
                obj[k] = copy.deepcopy(DEFAULTS[k]) if k in DEFAULTS else None
        objekty.append(obj)

    if not objekty:
        objekty = [{k: copy.deepcopy(DEFAULTS.get(k)) for k in OBJECT_KEYS}]

    st.session_state["objekty"] = objekty
    new_idx = min(int(data.get("aktivni_objekt_idx", 0)), len(objekty) - 1)
    st.session_state["aktivni_objekt_idx"] = new_idx
    _load_object(objekty[new_idx])
    return ""


def _penb_na_session_state(penb) -> dict:
    """
    Mapuje PENBData na session state klíče objektu.

    Vrací slovník aktualizací (neuplatňuje je – volající rozhodne co přepsat).
    Plochy a U-hodnoty se agregují váženým průměrem přes konstrukce stejného typu.
    """
    updates: dict = {}

    # ── Geometrie budovy ──────────────────────────────────────────────────────
    if penb.objem_m3 or penb.plocha_m2:
        updates["budovy"] = [{
            "nazev": "",
            "objem_m3": penb.objem_m3,
            "plocha_m2": penb.plocha_m2,
            "ochlaz_m2": penb.ochlazovana_plocha_m2,
        }]
    if penb.theta_e:
        updates["theta_e"] = penb.theta_e
    if penb.phi_total_kw:
        updates["phi_total_kw"] = penb.phi_total_kw

    # ── Baseline spotřeby ─────────────────────────────────────────────────────
    if penb.ut_mwh:
        updates["zp_ut"] = round(penb.ut_mwh, 1)
        updates["teplo_ut"] = round(penb.ut_mwh, 1)
    if penb.tuv_mwh:
        updates["zp_tuv"] = round(penb.tuv_mwh, 1)
        updates["teplo_tuv"] = round(penb.tuv_mwh, 1)
    if penb.ee_mwh:
        updates["ee"] = round(penb.ee_mwh, 1)

    # ── U-hodnoty a plochy z konstrukcí obálky ────────────────────────────────
    def _vaz_prumer(kce_list):
        """Vážený průměr U a celková plocha."""
        a_celk = sum(k.plocha_m2 for k in kce_list)
        if a_celk == 0:
            return 0.0, 0.0
        u_vaz = sum(k.plocha_m2 * k.U for k in kce_list) / a_celk
        return round(a_celk, 1), round(u_vaz, 3)

    def _vaz_u_ref(kce_list, a_celk):
        """Vážený průměr U_ref (normová hodnota) – použit jako návrh u_nove."""
        if a_celk == 0:
            return 0.0
        refs = [k for k in kce_list if k.U_ref]
        if not refs:
            return 0.0
        a_ref = sum(k.plocha_m2 for k in refs)
        if a_ref == 0:
            return 0.0
        return round(sum(k.plocha_m2 * k.U_ref for k in refs) / a_ref, 3)

    typy = {
        "stena":       ["op1a", "op1b"],
        "otvor":       ["op2"],
        "strecha":     ["op3"],
        "podlaha_ext": ["op4"],
        "podlaha_zem": ["op5"],
    }
    for typ, prefixes in typy.items():
        kce = [k for k in penb.konstrukce if k.typ == typ]
        plocha, u_stav = _vaz_prumer(kce)
        u_ref = _vaz_u_ref(kce, plocha)
        if plocha > 0:
            for prefix in prefixes:
                updates[f"{prefix}_plocha"] = plocha
                updates[f"{prefix}_u_stavajici"] = u_stav
                if u_ref:
                    updates[f"{prefix}_u_nove"] = u_ref

    return updates


# Inicializace: pokud dosud neexistuje seznam objektů, vytvoř ho z aktuálního stavu
if "objekty" not in st.session_state:
    st.session_state["objekty"] = [_snapshot_object()]
    st.session_state["aktivni_objekt_idx"] = 0

# Zpracování přepnutí objektu – musí proběhnout PŘED vykreslením widgetů
if st.session_state.get("_switch_to") is not None:
    _new_idx: int = st.session_state["_switch_to"]
    _cur_idx: int = st.session_state.get("aktivni_objekt_idx", 0)
    st.session_state["objekty"][_cur_idx] = _snapshot_object()
    _load_object(st.session_state["objekty"][_new_idx])
    st.session_state["aktivni_objekt_idx"] = _new_idx
    st.session_state["_switch_to"] = None
    st.rerun()


def _build_project_from_data(data: dict) -> Project:
    """Sestaví Project z explicitního slovníku (pro kombinovanou bilanci)."""
    pouzit_zp = data.get("nosic_zp", True)
    pouzit_teplo = data.get("nosic_czt", False)
    if not pouzit_zp and not pouzit_teplo:
        pouzit_zp = True
    energie = EnergyInputs(
        zp_ut=data.get("zp_ut", 0.0) if pouzit_zp else 0.0,
        zp_tuv=data.get("zp_tuv", 0.0) if pouzit_zp else 0.0,
        teplo_ut=data.get("teplo_ut", 0.0) if pouzit_teplo else 0.0,
        teplo_tuv=data.get("teplo_tuv", 0.0) if pouzit_teplo else 0.0,
        ee=data.get("ee", 0.0),
        voda=data.get("voda", 0.0),
        srazky=data.get("srazky", 0.0),
        cena_zp=data.get("cena_zp", 0.0),
        cena_teplo=data.get("cena_teplo", 0.0),
        cena_ee=data.get("cena_ee", 0.0),
        cena_ee_vykup=data.get("cena_ee_vykup", 0.0),
        cena_voda=data.get("cena_voda", 0.0),
        cena_srazky=data.get("cena_srazky", 0.0),
        pouzit_zp=pouzit_zp,
        pouzit_teplo=pouzit_teplo,
        pouzit_tuv_zp=pouzit_zp,
        pouzit_tuv_teplo=pouzit_teplo,
    )
    # Denostupně pro fyzikální výpočet zateplení (z lokality projektu)
    _lok_nazev = data.get("lokalita_projekt", "Praha (Karlov)")
    try:
        _lok = _lokalita_fn(_lok_nazev)
        _D = _lok.denostupne(theta_i=data.get("theta_i", 21.0), tem=13)
    except ValueError:
        _D = 0.0

    d = data
    opatreni = [
        OP1a(aktivni=d.get("op1a_on", False),
             uspora_zp_mwh=d.get("op1a_uspora", 0.0) if pouzit_zp else 0.0,
             uspora_teplo_mwh=d.get("op1a_uspora", 0.0) if pouzit_teplo else 0.0,
             plocha_m2=d.get("op1a_plocha", 0.0), cena_kc_m2=d.get("op1a_cena_m2", 0.0),
             u_stavajici=d.get("op1a_u_stavajici", 0.0), u_nove=d.get("op1a_u_nove", 0.0),
             denostupne=_D),
        OP1b(aktivni=d.get("op1b_on", False),
             uspora_zp_mwh=d.get("op1b_uspora", 0.0) if pouzit_zp else 0.0,
             uspora_teplo_mwh=d.get("op1b_uspora", 0.0) if pouzit_teplo else 0.0,
             plocha_m2=d.get("op1b_plocha", 0.0), cena_kc_m2=d.get("op1b_cena_m2", 0.0),
             u_stavajici=d.get("op1b_u_stavajici", 0.0), u_nove=d.get("op1b_u_nove", 0.0),
             denostupne=_D),
        OP2(aktivni=d.get("op2_on", False),
            uspora_zp_mwh=d.get("op2_uspora", 0.0) if pouzit_zp else 0.0,
            uspora_teplo_mwh=d.get("op2_uspora", 0.0) if pouzit_teplo else 0.0,
            plocha_m2=d.get("op2_plocha", 0.0), cena_kc_m2=d.get("op2_cena_m2", 0.0),
            u_stavajici=d.get("op2_u_stavajici", 0.0), u_nove=d.get("op2_u_nove", 0.0),
            denostupne=_D),
        OP3(aktivni=d.get("op3_on", False),
            uspora_zp_mwh=d.get("op3_uspora", 0.0) if pouzit_zp else 0.0,
            uspora_teplo_mwh=d.get("op3_uspora", 0.0) if pouzit_teplo else 0.0,
            plocha_m2=d.get("op3_plocha", 0.0), cena_kc_m2=d.get("op3_cena_m2", 0.0),
            u_stavajici=d.get("op3_u_stavajici", 0.0), u_nove=d.get("op3_u_nove", 0.0),
            denostupne=_D),
        OP4(aktivni=d.get("op4_on", False),
            uspora_zp_mwh=d.get("op4_uspora", 0.0) if pouzit_zp else 0.0,
            uspora_teplo_mwh=d.get("op4_uspora", 0.0) if pouzit_teplo else 0.0,
            plocha_m2=d.get("op4_plocha", 0.0), cena_kc_m2=d.get("op4_cena_m2", 0.0),
            u_stavajici=d.get("op4_u_stavajici", 0.0), u_nove=d.get("op4_u_nove", 0.0),
            denostupne=_D),
        OP5(aktivni=d.get("op5_on", False),
            uspora_zp_mwh=d.get("op5_uspora", 0.0) if pouzit_zp else 0.0,
            uspora_teplo_mwh=d.get("op5_uspora", 0.0) if pouzit_teplo else 0.0,
            plocha_m2=d.get("op5_plocha", 0.0), cena_kc_m2=d.get("op5_cena_m2", 0.0),
            u_stavajici=d.get("op5_u_stavajici", 0.0), u_nove=d.get("op5_u_nove", 0.0),
            denostupne=_D),
        OP6(aktivni=d.get("op6_on", False),
            uspora_zp_mwh=d.get("op6_uspora", 0.0) if pouzit_zp else 0.0,
            uspora_teplo_mwh=d.get("op6_uspora", 0.0) if pouzit_teplo else 0.0,
            plocha_m2=d.get("op6_plocha", 0.0), cena_kc_m2=d.get("op6_cena_m2", 0.0),
            u_stavajici=d.get("op6_u_stavajici", 0.0), u_nove=d.get("op6_u_nove", 0.0),
            denostupne=_D),
        OP7(aktivni=d.get("op7_on", False),
            uspora_zp_mwh=d.get("op7_uspora", 0.0) if pouzit_zp else 0.0,
            uspora_teplo_mwh=d.get("op7_uspora", 0.0) if pouzit_teplo else 0.0,
            zmena_ee_mwh=d.get("op7_ee_zmena", 0.0), investice_kc=d.get("op7_investice", 0.0)),
        OP8(aktivni=d.get("op8_on", False),
            pocet_vetvi=d.get("op8_vetvi", 3), procento_uspory=d.get("op8_pct", 5.0) / 100),
        OP9(aktivni=d.get("op9_on", False),
            pocet_ot=d.get("op9_ot", 0), procento_uspory=d.get("op9_pct", 10.0) / 100),
        OP10(aktivni=d.get("op10_on", False),
             uspora_ee_mwh=d.get("op10_uspora_ee", 0.0), pocet_svitidel=d.get("op10_svitidel", 0)),
        OP11(aktivni=d.get("op11_on", False),
             vyroba_mwh=d.get("op11_vyroba", 0.0), self_consumption_mwh=d.get("op11_vlastni", 0.0),
             export_mwh=d.get("op11_export", 0.0), n_panelu=d.get("op11_panelu", 0),
             cena_projektovani_kc=d.get("op11_projekt", 0.0),
             cena_revize_kc=d.get("op11_revize", 0.0), cena_montaz_kc=d.get("op11_montaz", 0.0)),
        OP12(aktivni=d.get("op12_on", False),
             velikost_mwh=d.get("op12_velikost", 0.1), cena_kc_mwh=d.get("op12_cena_mwh", 0.0),
             navice_vyuzito_mwh=d.get("op12_navic", 0.0)),
        OP13(aktivni=d.get("op13_on", False),
             uspora_zp_tuv_mwh=d.get("op13_uspora", 0.0) if pouzit_zp else 0.0,
             uspora_teplo_tuv_mwh=d.get("op13_uspora", 0.0) if pouzit_teplo else 0.0,
             velikost_nadrze_l=d.get("op13_nadrz", 0.0)),
        OP14(aktivni=d.get("op14_on", False), procento_uspory=d.get("op14_pct", 15.0) / 100,
             n_umyvadel=d.get("op14_umyvadel", 0), n_sprch=d.get("op14_sprch", 0),
             n_splachovadel=d.get("op14_splachovadel", 0)),
        OP15(aktivni=d.get("op15_on", False), procento_uspory=d.get("op15_pct", 50.0) / 100,
             velikost_nadrze_l=d.get("op15_nadrz", 0.0)),
        OP16(aktivni=d.get("op16_on", False), pocet_ot=d.get("op16_ot", 0)),
        OP17(aktivni=d.get("op17_on", False), pocet_jednotek=d.get("op17_jednotky", 2)),
        OP18(aktivni=d.get("op18_on", False), plocha_m2=d.get("op18_plocha", 0.0)),
        OP19(aktivni=d.get("op19_on", False), pocet_mist=d.get("op19_mista", 0)),
        OP20(aktivni=d.get("op20_on", False),
             plocha_m2=d.get("op20_plocha", 0.0), cena_kc_m2=d.get("op20_cena_m2", 500.0)),
        OP21(aktivni=d.get("op21_on", False), investice_kc=d.get("op21_investice", 0.0)),
        OP22(aktivni=d.get("op22_on", False), investice_kc=d.get("op22_investice", 0.0)),
    ]
    _ekon_par_d = EkonomickeParametry(
        horizont=int(d.get("horizont_let", 20)),
        diskontni_sazba=d.get("diskontni_sazba", 4.0) / 100.0,
        inflace_energie=d.get("inflace_energie", 3.0) / 100.0,
    )
    _budovy_d = d.get("budovy", [])
    _objem_d = sum(b.get("objem_m3", 0.0) for b in _budovy_d)
    _obalka_d = sum(b.get("ochlaz_m2", 0.0) for b in _budovy_d)
    _ft_d = _obalka_d / _objem_d if _objem_d > 0 else 0.0
    return Project(
        nazev=d.get("objekt_nazev", ""),
        energie=energie,
        opatreni=opatreni,
        ekonomicke_parametry=_ekon_par_d,
        uem_stav=d.get("uem_stav", 0.0),
        faktor_tvaru=_ft_d,
    )


# ── Pomocné funkce ────────────────────────────────────────────────────────────

def fmt_kc(value: float) -> str:
    """Formátuje Kč s mezerou jako oddělovačem tisíců."""
    return f"{value:,.0f} Kč".replace(",", "\u00a0")


def fmt_mwh(value: float) -> str:
    return f"{value:,.1f} MWh".replace(",", "\u00a0")


def _build_executive_summary(result, ss) -> str:
    """
    Sestaví manažerské shrnutí projektu jako formátovaný Markdown.
    Parametry:
        result – ProjectResult z build_project().vypocitej()
        ss     – st.session_state
    """
    from epc_engine.emissions import FAKTORY_PRIMARNI_ENERGIE as _FPE_S

    nazev_obj  = ss.get("objekt_nazev") or ss.get("nazev_zakazky") or "Objekt"
    nazev_proj = ss.get("nazev_zakazky") or ""
    adresa     = ss.get("objekt_adresa") or ""
    typ_dok    = ss.get("typ_dokumentu") or "Energetický audit"
    datum      = ss.get("datum") or ""
    zpracovatel = ss.get("zpracovatel_jmeno") or ""

    aktivni = result.aktivni
    if not aktivni:
        return "_Žádné aktivní opatření – shrnutí nelze vygenerovat._"

    # ── Investice a úspory ────────────────────────────────────────────────────
    inv = result.celkova_investice
    usp_kc = result.celkova_uspora_kc
    usp_pct = result.celkova_uspora_pct * 100
    servis  = result.celkove_servisni_naklady
    nav = result.prosta_navratnost_celkem

    # ── Ekonomika (pokud dostupná) ─────────────────────────────────────────────
    ek = result.ekonomika_projekt
    npv_txt = f"{ek.npv:,.0f} Kč".replace(",", "\u00a0") if ek else "–"
    irr_txt = f"{ek.irr * 100:.1f} %" if (ek and ek.irr is not None) else "–"
    tsd_txt = (
        f"{ek.tsd:.0f} let"
        if (ek and ek.tsd is not None)
        else (f"> {result.ekonomika_parametry.horizont} let" if result.ekonomika_parametry else "–")
    )

    # ── Energie ───────────────────────────────────────────────────────────────
    usp_teplo_zp = result.celkova_uspora_teplo + result.celkova_uspora_zp
    usp_ee       = result.celkova_uspora_ee
    en = result.energie

    # ── Primární energie ──────────────────────────────────────────────────────
    fpe_zp = _FPE_S["zp"]; fpe_t = _FPE_S["teplo"]; fpe_ee = _FPE_S["ee"]
    pe_pred = en.zp_total * fpe_zp + en.teplo_total * fpe_t + en.ee * fpe_ee
    pe_usp  = result.celkova_uspora_zp * fpe_zp + result.celkova_uspora_teplo * fpe_t + usp_ee * fpe_ee
    pe_pct  = pe_usp / pe_pred * 100 if pe_pred > 0 else 0.0

    # ── Emise CO₂ ─────────────────────────────────────────────────────────────
    co2_pred = result.emise_pred.co2_kg if result.emise_pred else 0.0
    co2_po   = result.emise_po.co2_kg   if result.emise_po   else 0.0
    co2_usp  = co2_pred - co2_po
    co2_pct  = co2_usp / co2_pred * 100 if co2_pred > 0 else 0.0

    # ── Klasifikace obálky ────────────────────────────────────────────────────
    klas_txt = ""
    if result.klasifikace_pred:
        klas_txt = (
            f"\n- **Třída obálky budovy (stav):** {result.klasifikace_pred.trida} "
            f"(Uem = {ss.get('uem_stav', 0):.2f} W/m²K, "
            f"Uem,N = {result.klasifikace_pred.uem_n:.2f} W/m²K)"
        )

    # ── Seznam opatření ───────────────────────────────────────────────────────
    op_seznam = "\n".join(
        f"  - **{r.id}** – {r.nazev} "
        f"(investice {r.investice:,.0f} Kč, úspora {r.uspora_kc:,.0f} Kč/rok)".replace(",", "\u00a0")
        for r in aktivni
    )

    # ── Sestavení textu ───────────────────────────────────────────────────────
    hlavicka = f"## Manažerské shrnutí – {nazev_obj}"
    if nazev_proj and nazev_proj != nazev_obj:
        hlavicka += f"\n**Projekt:** {nazev_proj}"
    if adresa:
        hlavicka += f"  \n**Adresa:** {adresa}"
    if typ_dok:
        hlavicka += f"  \n**Typ dokumentu:** {typ_dok}"
    if datum:
        hlavicka += f"  \n**Datum:** {datum}"
    if zpracovatel:
        hlavicka += f"  \n**Zpracovatel:** {zpracovatel}"

    summary = f"""{hlavicka}

---

### Navrhovaná opatření ({len(aktivni)})

{op_seznam}

---

### Klíčové ukazatele

- **Celková investice:** {inv:,.0f} Kč
- **Roční úspora nákladů:** {usp_kc:,.0f} Kč/rok ({usp_pct:.1f} % z celkových nákladů)
- **Roční servisní náklady:** {servis:,.0f} Kč/rok
- **Prostá návratnost:** {"%.1f let" % nav if nav else "nelze stanovit (záporná čistá úspora)"}
- **NPV:** {npv_txt}
- **IRR:** {irr_txt}
- **Diskontovaná doba úhrady (Tsd):** {tsd_txt}

---

### Energetické úspory

- **Úspora tepla a zemního plynu:** {usp_teplo_zp:,.1f} MWh/rok
- **Úspora elektrické energie:** {usp_ee:,.1f} MWh/rok
- **Úspora primární energie (PE,nOZE):** {pe_usp:,.1f} MWh/rok ({pe_pct:.1f} %)
- **Snížení emisí CO₂:** {co2_usp/1000:,.2f} t/rok ({co2_pct:.1f} %){klas_txt}
""".replace(",", "\u00a0")

    return summary


def build_building_info() -> BuildingInfo:
    """Sestaví BuildingInfo ze session state."""
    s = st.session_state
    budovy = [
        Budova(
            nazev=b["nazev"],
            objem_m3=b["objem_m3"],
            podlahova_plocha_m2=b["plocha_m2"],
            ochlazovana_plocha_m2=b["ochlaz_m2"],
        )
        for b in s.get("budovy", [])
    ]
    prostory = [
        Prostor(nazev=p["nazev"], ucel=p["ucel"], provoz=p["provoz"])
        for p in s.get("prostory", [])
    ]
    podklady = [
        Podklad(nazev=p["nazev"], k_dispozici=p["ok"])
        for p in s.get("podklady", [])
    ]
    # ── Sprint 4: tepelná obálka ──────────────────────────────────────────────
    konstrukce = []
    for k in s.get("konstrukce_obalka", []):
        vrstvy = [
            Vrstva(
                nazev=v.get("nazev", ""),
                tloustka_m=v.get("tloustka_mm", 0.0) / 1000.0,
                lambda_wm=v.get("lambda_wm", 0.0),
            )
            for v in k.get("vrstvy", [])
        ]
        u_zadane_raw = k.get("u_zadane", "")
        konstrukce.append(Konstrukce(
            nazev=k.get("nazev", ""),
            typ=k.get("typ", "stena"),
            plocha_m2=float(k.get("plocha_m2", 0.0)),
            vrstvy=vrstvy,
            u_zadane=float(u_zadane_raw) if u_zadane_raw not in ("", None) else None,
            un_value=float(k.get("un_value", 0.0)),
        ))

    # ── Sprint 4: technické systémy ────────────────────────────────────────────
    def _sys(key_prefix) -> TechnickySytem:
        return TechnickySytem(
            typ=s.get(f"{key_prefix}_typ", ""),
            vykon_kw=float(s.get(f"{key_prefix}_vykon", 0.0) or 0),
            ucinnost_pct=float(s.get(f"{key_prefix}_ucinnost", 0.0) or 0),
            rok_instalace=int(s.get(f"{key_prefix}_rok", 0) or 0),
            popis=s.get(f"{key_prefix}_popis", ""),
        )

    ts = TechnickeSystemy(
        vytapeni=_sys("ts_vytapeni"),
        tuv=_sys("ts_tuv"),
        vzt=_sys("ts_vzt"),
        osvetleni=TechnickySytem(
            typ=s.get("ts_osvetleni_typ", ""),
            popis=s.get("ts_osvetleni_popis", ""),
        ),
        mereni_ridici=s.get("ts_mar", ""),
    )

    # ── Sprint 4: bilance dle účelu ────────────────────────────────────────────
    _bil_keys = [
        "bilance_vytapeni_mwh", "bilance_chlazeni_mwh", "bilance_tuv_mwh",
        "bilance_vetrání_mwh", "bilance_osvetleni_mwh",
        "bilance_technologie_mwh", "bilance_phm_mwh",
    ]
    bilance = None
    if any(float(s.get(k, 0) or 0) > 0 for k in _bil_keys):
        bilance = BilancePouzitiEnergie(
            vytapeni_mwh=float(s.get("bilance_vytapeni_mwh", 0) or 0),
            chlazeni_mwh=float(s.get("bilance_chlazeni_mwh", 0) or 0),
            tuv_mwh=float(s.get("bilance_tuv_mwh", 0) or 0),
            vetrání_mwh=float(s.get("bilance_vetrání_mwh", 0) or 0),
            osvetleni_mwh=float(s.get("bilance_osvetleni_mwh", 0) or 0),
            technologie_mwh=float(s.get("bilance_technologie_mwh", 0) or 0),
            phm_mwh=float(s.get("bilance_phm_mwh", 0) or 0),
        )

    # ── Sprint 4: PENB ────────────────────────────────────────────────────────
    penb = None
    if s.get("penb_trida_stav") or s.get("penb_dodana_energie"):
        penb = PenbData(
            trida_stavajici=s.get("penb_trida_stav", ""),
            trida_navrhovy=s.get("penb_trida_nav", ""),
            merná_potreba_tepla=float(s.get("penb_potreba_tepla", 0) or 0),
            celkova_dodana_energie=float(s.get("penb_dodana_energie", 0) or 0),
            primarni_neobnovitelna=float(s.get("penb_primarni", 0) or 0),
            energeticka_vztazna_plocha=float(s.get("penb_plocha", 0) or 0),
            poznamka=s.get("penb_poznamka", ""),
        )

    # ── Sprint 4: klimatická data + historie spotřeby ─────────────────────────
    klima = None
    if s.get("klima_lokalita") or s.get("klima_stupnodni_norm", 0):
        klima = KlimatickaData(
            lokalita=s.get("klima_lokalita", ""),
            stupnodni_normovane=float(s.get("klima_stupnodni_norm", 3600) or 3600),
            teplota_vnitrni=float(s.get("klima_ti", 19) or 19),
            teplota_exterieru=float(s.get("klima_te", -12) or -12),
        )

    # Sestavit historii z „roky_spotreby" (B.2)
    pouzit_zp = s.get("nosic_zp", True)
    pouzit_teplo = s.get("nosic_czt", False)
    cena_zp = float(s.get("cena_zp", 0) or 0)
    cena_teplo = float(s.get("cena_teplo", 0) or 0)
    cena_ee = float(s.get("cena_ee", 0) or 0)

    # Měsíční profily (z Vstupní data → expandery) – přiřadí se k nejnovějšímu roku
    _zp_m = [float(v) for v in s.get("zp_ut_mesice", [0.0] * 12)]
    _zp_tuv_m = [float(v) for v in s.get("zp_tuv_mesice", [0.0] * 12)]
    _tep_m = [float(v) for v in s.get("teplo_ut_mesice", [0.0] * 12)]
    _tep_tuv_m = [float(v) for v in s.get("teplo_tuv_mesice", [0.0] * 12)]
    _ee_m = [float(v) for v in s.get("ee_mesice", [0.0] * 12)]
    _max_rok = max(
        (int(r.get("rok", 0) or 0) for r in s.get("roky_spotreby", [])),
        default=0,
    )

    historie = []
    for row in s.get("roky_spotreby", []):
        rok = int(row.get("rok", 0) or 0)
        is_latest = (rok == _max_rok and rok > 0)
        if pouzit_zp:
            zp_total = float(row.get("zp_ut", 0) or 0) + float(row.get("zp_tuv", 0) or 0)
            if zp_total > 0:
                mesicni_zp = [a + b for a, b in zip(_zp_m, _zp_tuv_m)] if is_latest else [0.0] * 12
                historie.append(HistorieRok(
                    rok=rok,
                    energonosic="Zemní plyn",
                    spotreba_mwh=zp_total,
                    naklady_kc=zp_total * cena_zp,
                    stupnodni=float(row.get("D", 0) or 0),
                    mesicni_mwh=mesicni_zp,
                ))
        if pouzit_teplo:
            tep_total = float(row.get("teplo_ut", 0) or 0) + float(row.get("teplo_tuv", 0) or 0)
            if tep_total > 0:
                mesicni_tep = [a + b for a, b in zip(_tep_m, _tep_tuv_m)] if is_latest else [0.0] * 12
                historie.append(HistorieRok(
                    rok=rok,
                    energonosic="Teplo (CZT)",
                    spotreba_mwh=tep_total,
                    naklady_kc=tep_total * cena_teplo,
                    stupnodni=float(row.get("D", 0) or 0),
                    mesicni_mwh=mesicni_tep,
                ))
        ee_val = float(row.get("ee", 0) or 0)
        if ee_val > 0:
            mesicni_ee = _ee_m if is_latest else [0.0] * 12
            historie.append(HistorieRok(
                rok=rok,
                energonosic="Elektrická energie",
                spotreba_mwh=ee_val,
                naklady_kc=ee_val * cena_ee,
                stupnodni=0.0,
                mesicni_mwh=mesicni_ee,
            ))

    # Bilance dle účelu – dopočítat náklady proporcionálně z celkových nákladů
    if bilance and bilance.celkem_mwh > 0:
        _naklady_zp = (float(s.get("zp_ut", 0) or 0) + float(s.get("zp_tuv", 0) or 0)) * cena_zp
        _naklady_tep = (float(s.get("teplo_ut", 0) or 0) + float(s.get("teplo_tuv", 0) or 0)) * cena_teplo
        _naklady_ee = float(s.get("ee", 0) or 0) * cena_ee
        _naklady_voda = float(s.get("voda", 0) or 0) * float(s.get("cena_voda", 0) or 0)
        _total_naklady = _naklady_zp + _naklady_tep + _naklady_ee + _naklady_voda
        if _total_naklady > 0:
            _kc_per_mwh = _total_naklady / bilance.celkem_mwh
            bilance.vytapeni_kc = bilance.vytapeni_mwh * _kc_per_mwh
            bilance.chlazeni_kc = bilance.chlazeni_mwh * _kc_per_mwh
            bilance.tuv_kc = bilance.tuv_mwh * _kc_per_mwh
            bilance.vetrání_kc = bilance.vetrání_mwh * _kc_per_mwh
            bilance.osvetleni_kc = bilance.osvetleni_mwh * _kc_per_mwh
            bilance.technologie_kc = bilance.technologie_mwh * _kc_per_mwh
            bilance.phm_kc = bilance.phm_mwh * _kc_per_mwh

    return BuildingInfo(
        nazev_zakazky=s["nazev_zakazky"],
        datum=s["datum"],
        program_efekt=s["program_efekt"],
        zadavatel_nazev=s["zadavatel_nazev"],
        zadavatel_adresa=s["zadavatel_adresa"],
        zadavatel_ico=s["zadavatel_ico"],
        zadavatel_kontakt=s["zadavatel_kontakt"],
        zadavatel_telefon=s["zadavatel_telefon"],
        zadavatel_email=s["zadavatel_email"],
        zpracovatel_zastupce=s["zpracovatel_zastupce"],
        objekt_nazev=s["objekt_nazev"],
        objekt_adresa=s["objekt_adresa"],
        predmet_analyzy=s["predmet_analyzy"],
        druh_cinnosti=s["druh_cinnosti"],
        pocet_zamestnancu=s["pocet_zamestnancu"],
        provozni_rezim=s["provozni_rezim"],
        budovy=budovy,
        prostory=prostory,
        podklady=podklady,
        poznamka_podklady=s["poznamka_podklady"],
        # Sprint 4
        objekt_ku=s.get("objekt_ku", ""),
        objekt_parcelni_cislo=s.get("objekt_parcelni_cislo", ""),
        evidencni_cislo=s.get("evidencni_cislo", ""),
        cislo_opravneni=s.get("cislo_opravneni", ""),
        ucel_ep=s.get("ucel_ep", ""),
        ceny_bez_dph=bool(s.get("ceny_bez_dph", True)),
        konstrukce=konstrukce,
        technicke_systemy=ts,
        bilance_pouziti=bilance,
        penb=penb,
        klimaticka_data=klima,
        historie_spotreby=historie,
        okrajove_podminky=s.get("okrajove_podminky", ""),
        enms=_build_enms(s),
        ea_data=_build_ea_data(s),
        fotografie=_build_fotografie(s),
        plan_ea=_build_plan_ea(s),
    )


_ENMS_OBLASTI_NAZVY = [
    "Energetická politika",
    "Energetické plánování",
    "Implementace a provoz",
    "Kontrola a měření",
    "Interní audit EnMS",
    "Přezkoumání vedením",
    "Neustálé zlepšování",
]


def _build_enms(s) -> EnMSHodnoceni | None:
    """Sestaví EnMSHodnoceni ze session state nebo vrátí None, pokud není nic zadáno."""
    oblasti = []
    any_filled = False
    for i, nazev in enumerate(_ENMS_OBLASTI_NAZVY):
        stav = s.get(f"enms_{i}_stav", "")
        h = int(s.get(f"enms_{i}_h", 0) or 0)
        oblasti.append(EnMSOblast(nazev=nazev, stav=stav, hodnoceni=h))
        if stav or h > 0:
            any_filled = True
    if not any_filled and not s.get("enms_certifikovan"):
        return None
    return EnMSHodnoceni(
        certifikovan=bool(s.get("enms_certifikovan", False)),
        oblasti=oblasti,
        komentar=s.get("enms_komentar", ""),
    )


# Předvolená MKH kritéria (pořadí musí odpovídat indexům ea_mkh_0..3)
_MKH_DEFAULTS = [
    {"nazev": "Čistá současná hodnota (NPV)", "jednotka": "tis. Kč", "typ": "max", "key": "npv"},
    {"nazev": "Prostá doba návratnosti", "jednotka": "roky", "typ": "min", "key": "td"},
    {"nazev": "Úspora energie", "jednotka": "MWh/rok", "typ": "max", "key": "mwh"},
    {"nazev": "Úspora nákladů na energii", "jednotka": "tis. Kč/rok", "typ": "max", "key": "kc"},
]


def _build_ea_data(s) -> EAData | None:
    """Sestaví EAData ze session state nebo vrátí None, pokud nic EA-specifického není zadáno."""
    ev = s.get("ea_evidencni_cislo", "")
    cil = s.get("ea_cil", "")
    datum_z = s.get("ea_datum_zahajeni", "")
    datum_u = s.get("ea_datum_ukonceni", "")
    plan = s.get("ea_plan_text", "")
    program = s.get("ea_program_realizace", "")

    # Energonosiče
    energonositele_raw = s.get("ea_energonositele", []) or []
    energonositele = [
        EnergonositelEA(
            nazev=e.get("nazev", ""),
            kategorie=e.get("kategorie", "NOZE"),
            oblast=e.get("oblast", "Budovy"),
        )
        for e in energonositele_raw
        if isinstance(e, dict) and e.get("nazev")
    ]

    # MKH kritéria
    kriteria = []
    for i, dflt in enumerate(_MKH_DEFAULTS):
        if s.get(f"ea_mkh_{i}_aktivni", True):
            vaha = float(s.get(f"ea_mkh_{i}_vaha", dflt.get("vaha", 0)) or 0)
            if vaha > 0:
                kriteria.append(MKHKriterium(
                    nazev=dflt["nazev"],
                    jednotka=dflt["jednotka"],
                    typ=dflt["typ"],
                    vaha=vaha,
                    key=dflt["key"],
                ))

    # EnPI
    enpi_raw = s.get("ea_enpi", []) or []
    enpi = [
        EnPIUkazatel(
            nazev=e.get("nazev", ""),
            jednotka=e.get("jednotka", ""),
            hodnota_stavajici=float(e.get("stavajici", 0) or 0),
            hodnota_navrhova=float(e.get("navrhova", 0) or 0),
        )
        for e in enpi_raw
        if isinstance(e, dict) and e.get("nazev")
    ]

    # Vrátit None pokud nic není zadáno
    has_data = any([ev, cil, datum_z, datum_u, plan, program,
                    energonositele, enpi])
    if not has_data and not kriteria:
        return EAData()  # prázdný, ale s výchozími MKH kritérii
    return EAData(
        evidencni_cislo_ea=ev,
        cil=cil,
        datum_zahajeni=datum_z,
        datum_ukonceni=datum_u,
        plan_text=plan,
        program_realizace=program,
        energonositele=energonositele,
        mkh_kriteria=kriteria if kriteria else list(EAData().mkh_kriteria),
        enpi=enpi,
    )


def _build_fotografie(s) -> list[Fotografie]:
    """Sestaví seznam Fotografie objektů ze session state (nahraných souborů)."""
    result = []
    for item in s.get("fotografie_upload", []):
        # item je dict: {"data": bytes, "name": str, "popisek": str, "sekce": str}
        if item.get("data"):
            result.append(Fotografie(
                data=item["data"],
                popisek=item.get("popisek", item.get("name", "")),
                sekce=item.get("sekce", "budova"),
                sirka_cm=item.get("sirka_cm", 14.0),
            ))
    return result


def _build_plan_ea(s) -> "PlanEA | None":
    """Sestaví PlanEA ze session state (strukturované vstupy → text pro dokument)."""
    from epc_engine.models import PlanEA

    # 1. Míra detailu
    _urovne_text = {
        1: (
            "Úroveň 1 – Přehledový audit (walk-through) dle přílohy A3 ČSN ISO 50002. "
            "Zahrnuje základní prohlídku objektu a identifikaci zjevných příležitostí úspor "
            "bez podrobného měření."
        ),
        2: (
            "Úroveň 2 – Úplný energetický audit dle přílohy A3 ČSN ISO 50002. "
            "Zahrnuje revizi historické spotřeby, místní šetření, výpočtové hodnocení "
            "úsporných opatření a ekonomickou analýzu."
        ),
        3: (
            "Úroveň 3 – Detailní energetický audit dle přílohy A3 ČSN ISO 50002. "
            "Zahrnuje podrobné měření, modelování energetického systému "
            "a analýzu citlivosti pro vybraná opatření."
        ),
    }
    mira_detailu = _urovne_text.get(
        int(s.get("plan_ea_uroven", 2) or 2),
        s.get("plan_ea_mira_detailu", ""),
    )

    # 2. Předmět EA
    _systemy = s.get("plan_ea_systemy", [])
    predmet_base = s.get("plan_ea_predmet", "")
    predmet_pozn = s.get("plan_ea_predmet_poznamka", "")
    predmet_parts = []
    if predmet_base:
        predmet_parts.append(predmet_base)
    if _systemy:
        predmet_parts.append("Energetické systémy zahrnuté v rozsahu EA: " + ", ".join(_systemy) + ".")
    if predmet_pozn:
        predmet_parts.append(predmet_pozn)
    predmet_ea = "\n".join(predmet_parts)

    # 3. Potřeby a cíle
    _cile = s.get("plan_ea_cile_seznam", [])
    _cil_pct = float(s.get("plan_ea_cil_uspory_pct", 0) or 0)
    _potreby_txt = s.get("plan_ea_potreby", "")
    potreby_parts = []
    if _cile:
        potreby_parts.append("Cíle zadavatele: " + "; ".join(_cile) + ".")
    if _cil_pct > 0:
        potreby_parts.append(f"Cílová úspora: min. {_cil_pct:.0f} % oproti stávajícímu stavu.")
    if _potreby_txt:
        potreby_parts.append(_potreby_txt)
    potreby_a_cile = "\n".join(potreby_parts)

    # 4. Ekonomické ukazatele a MKH
    _ukazatele = s.get("plan_ea_ukazatele_seznam", [])
    ekonomicke = ", ".join(_ukazatele) if _ukazatele else s.get("plan_ea_ekonomicke_ukazatele", "")
    _mkh = s.get("plan_ea_mkh_seznam", [])
    mkh_parts = []
    if _mkh:
        mkh_parts.append(
            "Vícekriteriální hodnocení dle přílohy č. 9 vyhl. 140/2021 Sb. zahrnuje: "
            + ", ".join(_mkh) + "."
        )
    if s.get("plan_ea_mkh_popis", ""):
        mkh_parts.append(s["plan_ea_mkh_popis"])
    mkh_kriteria_popis = "\n".join(mkh_parts) if mkh_parts else s.get("plan_ea_mkh_popis", "")

    # 5. Součinnost
    _souc = s.get("plan_ea_soucinnost_seznam", [])
    _souc_txt = s.get("plan_ea_soucinnost", "")
    souc_parts = []
    if _souc:
        souc_parts.append("Zadavatel zajistí: " + "; ".join(_souc).lower() + ".")
    if _souc_txt:
        souc_parts.append(_souc_txt)
    soucinnost = "\n".join(souc_parts) if souc_parts else _souc_txt

    # Harmonogram
    _faze_data = [
        ("Zahájení auditu", s.get("plan_ea_datum_zahajeni_plan", "")),
        ("Místní šetření", s.get("plan_ea_datum_setreni", "")),
        ("Předání návrhu zprávy", s.get("plan_ea_datum_navrhu", "")),
        ("Finalizace a předání", s.get("plan_ea_datum_finalizace", "")),
    ]
    harm_lines = [f"{f}: {d}" for f, d in _faze_data if d]
    harmonogram = "\n".join(harm_lines) if harm_lines else s.get("plan_ea_harmonogram", "")

    # 6. Strategické dokumenty
    _dok_list = s.get("plan_ea_strategicke_dok_list", [])
    strat_dok = "\n".join(_dok_list) if _dok_list else s.get("plan_ea_strategicke_dok", "")

    # 7. Formát
    format_zpravy = s.get("plan_ea_format_typ") or s.get("plan_ea_format", "")

    # 8. Projednání
    _projednani_typ = s.get("plan_ea_projednani_typ", "")
    _projednani_pozn = s.get("plan_ea_projednani_poznamka", "")
    projednani_parts = [p for p in [_projednani_typ, _projednani_pozn] if p]
    projednani = "\n".join(projednani_parts) if projednani_parts else s.get("plan_ea_projednani", "")

    return PlanEA(
        datum_planu=s.get("plan_ea_datum", ""),
        zadavatel_zastupce=s.get("plan_ea_zadavatel_zastupce", ""),
        mira_detailu=mira_detailu,
        predmet_ea=predmet_ea,
        lokalizace_predmetu=s.get("plan_ea_lokalizace", ""),
        potreby_a_cile=potreby_a_cile,
        ekonomicke_ukazatele=ekonomicke,
        horizont_hodnoceni_let=int(s.get("horizont_let", 20) or 20),
        diskontni_sazba_pct=float(s.get("diskontni_sazba", 4.0) or 4.0),
        inflace_energie_pct=float(s.get("inflace_energie", 3.0) or 3.0),
        zahrnout_financni_podporu=bool(s.get("plan_ea_dotace", False)),
        mkh_kriteria_popis=mkh_kriteria_popis,
        soucinnost_pozadavky=soucinnost,
        harmonogram=harmonogram,
        strategicke_dokumenty=strat_dok,
        format_zpravy=format_zpravy,
        projednani_vystupu=projednani,
        dodatky=list(s.get("plan_ea_dodatky", [])),
    )


def build_project() -> Project:
    """Sestaví Project ze session state."""
    s = st.session_state
    pouzit_zp = s.get("nosic_zp", True)
    pouzit_teplo = s.get("nosic_czt", False)
    # Pokud nikdo nezaškrtl, fallback na ZP
    if not pouzit_zp and not pouzit_teplo:
        pouzit_zp = True

    energie = EnergyInputs(
        zp_ut=s["zp_ut"] if pouzit_zp else 0.0,
        zp_tuv=s["zp_tuv"] if pouzit_zp else 0.0,
        teplo_ut=s["teplo_ut"] if pouzit_teplo else 0.0,
        teplo_tuv=s["teplo_tuv"] if pouzit_teplo else 0.0,
        ee=s["ee"],
        voda=s["voda"],
        srazky=s["srazky"],
        cena_zp=s["cena_zp"],
        cena_teplo=s["cena_teplo"],
        cena_ee=s["cena_ee"],
        cena_ee_vykup=s["cena_ee_vykup"],
        cena_voda=s["cena_voda"],
        cena_srazky=s["cena_srazky"],
        pouzit_zp=pouzit_zp,
        pouzit_teplo=pouzit_teplo,
        pouzit_tuv_zp=pouzit_zp,
        pouzit_tuv_teplo=pouzit_teplo,
    )

    label = "ZP" if pouzit_zp else "teplo"

    # Denostupně pro fyzikální výpočet zateplení (z lokality projektu)
    _lok_nazev = s.get("lokalita_projekt", "Praha (Karlov)")
    try:
        _lok_bp = _lokalita_fn(_lok_nazev)
        _D_bp = _lok_bp.denostupne(theta_i=s.get("theta_i", 21.0), tem=13)
    except ValueError:
        _D_bp = 0.0

    opatreni = [
        OP1a(
            aktivni=s["op1a_on"],
            uspora_zp_mwh=s["op1a_uspora"] if pouzit_zp else 0.0,
            uspora_teplo_mwh=s["op1a_uspora"] if pouzit_teplo else 0.0,
            plocha_m2=s["op1a_plocha"], cena_kc_m2=s["op1a_cena_m2"],
            u_stavajici=s.get("op1a_u_stavajici", 0.0),
            u_nove=s.get("op1a_u_nove", 0.0), denostupne=_D_bp,
        ),
        OP1b(
            aktivni=s["op1b_on"],
            uspora_zp_mwh=s["op1b_uspora"] if pouzit_zp else 0.0,
            uspora_teplo_mwh=s["op1b_uspora"] if pouzit_teplo else 0.0,
            plocha_m2=s["op1b_plocha"], cena_kc_m2=s["op1b_cena_m2"],
            u_stavajici=s.get("op1b_u_stavajici", 0.0),
            u_nove=s.get("op1b_u_nove", 0.0), denostupne=_D_bp,
        ),
        OP2(
            aktivni=s["op2_on"],
            uspora_zp_mwh=s["op2_uspora"] if pouzit_zp else 0.0,
            uspora_teplo_mwh=s["op2_uspora"] if pouzit_teplo else 0.0,
            plocha_m2=s["op2_plocha"], cena_kc_m2=s["op2_cena_m2"],
            u_stavajici=s.get("op2_u_stavajici", 0.0),
            u_nove=s.get("op2_u_nove", 0.0), denostupne=_D_bp,
        ),
        OP3(
            aktivni=s["op3_on"],
            uspora_zp_mwh=s["op3_uspora"] if pouzit_zp else 0.0,
            uspora_teplo_mwh=s["op3_uspora"] if pouzit_teplo else 0.0,
            plocha_m2=s["op3_plocha"], cena_kc_m2=s["op3_cena_m2"],
            u_stavajici=s.get("op3_u_stavajici", 0.0),
            u_nove=s.get("op3_u_nove", 0.0), denostupne=_D_bp,
        ),
        OP4(
            aktivni=s["op4_on"],
            uspora_zp_mwh=s["op4_uspora"] if pouzit_zp else 0.0,
            uspora_teplo_mwh=s["op4_uspora"] if pouzit_teplo else 0.0,
            plocha_m2=s["op4_plocha"], cena_kc_m2=s["op4_cena_m2"],
            u_stavajici=s.get("op4_u_stavajici", 0.0),
            u_nove=s.get("op4_u_nove", 0.0), denostupne=_D_bp,
        ),
        OP5(
            aktivni=s["op5_on"],
            uspora_zp_mwh=s["op5_uspora"] if pouzit_zp else 0.0,
            uspora_teplo_mwh=s["op5_uspora"] if pouzit_teplo else 0.0,
            plocha_m2=s["op5_plocha"], cena_kc_m2=s["op5_cena_m2"],
            u_stavajici=s.get("op5_u_stavajici", 0.0),
            u_nove=s.get("op5_u_nove", 0.0), denostupne=_D_bp,
        ),
        OP6(
            aktivni=s["op6_on"],
            uspora_zp_mwh=s["op6_uspora"] if pouzit_zp else 0.0,
            uspora_teplo_mwh=s["op6_uspora"] if pouzit_teplo else 0.0,
            plocha_m2=s["op6_plocha"], cena_kc_m2=s["op6_cena_m2"],
            u_stavajici=s.get("op6_u_stavajici", 0.0),
            u_nove=s.get("op6_u_nove", 0.0), denostupne=_D_bp,
        ),
        OP7(
            aktivni=s["op7_on"],
            uspora_zp_mwh=s["op7_uspora"] if pouzit_zp else 0.0,
            uspora_teplo_mwh=s["op7_uspora"] if pouzit_teplo else 0.0,
            zmena_ee_mwh=s["op7_ee_zmena"],
            investice_kc=s["op7_investice"],
        ),
        OP8(
            aktivni=s["op8_on"],
            pocet_vetvi=s["op8_vetvi"],
            procento_uspory=s["op8_pct"] / 100,
        ),
        OP9(
            aktivni=s["op9_on"],
            pocet_ot=s["op9_ot"],
            procento_uspory=s["op9_pct"] / 100,
        ),
        OP10(
            aktivni=s["op10_on"],
            uspora_ee_mwh=s["op10_uspora_ee"],
            pocet_svitidel=s["op10_svitidel"],
        ),
        OP11(
            aktivni=s["op11_on"],
            vyroba_mwh=s["op11_vyroba"],
            self_consumption_mwh=s["op11_vlastni"],
            export_mwh=s["op11_export"],
            n_panelu=s["op11_panelu"],
            cena_projektovani_kc=s["op11_projekt"],
            cena_revize_kc=s["op11_revize"],
            cena_montaz_kc=s["op11_montaz"],
        ),
        OP12(
            aktivni=s["op12_on"],
            velikost_mwh=s["op12_velikost"],
            cena_kc_mwh=s["op12_cena_mwh"],
            navice_vyuzito_mwh=s["op12_navic"],
        ),
        OP13(
            aktivni=s["op13_on"],
            uspora_zp_tuv_mwh=s["op13_uspora"] if pouzit_zp else 0.0,
            uspora_teplo_tuv_mwh=s["op13_uspora"] if pouzit_teplo else 0.0,
            velikost_nadrze_l=s["op13_nadrz"],
        ),
        OP14(
            aktivni=s["op14_on"],
            procento_uspory=s["op14_pct"] / 100,
            n_umyvadel=s["op14_umyvadel"],
            n_sprch=s["op14_sprch"],
            n_splachovadel=s["op14_splachovadel"],
        ),
        OP15(
            aktivni=s["op15_on"],
            procento_uspory=s["op15_pct"] / 100,
            velikost_nadrze_l=s["op15_nadrz"],
        ),
        OP16(
            aktivni=s["op16_on"],
            pocet_ot=s["op16_ot"],
        ),
        OP17(
            aktivni=s["op17_on"],
            pocet_jednotek=s["op17_jednotky"],
        ),
        OP18(
            aktivni=s["op18_on"],
            plocha_m2=s["op18_plocha"],
        ),
        OP19(
            aktivni=s["op19_on"],
            pocet_mist=s["op19_mista"],
        ),
        OP20(
            aktivni=s["op20_on"],
            plocha_m2=s["op20_plocha"],
            cena_kc_m2=s["op20_cena_m2"],
        ),
        OP21(aktivni=s["op21_on"], investice_kc=s["op21_investice"]),
        OP22(aktivni=s["op22_on"], investice_kc=s["op22_investice"]),
    ]

    # Ekonomické parametry
    _ekon_par = EkonomickeParametry(
        horizont=int(s.get("horizont_let", 20)),
        diskontni_sazba=s.get("diskontni_sazba", 4.0) / 100.0,
        inflace_energie=s.get("inflace_energie", 3.0) / 100.0,
    )

    # Faktor tvaru A/V z budov (součet přes všechny budovy objektu)
    _budovy_data = s.get("budovy", [])
    _objem_celk = sum(b.get("objem_m3", 0.0) for b in _budovy_data)
    _obalka_celk = sum(b.get("ochlaz_m2", 0.0) for b in _budovy_data)
    _faktor_tvaru_bp = _obalka_celk / _objem_celk if _objem_celk > 0 else 0.0

    return Project(
        nazev=s["nazev"],
        budova=build_building_info(),
        energie=energie,
        opatreni=opatreni,
        ekonomicke_parametry=_ekon_par,
        uem_stav=s.get("uem_stav", 0.0),
        faktor_tvaru=_faktor_tvaru_bp,
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Kalkulátor energeticky úsporných projektů")
    st.caption("DPU ENERGY s.r.o.")
    st.divider()

    # ── Ekonomické parametry ──────────────────────────────────────────────────
    st.divider()
    st.subheader("Ekonomické parametry")
    _ek_col1, _ek_col2, _ek_col3 = st.columns(3)
    with _ek_col1:
        st.number_input(
            "Horizont [roky]",
            key="horizont_let",
            min_value=5, max_value=30, step=1,
            help="Délka ekonomické analýzy (typicky 20 let)",
        )
    with _ek_col2:
        st.number_input(
            "Diskont. sazba [%]",
            key="diskontni_sazba",
            min_value=0.0, max_value=15.0, step=0.5, format="%.1f",
            help="Reálná diskontní sazba (4 % = standard OPŽP)",
        )
    with _ek_col3:
        st.number_input(
            "Inflace energií [%]",
            key="inflace_energie",
            min_value=0.0, max_value=10.0, step=0.5, format="%.1f",
            help="Očekávané roční zdražování energie",
        )

    st.divider()
    st.page_link("pages/Popis_stavajiciho_stavu.py", label="Popis stávajícího stavu", icon="📋")
    st.page_link("pages/Fyzikální_kalkulátor.py", label="Fyzikální kalkulátor", icon="🔬")
    st.divider()
    st.caption("Navigace")
    st.markdown("""
- [Vstupní data](#vstupn-data)
- [Opatření](#opat-en)
- [Výsledky](#v-sledky)
""")


# ── Hlavní obsah ──────────────────────────────────────────────────────────────

st.title(st.session_state.get("nazev_zakazky") or "Kalkulátor energeticky úsporných projektů")

# ── Typ dokumentu – vždy viditelný přepínač ──────────────────────────────────
_TYPY_DOK = [
    "Obecná studie",
    "Podrobná analýza",
    "Energetický posudek",
    "Energetický audit",
]
_TYP_IKONY = {
    "Obecná studie":      "📋",
    "Podrobná analýza":   "🔍",
    "Energetický posudek": "📑",
    "Energetický audit":  "🏛️",
}
_TYP_POPIS = {
    "Obecná studie":      "Přehledové posouzení bez zákonných náležitostí",
    "Podrobná analýza":   "Detailní technická a ekonomická analýza",
    "Energetický posudek": "Dle vyhl. 141/2021 Sb.",
    "Energetický audit":  "Dle vyhl. 140/2021 Sb. – zahrnuje Plán EA",
}
_cur_typ = st.session_state.get("typ_dokumentu", "Energetický audit")
_typ_col, _typ_info_col = st.columns([3, 2])
with _typ_col:
    st.segmented_control(
        "Typ dokumentu",
        options=_TYPY_DOK,
        format_func=lambda t: f"{_TYP_IKONY[t]} {t}",
        key="typ_dokumentu",
        label_visibility="collapsed",
    )
with _typ_info_col:
    st.caption(_TYP_POPIS.get(st.session_state.get("typ_dokumentu", _cur_typ), ""))

# Odvozené příznaky – použity v celém souboru níže
_je_ea   = st.session_state.get("typ_dokumentu") == "Energetický audit"
_je_ep   = st.session_state.get("typ_dokumentu") in ("Energetický posudek", "Energetický audit")
_je_studie = st.session_state.get("typ_dokumentu") in ("Obecná studie", "Podrobná analýza")

# Řádek 1 – projektové záložky
tab_projekt, tab_plan_ea, tab_export = st.tabs([
    "📁 Projekt",
    "📝 Plán EA" + ("" if _je_ea else " ✗"),
    "📄 Export",
])


# ══════════════════════════════════════════════════════════════════════════════
# PROJECT TAB – Identifikace projektu (zadavatel, zpracovatel, účel)
# ══════════════════════════════════════════════════════════════════════════════

with tab_projekt:

    # ── Identifikace projektu ─────────────────────────────────────────────────
    st.subheader("Identifikace projektu")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.text_input("Název zakázky (nadřazený projekt)",
                      key="nazev_zakazky",
                      placeholder="Analýza potenciálu úspor objektů ve správě XY a.s.")
    with col2:
        st.text_input("Datum vypracování", key="datum",
                      placeholder="18. prosince 2024")
        st.checkbox("Podpořeno programem EFEKT III", key="program_efekt")

    st.divider()

    # ── Zadavatel a zpracovatel ───────────────────────────────────────────────
    st.subheader("Zadavatel a zpracovatel")
    col_z, col_p = st.columns(2)

    with col_z:
        st.markdown("**Zadavatel (klient)**")
        st.text_input("Název společnosti / organizace", key="zadavatel_nazev",
                      placeholder="Jihoměstská majetková a.s.")
        st.text_input("Adresa", key="zadavatel_adresa",
                      placeholder="Ocelíkova 672/1, 149 00 Praha 4")
        col_ico, col_kontakt = st.columns(2)
        with col_ico:
            st.text_input("IČ", key="zadavatel_ico", placeholder="28199081")
        with col_kontakt:
            st.text_input("Kontaktní osoba", key="zadavatel_kontakt",
                          placeholder="Jan Novák")
        col_tel, col_mail = st.columns(2)
        with col_tel:
            st.text_input("Telefon", key="zadavatel_telefon",
                          placeholder="+420 226 801 200")
        with col_mail:
            st.text_input("E-mail", key="zadavatel_email",
                          placeholder="novak@klient.cz")

    with col_p:
        st.markdown("**Zpracovatel**")
        st.text_input("Odpovědný zástupce", key="zpracovatel_zastupce")
        st.caption(
            "DPU ENERGY s.r.o.  \n"
            "Na Pankráci 1618/30, 140 00 Praha 4  \n"
            "IČO: 017 32 897 | DIČ: CZ01732897  \n"
            "info@DPUenergy.cz"
        )

    st.divider()

    # ── Účel a nastavení ──────────────────────────────────────────────────────
    col_ucel, col_dph = st.columns([3, 1])
    with col_ucel:
        st.selectbox("Účel EP/EA", key="ucel_ep",
                     options=["", "EPC studie", "Dotace OPŽP", "Nová zelená úsporám",
                              "MPO EFEKT", "Zákonná povinnost", "Jiný"])
    with col_dph:
        st.checkbox("Ceny bez DPH", key="ceny_bez_dph")

    st.divider()

    # ── Uložení a načtení projektu ────────────────────────────────────────────
    st.subheader("Uložení a načtení projektu")
    _save_col, _load_col = st.columns(2)

    with _save_col:
        st.markdown("**Uložit projekt**")
        _json_str = _uloz_projekt()
        _proj_name = (
            st.session_state.get("nazev_zakazky", "").strip()
            or "projekt"
        )
        # nahradit znaky nevhodné pro název souboru
        _safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in _proj_name)
        import datetime as _dt
        _fname = f"{_safe_name}_{_dt.date.today().isoformat()}.json"
        st.download_button(
            label="⬇️ Stáhnout projekt (.json)",
            data=_json_str.encode("utf-8"),
            file_name=_fname,
            mime="application/json",
            use_container_width=True,
        )
        _n_obj = len(st.session_state.get("objekty", []))
        st.caption(
            f"Projekt: **{st.session_state.get('nazev_zakazky') or '(bez názvu)'}** | "
            f"{_n_obj} {'objekt' if _n_obj == 1 else 'objekty' if _n_obj < 5 else 'objektů'}"
        )

    with _load_col:
        st.markdown("**Načíst projekt**")
        _upload = st.file_uploader(
            "Nahrát soubor projektu (.json)",
            type="json",
            key="_projekt_upload",
            label_visibility="collapsed",
        )
        if _upload is not None:
            if st.button("📂 Načíst projekt", type="primary", use_container_width=True):
                _err = _nacti_projekt(_upload.read())
                if _err:
                    st.error(_err)
                else:
                    st.success("Projekt načten.")
                    st.rerun()
        st.caption("⚠️ Načtení přepíše veškerá aktuální data projektu.")

    # ── Manažerské shrnutí (aktivního objektu) ────────────────────────────────
    st.divider()
    st.subheader("Manažerské shrnutí objektu")
    _ms_result = build_project().vypocitej()
    _ms_text = _build_executive_summary(_ms_result, st.session_state)
    st.markdown(_ms_text)
    st.text_area(
        "Zkopírovat jako prostý text (Markdown)",
        value=_ms_text,
        height=300,
        label_visibility="collapsed",
        help="Označte vše (Ctrl+A) a zkopírujte do dokumentu.",
        key="_ms_textarea",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Řádek 2 – výběr aktivního objektu
# ══════════════════════════════════════════════════════════════════════════════

st.divider()

_obj_nazvy = [
    st.session_state["objekty"][i].get("objekt_nazev") or f"Objekt {i + 1}"
    for i in range(len(st.session_state["objekty"]))
]
_aktivni_idx = min(
    st.session_state.get("aktivni_objekt_idx", 0),
    len(_obj_nazvy) - 1,
)


def _on_obj_switch() -> None:
    """Callback pro přepnutí aktivního objektu přes selectbox."""
    new_idx = st.session_state["_obj_selectbox"]
    cur_idx = st.session_state.get("aktivni_objekt_idx", 0)
    if new_idx != cur_idx:
        st.session_state["objekty"][cur_idx] = _snapshot_object()
        _load_object(st.session_state["objekty"][new_idx])
        st.session_state["aktivni_objekt_idx"] = new_idx


def _add_object_cb():
    """Callback pro přidání nového objektu – volá se před renderem."""
    _cur = st.session_state.get("aktivni_objekt_idx", 0)
    st.session_state["objekty"][_cur] = _snapshot_object()
    _idx_novy = len(st.session_state["objekty"])
    _novy_obj = {k: copy.deepcopy(DEFAULTS[k]) for k in OBJECT_KEYS if k in DEFAULTS}
    _novy_obj["objekt_nazev"] = f"Objekt {_idx_novy + 1}"
    st.session_state["objekty"].append(_novy_obj)
    _load_object(st.session_state["objekty"][_idx_novy])
    st.session_state["aktivni_objekt_idx"] = _idx_novy


def _del_object_cb():
    """Callback pro smazání aktivního objektu – volá se před renderem."""
    _cur = st.session_state.get("aktivni_objekt_idx", 0)
    st.session_state["objekty"].pop(_cur)
    _new = max(0, _cur - 1)
    st.session_state["aktivni_objekt_idx"] = _new
    _load_object(st.session_state["objekty"][_new])


_obj_col, _add_col, _del_col = st.columns([6, 1, 1])
with _obj_col:
    st.selectbox(
        "Aktivní objekt",
        options=range(len(_obj_nazvy)),
        format_func=lambda i: _obj_nazvy[i],
        index=_aktivni_idx,
        key="_obj_selectbox",
        on_change=_on_obj_switch,
        label_visibility="collapsed",
    )
with _add_col:
    st.button("+ Přidat objekt", key="_obj_add", on_click=_add_object_cb)
with _del_col:
    st.button(
        "🗑 Smazat", key="_obj_del",
        disabled=len(st.session_state["objekty"]) <= 1,
        on_click=_del_object_cb,
    )

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# Řádek 3 – záložky objektu
# ══════════════════════════════════════════════════════════════════════════════

tab_data, tab_op, tab_vysledky, tab_ekonomika, tab_emise, tab_klasifikace, tab_obalka, tab_foto, tab_ea, tab_dotace = st.tabs([
    "📋 Vstupní data",
    "🔧 Opatření",
    "📊 Výsledky",
    "💰 Ekonomika",
    "🌿 Emise",
    "🏗️ Klasifikace",
    "🏗️ Obálka & systémy",
    "📷 Fotodokumentace",
    "📋 EA – rozšíření",
    "🏦 Dotace",
])

# ══════════════════════════════════════════════════════════════════════════════
# OBJECT TAB 0 – Vstupní data (identifikace objektu + spotřeby)
# ══════════════════════════════════════════════════════════════════════════════

with tab_data:

    # ── Import PENB ───────────────────────────────────────────────────────────
    with st.expander("⬆️ Import PENB / Svoboda SW", expanded=False):
        st.caption("Automaticky vyplní plochy, U-hodnoty a baseline spotřeby pro tento objekt.")
        _penb_file = st.file_uploader(
            "Nahrát PENB nebo výpočet Svoboda SW (PDF)",
            type="pdf",
            key="_penb_upload",
        )
        if _penb_file is not None:
            if st.button("Importovat", key="_penb_import_btn", type="primary"):
                try:
                    import io as _io
                    _penb_data = _parse_penb_pdf(_io.BytesIO(_penb_file.read()))
                    _updates = _penb_na_session_state(_penb_data)
                    for _k, _v in _updates.items():
                        if _k in OBJECT_KEYS:
                            st.session_state[_k] = _v
                    _n_kce = len(_penb_data.konstrukce)
                    st.success(
                        f"Importováno ({_penb_data.zdroj}): "
                        f"{_n_kce} konstrukcí, "
                        f"ZP {_penb_data.zp_mwh:.0f} MWh, "
                        f"EE {_penb_data.ee_mwh:.0f} MWh"
                    )
                    st.rerun()
                except Exception as _e:
                    st.error(f"Chyba při parsování PENB: {_e}")

    st.divider()

    # ── Identifikace objektu ──────────────────────────────────────────────────
    st.subheader("Identifikace objektu")
    col_id1, col_id2 = st.columns([2, 1])
    with col_id1:
        st.text_input("Název objektu", key="objekt_nazev",
                      placeholder="ZŠ Politických vězňů")
        st.text_input("Adresa objektu", key="objekt_adresa",
                      placeholder="Politických vězňů 9, 110 00 Praha 1")
        st.text_input("Druh činnosti", key="druh_cinnosti",
                      placeholder="Základní škola")
        st.text_input("Počet zaměstnanců / uživatelů", key="pocet_zamestnancu",
                      placeholder="84 zaměstnanců / 678 žáků")
    with col_id2:
        st.text_area("Provozní režim", key="provozni_rezim", height=120,
                     placeholder="Školní rok září–červen, Po–Pá 6:00–16:30")
    st.text_area("Předmět analýzy", key="predmet_analyzy", height=80)

    with st.expander("Katastr a evidenční čísla (volitelné)", expanded=False):
        col_ka, col_par = st.columns(2)
        with col_ka:
            st.text_input("Katastrální území", key="objekt_ku",
                          placeholder="Praha-Dejvice")
        with col_par:
            st.text_input("Parcelní číslo", key="objekt_parcelni_cislo",
                          placeholder="1234/5")
        col_enex, col_op = st.columns(2)
        with col_enex:
            st.text_input("Evidenční číslo (ENEX)", key="evidencni_cislo",
                          placeholder="ENEX-001")
        with col_op:
            st.text_input("Číslo oprávnění specialisty", key="cislo_opravneni",
                          placeholder="OP-12345")

    st.divider()

    # ── Parametry vytápěných budov ────────────────────────────────────────────
    st.subheader("Parametry vytápěných budov")
    st.caption("Faktor tvaru A/V se vypočítá automaticky.")

    budovy = st.session_state["budovy"]
    updated_budovy = []
    for i, b in enumerate(budovy):
        st.markdown(f"**Budova {i + 1}**")
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 0.4])
        with c1:
            nazev = st.text_input("Název", value=b["nazev"],
                                  key=f"bud_{i}_nazev", placeholder="Hlavní objekt")
        with c2:
            objem = st.number_input("Objem [m³]", value=b["objem_m3"],
                                    min_value=0.0, step=100.0, key=f"bud_{i}_objem")
        with c3:
            plocha = st.number_input("Vytáp. plocha [m²]", value=b["plocha_m2"],
                                     min_value=0.0, step=50.0, key=f"bud_{i}_plocha")
        with c4:
            ochlaz = st.number_input("Ochl. plocha [m²]", value=b["ochlaz_m2"],
                                     min_value=0.0, step=50.0, key=f"bud_{i}_ochlaz")
        with c5:
            av = ochlaz / objem if objem > 0 else 0.0
            st.metric("A/V", f"{av:.2f}")
        updated_budovy.append({"nazev": nazev, "objem_m3": objem,
                                "plocha_m2": plocha, "ochlaz_m2": ochlaz})

    col_btn1, col_btn2, _ = st.columns([1, 1, 4])
    with col_btn1:
        if st.button("+ Přidat budovu"):
            updated_budovy.append({"nazev": "", "objem_m3": 0.0,
                                   "plocha_m2": 0.0, "ochlaz_m2": 0.0})
    with col_btn2:
        if st.button("− Odebrat poslední") and len(updated_budovy) > 1:
            updated_budovy.pop()
    st.session_state["budovy"] = updated_budovy

    # ── Obálka budovy – Uem stávající ─────────────────────────────────────────
    _budovy_ob = st.session_state.get("budovy", [])
    _objem_ob = sum(b.get("objem_m3", 0.0) for b in _budovy_ob)
    _obalka_ob = sum(b.get("ochlaz_m2", 0.0) for b in _budovy_ob)
    _uem_col1, _uem_col2, _uem_col3 = st.columns([2, 1, 1])
    with _uem_col1:
        st.number_input(
            "Uem stávající [W/m²K]",
            key="uem_stav",
            min_value=0.0, max_value=5.0, step=0.01, format="%.3f",
            help="Průměrný součinitel prostupu tepla obálky budovy (z PENB nebo výpočtu)",
        )
    if _objem_ob > 0 and _obalka_ob > 0:
        from epc_engine.building_class import vypocitej_uem_n, klasifikuj_uem
        _ft_ob = _obalka_ob / _objem_ob
        _uem_n_ob = vypocitej_uem_n(_ft_ob)
        _uem_ob = st.session_state.get("uem_stav", 0.0)
        _trida_ob = klasifikuj_uem(_uem_ob, _uem_n_ob) if _uem_ob > 0 else "–"
        with _uem_col2:
            st.metric("Uem,N [W/m²K]", f"{_uem_n_ob:.3f}")
        with _uem_col3:
            st.metric("Třída obálky", _trida_ob)

    st.divider()

    # ── Prostory ──────────────────────────────────────────────────────────────
    st.subheader("Seznam a využití prostor")

    prostory = st.session_state["prostory"]
    updated_prostory = []
    for i, p in enumerate(prostory):
        c1, c2, c3 = st.columns([2, 2, 2])
        with c1:
            nazev = st.text_input("Část objektu", value=p["nazev"],
                                  key=f"pros_{i}_nazev",
                                  placeholder="Třídy" if i == 0 else "")
        with c2:
            ucel = st.text_input("Účel využití", value=p["ucel"],
                                 key=f"pros_{i}_ucel",
                                 placeholder="Výuka" if i == 0 else "")
        with c3:
            provoz = st.text_input("Doba provozu", value=p["provoz"],
                                   key=f"pros_{i}_provoz",
                                   placeholder="Po–Pá 7:00–17:00" if i == 0 else "")
        updated_prostory.append({"nazev": nazev, "ucel": ucel, "provoz": provoz})

    col_btn3, col_btn4, _ = st.columns([1, 1, 4])
    with col_btn3:
        if st.button("+ Přidat prostor"):
            updated_prostory.append({"nazev": "", "ucel": "", "provoz": ""})
    with col_btn4:
        if st.button("− Odebrat poslední ", key="rm_pros") and len(updated_prostory) > 1:
            updated_prostory.pop()
    st.session_state["prostory"] = updated_prostory

    st.divider()

    # ── Vstupní podklady ──────────────────────────────────────────────────────
    st.subheader("Seznam obdržených podkladů")

    podklady = st.session_state["podklady"]
    updated_podklady = []
    for i, p in enumerate(podklady):
        c1, c2, c3 = st.columns([0.06, 3, 0.4])
        with c1:
            ok = st.checkbox("", value=p["ok"], key=f"pod_{i}_ok",
                             label_visibility="collapsed")
        with c2:
            nazev = st.text_input("", value=p["nazev"], key=f"pod_{i}_nazev",
                                  label_visibility="collapsed")
        with c3:
            rm = st.button("✕", key=f"pod_{i}_rm", help="Odebrat")
        if not rm:
            updated_podklady.append({"nazev": nazev, "ok": ok})

    if st.button("+ Přidat podklad"):
        updated_podklady.append({"nazev": "", "ok": False})
    st.session_state["podklady"] = updated_podklady

    st.text_area("Poznámka k podkladům", key="poznamka_podklady", height=60)

    st.divider()

    # ── Popis stávajícího stavu ───────────────────────────────────────────────
    st.subheader("Popis stávajícího stavu")
    st.caption(
        "Popis technických soustav a stavebního stavu objektu. "
        "Data z Osvětlení se použijí v kalkulaci OP10."
    )
    st.page_link("pages/Popis_stavajiciho_stavu.py", label="Otevřít popis stávajícího stavu", icon="📋")

    # Náhled – přehled osvětlení pokud jsou data
    _osv_preview = st.session_state.get("sys_osv_zony", [])
    _osv_prev_mwh = sum(
        z.get("prikon_kw", 0) * z.get("hodiny_rok", 0) / 1000
        for z in _osv_preview if z.get("prikon_kw", 0) > 0
    )
    if _osv_prev_mwh > 0:
        st.caption(
            f"Osvětlení: {len([z for z in _osv_preview if z.get('prikon_kw', 0) > 0])} zón, "
            f"odhadovaná spotřeba {_osv_prev_mwh:.1f} MWh/rok"
        )

    st.divider()

    # ── Energonosiče pro vytápění ─────────────────────────────────────────────
    st.subheader("Energonosiče a okrajové podmínky")
    _en_col1, _en_col2 = st.columns(2)
    with _en_col1:
        st.checkbox("Zemní plyn (ZP)", key="nosic_zp")
        st.checkbox("Teplo (CZT)", key="nosic_czt")
    # Odvoď legacy klíč nosic pro kompatibilitu
    if st.session_state["nosic_zp"] and not st.session_state["nosic_czt"]:
        st.session_state["nosic"] = "Zemní plyn"
    elif st.session_state["nosic_czt"] and not st.session_state["nosic_zp"]:
        st.session_state["nosic"] = "Teplo (CZT)"
    elif st.session_state["nosic_zp"] and st.session_state["nosic_czt"]:
        st.session_state["nosic"] = "Kombinace ZP + CZT"
    else:
        st.session_state["nosic"] = "Zemní plyn"

    # ── Okrajové podmínky ─────────────────────────────────────────────────────
    _ok_col1, _ok_col2, _ok_col3 = st.columns([1, 1, 2])
    with _ok_col1:
        st.number_input("θi [°C]", step=0.5, key="theta_i",
                        help="Vnitřní výpočtová teplota")
    with _ok_col2:
        st.number_input("θe [°C]", step=1.0, key="theta_e",
                        help="Venkovní výpočtová teplota")
    with _ok_col3:
        from epc_engine.physics import nazvy_lokalit as _naz_lok
        _lok_list = _naz_lok()
        _lok_idx = _lok_list.index(st.session_state.get("lokalita_projekt", "Praha (Karlov)")) \
                   if st.session_state.get("lokalita_projekt", "Praha (Karlov)") in _lok_list else 45
        st.selectbox("Lokalita", _lok_list, index=_lok_idx, key="lokalita_projekt")

    _delta_T = st.session_state["theta_i"] - st.session_state["theta_e"]
    _phi_val = st.session_state.get("phi_total_kw", 0.0)
    _phi_info = f"  |  Φ = {_phi_val:.0f} kW (z Fyz. kalkulátoru)" if _phi_val > 0 else ""
    st.caption(f"ΔT = {_delta_T:.0f} K{_phi_info}")

    st.divider()

    # ── Spotřeby ──────────────────────────────────────────────────────────────
    pouzit_zp = st.session_state.get("nosic_zp", True)
    pouzit_teplo = st.session_state.get("nosic_czt", False)
    if not pouzit_zp and not pouzit_teplo:
        pouzit_zp = True

    # ── Denostupně – referenční hodnota z vybrané lokality ────────────────────
    _lok_nazev_p = st.session_state.get("lokalita_projekt", "Praha (Karlov)")
    _theta_i_p   = st.session_state.get("theta_i", 21.0)
    try:
        _lok_p = _lokalita_fn(_lok_nazev_p)
        _D_ref_long = round(_lok_p.d13 * (_theta_i_p - _lok_p.tes13), 0)
    except Exception:
        _D_ref_long = 3200.0

    # ── Vstupní data po rocích ────────────────────────────────────────────────
    st.subheader("Vstupní data po rocích")
    st.caption(
        "Zadejte skutečné spotřeby pro každý referenční rok. "
        "Sloupec **D [K·day]** se automaticky vyplní z databáze dle lokality a roku "
        "(lze přepsat). Spotřeba tepla na ÚT je normována poměrem D_ref / D_rok; "
        "TUV, EE a voda se nemění."
    )

    import pandas as pd

    _roky = list(st.session_state.get("roky_spotreby", []))

    # Sestavení sloupců tabulky dle aktivních energonosičů
    _col_cfg: dict = {
        "Rok": st.column_config.NumberColumn("Rok", min_value=1990, max_value=2100, step=1, format="%d"),
    }
    if pouzit_zp:
        _col_cfg["ZP ÚT [MWh]"]  = st.column_config.NumberColumn("ZP ÚT [MWh]",  min_value=0.0, step=1.0, format="%.1f")
        _col_cfg["ZP TUV [MWh]"] = st.column_config.NumberColumn("ZP TUV [MWh]", min_value=0.0, step=1.0, format="%.1f")
    if pouzit_teplo:
        _col_cfg["Teplo ÚT [MWh]"]  = st.column_config.NumberColumn("Teplo ÚT [MWh]",  min_value=0.0, step=1.0, format="%.1f")
        _col_cfg["Teplo TUV [MWh]"] = st.column_config.NumberColumn("Teplo TUV [MWh]", min_value=0.0, step=1.0, format="%.1f")
    _col_cfg["EE [MWh]"]  = st.column_config.NumberColumn("EE [MWh]",  min_value=0.0, step=1.0, format="%.1f")
    _col_cfg["Voda [m³]"] = st.column_config.NumberColumn("Voda [m³]", min_value=0.0, step=10.0, format="%.0f")
    _col_cfg["D [K·day]"] = st.column_config.NumberColumn(
        "D [K·day]",
        min_value=0.0, step=10.0, format="%.0f",
        help=(
            "Skutečné denostupně daného roku (auto z lokality + korekce dle ČHMÚ). "
            "Lze přepsat vlastní hodnotou. "
            f"Dlouhodobý průměr {_lok_nazev_p}: {_D_ref_long:.0f} K·day."
        ),
    )

    # Auto-výpočet D pro každý rok (přepíše jen nuly)
    def _auto_D(rok: int) -> float:
        try:
            return _denostupne_rok_fn(_lok_nazev_p, rok, theta_i=_theta_i_p, tem=13)
        except Exception:
            return _D_ref_long

    # DataFrame pro editor – D se auto-vyplní pokud je 0
    def _roky_to_df(roky: list[dict]) -> "pd.DataFrame":
        rows = []
        for r in roky:
            rok = int(r.get("rok", 2022))
            D_saved = float(r.get("D", 0.0))
            row = {"Rok": rok}
            if pouzit_zp:
                row["ZP ÚT [MWh]"]  = float(r.get("zp_ut",  0.0))
                row["ZP TUV [MWh]"] = float(r.get("zp_tuv", 0.0))
            if pouzit_teplo:
                row["Teplo ÚT [MWh]"]  = float(r.get("teplo_ut",  0.0))
                row["Teplo TUV [MWh]"] = float(r.get("teplo_tuv", 0.0))
            row["EE [MWh]"]  = float(r.get("ee",   0.0))
            row["Voda [m³]"] = float(r.get("voda", 0.0))
            row["D [K·day]"] = D_saved if D_saved > 0 else _auto_D(rok)
            rows.append(row)
        return pd.DataFrame(rows)

    _df_roky = _roky_to_df(_roky)

    _btn_add, _btn_del = st.columns([1, 1])
    with _btn_add:
        if st.button("+ Přidat rok", key="_roky_add"):
            _next_rok = (max(int(r.get("rok", 2024)) for r in _roky) + 1) if _roky else 2025
            _roky.append({"rok": _next_rok, "zp_ut": 0.0, "zp_tuv": 0.0,
                          "teplo_ut": 0.0, "teplo_tuv": 0.0, "ee": 0.0, "voda": 0.0, "D": 0.0})
            st.session_state["roky_spotreby"] = _roky
            st.rerun()
    with _btn_del:
        if len(_roky) > 1 and st.button("✕ Odebrat poslední rok", key="_roky_del"):
            _roky.pop()
            st.session_state["roky_spotreby"] = _roky
            st.rerun()

    _edited_df = st.data_editor(
        _df_roky,
        column_config=_col_cfg,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="_roky_editor",
    )

    # Uložit zpět do session_state (D se ukládá tak jak ji uživatel vidí)
    _roky_new: list[dict] = []
    for _, row in _edited_df.iterrows():
        _roky_new.append({
            "rok":       int(row["Rok"]),
            "zp_ut":     float(row.get("ZP ÚT [MWh]",  0.0)),
            "zp_tuv":    float(row.get("ZP TUV [MWh]", 0.0)),
            "teplo_ut":  float(row.get("Teplo ÚT [MWh]",  0.0)),
            "teplo_tuv": float(row.get("Teplo TUV [MWh]", 0.0)),
            "ee":        float(row.get("EE [MWh]",  0.0)),
            "voda":      float(row.get("Voda [m³]", 0.0)),
            "D":         float(row.get("D [K·day]", 0.0)),
        })
    st.session_state["roky_spotreby"] = _roky_new

    # Zobraz použité D hodnoty a zda jsou z databáze nebo vlastní
    _D_info = []
    for r in _roky_new:
        _D_auto = _auto_D(r["rok"])
        _is_auto = abs(r["D"] - _D_auto) < 1.0
        _korekce = _ROCNI_KOREKCE_D.get(r["rok"])
        _D_info.append(
            f"**{r['rok']}**: D = {r['D']:.0f} K·day "
            + (f"(aut., k={_korekce:.2f})" if _is_auto and _korekce else
               "(aut., průměr)" if _is_auto else "(vlastní)")
        )
    st.caption("  |  ".join(_D_info))

    # ── Normalizace a průměr ───────────────────────────────────────────────────
    st.caption(f"D_ref (dlouhodobý průměr): **{_D_ref_long:.0f} K·day** ({_lok_nazev_p}, tem=13 °C, θi={_theta_i_p:.0f} °C)")

    _platne = [r for r in _roky_new if r["D"] > 0 and (
        r["zp_ut"] + r["zp_tuv"] + r["teplo_ut"] + r["teplo_tuv"] + r["ee"] > 0)]

    if _platne:
        _norm_rows = []
        for r in _platne:
            _f = _D_ref_long / r["D"]
            _norm_rows.append({
                "Rok": r["rok"],
                "k = D_ref/D": round(_f, 3),
                **({"ZP ÚT norm [MWh]":  round(r["zp_ut"]    * _f, 1)} if pouzit_zp    else {}),
                **({"ZP TUV [MWh]":      round(r["zp_tuv"],      1)} if pouzit_zp    else {}),
                **({"Teplo ÚT norm [MWh]": round(r["teplo_ut"] * _f, 1)} if pouzit_teplo else {}),
                **({"Teplo TUV [MWh]":    round(r["teplo_tuv"],   1)} if pouzit_teplo else {}),
                "EE [MWh]":   round(r["ee"],  1),
                "Voda [m³]":  round(r["voda"], 0),
            })
        _norm_df = pd.DataFrame(_norm_rows)
        with st.expander("Normalizované hodnoty a průměry", expanded=True):
            st.dataframe(_norm_df, use_container_width=True, hide_index=True)

            # Průměry
            def _mean_norm(key: str) -> float:
                vals = [r[key] for r in _norm_rows if key in r and r[key] is not None]
                return round(sum(vals) / len(vals), 1) if vals else 0.0

            _avg = {
                "zp_ut":     _mean_norm("ZP ÚT norm [MWh]"),
                "zp_tuv":    _mean_norm("ZP TUV [MWh]"),
                "teplo_ut":  _mean_norm("Teplo ÚT norm [MWh]"),
                "teplo_tuv": _mean_norm("Teplo TUV [MWh]"),
                "ee":        _mean_norm("EE [MWh]"),
                "voda":      _mean_norm("Voda [m³]"),
            }
            st.caption("**Průměr normalizovaných hodnot:**")
            _avg_cols = st.columns(6)
            _avg_labels = [
                ("ZP ÚT", "zp_ut", "MWh", pouzit_zp),
                ("ZP TUV", "zp_tuv", "MWh", pouzit_zp),
                ("Teplo ÚT", "teplo_ut", "MWh", pouzit_teplo),
                ("Teplo TUV", "teplo_tuv", "MWh", pouzit_teplo),
                ("EE", "ee", "MWh", True),
                ("Voda", "voda", "m³", True),
            ]
            for _c, (_lbl, _key, _jed, _show) in zip(_avg_cols, _avg_labels):
                if _show:
                    _c.metric(f"{_lbl} [{_jed}]", f"{_avg[_key]:.1f}")

            if st.button(
                "Použít průměry jako referenční spotřeby",
                type="primary", key="_roky_apply_avg",
            ):
                for _key in ("zp_ut", "zp_tuv", "teplo_ut", "teplo_tuv", "ee"):
                    if _avg[_key] > 0:
                        st.session_state[_key] = _avg[_key]
                if _avg["voda"] > 0:
                    st.session_state["voda"] = _avg["voda"]
                st.success("Referenční spotřeby aktualizovány z normalizovaných průměrů.")

    # ── Pomůcka: rozdělení ZP celkem na ÚT a TUV ────────────────────────────
    with st.expander("Pomůcka: rozdělení ZP/tepla na ÚT a TUV", expanded=False):
        st.caption(
            "Pokud nemáte oddělené měření ÚT a TUV, odhadněte podíl některou z metod níže."
        )
        _split_met = st.radio(
            "Metoda",
            ["Letní základ (z měsíčních dat)", "Zadáním očekávané TUV spotřeby"],
            horizontal=True, key="_split_met",
        )

        if _split_met == "Letní základ (z měsíčních dat)":
            st.caption(
                "Průměrná spotřeba v červnu–srpnu (bez vytápění) = základní TUV. "
                "Roční TUV ≈ letní průměr × 12. ÚT = celkem − TUV."
            )
            _nosic_key_m = "zp_ut_mesice" if pouzit_zp else "teplo_ut_mesice"
            _mesice_data = st.session_state.get(_nosic_key_m, [0.0] * 12)
            _letni = [float(_mesice_data[i]) for i in [5, 6, 7]]  # červen, červenec, srpen
            _letni_prumer = sum(_letni) / 3 if any(v > 0 for v in _letni) else 0.0
            _tuv_odhad  = round(_letni_prumer * 12, 1)
            _celkem_zp  = st.session_state.get("zp_ut", 0.0) + st.session_state.get("zp_tuv", 0.0)
            if _celkem_zp == 0:
                _celkem_zp = st.session_state.get("teplo_ut", 0.0) + st.session_state.get("teplo_tuv", 0.0)
            _ut_odhad   = round(max(0.0, _celkem_zp - _tuv_odhad), 1)

            if _letni_prumer > 0:
                _sc1, _sc2, _sc3 = st.columns(3)
                _sc1.metric("Letní průměr [MWh/měsíc]", f"{_letni_prumer:.1f}")
                _sc2.metric("TUV odhad [MWh/rok]",  f"{_tuv_odhad:.1f}")
                _sc3.metric("ÚT odhad [MWh/rok]",   f"{_ut_odhad:.1f}")
                if st.button("Přenést do ZP ÚT / ZP TUV", key="_split_apply_letni"):
                    if pouzit_zp:
                        st.session_state["zp_ut"]  = _ut_odhad
                        st.session_state["zp_tuv"] = _tuv_odhad
                    else:
                        st.session_state["teplo_ut"]  = _ut_odhad
                        st.session_state["teplo_tuv"] = _tuv_odhad
                    st.success("Hodnoty přeneseny do referenčních spotřeb.")
            else:
                st.info("Vyplňte měsíční průběh spotřeby (červen–srpen) v sekci Měsíční rozpad níže.")

        else:  # Zadáním TUV
            st.caption(
                "Zadejte celkovou spotřebu energonosiče a odhadovanou roční spotřebu TUV. "
                "ÚT = celkem − TUV."
            )
            _celkem_inp = st.number_input(
                "Celková spotřeba ZP/tepla [MWh/rok]", min_value=0.0, step=10.0,
                key="_split_celkem",
            )
            # Auto-nabídnout výsledek z Fyzikálního kalkulátoru pokud je k dispozici
            _tuv_from_calc = st.session_state.get("_tuv_calc_mwh", 0.0)
            if _tuv_from_calc > 0:
                st.info(
                    f"Fyzikální kalkulátor spočítal Q_TUV = **{_tuv_from_calc:.1f} MWh/rok**. "
                    "Klikněte pro předvyplnění pole níže."
                )
                if st.button(f"Použít {_tuv_from_calc:.1f} MWh/rok z kalkulátoru", key="_split_use_calc"):
                    st.session_state["_split_tuv_inp"] = _tuv_from_calc
                    st.rerun()
            else:
                st.page_link(
                    "pages/Fyzikální_kalkulátor.py",
                    label="Otevřít Fyzikální kalkulátor → záložka Potřeba tepla – TUV",
                )
            _tuv_inp = st.number_input(
                "Očekávaná TUV [MWh/rok]",
                min_value=0.0, step=5.0, key="_split_tuv_inp",
                help="Výsledek z Fyzikálního kalkulátoru → záložka Potřeba tepla – TUV",
            )
            if _celkem_inp > 0:
                _ut_inp = round(max(0.0, _celkem_inp - _tuv_inp), 1)
                _si1, _si2 = st.columns(2)
                _si1.metric("ÚT [MWh/rok]",  f"{_ut_inp:.1f}")
                _si2.metric("TUV [MWh/rok]", f"{_tuv_inp:.1f}")
                if st.button("Přenést do ZP ÚT / ZP TUV", key="_split_apply_tuv"):
                    if pouzit_zp:
                        st.session_state["zp_ut"]  = _ut_inp
                        st.session_state["zp_tuv"] = _tuv_inp
                    else:
                        st.session_state["teplo_ut"]  = _ut_inp
                        st.session_state["teplo_tuv"] = _tuv_inp
                    st.success("Hodnoty přeneseny.")

    st.divider()

    st.subheader("Referenční spotřeby")
    st.caption(
        "Spotřeby tepla a ZP pro ÚT musí být normovány dle denostupňů "
        "(odpovídá listu Denostupně v Excel šabloně)."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if pouzit_zp:
            st.markdown("**Zemní plyn**")
            st.number_input(
                "ZP – ústřední vytápění [MWh/rok]",
                min_value=0.0, step=10.0, key="zp_ut",
            )
            st.number_input(
                "ZP – příprava TUV [MWh/rok]",
                min_value=0.0, step=5.0, key="zp_tuv",
            )
        if pouzit_teplo:
            st.markdown("**Teplo (CZT)**")
            st.number_input(
                "Teplo ÚT [MWh/rok]",
                min_value=0.0, step=10.0, key="teplo_ut",
            )
            st.number_input(
                "Teplo TUV [MWh/rok]",
                min_value=0.0, step=5.0, key="teplo_tuv",
            )

    with col2:
        st.markdown("**Elektrická energie**")
        st.number_input("EE [MWh/rok]", min_value=0.0, step=5.0, key="ee")
        st.markdown("**Voda**")
        st.number_input("Vodné a stočné [m³/rok]", min_value=0.0, step=50.0, key="voda")
        st.number_input("Srážkový poplatek [m³/rok]", min_value=0.0, step=10.0, key="srazky")

    with col3:
        st.markdown("**Referenční ceny**")
        if pouzit_zp:
            st.number_input("Cena ZP [Kč/MWh]", min_value=0.0, step=100.0, key="cena_zp")
        if pouzit_teplo:
            st.number_input("Cena tepla CZT [Kč/MWh]", min_value=0.0, step=100.0, key="cena_teplo")
        st.number_input("Cena EE [Kč/MWh]", min_value=0.0, step=100.0, key="cena_ee",
                        help="Celková cena včetně distribuce a daní [Kč/MWh]")
        st.number_input("Výkupní cena FVE [Kč/MWh]", min_value=0.0, step=50.0, key="cena_ee_vykup")
        st.number_input("Vodné a stočné [Kč/m³]", min_value=0.0, step=5.0, key="cena_voda")
        st.number_input("Srážkový poplatek [Kč/m³]", min_value=0.0, step=5.0, key="cena_srazky")

    # ── Pomocník pro cenu EE ──────────────────────────────────────────────────
    with st.expander("Pomocník pro cenu EE (distribuční sazba)"):
        st.caption(
            "Orientační přepočet tarifu na Kč/MWh. "
            "Pro přesný výpočet použijte kalkulačku sazeb."
        )
        _TARIFY = {
            "– vyberte –": None,
            "D01d / C01d – maloodběr, 1 pásmo (cca 5 500 Kč/MWh)": 5_500,
            "D02d / C02d – maloodběr, 2 pásma NT (cca 4 200 Kč/MWh)": 4_200,
            "D25d – přímotopy (cca 3 100 Kč/MWh)": 3_100,
            "D26d – akumulační vytápění (cca 2 800 Kč/MWh)": 2_800,
            "C03d – maloodběr 3f, 1 pásmo (cca 4 800 Kč/MWh)": 4_800,
            "C25d – pohon elektrické trakce (cca 2 500 Kč/MWh)": 2_500,
            "Střední odběr / VN (cca 2 200–3 500 Kč/MWh)": 2_800,
        }
        _tar_sel = st.selectbox("Distribuční sazba", list(_TARIFY.keys()),
                                key="_tar_helper")
        _tar_val = _TARIFY[_tar_sel]
        if _tar_val:
            st.info(f"Orientační cena: **{_tar_val:,} Kč/MWh**".replace(",", "\u00a0"))
            if st.button("Přenést do pole Cena EE", key="_tar_apply"):
                st.session_state["cena_ee"] = float(_tar_val)
                st.rerun()
        st.page_link(
            "https://calm-cocada-79e019.netlify.app/sazby/",
            label="Otevřít kalkulačku sazeb (DPU Energy)",
        )

    st.divider()

    # ── Měsíční rozpad spotřeby ───────────────────────────────────────────────
    st.subheader("Měsíční rozpad spotřeby")
    st.caption(
        "Volitelný doplněk k ročním hodnotám výše. "
        "Slouží pro ověření sezónního profilu a identifikaci anomálií."
    )

    _MESICE = ["Led", "Úno", "Bře", "Dub", "Kvě", "Čvn",
               "Čvc", "Srp", "Zář", "Říj", "Lis", "Pro"]

    def _mesicni_sekce(label: str, key_mesice: str, key_rocni: str,
                       jednotka: str = "MWh"):
        """Zobrazí 12 number_inputů v řádku a sloupcový graf."""
        hodnoty = list(st.session_state.get(key_mesice, [0.0] * 12))
        rocni = st.session_state.get(key_rocni, 0.0)
        celkem = sum(hodnoty)

        cols_m = st.columns(12)
        for i, col in enumerate(cols_m):
            with col:
                hodnoty[i] = st.number_input(
                    _MESICE[i], value=float(hodnoty[i]),
                    min_value=0.0, step=1.0, format="%.1f",
                    key=f"_m_{key_mesice}_{i}",
                    label_visibility="visible",
                )
        st.session_state[key_mesice] = hodnoty

        if celkem > 0:
            _diff = rocni - celkem
            _status = (f"Součet: {celkem:.1f} {jednotka} | Roční: {rocni:.1f} {jednotka} | "
                       f"Rozdíl: {_diff:+.1f} {jednotka}")
            if abs(_diff) > rocni * 0.05 and rocni > 0:
                st.warning(_status)
            else:
                st.caption(_status)

            _fig = go.Figure(go.Bar(x=_MESICE, y=hodnoty, name=label))
            _fig.update_layout(height=200, margin=dict(t=0, b=0, l=0, r=0),
                               showlegend=False)
            st.plotly_chart(_fig, use_container_width=True)
        st.caption(
            "[Načíst profil z DPU Hub](https://profily-13vt-5btc9taff-dpuenergys-projects.vercel.app/"
            "?dpu_user=hridel%40dpuenergy.cz)"
        )

    if pouzit_zp:
        with st.expander("ZP – ústřední vytápění [MWh/měsíc]"):
            _mesicni_sekce("ZP ÚT", "zp_ut_mesice", "zp_ut")
        with st.expander("ZP – příprava TUV [MWh/měsíc]"):
            _mesicni_sekce("ZP TUV", "zp_tuv_mesice", "zp_tuv")

    if pouzit_teplo:
        with st.expander("Teplo CZT – ústřední vytápění [MWh/měsíc]"):
            _mesicni_sekce("Teplo ÚT", "teplo_ut_mesice", "teplo_ut")
        with st.expander("Teplo CZT – příprava TUV [MWh/měsíc]"):
            _mesicni_sekce("Teplo TUV", "teplo_tuv_mesice", "teplo_tuv")

    with st.expander("Elektrická energie [MWh/měsíc]"):
        _mesicni_sekce("EE", "ee_mesice", "ee")

    with st.expander("Vodné a stočné [m³/měsíc]"):
        _mesicni_sekce("Voda", "voda_mesice", "voda", "m³")

    # Přehled referenčních nákladů
    st.divider()
    st.subheader("Referenční náklady (výchozí stav)")

    e_preview = build_project().energie
    mc1, mc2, mc3, mc4 = st.columns(4)

    with mc1:
        val = (e_preview.teplo_total * e_preview.cena_teplo if e_preview.pouzit_teplo
               else e_preview.zp_total * e_preview.cena_zp)
        label = "Teplo/ZP" if pouzit_zp else "Teplo CZT"
        st.metric(label, fmt_kc(val))
    with mc2:
        st.metric("Elektrická energie", fmt_kc(e_preview.ee * e_preview.cena_ee))
    with mc3:
        st.metric("Voda", fmt_kc(e_preview.voda * e_preview.cena_voda))
    with mc4:
        st.metric("Celkem", fmt_kc(e_preview.celkove_naklady))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – Opatření
# ══════════════════════════════════════════════════════════════════════════════

with tab_op:
    pouzit_zp = st.session_state.get("nosic_zp", True)
    pouzit_teplo_op = st.session_state.get("nosic_czt", False)
    if not pouzit_zp and not pouzit_teplo_op:
        pouzit_zp = True
    if pouzit_zp and pouzit_teplo_op:
        nosic_label = "ZP / Teplo"
    elif pouzit_teplo_op:
        nosic_label = "Teplo"
    else:
        nosic_label = "ZP"

    # Denostupně pro živý náhled výpočtu zateplení
    try:
        _lok_op = _lokalita_fn(st.session_state.get("lokalita_projekt", "Praha (Karlov)"))
        _D_op = _lok_op.denostupne(theta_i=st.session_state.get("theta_i", 21.0), tem=13)
    except ValueError:
        _D_op = 0.0

    # ── pomocná funkce pro textaci opatření ──────────────────────────────────
    def op_textace(op_id: str):
        """Zobrazí expander s textací popis + dotace + požadované podklady z OP_INFO."""
        info = OP_INFO.get(op_id, {})
        if not info:
            return
        with st.expander("Popis opatření, dotační požadavky a podklady"):
            st.markdown(info.get("popis", ""))
            dotace = info.get("dotace")
            if dotace:
                st.markdown("**Požadavky dotačních programů:**")
                st.markdown(dotace)
            # Podklady specifické pro toto opatření
            podklady = OP_PODKLADY.get(op_id, [])
            if podklady:
                st.markdown("**Požadované podklady od zadavatele:**")
                for p in podklady:
                    _flag = " *(pouze při dotaci)*" if p["dotace_only"] else ""
                    _nahradni = f" – pokud zákazník nemá: **{p['nahradni']}** ({p['role']})" if p["nahradni"] != "—" else ""
                    st.markdown(
                        f"- **{p['cinnost']}**{_flag}  \n"
                        f"  Zajišťuje: {p['zajisteni']}{_nahradni}"
                    )

    # ── pomocná funkce pro kompaktní záhlaví opatření ────────────────────────
    def op_header(op_id: str, title: str, on_key: str) -> bool:
        col_check, col_title = st.columns([0.05, 0.95])
        with col_check:
            return st.checkbox("", key=on_key, label_visibility="collapsed")
        with col_title:
            st.markdown(f"**{op_id}** – {title}")

    # ── Checklist podkladů pro aktivní opatření ──────────────────────────────
    with st.expander("📋 Checklist podkladů pro zadavatele", expanded=False):
        st.caption(
            "Agregovaný přehled podkladů, které musí zajistit zadavatel pro aktivní opatření. "
            "Opatření aktivujte zaškrtnutím níže, checklist se aktualizuje automaticky."
        )

        # Zjisti aktivní OP z session state
        _aktivni_op_ids_check = [
            op_id for op_id in OP_PODKLADY
            if st.session_state.get(f"{op_id.lower()}_on", False)
               or st.session_state.get(f"op_{op_id.lower()}_on", False)
               or st.session_state.get(f"{op_id}_on", False)
        ]

        import pandas as _pd_check
        _check_rows = []

        # Obecné podklady (vždy)
        for _p in OP_PODKLADY_OBECNE:
            _check_rows.append({
                "Opatření": "Všechna",
                "Podklad": _p["cinnost"],
                "Zajišťuje": _p["zajisteni"],
                "Náhradně": _p["nahradni"] if _p["nahradni"] != "—" else "—",
                "Role": _p["role"],
                "Pouze při dotaci": "Ano" if _p["dotace_only"] else "Ne",
            })

        # Per-opatření podklady pro aktivní OP
        _seen = set()
        for _op_id in _aktivni_op_ids_check:
            for _p in OP_PODKLADY.get(_op_id, []):
                _key = (_p["cinnost"], _p["zajisteni"])
                if _key in _seen:
                    continue  # de-duplikace stejných podkladů
                _seen.add(_key)
                _check_rows.append({
                    "Opatření": _op_id,
                    "Podklad": _p["cinnost"],
                    "Zajišťuje": _p["zajisteni"],
                    "Náhradně": _p["nahradni"] if _p["nahradni"] != "—" else "—",
                    "Role": _p["role"],
                    "Pouze při dotaci": "Ano" if _p["dotace_only"] else "Ne",
                })

        if len(_check_rows) > len(OP_PODKLADY_OBECNE):
            st.dataframe(
                _pd_check.DataFrame(_check_rows),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Pouze při dotaci": st.column_config.TextColumn(width="small"),
                    "Opatření": st.column_config.TextColumn(width="small"),
                },
            )
            st.caption(
                f"Celkem {len(_check_rows)} položek · "
                f"{sum(1 for r in _check_rows if r['Zajišťuje'] == 'Zákazník')} zajišťuje zákazník"
            )
        elif _aktivni_op_ids_check:
            st.info("Pro aktivní opatření nejsou definovány zvláštní podklady nad rámec obecných.")
        else:
            st.info("Žádné opatření není aktivní. Aktivujte opatření níže – checklist se doplní.")

    # ─────────────────────────────────────────────────────────────────────────
    # SKUPINA 1 – Tepelný plášť
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("### Skupina 1 – Tepelný plášť")

    def envelope_op(op_id: str, title: str, on_key: str,
                    uspora_key: str, plocha_key: str, cena_key: str,
                    u_stav_key: str, u_nove_key: str):
        """
        UI pro opatření tepelného pláště (OP1a–OP6).

        Primární vstup: fyzikální parametry (U stávající, U nové, plocha).
        Úspora se zobrazuje jako živý výsledek výpočtu.
        Ruční override (uspora_key) je skrytý v expanderu.
        """
        cols = st.columns([0.04, 0.96])
        with cols[0]:
            st.checkbox("", key=on_key, label_visibility="collapsed")
        with cols[1]:
            aktivni = st.session_state[on_key]
            label_color = "" if aktivni else "color: #888;"
            st.markdown(
                f"<span style='{label_color}'><b>{op_id}</b> – {title}</span>",
                unsafe_allow_html=True,
            )

            if aktivni:
                # ── Fyzikální vstupy ─────────────────────────────────────────
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.number_input("Plocha [m²]", min_value=0.0, step=10.0, key=plocha_key)
                with c2:
                    st.number_input("U stávající [W/m²K]", min_value=0.0, max_value=10.0,
                                    step=0.05, format="%.3f", key=u_stav_key,
                                    help="Stávající U-hodnota konstrukce (z PENB nebo měření)")
                with c3:
                    st.number_input("U nové [W/m²K]", min_value=0.0, max_value=10.0,
                                    step=0.05, format="%.3f", key=u_nove_key,
                                    help="Cílová U-hodnota po realizaci opatření")
                with c4:
                    st.number_input("Cena [Kč/m²]", min_value=0.0, step=100.0, key=cena_key)

                # ── Živý výsledek výpočtu ────────────────────────────────────
                _plocha = st.session_state.get(plocha_key, 0.0)
                _u_stav = st.session_state.get(u_stav_key, 0.0)
                _u_nove = st.session_state.get(u_nove_key, 0.0)
                _uspora_override = st.session_state.get(uspora_key, 0.0)

                if _u_stav > _u_nove > 0 and _plocha > 0 and _D_op > 0:
                    _delta_u = _u_stav - _u_nove
                    _uspora_phys = _delta_u * _plocha * _D_op * 24.0 / 1_000_000.0
                    if _uspora_override == 0.0:
                        st.success(
                            f"Vypočtená úspora: **{_uspora_phys:.1f} MWh/rok**  \n"
                            f"ΔU = {_delta_u:.3f} W/m²K · {_plocha:.0f} m² · D = {_D_op:.0f} K·d"
                        )
                    else:
                        st.info(
                            f"Fyzikální výpočet: {_uspora_phys:.1f} MWh/rok  \n"
                            f"*(přepsáno ručním zadáním: {_uspora_override:.1f} MWh/rok)*"
                        )
                elif _u_stav == 0 and _u_nove == 0:
                    st.caption("Zadejte U stávající a U nové pro automatický výpočet úspory.")
                elif _u_stav <= _u_nove:
                    st.warning("U stávající musí být větší než U nové.")

                # ── Ruční override ───────────────────────────────────────────
                with st.expander("Zadat úsporu ručně (přepíše výpočet)"):
                    st.number_input(
                        f"Úspora {nosic_label} [MWh/rok]",
                        min_value=0.0, step=1.0, key=uspora_key,
                        help="Pokud je > 0, použije se místo výpočtu z U-hodnot. "
                             "Nastavte na 0 pro návrat k fyzikálnímu výpočtu.",
                    )

            op_textace(op_id)

    envelope_op("OP1a", "Zateplení obvodových stěn (ETICS)",
                "op1a_on", "op1a_uspora", "op1a_plocha", "op1a_cena_m2",
                "op1a_u_stavajici", "op1a_u_nove")
    st.divider()
    envelope_op("OP1b", "Obnova zateplení (termoizolační omítka)",
                "op1b_on", "op1b_uspora", "op1b_plocha", "op1b_cena_m2",
                "op1b_u_stavajici", "op1b_u_nove")
    st.divider()
    envelope_op("OP2", "Výměna otvorových výplní",
                "op2_on", "op2_uspora", "op2_plocha", "op2_cena_m2",
                "op2_u_stavajici", "op2_u_nove")
    st.divider()
    envelope_op("OP3", "Rekonstrukce střechy (zateplení)",
                "op3_on", "op3_uspora", "op3_plocha", "op3_cena_m2",
                "op3_u_stavajici", "op3_u_nove")
    st.divider()
    envelope_op("OP4", "Zateplení podlahy půdy",
                "op4_on", "op4_uspora", "op4_plocha", "op4_cena_m2",
                "op4_u_stavajici", "op4_u_nove")
    st.divider()
    envelope_op("OP5", "Zateplení podlahy na terénu",
                "op5_on", "op5_uspora", "op5_plocha", "op5_cena_m2",
                "op5_u_stavajici", "op5_u_nove")
    st.divider()
    envelope_op("OP6", "Termoreflexní nátěry interiérů",
                "op6_on", "op6_uspora", "op6_plocha", "op6_cena_m2",
                "op6_u_stavajici", "op6_u_nove")

    # ─────────────────────────────────────────────────────────────────────────
    # SKUPINA 2 – Zdroj tepla a regulace
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("### Skupina 2 – Zdroj tepla a regulace")

    # OP7
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op7_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP7** – Výměna zdroje tepla")
        if st.session_state["op7_on"]:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input(f"Úspora {nosic_label} [MWh/rok]",
                                min_value=0.0, step=5.0, key="op7_uspora")
            with c2:
                st.number_input("Změna EE [MWh/rok] (−=navýšení)",
                                step=1.0, key="op7_ee_zmena")
            with c3:
                st.number_input("Investice [Kč]", min_value=0.0,
                                step=100_000.0, key="op7_investice")
        op_textace("OP7")
    st.divider()

    # OP8
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op8_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP8** – Nadřazená regulace a výzbroj rozdělovače/sběrače")
        if st.session_state["op8_on"]:
            c1, c2 = st.columns(2)
            with c1:
                st.number_input("Počet větví otopné soustavy", min_value=1,
                                step=1, key="op8_vetvi")
            with c2:
                st.number_input("Úspora [%]", min_value=0.0, max_value=30.0,
                                step=0.5, key="op8_pct",
                                help="Typicky 3–8 % z ÚT spotřeby")
        op_textace("OP8")
    st.divider()

    # OP9
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op9_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP9** – IRC systém (individuální regulace topení)")
        if st.session_state["op9_on"]:
            c1, c2 = st.columns(2)
            with c1:
                st.number_input("Počet otopných těles [ks]", min_value=0,
                                step=10, key="op9_ot")
            with c2:
                st.number_input("Úspora [%]", min_value=0.0, max_value=30.0,
                                step=0.5, key="op9_pct",
                                help="Typicky 8–12 % z ÚT spotřeby")
        op_textace("OP9")

    # ─────────────────────────────────────────────────────────────────────────
    # SKUPINA 3 – Elektrická energie / FVE
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("### Skupina 3 – Elektrická energie / FVE")

    # OP10
    # Koeficienty úspory LED dle původní technologie
    _LED_USPORA_KOEF = {
        "LED":                                    0.00,
        "Lineární fluorescenční (T8/T5)":         0.55,
        "Kompaktní fluorescenční (CFL)":          0.65,
        "Halogenové / výbojkové":                 0.80,
        "Mix (LED + fluorescenční)":              0.40,
        "Jiný":                                   0.55,
    }
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op10_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP10** – Instalace LED osvětlení")
        if st.session_state["op10_on"]:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("Úspora EE [MWh/rok]", min_value=0.0,
                                step=1.0, key="op10_uspora_ee")
            with c2:
                st.number_input("Počet nahrazovaných svítidel [ks]", min_value=0,
                                step=10, key="op10_svitidel")
            with c3:
                st.number_input("Cap osvětlení [% z EE]", min_value=0.0, max_value=100.0,
                                step=5.0, key="op10_ee_cap_pct",
                                help="Varování se zobrazí, pokud odhadovaná spotřeba osvětlení překročí tento podíl z celkové EE.")

            # ── Kalkulace LED úspor z pasportu ───────────────────────────────
            with st.expander("Kalkulace LED úspor z pasportu"):
                _zony_pasport = st.session_state.get("sys_osv_zony", [])
                _non_led = [z for z in _zony_pasport
                            if z.get("typ", "LED") != "LED"
                            and z.get("prikon_kw", 0) > 0
                            and z.get("hodiny_rok", 0) > 0]
                if not _non_led:
                    st.info("V popisu stávajícího stavu nejsou zadány žádné non-LED zóny s příkonem a hodinami provozu.")
                    st.page_link("pages/Popis_stavajiciho_stavu.py", label="Zadat osvětlení → Popis stávajícího stavu", icon="📋")
                else:
                    # Tabulka zón s odhadovanou úsporou
                    _rows = []
                    _uspora_celkem = 0.0
                    for _z in _non_led:
                        _koef = _LED_USPORA_KOEF.get(_z.get("typ", "Jiný"), 0.55)
                        _spotr = _z.get("prikon_kw", 0) * _z.get("hodiny_rok", 0) / 1000
                        _usp = _spotr * _koef
                        _uspora_celkem += _usp
                        _rows.append({
                            "Zóna": _z.get("nazev") or "(bez názvu)",
                            "Typ": _z.get("typ", ""),
                            "Příkon [kW]": f"{_z.get('prikon_kw', 0):.1f}",
                            "Hodiny/rok": _z.get("hodiny_rok", 0),
                            "Spotřeba [MWh]": f"{_spotr:.1f}",
                            "Koef. LED": f"{_koef:.0%}",
                            "Úspora [MWh]": f"{_usp:.1f}",
                        })
                    import pandas as _pd
                    st.dataframe(_pd.DataFrame(_rows), use_container_width=True, hide_index=True)

                    _ee_total_op10 = st.session_state.get("ee", 0.0)
                    _cap_pct = st.session_state.get("op10_ee_cap_pct", 50.0)
                    _mc1, _mc2 = st.columns(2)
                    _mc1.metric("Odhadovaná úspora LED", f"{_uspora_celkem:.1f} MWh/rok")
                    if _ee_total_op10 > 0:
                        _podil = _uspora_celkem / _ee_total_op10 * 100
                        _mc2.metric("Podíl z celkové EE", f"{_podil:.0f} %")
                        if _podil > _cap_pct:
                            st.warning(
                                f"Odhadovaná úspora ({_podil:.0f} %) překračuje "
                                f"cap {_cap_pct:.0f} % z celkové EE. "
                                "Zkontrolujte příkony nebo koeficienty."
                            )

                    if st.button("Použít jako úsporu OP10", key="op10_z_pasportu",
                                 help=f"Nastaví úsporu EE na {_uspora_celkem:.1f} MWh/rok"):
                        st.session_state["op10_uspora_ee"] = round(_uspora_celkem, 1)
                        st.rerun()

        op_textace("OP10")
    st.divider()

    # OP11
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op11_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP11** – Instalace fotovoltaické elektrárny (FVE)")
        if st.session_state["op11_on"]:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("Celková roční výroba [MWh/rok]",
                                min_value=0.0, step=5.0, key="op11_vyroba")
                st.number_input("Vlastní spotřeba [MWh/rok]",
                                min_value=0.0, step=5.0, key="op11_vlastni")
                st.number_input("Přetoky do sítě [MWh/rok]",
                                min_value=0.0, step=5.0, key="op11_export")
            with c2:
                st.number_input("Počet panelů [ks]", min_value=0,
                                step=10, key="op11_panelu")
                st.number_input("Projektování [Kč]", min_value=0.0,
                                step=10_000.0, key="op11_projekt")
            with c3:
                st.number_input("Revize [Kč]", min_value=0.0,
                                step=5_000.0, key="op11_revize")
                st.number_input("Montáž [Kč]", min_value=0.0,
                                step=10_000.0, key="op11_montaz")
            # Validace součtu
            if abs(st.session_state["op11_vlastni"] + st.session_state["op11_export"]
                   - st.session_state["op11_vyroba"]) > 0.1:
                st.warning(
                    "Vlastní spotřeba + přetoky se nerovnají celkové výrobě. "
                    "Zkontrolujte hodnoty."
                )
        op_textace("OP11")
    st.divider()

    # OP12
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op12_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP12** – Bateriové uložiště")
        if st.session_state["op12_on"]:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("Kapacita baterie [MWh]", min_value=0.0,
                                step=0.05, format="%.2f", key="op12_velikost")
            with c2:
                st.number_input("Cena [Kč/MWh kapacity]", min_value=0.0,
                                step=50_000.0, key="op12_cena_mwh")
            with c3:
                st.number_input("Navíc využito FVE [MWh/rok]", min_value=0.0,
                                step=1.0, key="op12_navic")
        op_textace("OP12")
    st.divider()

    # OP13
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op13_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP13** – Využití přebytků FVE pro ohřev TUV")
        if st.session_state["op13_on"]:
            c1, c2 = st.columns(2)
            with c1:
                st.number_input(f"Úspora {nosic_label} pro TUV [MWh/rok]",
                                min_value=0.0, step=1.0, key="op13_uspora")
            with c2:
                st.number_input("Velikost akumulační nádrže [l]", min_value=0.0,
                                step=100.0, key="op13_nadrz")
        op_textace("OP13")

    # ─────────────────────────────────────────────────────────────────────────
    # SKUPINA 4 – Voda
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("### Skupina 4 – Voda")

    # OP14
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op14_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP14** – Instalace spořičů vody")
        if st.session_state["op14_on"]:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.number_input("Úspora vody [%]", min_value=0.0, max_value=50.0,
                                step=1.0, key="op14_pct")
            with c2:
                st.number_input("Umyvadlové baterie [ks]", min_value=0,
                                step=5, key="op14_umyvadel")
            with c3:
                st.number_input("Sprchové hlavice [ks]", min_value=0,
                                step=5, key="op14_sprch")
            with c4:
                st.number_input("Splachovadla [ks]", min_value=0,
                                step=5, key="op14_splachovadel")
        op_textace("OP14")
    st.divider()

    # OP15
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op15_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP15** – Retenční nádrž na dešťovou vodu")
        if st.session_state["op15_on"]:
            c1, c2 = st.columns(2)
            with c1:
                st.number_input("Snížení srážkového poplatku [%]",
                                min_value=0.0, max_value=100.0,
                                step=5.0, key="op15_pct")
            with c2:
                st.number_input("Objem nádrže [l]", min_value=0.0,
                                step=500.0, key="op15_nadrz")
        op_textace("OP15")

    # ─────────────────────────────────────────────────────────────────────────
    # SKUPINA 5 – Dotační povinnosti
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("### Skupina 5 – Povinná opatření dle dotačních podmínek")

    # OP16
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op16_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP16** – Hydraulické vyvážení otopné soustavy")
        if st.session_state["op16_on"]:
            st.number_input("Počet otopných těles [ks]", min_value=0,
                            step=10, key="op16_ot",
                            help="Obvykle stejný počet jako OP9")
        op_textace("OP16")
    st.divider()

    # OP17
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op17_on", label_visibility="collapsed")
    with cols[1]:
        _hdr17, _lnk17 = st.columns([0.85, 0.15])
        with _hdr17:
            st.markdown("**OP17** – VZT se zpětným získáváním tepla (ZZT)")
        with _lnk17:
            st.page_link("pages/Fyzikální_kalkulátor.py", label="🔬 Kalkulátor",
                         help="Spočítat úsporu ZZT z objemu a účinnosti rekuperace")
        if st.session_state["op17_on"]:
            st.number_input("Počet VZT jednotek [ks]", min_value=0,
                            step=1, key="op17_jednotky")
            st.info(
                "Opatření ušetří 3 % tepla a zvýší spotřebu EE o 2 % "
                "(pevné koeficienty dle Excel šablony). Pro detailní výpočet "
                "použijte záložku Větrání a ZZT v 🔬 Fyzikálním kalkulátoru."
            )

            # ── Kalkulátor větrání škol ────────────────────────────────────
            with st.expander("🏫 Kalkulátor větrání škol (metodický pokyn SFŽP)", expanded=False):
                import math as _math

                st.caption(
                    "Výpočetní pomůcka dle Metodického pokynu pro návrh větrání škol (SFŽP/MPO). "
                    "Stanoví návrhový průtok vzduchu a zobrazí průběh CO₂ v učebně během školního dne."
                )

                # ── Produkce CO₂ dle věkové skupiny [m³/h/osobu]
                _CO2_PROD = {
                    1: ("Mateřská škola (3–6 let)",      0.0072796, 10),
                    2: ("ZŠ 1. stupeň (6–10 let)",       0.0099654, 12),
                    3: ("ZŠ 2. stupeň (10–15 let)",      0.0147251, 18),
                    4: ("Střední škola (15–18 let)",      0.0162780, 20),
                }

                _sc1, _sc2 = st.columns(2)
                with _sc1:
                    st.markdown("**Zadání učebny**")
                    _typ_idx = st.selectbox(
                        "Typ školy",
                        options=[1, 2, 3, 4],
                        format_func=lambda i: _CO2_PROD[i][0],
                        key="op17_skola_typ",
                    )
                    _n_zaci = st.number_input(
                        "Počet žáků ve třídě [osob]",
                        min_value=1, max_value=50, step=1,
                        key="op17_skola_zaci",
                    )
                    _n_ucit = st.number_input(
                        "Počet vyučujících / asistentů [osob]",
                        min_value=0, max_value=5, step=1,
                        key="op17_skola_ucitele",
                    )
                    _objem = st.number_input(
                        "Objem místnosti [m³]",
                        min_value=10.0, max_value=2000.0, step=5.0,
                        key="op17_skola_objem",
                        help="Orientačně: délka × šířka × výška (m). Typická ZŠ učebna ≈ 175 m³.",
                    )
                    _ucitel_prut = st.number_input(
                        "Průtok vzduchu na vyučujícího [m³/h]",
                        min_value=5.0, max_value=100.0, step=5.0,
                        key="op17_skola_ucitel_prut",
                        help="NV č. 93/2012: min. 25 m³/h. Doporučeno 25–50 m³/h.",
                    )

                with _sc2:
                    st.markdown("**Parametry CO₂ a větrání**")
                    _co2_max = st.selectbox(
                        "Max. koncentrace CO₂ v učebně [ppm]",
                        options=[1000, 1200, 1500],
                        index=1,
                        key="op17_skola_co2_max",
                        help="Vyhl. č. 146/2024: max. 1200 ppm. Přísnější limit 1000 ppm pro dotace.",
                    )
                    _co2_out = st.selectbox(
                        "Koncentrace CO₂ ve venkovním vzduchu [ppm]",
                        options=[400, 550, 700],
                        index=0,
                        key="op17_skola_co2_out",
                        help="400 ppm – venkovská oblast; 550 – město; 700 – průmyslová oblast.",
                    )
                    _prestávky_pct = st.selectbox(
                        "Procento žáků ve třídě o přestávkách [%]",
                        options=[0, 50, 100],
                        index=0,
                        key="op17_skola_prestávky_pct",
                        help="0 % = žáci opouštějí třídu; 50 % = volný pohyb; 100 % = žáci zůstávají.",
                    )
                    st.markdown("**Tepelná ztráta větráním**")
                    _ti = float(st.session_state.get("theta_i", 21.0))
                    _te = float(st.session_state.get("theta_e", -13.0))
                    st.caption(f"Teploty přebírám z projektu: tᵢ = {_ti} °C, tₑ = {_te} °C")
                    _zzt_pct = st.number_input(
                        "Účinnost ZZT rekuperátoru [%]",
                        min_value=0.0, max_value=100.0, step=5.0,
                        key="op17_skola_zzt",
                        help="Typické hodnoty: 70–85 %. Dle ČSN EN 308.",
                    )

                # ── Výpočet ───────────────────────────────────────────────
                _co2_prod_zak, _q_pp_zak = _CO2_PROD[_typ_idx][1], _CO2_PROD[_typ_idx][2]
                _co2_ucitel = 0.017  # m³/h – dospělý (ze vzorového listu Excel)

                # Celková produkce CO₂ [m³/h]
                _M_vyuka   = _n_zaci * _co2_prod_zak + _n_ucit * _co2_ucitel
                _M_prestávka = _n_zaci * _co2_prod_zak * (_prestávky_pct / 100) + _n_ucit * _co2_ucitel

                # Průtok dle osob [m³/h]
                _Q_pp = _n_zaci * _q_pp_zak + _n_ucit * _ucitel_prut

                # Průtok dle CO₂ bilance [m³/h] (steady-state)
                _dC = (_co2_max - _co2_out) * 1e-6  # [m³/m³]
                _Q_co2 = _M_vyuka / _dC if _dC > 0 else 9999.0

                # Návrhový průtok
                _Q_nav = max(_Q_pp, _Q_co2)
                _intenzita = _Q_nav / _objem if _objem > 0 else 0.0

                # Tepelná ztráta větráním [W]
                # Qv = 0.34 × Q [m³/h] × ΔT [K] × (1 – η_ZZT)
                _Qv_W = 0.34 * _Q_nav * (_ti - _te) * (1 - _zzt_pct / 100)

                # ── Výsledkové metriky ─────────────────────────────────────
                _r1, _r2, _r3, _r4 = st.columns(4)
                _r1.metric("Průtok dle osob", f"{_Q_pp:.0f} m³/h")
                _r2.metric(
                    "Průtok dle CO₂",
                    f"{_Q_co2:.0f} m³/h",
                    delta="limitující" if _Q_co2 > _Q_pp else "v normě",
                    delta_color="inverse" if _Q_co2 > _Q_pp else "normal",
                )
                _r3.metric("Návrhový průtok", f"{_Q_nav:.0f} m³/h",
                           delta=f"{_intenzita:.1f} h⁻¹ (intenzita)")
                _r4.metric("Tepelná ztráta větráním", f"{_Qv_W / 1000:.2f} kW",
                           delta=f"ZZT {_zzt_pct:.0f} %")

                # ── Simulace průběhu CO₂ ──────────────────────────────────
                # Školní den: 5 × 45 min výuka + přestávky (10+20+10+10 min)
                # Struktura: (délka v min, typ: 'H'=hodina, 'P'=přestávka)
                _BLOKY = [
                    (45, 'H'), (10, 'P'), (45, 'H'), (20, 'P'),
                    (45, 'H'), (10, 'P'), (45, 'H'), (10, 'P'), (45, 'H'),
                ]
                _CELKEM_MIN = sum(d for d, _ in _BLOKY)  # 275 min

                _C_out_frac = _co2_out * 1e-6
                _C = _C_out_frac  # počáteční koncentrace
                _n_air = _Q_nav / _objem if _objem > 0 else 0.0
                _dt = 1 / 60  # 1 minuta v hodinách

                _cas_min = []
                _co2_ppm_sim = []

                _t = 0
                for _delka, _typ in _BLOKY:
                    _M = _M_vyuka if _typ == 'H' else _M_prestávka
                    for _ in range(_delka):
                        _cas_min.append(_t)
                        _co2_ppm_sim.append(_C * 1e6)
                        if _n_air > 0:
                            _C_ss = _C_out_frac + _M / _Q_nav
                            _exp = _math.exp(-_n_air * _dt)
                            _C = _C_ss + (_C - _C_ss) * _exp
                        else:
                            _C += _M * _dt / _objem
                        _t += 1

                # Přidat poslední bod
                _cas_min.append(_t)
                _co2_ppm_sim.append(_C * 1e6)

                # Čas → hodiny od 8:00
                import pandas as _pd_vetr
                _df_co2 = _pd_vetr.DataFrame({
                    "Čas (min od 8:00)": _cas_min,
                    "CO₂ [ppm]": [round(c, 0) for c in _co2_ppm_sim],
                })

                _fig_co2 = px.line(
                    _df_co2,
                    x="Čas (min od 8:00)",
                    y="CO₂ [ppm]",
                    title=f"Průběh CO₂ v učebně – školní den (Q = {_Q_nav:.0f} m³/h)",
                )
                # Limit linka
                _fig_co2.add_hline(
                    y=_co2_max, line_dash="dash", line_color="red",
                    annotation_text=f"Limit {_co2_max} ppm",
                    annotation_position="top right",
                )
                _fig_co2.add_hline(
                    y=_co2_out, line_dash="dot", line_color="green",
                    annotation_text=f"Venkovní CO₂ {_co2_out} ppm",
                )

                # Šrafování přestávek
                _t2 = 0
                for _delka, _typ in _BLOKY:
                    if _typ == 'P':
                        _fig_co2.add_vrect(
                            x0=_t2, x1=_t2 + _delka,
                            fillcolor="lightblue", opacity=0.25, line_width=0,
                            annotation_text="přestávka", annotation_position="top left",
                        )
                    _t2 += _delka

                _fig_co2.update_layout(
                    plot_bgcolor="white",
                    yaxis_title="CO₂ [ppm]",
                    xaxis_title="Čas od začátku výuky [min]",
                    margin=dict(t=40, b=10),
                    yaxis_range=[
                        max(0, _co2_out - 50),
                        max(_co2_max * 1.15, max(_co2_ppm_sim) * 1.05),
                    ],
                )
                _fig_co2.update_traces(line_color="#2E86AB")
                st.plotly_chart(_fig_co2, use_container_width=True)

                # ── Srovnání systémů větrání ───────────────────────────────
                st.markdown("**Srovnání tepelné ztráty větráním dle systému větrání**")
                _sys_data = {
                    "Systém": [
                        "Přirozené větrání (okna)",
                        "Nucené podtlakové",
                        "Nucené rovnotlaké – ZZT 70 %",
                        "Nucené rovnotlaké – ZZT 85 %",
                    ],
                    "Tepelná ztráta [W]": [
                        round(0.34 * _Q_nav * (_ti - _te), 0),
                        round(0.34 * _Q_nav * (_ti - _te), 0),
                        round(0.34 * _Q_nav * (_ti - _te) * 0.30, 0),
                        round(0.34 * _Q_nav * (_ti - _te) * 0.15, 0),
                    ],
                    "ZZT": ["–", "–", "ANO (70 %)", "ANO (85 %)"],
                    "Doporučení": [
                        "Nedoporučeno (jen výjimečně)",
                        "Nedoporučeno (energetická náročnost)",
                        "Doporučeno ✓",
                        "Doporučeno ✓",
                    ],
                }
                import pandas as _pd_syst
                st.dataframe(
                    _pd_syst.DataFrame(_sys_data),
                    use_container_width=True,
                    hide_index=True,
                )
                st.caption(
                    f"Výpočet: Q = {_Q_nav:.0f} m³/h | tᵢ = {_ti} °C | tₑ = {_te} °C | "
                    f"Qᵥ = 0,34 × Q × Δt × (1 − η_ZZT). "
                    "Elektřina pro pohon ventilátorů není zahrnuta."
                )

        op_textace("OP17")
    st.divider()

    # OP18
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op18_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP18** – Venkovní stínicí prvky")
        if st.session_state["op18_on"]:
            st.number_input("Plocha osazovaných prvků [m²]", min_value=0.0,
                            step=10.0, key="op18_plocha",
                            help="Obvykle plocha měněných oken (OP2) / 2,5")
        op_textace("OP18")
    st.divider()

    # OP19
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op19_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP19** – Energetický management (měření a monitoring)")
        if st.session_state["op19_on"]:
            st.number_input("Počet měřených odběrných míst [ks]", min_value=0,
                            step=1, key="op19_mista")
        op_textace("OP19")

    # ─────────────────────────────────────────────────────────────────────────
    # SKUPINA 6 – Infrastruktura
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("### Skupina 6 – Infrastruktura / bezpečný provoz")

    # OP20
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op20_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP20** – Rekonstrukce otopné soustavy")
        if st.session_state["op20_on"]:
            c1, c2 = st.columns(2)
            with c1:
                st.number_input("Podlahová plocha [m²]", min_value=0.0,
                                step=50.0, key="op20_plocha")
            with c2:
                st.number_input("Cena [Kč/m²]", min_value=0.0,
                                step=100.0, key="op20_cena_m2")
        op_textace("OP20")
    st.divider()

    # OP21
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op21_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP21** – Rekonstrukce elektroinstalace")
        if st.session_state["op21_on"]:
            st.number_input("Investice [Kč]", min_value=0.0,
                            step=100_000.0, key="op21_investice")
        op_textace("OP21")
    st.divider()

    # OP22
    cols = st.columns([0.04, 0.96])
    with cols[0]:
        st.checkbox("", key="op22_on", label_visibility="collapsed")
    with cols[1]:
        st.markdown("**OP22** – Rekonstrukce rozvodů teplé a studené vody")
        if st.session_state["op22_on"]:
            st.number_input("Investice [Kč]", min_value=0.0,
                            step=100_000.0, key="op22_investice")
        op_textace("OP22")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – Výsledky
# ══════════════════════════════════════════════════════════════════════════════

with tab_vysledky:
    projekt = build_project()
    result = projekt.vypocitej()
    aktivni = result.aktivni

    if not aktivni:
        st.info("Žádné opatření není aktivní. Aktivujte alespoň jedno v záložce Opatření.")
        st.stop()

    # ── Výpočet primární energie ───────────────────────────────────────────────
    from epc_engine.emissions import FAKTORY_PRIMARNI_ENERGIE as _FPE
    _fpe_zp = _FPE["zp"]          # 1.0
    _fpe_teplo = _FPE["teplo"]    # 1.3 (CZT ostatní)
    _fpe_ee = _FPE["ee"]          # 2.1
    _en = result.energie
    _pe_pred = (
        _en.zp_total * _fpe_zp
        + _en.teplo_total * _fpe_teplo
        + _en.ee * _fpe_ee
    )
    _pe_uspora = (
        result.celkova_uspora_zp * _fpe_zp
        + result.celkova_uspora_teplo * _fpe_teplo
        + result.celkova_uspora_ee * _fpe_ee
    )
    _pe_po = _pe_pred - _pe_uspora
    _pe_pct = (_pe_uspora / _pe_pred * 100) if _pe_pred > 0 else 0.0

    # ── 5 hlavních metrik ──────────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(
        "Celková investice",
        fmt_kc(result.celkova_investice),
    )
    m2.metric(
        "Roční úspora",
        fmt_kc(result.celkova_uspora_kc),
    )
    m3.metric(
        "Úspora z nákladů",
        f"{result.celkova_uspora_pct * 100:.1f} %",
    )
    nav = result.prosta_navratnost_celkem
    m4.metric(
        "Prostá návratnost",
        f"{nav:.1f} let" if nav else "∞",
    )
    m5.metric(
        "Úspora PE (nOZE)",
        f"{_pe_uspora:,.0f} MWh",
        delta=f"−{_pe_pct:.1f} %",
        help=f"Primární energie z neobnovitelných zdrojů (fpe,nOZE). "
             f"Před: {_pe_pred:,.0f} MWh → Po: {_pe_po:,.0f} MWh. "
             f"Faktory: ZP {_fpe_zp}, Teplo {_fpe_teplo}, EE {_fpe_ee} (vyhl. 264/2020 Sb., novela 222/2024).",
    )

    st.divider()

    # ── Grafy ─────────────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    # Investice per OP
    with col_l:
        st.subheader("Investice po opatřeních")
        df_inv = {
            "Opatření": [r.id for r in aktivni if r.investice > 0],
            "Investice [Kč]": [r.investice for r in aktivni if r.investice > 0],
        }
        if df_inv["Opatření"]:
            fig_inv = px.bar(
                df_inv,
                x="Opatření",
                y="Investice [Kč]",
                color_discrete_sequence=["#1B4F72"],
                text_auto=".3s",
            )
            fig_inv.update_layout(
                plot_bgcolor="white", showlegend=False,
                margin=dict(t=10, b=0),
                yaxis_tickformat=",.0f",
            )
            st.plotly_chart(fig_inv, use_container_width=True)

    # Roční úspora per OP
    with col_r:
        st.subheader("Roční úspora po opatřeních")
        df_usp = {
            "Opatření": [r.id for r in aktivni],
            "Úspora [Kč/rok]": [r.uspora_kc for r in aktivni],
        }
        fig_usp = px.bar(
            df_usp,
            x="Opatření",
            y="Úspora [Kč/rok]",
            color_discrete_sequence=["#1E8449"],
            text_auto=".3s",
        )
        fig_usp.update_layout(
            plot_bgcolor="white", showlegend=False,
            margin=dict(t=10, b=0),
            yaxis_tickformat=",.0f",
        )
        st.plotly_chart(fig_usp, use_container_width=True)

    # Scatter: investice vs. návratnost
    st.subheader("Investice vs. prostá návratnost")
    scatter_data = [
        {
            "Opatření": r.id,
            "Investice [Kč]": r.investice,
            "Návratnost [let]": r.prosta_navratnost or 99,
            "Úspora [Kč/rok]": r.uspora_kc,
        }
        for r in aktivni if r.investice > 0
    ]
    if scatter_data:
        fig_sc = px.scatter(
            scatter_data,
            x="Investice [Kč]",
            y="Návratnost [let]",
            text="Opatření",
            size="Úspora [Kč/rok]",
            size_max=40,
            color="Návratnost [let]",
            color_continuous_scale="RdYlGn_r",
        )
        fig_sc.update_traces(textposition="top center")
        fig_sc.update_layout(
            plot_bgcolor="white",
            xaxis_tickformat=",.0f",
            coloraxis_showscale=False,
            margin=dict(t=10, b=0),
        )
        st.plotly_chart(fig_sc, use_container_width=True)

    # ── Sankey – toky nákladů ─────────────────────────────────────────────────
    st.subheader("Toky nákladů na energie")

    def _build_sankey(en) -> go.Figure:
        """
        Sankey: Zdroj → Médium (interní systém) → Účel užití energie.
        Hodnoty v tis. Kč/rok – jednotný jmenovatel pro srovnání nosičů.
        """
        ss = st.session_state
        labels, colors = [], []

        # ── helpers ───────────────────────────────────────────────────────────
        def _node(label, color):
            idx = len(labels)
            labels.append(label); colors.append(color)
            return idx

        src_l, tgt_l, val_l, col_l = [], [], [], []

        def _link(s, t, kc_rok, color="#D5F5E3"):
            v = round(kc_rok / 1000, 2)
            if v > 0.05:
                src_l.append(s); tgt_l.append(t)
                val_l.append(v); col_l.append(color)

        # ── LEVEL 1 – Zdroj (co se nakupuje) ─────────────────────────────────
        has_zp  = en.pouzit_zp  and en.zp_total  > 0
        has_t   = en.pouzit_teplo and en.teplo_total > 0
        has_ee  = en.ee > 0
        has_vod = (en.voda + en.srazky) > 0

        iz_zp = _node("Zemní plyn",        "#C0392B") if has_zp  else None
        iz_t  = _node("Teplo (CZT)",       "#922B21") if has_t   else None
        iz_ee = _node("Elektrická energie","#E67E22") if has_ee  else None
        iz_vd = _node("Voda a srážky",     "#2980B9") if has_vod else None

        # ── LEVEL 2 – Médium / interní systém ─────────────────────────────────
        # Zdroj tepla – použij skutečný typ z pasportu pokud je vyplněn
        if has_zp:
            _vyt = ss.get("sys_vyt_zdroje", [])
            _label_k = _vyt[0]["typ"] if _vyt and _vyt[0].get("typ") else "Plynová kotelna"
            im_k = _node(_label_k, "#E59866")
            _link(iz_zp, im_k, en.zp_total * en.cena_zp, "#FADBD8")
        else:
            im_k = None

        if has_t:
            im_czt = _node("Předávací stanice CZT", "#D98880")
            _link(iz_t, im_czt, en.teplo_total * en.cena_teplo, "#FADBD8")
        else:
            im_czt = None

        if has_ee:
            im_ee = _node("Silnoproudé rozvody", "#F8C471")
            _link(iz_ee, im_ee, en.ee * en.cena_ee, "#FDEBD0")
        else:
            im_ee = None

        if has_vod:
            im_vd = _node("Rozvody vody", "#85C1E9")
            vod_kc = en.voda * en.cena_voda + en.srazky * en.cena_srazky
            _link(iz_vd, im_vd, vod_kc, "#D6EAF8")
        else:
            im_vd = None

        # ── LEVEL 3 – Účel užití ──────────────────────────────────────────────
        has_ut  = (en.zp_ut  + en.teplo_ut)  > 0
        has_tuv = (en.zp_tuv + en.teplo_tuv) > 0

        if has_ut:
            iu_ut = _node("Vytápění (ÚT)", "#AED6F1")
            if im_k   is not None:
                _link(im_k,   iu_ut, en.zp_ut   * en.cena_zp,    "#EBF5FB")
            if im_czt is not None:
                _link(im_czt, iu_ut, en.teplo_ut * en.cena_teplo, "#EBF5FB")

        if has_tuv:
            iu_tuv = _node("Příprava TUV", "#A9DFBF")
            # TUV může mít vlastní nosič ze session state (tuv_zdroje)
            _tuv = ss.get("sys_tuv_zdroje", [])
            _tuv_typ = _tuv[0]["typ"] if _tuv else ""
            if "Elektrický" in _tuv_typ and im_ee is not None:
                # TUV ohřívána elektřinou – připočti k el. toku
                tuv_kc_ee = en.zp_tuv * en.cena_zp + en.teplo_tuv * en.cena_teplo
                _link(im_ee, iu_tuv, tuv_kc_ee, "#E8F8F5")
            else:
                if im_k   is not None:
                    _link(im_k,   iu_tuv, en.zp_tuv    * en.cena_zp,    "#E8F8F5")
                if im_czt is not None:
                    _link(im_czt, iu_tuv, en.teplo_tuv * en.cena_teplo, "#E8F8F5")

        if has_ee and im_ee is not None:
            # Osvětlení: odhadni spotřebu ze zón pasportu (s hodinami) nebo příkonem
            _osv_zony_s = ss.get("sys_osv_zony", [])
            _osv_mwh = sum(
                z.get("prikon_kw", 0) * z.get("hodiny_rok", 2000) / 1000
                for z in _osv_zony_s
            )
            _osv_frac = min(_osv_mwh / en.ee, 0.9) if en.ee > 0 and _osv_mwh > 0 else 0.0

            if _osv_frac > 0.01:
                iu_osv = _node("Osvětlení", "#F9E79F")
                _link(im_ee, iu_osv, en.ee * _osv_frac * en.cena_ee, "#FEF9E7")
                iu_ost = _node("Ostatní EE", "#FAD7A0")
                _link(im_ee, iu_ost, en.ee * (1 - _osv_frac) * en.cena_ee, "#FDEBD0")
            else:
                iu_ost = _node("Spotřeba EE", "#FAD7A0")
                _link(im_ee, iu_ost, en.ee * en.cena_ee, "#FDEBD0")

        if has_vod and im_vd is not None:
            iu_vd = _node("Vodné a stočné / srážky", "#AED6F1")
            _link(im_vd, iu_vd, vod_kc, "#D6EAF8")

        # ── Figura ────────────────────────────────────────────────────────────
        fig = go.Figure(go.Sankey(
            arrangement="snap",
            node=dict(pad=15, thickness=20, label=labels, color=colors),
            link=dict(source=src_l, target=tgt_l, value=val_l, color=col_l),
        ))
        fig.update_layout(
            height=440, font_size=12,
            margin=dict(t=10, b=10, l=10, r=10),
        )
        return fig

    st.plotly_chart(_build_sankey(result.energie), use_container_width=True)
    st.caption(
        "Hodnoty v tis. Kč/rok · Zdroj → interní systém → účel užití. "
        "Typ zdroje tepla a podíl osvětlení se načítají z pasportu (tab Identifikace)."
    )

    # ── Detailní tabulka ──────────────────────────────────────────────────────
    st.subheader("Podrobná bilance")

    import pandas as pd
    rows = []
    for r in result.vysledky:
        if not r.aktivni:
            continue
        rows.append({
            "ID": r.id,
            "Opatření": r.nazev,
            "Investice [Kč]": r.investice,
            "Úspora tepla [MWh]": r.uspora_teplo,
            "Úspora ZP [MWh]": r.uspora_zp,
            "Úspora EE [MWh]": r.uspora_ee,
            "Výnos FVE [Kč]": r.vynos_pretoky,
            "Úspora voda [m³]": r.uspora_voda,
            "Úspora [Kč/rok]": r.uspora_kc,
            "Úspora [%]": round(r.uspora_pct * 100, 1),
            "Servis [Kč/rok]": r.servisni_naklady,
            "Návratnost [let]": (
                round(r.prosta_navratnost, 1)
                if r.prosta_navratnost else "∞"
            ),
        })
    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Investice [Kč]": st.column_config.NumberColumn(format="%.0f Kč"),
            "Úspora [Kč/rok]": st.column_config.NumberColumn(format="%.0f Kč"),
            "Servis [Kč/rok]": st.column_config.NumberColumn(format="%.0f Kč"),
            "Výnos FVE [Kč]": st.column_config.NumberColumn(format="%.0f Kč"),
        },
    )

    # ── Souhrnná lišta dole ───────────────────────────────────────────────────
    st.divider()
    tot1, tot2, tot3, tot4, tot5 = st.columns(5)
    tot1.metric("Počet aktivních opatření", len(aktivni))
    tot2.metric("Úspora tepla/ZP celkem",
                fmt_mwh(result.celkova_uspora_teplo + result.celkova_uspora_zp))
    tot3.metric("Úspora EE celkem", fmt_mwh(result.celkova_uspora_ee))
    tot4.metric("Úspora vody celkem",
                f"{result.celkova_uspora_voda + result.celkova_uspora_srazky:,.0f} m³")
    tot5.metric("Servisní náklady / rok",
                fmt_kc(result.celkove_servisni_naklady))

    # ── Manažerské shrnutí ────────────────────────────────────────────────────
    with st.expander("📄 Manažerské shrnutí", expanded=False):
        _ms_vysl = _build_executive_summary(result, st.session_state)
        st.markdown(_ms_vysl)
        st.text_area(
            "Markdown ke zkopírování",
            value=_ms_vysl,
            height=250,
            label_visibility="collapsed",
            key="_ms_vysledky_area",
        )

    # ── Celková bilance projektu (všechny objekty) ────────────────────────────
    if len(st.session_state["objekty"]) > 1:
        st.divider()
        st.subheader("Celková bilance projektu – všechny objekty")

        # Ulož aktuální objekt do snapshotu před iterací
        _all_objs = list(st.session_state["objekty"])
        _all_objs[st.session_state["aktivni_objekt_idx"]] = _snapshot_object()

        _proj_rows = []
        _proj_inv = 0.0
        _proj_uspora_kc = 0.0
        _proj_uspora_teplo = 0.0
        _proj_uspora_zp = 0.0
        _proj_uspora_ee = 0.0
        _proj_uspora_voda = 0.0
        _proj_servis = 0.0
        _proj_naklady = 0.0

        for _obj_data in _all_objs:
            try:
                _p = _build_project_from_data(_obj_data)
                _r = _p.vypocitej()
                _nazev = _obj_data.get("objekt_nazev") or "Objekt"
                _proj_rows.append({
                    "Objekt": _nazev,
                    "Investice [Kč]": _r.celkova_investice,
                    "Úspora [Kč/rok]": _r.celkova_uspora_kc,
                    "Servis [Kč/rok]": _r.celkove_servisni_naklady,
                    "Úspora teplo+ZP [MWh]": _r.celkova_uspora_teplo + _r.celkova_uspora_zp,
                    "Úspora EE [MWh]": _r.celkova_uspora_ee,
                    "Návratnost [let]": (
                        round(_r.prosta_navratnost_celkem, 1)
                        if _r.prosta_navratnost_celkem else "∞"
                    ),
                })
                _proj_inv += _r.celkova_investice
                _proj_uspora_kc += _r.celkova_uspora_kc
                _proj_uspora_teplo += _r.celkova_uspora_teplo + _r.celkova_uspora_zp
                _proj_uspora_ee += _r.celkova_uspora_ee
                _proj_uspora_voda += _r.celkova_uspora_voda + _r.celkova_uspora_srazky
                _proj_servis += _r.celkove_servisni_naklady
                _proj_naklady += _r.energie.celkove_naklady
            except Exception:
                pass

        if _proj_rows:
            st.dataframe(pd.DataFrame(_proj_rows), use_container_width=True, hide_index=True,
                         column_config={
                             "Investice [Kč]": st.column_config.NumberColumn(format="%.0f Kč"),
                             "Úspora [Kč/rok]": st.column_config.NumberColumn(format="%.0f Kč"),
                             "Servis [Kč/rok]": st.column_config.NumberColumn(format="%.0f Kč"),
                         })

            _net = _proj_uspora_kc - _proj_servis
            _nav_celk = (_proj_inv / _net) if _net > 0 else None
            _pct_celk = (_proj_uspora_kc / _proj_naklady * 100) if _proj_naklady > 0 else 0.0

            _pc1, _pc2, _pc3, _pc4 = st.columns(4)
            _pc1.metric("Celková investice projektu", fmt_kc(_proj_inv))
            _pc2.metric("Celková roční úspora", fmt_kc(_proj_uspora_kc))
            _pc3.metric("Úspora z nákladů", f"{_pct_celk:.1f} %")
            _pc4.metric("Prostá návratnost projektu",
                        f"{_nav_celk:.1f} let" if _nav_celk else "∞")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 – Ekonomika (NPV / IRR / Tsd)
# ══════════════════════════════════════════════════════════════════════════════

import pandas as _pd_ekon

with tab_ekonomika:
    _result_ek = build_project().vypocitej()
    _par_ek = _result_ek.ekonomika_parametry

    st.subheader("Ekonomická analýza opatření")
    if _par_ek:
        st.caption(
            f"Horizont: {_par_ek.horizont} let | "
            f"Diskontní sazba: {_par_ek.diskontni_sazba * 100:.1f} % | "
            f"Inflace energií: {_par_ek.inflace_energie * 100:.1f} %"
        )
    else:
        st.info("Ekonomické parametry nejsou k dispozici – zkontrolujte sidebar.")

    _ek_rows = []
    for _r in _result_ek.vysledky:
        if not _r.aktivni or _r.investice <= 0:
            continue
        _ek = _r.ekonomika
        _ek_rows.append({
            "ID": _r.id,
            "Název": _r.nazev,
            "Investice [Kč]": _r.investice,
            "Úspora [Kč/rok]": _r.uspora_kc,
            "Prostá návratnost [let]": (
                round(_r.prosta_navratnost, 1) if _r.prosta_navratnost else None
            ),
            "NPV [Kč]": _ek.npv if _ek else None,
            "IRR [%]": round(_ek.irr * 100, 1) if (_ek and _ek.irr is not None) else None,
            "Tsd [roky]": _ek.tsd if _ek else None,
        })

    if _ek_rows:
        _df_ek = _pd_ekon.DataFrame(_ek_rows)
        st.dataframe(
            _df_ek,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Investice [Kč]": st.column_config.NumberColumn(format="%.0f Kč"),
                "Úspora [Kč/rok]": st.column_config.NumberColumn(format="%.0f Kč"),
                "Prostá návratnost [let]": st.column_config.NumberColumn(format="%.1f"),
                "NPV [Kč]": st.column_config.NumberColumn(format="%.0f Kč"),
                "IRR [%]": st.column_config.NumberColumn(format="%.1f %%"),
                "Tsd [roky]": st.column_config.NumberColumn(format="%.0f"),
            },
        )
    else:
        st.info("Žádná aktivní opatření s investicí > 0.")

    # Souhrn projektu
    _ek_proj = _result_ek.ekonomika_projekt
    if _ek_proj is not None:
        st.divider()
        st.subheader("Souhrn projektu")
        _ek_c1, _ek_c2, _ek_c3, _ek_c4 = st.columns(4)
        _ek_c1.metric("Celková investice", fmt_kc(_result_ek.celkova_investice))
        _ek_c2.metric(
            "NPV",
            fmt_kc(_ek_proj.npv),
            help="Čistá současná hodnota – kladná = projekt je výnosný",
        )
        _ek_c3.metric(
            "IRR",
            f"{_ek_proj.irr * 100:.1f} %" if _ek_proj.irr is not None else "–",
            help="Vnitřní výnosové procento",
        )
        _ek_c4.metric(
            "Tsd",
            f"{_ek_proj.tsd:.0f} let" if _ek_proj.tsd is not None else f"> {_par_ek.horizont} let",
            help="Diskontovaná doba úhrady",
        )

    # ── Životnost a obnova zařízení ───────────────────────────────────────────
    _aktivni_op_ids = [_r.id for _r in _result_ek.vysledky if _r.aktivni and _r.investice > 0]
    if _aktivni_op_ids and _par_ek:
        st.divider()
        with st.expander("🔄 Životnost a obnova zařízení", expanded=False):
            st.caption(
                "Zadejte technickou životnost opatření. "
                "Pokud životnost < horizont analýzy, bude v cash-flow zahrnut výdaj na obnovu. "
                "Tato pole jsou čistě informativní – nemění NPV/IRR z engine."
            )
            # Inicializuj slovník životností pokud chybí
            if "op_zivotnost" not in st.session_state:
                st.session_state["op_zivotnost"] = {}

            _ziv_cols = st.columns(min(len(_aktivni_op_ids), 4))
            for _zi, _op_id in enumerate(_aktivni_op_ids):
                with _ziv_cols[_zi % 4]:
                    _default_ziv = st.session_state["op_zivotnost"].get(_op_id, 20)
                    _new_ziv = st.number_input(
                        f"{_op_id} [let]",
                        min_value=1, max_value=50,
                        value=_default_ziv,
                        key=f"_ziv_{_op_id}",
                    )
                    st.session_state["op_zivotnost"][_op_id] = _new_ziv

            # Harmonogram obnovy
            _obnova_rows = []
            for _r_op in _result_ek.vysledky:
                if not _r_op.aktivni or _r_op.investice <= 0:
                    continue
                _ziv = st.session_state["op_zivotnost"].get(_r_op.id, 20)
                _rok_obnovy = _ziv
                while _rok_obnovy <= _par_ek.horizont:
                    _obnova_rows.append({
                        "Opatření": _r_op.id,
                        "Rok obnovy": _rok_obnovy,
                        "Investice obnovy [Kč]": _r_op.investice,
                    })
                    _rok_obnovy += _ziv

            if _obnova_rows:
                st.markdown("**Harmonogram obnov v horizontu analýzy:**")
                st.dataframe(
                    _pd_ekon.DataFrame(_obnova_rows),
                    use_container_width=True, hide_index=True,
                    column_config={
                        "Investice obnovy [Kč]": st.column_config.NumberColumn(format="%.0f Kč"),
                    },
                )
                _celk_obnova = sum(r["Investice obnovy [Kč]"] for r in _obnova_rows)
                st.metric("Celkové náklady obnov v horizontu", f"{_celk_obnova:,.0f} Kč")
            else:
                st.success("Žádná obnova v horizontu analýzy (životnosti ≥ horizont).")

    # ── Grafy ─────────────────────────────────────────────────────────────────
    if _par_ek and _ek_rows:
        st.divider()

        # Pomocná funkce – diskontovaný CF v roce t
        def _dcf(uspora, servis, t, g, r):
            return (uspora * (1 + g) ** (t - 1) - servis) / (1 + r) ** t

        _g = _par_ek.inflace_energie
        _r = _par_ek.diskontni_sazba
        _n = _par_ek.horizont

        # ── 1. Kumulativní diskontovaný cash-flow (vč. obnov) ────────────────
        st.subheader("Kumulativní diskontovaný cash-flow")
        _cf_data = []
        _zivotnosti = st.session_state.get("op_zivotnost", {})

        for _r_op in _result_ek.vysledky:
            if not _r_op.aktivni or _r_op.investice <= 0:
                continue
            _ziv_op = _zivotnosti.get(_r_op.id, 20)
            _cf_data.append({"Rok": 0, "Opatření": _r_op.id, "Kumulativní DCF [Kč]": -_r_op.investice})
            _cum = -_r_op.investice
            for _t in range(1, _n + 1):
                _cum += _dcf(_r_op.uspora_kc, _r_op.servisni_naklady, _t, _g, _r)
                # obnova v roce = násobek životnosti
                if _ziv_op > 0 and _t % _ziv_op == 0 and _t < _n:
                    _cum -= _r_op.investice / (1 + _r) ** _t  # diskontovaná obnova
                _cf_data.append({"Rok": _t, "Opatření": _r_op.id, "Kumulativní DCF [Kč]": _cum})

        # Přebuduj kumulativu projektu správně
        _cf_proj_rows = []
        _proj_rok0_inv = sum(
            _r_op.investice for _r_op in _result_ek.vysledky
            if _r_op.aktivni and _r_op.investice > 0
        )
        _proj_cum = -_proj_rok0_inv
        _cf_proj_rows.append({"Rok": 0, "Opatření": "Projekt celkem", "Kumulativní DCF [Kč]": _proj_cum})
        for _t in range(1, _n + 1):
            for _r_op in _result_ek.vysledky:
                if not _r_op.aktivni or _r_op.investice <= 0:
                    continue
                _proj_cum += _dcf(_r_op.uspora_kc, _r_op.servisni_naklady, _t, _g, _r)
            _cf_proj_rows.append({"Rok": _t, "Opatření": "Projekt celkem", "Kumulativní DCF [Kč]": _proj_cum})

        _df_cf = _pd_ekon.DataFrame(_cf_data + _cf_proj_rows).sort_values(["Opatření", "Rok"])

        _fig_cf = px.line(
            _df_cf,
            x="Rok",
            y="Kumulativní DCF [Kč]",
            color="Opatření",
            markers=False,
            line_dash="Opatření",
            line_dash_map={"Projekt celkem": "dot"},
        )
        _fig_cf.add_hline(y=0, line_color="gray", line_dash="dash", line_width=1)
        _fig_cf.update_layout(
            plot_bgcolor="white",
            yaxis_tickformat=",.0f",
            margin=dict(t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(_fig_cf, use_container_width=True)
        st.caption(
            "Diskontovaný kumulativní cash-flow. Průsečík s nulovou osou = Tsd. "
            "Čárkovaná linie = projekt celkem."
        )

        # ── 2. NPV srovnání per opatření ──────────────────────────────────────
        st.subheader("NPV a IRR per opatření")
        _npv_data = [
            {
                "Opatření": row["ID"],
                "NPV [Kč]": row["NPV [Kč]"],
                "IRR [%]": row["IRR [%]"],
            }
            for row in _ek_rows
            if row.get("NPV [Kč]") is not None
        ]
        if _npv_data:
            _col_npv, _col_irr = st.columns(2)
            with _col_npv:
                _fig_npv = px.bar(
                    _npv_data,
                    x="Opatření",
                    y="NPV [Kč]",
                    color="NPV [Kč]",
                    color_continuous_scale=["#E74C3C", "#F39C12", "#27AE60"],
                    text_auto=".3s",
                )
                _fig_npv.add_hline(y=0, line_color="gray", line_dash="dash", line_width=1)
                _fig_npv.update_layout(
                    plot_bgcolor="white",
                    yaxis_tickformat=",.0f",
                    coloraxis_showscale=False,
                    margin=dict(t=10, b=0),
                )
                st.plotly_chart(_fig_npv, use_container_width=True)

            with _col_irr:
                _irr_data = [d for d in _npv_data if d.get("IRR [%]") is not None]
                if _irr_data:
                    _fig_irr = px.bar(
                        _irr_data,
                        x="Opatření",
                        y="IRR [%]",
                        color="IRR [%]",
                        color_continuous_scale=["#E74C3C", "#F39C12", "#27AE60"],
                        text_auto=".1f",
                    )
                    if _par_ek:
                        _fig_irr.add_hline(
                            y=_par_ek.diskontni_sazba * 100,
                            line_color="#1A5276",
                            line_dash="dot",
                            annotation_text=f"diskont {_par_ek.diskontni_sazba * 100:.1f} %",
                            annotation_position="top left",
                        )
                    _fig_irr.update_layout(
                        plot_bgcolor="white",
                        coloraxis_showscale=False,
                        margin=dict(t=10, b=0),
                    )
                    st.plotly_chart(_fig_irr, use_container_width=True)
                else:
                    st.info("IRR nelze spočítat (žádné opatření není rentabilní).")

    # ── Náklady odkladu / obětované příležitosti ──────────────────────────────
    if _par_ek and _ek_rows:
        with st.expander("⏳ Náklady odkladu (obětované příležitosti)", expanded=False):
            st.caption(
                "Kolik stojí odkládání investice? "
                "Za každý rok odkladu přicházíte o čistou úsporu (úspora − servis). "
                "Zobrazené hodnoty jsou nominální (bez diskontování)."
            )
            _net_uspora_rok = sum(
                _r_op.uspora_kc - _r_op.servisni_naklady
                for _r_op in _result_ek.vysledky
                if _r_op.aktivni and _r_op.investice > 0
            )

            if _net_uspora_rok > 0:
                _odkl_data = []
                for _odkl in [1, 2, 3, 5, 10]:
                    if _odkl <= _par_ek.horizont:
                        _ztrata_uspory = _net_uspora_rok * _odkl
                        # Ztráta na NPV: při odkladu o N let dostaneme úspory jen (horizont-N) let
                        # Přibližně: NPV_odkl ≈ NPV_ted - sum(t=1..N: dcf_t)
                        _ztrata_npv = sum(
                            _dcf(
                                sum(_r_op.uspora_kc for _r_op in _result_ek.vysledky if _r_op.aktivni and _r_op.investice > 0),
                                sum(_r_op.servisni_naklady for _r_op in _result_ek.vysledky if _r_op.aktivni and _r_op.investice > 0),
                                _t, _g, _r,
                            )
                            for _t in range(1, _odkl + 1)
                        )
                        _odkl_data.append({
                            "Odkládání [roky]": _odkl,
                            "Ušlé úspory [Kč]": round(_ztrata_uspory),
                            "Ztráta na NPV [Kč]": round(_ztrata_npv),
                        })

                if _odkl_data:
                    st.dataframe(
                        _pd_ekon.DataFrame(_odkl_data),
                        use_container_width=True, hide_index=True,
                        column_config={
                            "Ušlé úspory [Kč]": st.column_config.NumberColumn(format="%.0f Kč"),
                            "Ztráta na NPV [Kč]": st.column_config.NumberColumn(format="%.0f Kč"),
                        },
                    )

                    _fig_odkl = px.bar(
                        _odkl_data,
                        x="Odkládání [roky]",
                        y=["Ušlé úspory [Kč]", "Ztráta na NPV [Kč]"],
                        barmode="group",
                        color_discrete_map={
                            "Ušlé úspory [Kč]": "#E74C3C",
                            "Ztráta na NPV [Kč]": "#8E44AD",
                        },
                        text_auto=".3s",
                    )
                    _fig_odkl.update_layout(
                        plot_bgcolor="white",
                        yaxis_tickformat=",.0f",
                        margin=dict(t=10, b=0),
                        legend_title_text="",
                    )
                    st.plotly_chart(_fig_odkl, use_container_width=True)
                    st.caption(
                        f"Čistá roční úspora projektu: {_net_uspora_rok:,.0f} Kč/rok "
                        f"(úspora − servis). Za každý rok odkladu přijdete o tuto částku."
                    )
            else:
                st.info("Čistá úspora (úspora − servis) je nulová nebo záporná – projekt není rentabilní.")

    # ── Tabulka vyhodnocení EPC projektu ─────────────────────────────────────
    st.divider()
    st.subheader("Tabulka vyhodnocení EPC projektu")
    st.caption(
        "Strukturované vyhodnocení dle vzoru KV (Porovnání variant). "
        "Data se načítají z aktuálního stavu projektu – zadejte způsobilé výdaje a parametry dotace níže."
    )

    _epc_result = build_project().vypocitej()
    _epc_en = _epc_result.energie
    from epc_engine.emissions import FAKTORY_PRIMARNI_ENERGIE as _FPE_EPC

    # Přepočet primární energie
    _epc_fpe_ee  = _FPE_EPC["ee"]
    _epc_fpe_zp  = _FPE_EPC["zp"]
    _epc_fpe_t   = _FPE_EPC["teplo"]
    _epc_pe_pred = _epc_en.zp_total * _epc_fpe_zp + _epc_en.teplo_total * _epc_fpe_t + _epc_en.ee * _epc_fpe_ee
    _epc_pe_usp  = (
        _epc_result.celkova_uspora_zp * _epc_fpe_zp
        + _epc_result.celkova_uspora_teplo * _epc_fpe_t
        + _epc_result.celkova_uspora_ee * _epc_fpe_ee
    )
    _epc_pe_po   = _epc_pe_pred - _epc_pe_usp
    _epc_pe_pct  = _epc_pe_usp / _epc_pe_pred * 100 if _epc_pe_pred > 0 else 0.0

    # CO₂
    _epc_co2_pred = _epc_result.emise_pred.co2_kg / 1000 if _epc_result.emise_pred else 0.0
    _epc_co2_po   = _epc_result.emise_po.co2_kg   / 1000 if _epc_result.emise_po   else 0.0
    _epc_co2_usp_pct = (_epc_co2_pred - _epc_co2_po) / _epc_co2_pred * 100 if _epc_co2_pred > 0 else 0.0

    # Ekonomika
    _epc_inv    = _epc_result.celkova_investice
    _epc_usp_kc = _epc_result.celkova_uspora_kc
    _epc_servis = _epc_result.celkove_servisni_naklady
    _epc_cf     = _epc_usp_kc - _epc_servis   # roční čistý cashflow
    _epc_nav    = _epc_result.prosta_navratnost_celkem
    _epc_ek     = _epc_result.ekonomika_projekt
    _epc_par    = _epc_result.ekonomika_parametry

    # Indikátor vhodnosti pro dotaci (PE úspora ≥ 30 %)
    _epc_dotace_ok = _epc_pe_pct >= 30.0

    # ── Vstupy pro dotační výpočet ─────────────────────────────────────────────
    with st.expander("⚙️ Parametry dotačního vyhodnocení", expanded=True):
        _dc1, _dc2, _dc3 = st.columns(3)
        with _dc1:
            _epc_zpusobile = st.number_input(
                "Způsobilé výdaje [Kč]",
                min_value=0.0, step=100_000.0,
                value=float(st.session_state.get("dotace_zpusobile", _epc_inv * 0.8)),
                key="dotace_zpusobile",
                help="Část investice uznatelná jako způsobilý výdaj dle pravidel dotačního programu.",
            )
        with _dc2:
            _epc_max_pct = st.number_input(
                "Max. procento podpory [%]",
                min_value=0.0, max_value=100.0, step=1.0,
                value=float(st.session_state.get("dotace_max_pct", 68.0)),
                key="dotace_max_pct",
            )
        with _dc3:
            _epc_urok = st.number_input(
                "Úroková sazba dodav. úvěru [% p.a.]",
                min_value=0.0, max_value=20.0, step=0.5,
                value=float(st.session_state.get("dotace_urok", 6.0)),
                key="dotace_urok",
            )

    # ── Výpočet dotačních ukazatelů ────────────────────────────────────────────
    _epc_dotace_kc   = _epc_zpusobile * _epc_max_pct / 100
    _epc_inv_po_dot  = _epc_inv - _epc_dotace_kc
    _epc_nav_po_dot  = (_epc_inv_po_dot / _epc_cf) if _epc_cf > 0 else None

    # NPV po dotaci (přibližně: odečteme dotaci od investice)
    _epc_npv_po_dot = (_epc_ek.npv + _epc_dotace_kc) if _epc_ek else None

    # EPC úvěrová analýza (splácení z úspor)
    _epc_horizont = _epc_par.horizont if _epc_par else 20
    _epc_r_urok   = _epc_urok / 100
    _epc_max_splaceni = None
    if _epc_cf > 0 and _epc_inv_po_dot > 0:
        for _yr in range(1, _epc_horizont + 1):
            if _epc_r_urok > 0:
                _pv_anuity = _epc_cf * (1 - (1 + _epc_r_urok) ** (-_yr)) / _epc_r_urok
            else:
                _pv_anuity = _epc_cf * _yr
            if _pv_anuity >= _epc_inv_po_dot:
                _epc_max_splaceni = _yr
                break

    _epc_uver_celk  = (_epc_cf * _epc_max_splaceni) if _epc_max_splaceni else None
    _epc_uroku_celk = (_epc_uver_celk - _epc_inv_po_dot) if _epc_uver_celk else None
    _epc_spolucast  = max(0.0, _epc_inv_po_dot - (_epc_uver_celk or 0.0))

    # ── Tabulka výsledků ───────────────────────────────────────────────────────
    def _fmt_mil(v):
        return f"{v / 1_000_000:.2f} mil. Kč" if v else "–"
    def _fmt_pct_epc(v):
        return f"{v:.1f} %" if v is not None else "–"
    def _fmt_let_epc(v):
        return f"{v:.1f} let" if v is not None else "nehodnoceno"

    _epc_tbl_rows = [
        ("VÝCHOZÍ STAV", "", ""),
        ("Spotřeba elektrické energie", f"{_epc_en.ee:.1f}", "MWh/rok"),
        ("Spotřeba zemního plynu", f"{_epc_en.zp_total:.1f}", "MWh/rok"),
        ("Spotřeba tepelné energie (CZT)", f"{_epc_en.teplo_total:.1f}", "MWh/rok"),
        ("Celková spotřeba PNE – výchozí stav", f"{_epc_pe_pred:.1f}", "MWh/rok"),
        ("Celkové náklady na energie", f"{_epc_en.celkove_naklady:,.0f}".replace(",", "\u00a0"), "Kč/rok"),
        ("NÁVRHOVÝ STAV", "", ""),
        ("Celková spotřeba PNE – po realizaci", f"{_epc_pe_po:.1f}", "MWh/rok"),
        ("Roční úspora nákladů", f"{_epc_usp_kc:,.0f}".replace(",", "\u00a0"), "Kč/rok"),
        ("Roční servisní náklady", f"{_epc_servis:,.0f}".replace(",", "\u00a0"), "Kč/rok"),
        ("Roční čistý cashflow projektu", f"{_epc_cf:,.0f}".replace(",", "\u00a0"), "Kč/rok"),
        ("ÚSPORA ENERGIE", "", ""),
        ("Úspora PNE", f"{_epc_pe_usp:.1f}", "MWh/rok"),
        ("Úspora PNE [%]", _fmt_pct_epc(_epc_pe_pct), "%"),
        ("Vhodné pro dotaci (PE úspora ≥ 30 %)", "ANO ✓" if _epc_dotace_ok else "NE ✗", ""),
        ("EKONOMICKÉ VYHODNOCENÍ BEZ DOTACE", "", ""),
        ("Předpokládaná investice", f"{_epc_inv:,.0f}".replace(",", "\u00a0"), "Kč"),
        ("Prostá doba návratnosti", _fmt_let_epc(_epc_nav), "roky"),
        ("NPV", f"{_epc_ek.npv:,.0f}".replace(",", "\u00a0") if _epc_ek else "–", "Kč"),
        ("IRR", _fmt_pct_epc(_epc_ek.irr * 100 if _epc_ek and _epc_ek.irr else None), "%"),
        ("Diskontovaná doba návratnosti (Tsd)", _fmt_let_epc(_epc_ek.tsd if _epc_ek else None), "roky"),
        ("EKOLOGICKÉ VYHODNOCENÍ", "", ""),
        ("Produkce CO₂ – výchozí stav", f"{_epc_co2_pred:.2f}", "t CO₂/rok"),
        ("Produkce CO₂ – po realizaci", f"{_epc_co2_po:.2f}", "t CO₂/rok"),
        ("Úspora emisí CO₂", _fmt_pct_epc(_epc_co2_usp_pct), "%"),
        ("DOTAČNÍ VYHODNOCENÍ", "", ""),
        ("Způsobilé výdaje", f"{_epc_zpusobile:,.0f}".replace(",", "\u00a0"), "Kč"),
        ("Max. procento podpory", _fmt_pct_epc(_epc_max_pct), "%"),
        ("Max. výše dotace", f"{_epc_dotace_kc:,.0f}".replace(",", "\u00a0"), "Kč"),
        ("Investice po odečtení dotace", f"{_epc_inv_po_dot:,.0f}".replace(",", "\u00a0"), "Kč"),
        ("Prostá návratnost po dotaci", _fmt_let_epc(_epc_nav_po_dot), "roky"),
        ("NPV po dotaci", f"{_epc_npv_po_dot:,.0f}".replace(",", "\u00a0") if _epc_npv_po_dot is not None else "–", "Kč"),
        ("EPC ÚVĚROVÁ ANALÝZA", "", ""),
        ("Úroková sazba dodavatelského úvěru", _fmt_pct_epc(_epc_urok), "% p.a."),
        ("Max. délka splácení z úspor", _fmt_let_epc(_epc_max_splaceni), "roky"),
        ("Celková výše úvěru (splátky z úspor)", f"{_epc_uver_celk:,.0f}".replace(",", "\u00a0") if _epc_uver_celk else "–", "Kč"),
        ("Celková výše úroků", f"{_epc_uroku_celk:,.0f}".replace(",", "\u00a0") if _epc_uroku_celk else "–", "Kč"),
        ("Nutná spoluúčast zadavatele", f"{_epc_spolucast:,.0f}".replace(",", "\u00a0") if _epc_max_splaceni else "–", "Kč"),
    ]

    _df_epc = _pd_ekon.DataFrame(_epc_tbl_rows, columns=["Parametr", "Hodnota", "Jednotka"])
    st.dataframe(
        _df_epc,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Parametr": st.column_config.TextColumn(width="large"),
            "Hodnota":  st.column_config.TextColumn(width="medium"),
            "Jednotka": st.column_config.TextColumn(width="small"),
        },
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 – Emisní bilance
# ══════════════════════════════════════════════════════════════════════════════

with tab_emise:
    _result_em = build_project().vypocitej()
    _em_pred = _result_em.emise_pred
    _em_po = _result_em.emise_po

    st.subheader("Emisní bilance – stav před a po opatřeních")
    st.caption(
        "Zdroj emisních faktorů: vyhláška 141/2021 Sb., příloha 3. "
        "EPS = 1,0×TZL + 0,88×NOₓ + 0,54×SO₂ + 0,64×NH₃."
    )

    if _em_pred and _em_po:
        _em_col_pred, _em_col_po, _em_col_delta = st.columns(3)

        def _fmt_em(v: float, unit: str = "kg") -> str:
            if v >= 1000:
                return f"{v / 1000:.2f} t"
            return f"{v:.1f} {unit}"

        with _em_col_pred:
            st.markdown("**Stávající stav**")
            st.metric("CO₂", _fmt_em(_em_pred.co2_kg))
            st.metric("NOₓ", f"{_em_pred.nox_kg:.1f} kg")
            st.metric("SO₂", f"{_em_pred.so2_kg:.1f} kg")
            st.metric("TZL", f"{_em_pred.tzl_kg:.2f} kg")
            st.metric("EPS", f"{_em_pred.eps_kg:.2f} kg")

        with _em_col_po:
            st.markdown("**Po opatřeních**")
            st.metric("CO₂", _fmt_em(_em_po.co2_kg))
            st.metric("NOₓ", f"{_em_po.nox_kg:.1f} kg")
            st.metric("SO₂", f"{_em_po.so2_kg:.1f} kg")
            st.metric("TZL", f"{_em_po.tzl_kg:.2f} kg")
            st.metric("EPS", f"{_em_po.eps_kg:.2f} kg")

        with _em_col_delta:
            st.markdown("**Snížení**")
            _delta_co2 = _em_pred.co2_kg - _em_po.co2_kg
            _delta_nox = _em_pred.nox_kg - _em_po.nox_kg
            _delta_so2 = _em_pred.so2_kg - _em_po.so2_kg
            _delta_tzl = _em_pred.tzl_kg - _em_po.tzl_kg
            _delta_eps = _em_pred.eps_kg - _em_po.eps_kg
            st.metric("CO₂", _fmt_em(_delta_co2), delta=f"{_fmt_em(_delta_co2)} ↓")
            st.metric("NOₓ", f"{_delta_nox:.1f} kg")
            st.metric("SO₂", f"{_delta_so2:.1f} kg")
            st.metric("TZL", f"{_delta_tzl:.2f} kg")
            st.metric("EPS", f"{_delta_eps:.2f} kg")

        # Tabulkový přehled
        st.divider()
        _em_tbl = _pd_ekon.DataFrame({
            "Látka": ["CO₂ [t/rok]", "NOₓ [kg/rok]", "SO₂ [kg/rok]", "TZL [kg/rok]", "EPS [kg/rok]"],
            "Stávající stav": [
                round(_em_pred.co2_kg / 1000, 2),
                round(_em_pred.nox_kg, 1),
                round(_em_pred.so2_kg, 1),
                round(_em_pred.tzl_kg, 2),
                round(_em_pred.eps_kg, 2),
            ],
            "Po opatřeních": [
                round(_em_po.co2_kg / 1000, 2),
                round(_em_po.nox_kg, 1),
                round(_em_po.so2_kg, 1),
                round(_em_po.tzl_kg, 2),
                round(_em_po.eps_kg, 2),
            ],
            "Snížení": [
                round(_delta_co2 / 1000, 2),
                round(_delta_nox, 1),
                round(_delta_so2, 1),
                round(_delta_tzl, 2),
                round(_delta_eps, 2),
            ],
        })
        st.dataframe(_em_tbl, use_container_width=True, hide_index=True)

        # ── Primární energie (neobnovitelná) ──────────────────────────────────
        st.divider()
        st.subheader("Primární energie z neobnovitelných zdrojů (PE,nOZE)")
        st.caption(
            "Vyhl. 264/2020 Sb., příloha 3, ve znění novely č. 222/2024 Sb. "
            "fpe,nOZE: ZP = 1,0 · Teplo (CZT) = 1,3 · EE = 2,1."
        )

        from epc_engine.emissions import FAKTORY_PRIMARNI_ENERGIE as _FPE_EM
        _fpe_zp_em = _FPE_EM["zp"]
        _fpe_t_em = _FPE_EM["teplo"]
        _fpe_ee_em = _FPE_EM["ee"]
        _en_em = _result_em.energie
        _pe_pred_em = (
            _en_em.zp_total * _fpe_zp_em
            + _en_em.teplo_total * _fpe_t_em
            + _en_em.ee * _fpe_ee_em
        )
        _pe_uspora_em = (
            _result_em.celkova_uspora_zp * _fpe_zp_em
            + _result_em.celkova_uspora_teplo * _fpe_t_em
            + _result_em.celkova_uspora_ee * _fpe_ee_em
        )
        _pe_po_em = _pe_pred_em - _pe_uspora_em
        _pe_pct_em = (_pe_uspora_em / _pe_pred_em * 100) if _pe_pred_em > 0 else 0.0

        _pe_c1, _pe_c2, _pe_c3 = st.columns(3)
        _pe_c1.metric("PE,nOZE před", f"{_pe_pred_em:,.0f} MWh/rok")
        _pe_c2.metric("PE,nOZE po", f"{_pe_po_em:,.0f} MWh/rok")
        _pe_c3.metric(
            "Úspora PE,nOZE",
            f"{_pe_uspora_em:,.0f} MWh/rok",
            delta=f"−{_pe_pct_em:.1f} %",
        )

        # Složkový bar chart – příspěvek nosičů k PE
        _pe_bar_data = []
        for _nosic, _spotreba_pred, _spotreba_po, _fpe_val in [
            ("Zemní plyn", _en_em.zp_total, _en_em.zp_total - _result_em.celkova_uspora_zp, _fpe_zp_em),
            ("Teplo (CZT)", _en_em.teplo_total, _en_em.teplo_total - _result_em.celkova_uspora_teplo, _fpe_t_em),
            ("Elektřina", _en_em.ee, _en_em.ee - _result_em.celkova_uspora_ee, _fpe_ee_em),
        ]:
            if _spotreba_pred > 0:
                _pe_bar_data.append({"Nosič": _nosic, "Stav": "Před", "PE,nOZE [MWh]": _spotreba_pred * _fpe_val})
                _pe_bar_data.append({"Nosič": _nosic, "Stav": "Po", "PE,nOZE [MWh]": max(0.0, _spotreba_po) * _fpe_val})

        if _pe_bar_data:
            _fig_pe = px.bar(
                _pd_ekon.DataFrame(_pe_bar_data),
                x="Stav",
                y="PE,nOZE [MWh]",
                color="Nosič",
                barmode="stack",
                color_discrete_map={
                    "Zemní plyn": "#E59866",
                    "Teplo (CZT)": "#C0392B",
                    "Elektřina": "#F4D03F",
                },
                text_auto=".0f",
            )
            _fig_pe.update_layout(
                plot_bgcolor="white",
                yaxis_tickformat=",.0f",
                margin=dict(t=10, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(_fig_pe, use_container_width=True)

    else:
        st.info("Zadejte spotřeby energií v záložce Vstupní data.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 – Klasifikace obálky budovy (A–G)
# ══════════════════════════════════════════════════════════════════════════════

with tab_klasifikace:
    _result_kl = build_project().vypocitej()
    _klas = _result_kl.klasifikace_pred

    st.subheader("Klasifikace obálky budovy")
    st.caption(
        "Dle ČSN 73 0540-2 a vyhlášky 264/2020 Sb. "
        "Uem,N = 0,30 + 0,15 / (A/V)  [W/m²K]."
    )

    if _klas:
        _trida_barvy = {
            "A": "success", "B": "success",
            "C": "info",
            "D": "warning", "E": "warning",
            "F": "error", "G": "error",
        }
        _trida_popisy = {
            "A": "Mimořádně úsporná",
            "B": "Velmi úsporná",
            "C": "Úsporná (referenční nová budova)",
            "D": "Méně úsporná",
            "E": "Nehospodárná",
            "F": "Velmi nehospodárná",
            "G": "Mimořádně nehospodárná",
        }
        _typ_upozorneni = _trida_barvy.get(_klas.trida, "info")
        _popis_tridy = _trida_popisy.get(_klas.trida, "")
        _msg = (
            f"Budova je zařazena do třídy **{_klas.trida}** – {_popis_tridy}  \n"
            f"Uem = {_klas.uem:.3f} W/m²K | Uem,N = {_klas.uem_n:.3f} W/m²K | "
            f"Uem/Uem,N = {_klas.pomer:.3f}"
        )
        if _typ_upozorneni == "success":
            st.success(_msg)
        elif _typ_upozorneni == "warning":
            st.warning(_msg)
        else:
            st.error(_msg)

        st.divider()
        _kl_c1, _kl_c2, _kl_c3, _kl_c4 = st.columns(4)
        _kl_c1.metric("Uem [W/m²K]", f"{_klas.uem:.3f}")
        _kl_c2.metric("Uem,N [W/m²K]", f"{_klas.uem_n:.3f}")
        _kl_c3.metric("Uem / Uem,N", f"{_klas.pomer:.3f}")
        _kl_c4.metric("Třída", _klas.trida)

        # Tabulka mezních hodnot
        st.divider()
        st.markdown("**Mezní hodnoty Uem/Uem,N pro třídy A–G:**")
        _meze_tbl = _pd_ekon.DataFrame({
            "Třída": ["A", "B", "C", "D", "E", "F", "G"],
            "Popis": [
                "Mimořádně úsporná", "Velmi úsporná", "Úsporná (referenční)",
                "Méně úsporná", "Nehospodárná", "Velmi nehospodárná", "Mimořádně nehospodárná",
            ],
            "Uem/Uem,N ≤": ["0,50", "0,75", "1,00", "1,50", "2,00", "2,50", "> 2,50"],
            "Uem ≤ [W/m²K]": [
                f"{0.50 * _klas.uem_n:.3f}", f"{0.75 * _klas.uem_n:.3f}",
                f"{1.00 * _klas.uem_n:.3f}", f"{1.50 * _klas.uem_n:.3f}",
                f"{2.00 * _klas.uem_n:.3f}", f"{2.50 * _klas.uem_n:.3f}", "–",
            ],
        })
        st.dataframe(_meze_tbl, use_container_width=True, hide_index=True)
    else:
        st.info(
            "Zadejte **Uem stávající** a **objem budovy + plochu ochlazované obálky** v postranním panelu "
            "(sekce 'Ob\u00e1lka budovy' a z\u00e1lo\u017eka Identifikace > Budovy)."
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 – Obálka budovy & technické systémy (Sprint 4)
# ══════════════════════════════════════════════════════════════════════════════

with tab_obalka:

    st.subheader("Tepelně technické vlastnosti obálky budovy")
    st.caption(
        "Zadejte stavební konstrukce pro výpočet U-hodnot dle ČSN EN ISO 6946. "
        "Pro okna a dveře lze zadat U přímo. Data se promítnou do sekce B.3 EP/EA."
    )

    # ── Klimatická data (pro sekci B.2 – historii spotřeby) ───────────────────
    with st.expander("Klimatická data lokality (sekce B.2)", expanded=False):
        col_lok, col_d = st.columns(2)
        with col_lok:
            st.text_input("Lokalita (meteorologická stanice)", key="klima_lokalita",
                          placeholder="Praha, Brno-Tuřany, …")
        with col_d:
            st.number_input("Normované denostupně D [°C·dny/rok]",
                            key="klima_stupnodni_norm",
                            min_value=0.0, step=100.0)
        col_ti, col_te = st.columns(2)
        with col_ti:
            st.number_input("Vnitřní výpočtová teplota ti [°C]",
                            key="klima_ti", step=0.5)
        with col_te:
            st.number_input("Venkovní výpočtová teplota te [°C]",
                            key="klima_te", step=0.5)

    st.divider()

    # ── Správa seznamu konstrukcí ─────────────────────────────────────────────
    konstrukce_list = st.session_state.get("konstrukce_obalka", [])
    updated_konstrukce = list(konstrukce_list)

    _TYP_OPTIONS = list(TYP_POPISY.keys())
    _TYP_LABELS = list(TYP_POPISY.values())

    for i, k in enumerate(updated_konstrukce):
        with st.expander(
            f"Konstrukce {i+1}: {k.get('nazev') or TYP_POPISY.get(k.get('typ','stena'), '')}",
            expanded=False
        ):
            col_naz, col_typ = st.columns(2)
            with col_naz:
                k["nazev"] = st.text_input("Název", value=k.get("nazev", ""),
                                           key=f"ko_{i}_naz",
                                           placeholder="Obvodová stěna")
            with col_typ:
                typ_idx = _TYP_OPTIONS.index(k.get("typ", "stena")) if k.get("typ", "stena") in _TYP_OPTIONS else 0
                chosen_typ = st.selectbox("Typ", _TYP_LABELS, index=typ_idx,
                                          key=f"ko_{i}_typ")
                k["typ"] = _TYP_OPTIONS[_TYP_LABELS.index(chosen_typ)]

            col_pl, col_un = st.columns(2)
            with col_pl:
                k["plocha_m2"] = st.number_input("Plocha [m²]",
                                                  value=float(k.get("plocha_m2", 0.0)),
                                                  min_value=0.0, step=10.0,
                                                  key=f"ko_{i}_pl")
            with col_un:
                _un_default = un_pozadovana(k.get("typ", "stena"))
                k["un_value"] = st.number_input("UN [W/m²K] (normový)",
                                                 value=float(k.get("un_value", _un_default)),
                                                 min_value=0.0, step=0.01, format="%.2f",
                                                 key=f"ko_{i}_un")

            primy_vstup = st.checkbox(
                "Zadat U přímo (okno/dveře nebo přímé měření)",
                value=(k.get("u_zadane", "") != ""),
                key=f"ko_{i}_primy"
            )
            if primy_vstup:
                k["u_zadane"] = st.number_input(
                    "U přímo [W/m²K]",
                    value=float(k.get("u_zadane") or 1.0),
                    min_value=0.0, step=0.1, format="%.2f",
                    key=f"ko_{i}_uprimy"
                )
                vrstvy_for_calc = []
            else:
                k["u_zadane"] = ""
                # Tabulka vrstev
                st.markdown("**Složení konstrukce (vrstvy)**")
                vrstvy = k.get("vrstvy", [])
                vrstvy_df_data = {
                    "Název materiálu": [v.get("nazev", "") for v in vrstvy],
                    "d [mm]": [v.get("tloustka_mm", 0.0) for v in vrstvy],
                    "λ [W/(m·K)]": [v.get("lambda_wm", 0.0) for v in vrstvy],
                }
                import pandas as _pd_obalka
                _df_vrstvy = _pd_obalka.DataFrame(vrstvy_df_data)
                edited = st.data_editor(
                    _df_vrstvy,
                    key=f"ko_{i}_vrstvy",
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "Název materiálu": st.column_config.TextColumn(width="medium"),
                        "d [mm]": st.column_config.NumberColumn(min_value=0.0, step=1.0, format="%.0f"),
                        "λ [W/(m·K)]": st.column_config.NumberColumn(min_value=0.0, step=0.01, format="%.3f"),
                    }
                )
                k["vrstvy"] = [
                    {
                        "nazev": str(row["Název materiálu"]),
                        "tloustka_mm": float(row["d [mm]"]) if row["d [mm]"] else 0.0,
                        "lambda_wm": float(row["λ [W/(m·K)]"]) if row["λ [W/(m·K)]"] else 0.0,
                    }
                    for _, row in edited.iterrows()
                ]
                vrstvy_for_calc = [
                    Vrstva(v["nazev"], v["tloustka_mm"] / 1000, v["lambda_wm"])
                    for v in k["vrstvy"]
                ]

            # Live výpočet U
            if primy_vstup:
                u_val = float(k.get("u_zadane") or 0)
            else:
                from epc_engine.tepelna_technika import vypocitej_u_z_vrstev as _calc_u
                u_val = _calc_u(vrstvy_for_calc, k.get("typ", "stena"))

            un_val = float(k.get("un_value", 0.0))
            col_u, col_hodnoceni, col_rm = st.columns([1, 1, 0.5])
            with col_u:
                st.metric("U [W/m²K]", f"{u_val:.3f}")
            with col_hodnoceni:
                if un_val > 0:
                    if u_val <= un_val:
                        st.success("✓ Vyhovuje normě")
                    else:
                        st.error(f"✗ Nevyhovuje (UN = {un_val:.2f})")
            with col_rm:
                if st.button("Odebrat", key=f"ko_{i}_rm"):
                    updated_konstrukce.pop(i)
                    st.session_state["konstrukce_obalka"] = updated_konstrukce
                    st.rerun()

    if st.button("+ Přidat konstrukci"):
        updated_konstrukce.append({
            "nazev": "", "typ": "stena", "plocha_m2": 0.0,
            "u_zadane": "", "un_value": 0.30, "vrstvy": [],
        })
    st.session_state["konstrukce_obalka"] = updated_konstrukce

    st.divider()

    # ── Technické systémy (B.4) ───────────────────────────────────────────────
    st.subheader("Technické systémy")
    st.caption("Pasport technických systémů objektu – kombinace strukturovaných polí a volného textu.")

    _sys_def = [
        ("Vytápění", "ts_vytapeni"),
        ("Příprava teplé vody (TUV)", "ts_tuv"),
        ("Vzduchotechnika a větrání (VZT)", "ts_vzt"),
        ("Osvětlení", "ts_osvetleni"),
    ]
    for sys_label, sys_key in _sys_def:
        with st.expander(sys_label, expanded=False):
            col_t, col_v = st.columns(2)
            with col_t:
                st.text_input("Typ / zdroj", key=f"{sys_key}_typ",
                              placeholder="Např. plynový kondenzační kotel, LED svítidla")
            with col_v:
                if sys_key != "ts_osvetleni":
                    st.number_input("Instalovaný výkon [kW]", key=f"{sys_key}_vykon",
                                    min_value=0.0, step=10.0)
            if sys_key not in ("ts_osvetleni",):
                col_uc, col_rok = st.columns(2)
                with col_uc:
                    st.number_input("Účinnost [%]", key=f"{sys_key}_ucinnost",
                                    min_value=0.0, max_value=200.0, step=1.0)
                with col_rok:
                    st.number_input("Rok instalace", key=f"{sys_key}_rok",
                                    min_value=1900, max_value=2030, step=1,
                                    value=int(st.session_state.get(f"{sys_key}_rok", 2000) or 2000))
            st.text_area("Popis (volný text)", key=f"{sys_key}_popis", height=80)

    with st.expander("MaR a monitoring spotřeb", expanded=False):
        st.text_area("Popis systému měření, regulace a monitoringu",
                     key="ts_mar", height=100,
                     placeholder="Centrální řízení pomocí MaR Siemens DESIGO, měření spotřeby tepla …")

    st.divider()

    # ── Bilance dle účelu (příloha č. 4 vyhl. 141/2021) ──────────────────────
    st.subheader("Energetická bilance dle způsobu užití")
    st.caption(
        "Příloha č. 4 vyhl. 141/2021 Sb. "
        "Součet MWh by měl odpovídat celkové referenční spotřebě energií."
    )

    _bilance_keys = [
        ("Vytápění", "bilance_vytapeni_mwh"),
        ("Chlazení", "bilance_chlazeni_mwh"),
        ("Příprava teplé vody", "bilance_tuv_mwh"),
        ("Nucené větrání", "bilance_vetrání_mwh"),
        ("Osvětlení", "bilance_osvetleni_mwh"),
        ("Technologie a spotřebiče", "bilance_technologie_mwh"),
        ("PHM", "bilance_phm_mwh"),
    ]
    col_bil1, col_bil2 = st.columns(2)
    for idx, (label, key) in enumerate(_bilance_keys):
        col = col_bil1 if idx % 2 == 0 else col_bil2
        with col:
            st.number_input(f"{label} [MWh/rok]", key=key, min_value=0.0, step=5.0)

    _celkem_bil = sum(
        st.session_state.get(k, 0.0) for _, k in _bilance_keys
    )
    st.info(f"Zadaný součet: **{_celkem_bil:,.1f} MWh/rok**".replace(",", "\u00a0"))

    st.divider()

    # ── PENB data (D.4) ───────────────────────────────────────────────────────
    st.subheader("Data průkazu energetické náročnosti budovy (PENB)")
    st.caption(
        "Výsledky z externího softwaru (Energie+, TechCon…). "
        "Klasifikace dle vyhlášky č. 264/2020 Sb."
    )

    _tridy = ["", "A", "B", "C", "D", "E", "F", "G"]
    col_ps, col_pn = st.columns(2)
    with col_ps:
        st.selectbox("Klasifikační třída – stávající stav", _tridy,
                     index=_tridy.index(st.session_state.get("penb_trida_stav", "") or ""),
                     key="penb_trida_stav")
    with col_pn:
        st.selectbox("Klasifikační třída – navrhovaný stav", _tridy,
                     index=_tridy.index(st.session_state.get("penb_trida_nav", "") or ""),
                     key="penb_trida_nav")

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.number_input("Měrná potřeba tepla [kWh/(m²·rok)]",
                        key="penb_potreba_tepla", min_value=0.0, step=5.0)
    with col_p2:
        st.number_input("Celková dodaná energie [kWh/(m²·rok)]",
                        key="penb_dodana_energie", min_value=0.0, step=5.0)
    with col_p3:
        st.number_input("Primární energie z neobn. zdrojů [kWh/(m²·rok)]",
                        key="penb_primarni", min_value=0.0, step=5.0)

    col_pp, col_ppos = st.columns(2)
    with col_pp:
        st.number_input("Energeticky vztažná plocha [m²]",
                        key="penb_plocha", min_value=0.0, step=10.0)
    with col_ppos:
        st.text_input("Poznámka (zpracovatel PENB, datum, č. oprávnění)",
                      key="penb_poznamka",
                      placeholder="Ing. Novák, 03/2026, č. opr. OP-123")

    st.divider()

    # ── EnMS hodnocení (B.5.2 / C.3) ─────────────────────────────────────────
    st.subheader("Hodnocení EnMS dle ČSN EN ISO 50001")
    st.caption(
        "Škála: 0 = nezadáno, 1 = nesplnění, 2 = částečné splnění, 3 = plné splnění"
    )
    st.checkbox("Organizace má certifikovaný EnMS dle ISO 50001",
                key="enms_certifikovan")
    for _ei, _en in enumerate(_ENMS_OBLASTI_NAZVY):
        with st.expander(_en, expanded=False):
            col_h, col_s = st.columns([1, 4])
            with col_h:
                st.selectbox(
                    "Hodnocení",
                    options=[0, 1, 2, 3],
                    format_func=lambda x: {0: "–", 1: "1 – Nesplnění", 2: "2 – Částečné", 3: "3 – Plné"}[x],
                    key=f"enms_{_ei}_h",
                )
            with col_s:
                st.text_area(
                    "Popis stávajícího stavu",
                    key=f"enms_{_ei}_stav",
                    height=80,
                    label_visibility="visible",
                )
    st.text_area(
        "Komentář k celkovému hodnocení EnMS",
        key="enms_komentar",
        height=80,
    )

    st.divider()

    # ── Okrajové podmínky (sekce E) ───────────────────────────────────────────
    st.subheader("Okrajové podmínky")
    st.text_area(
        "Text okrajových podmínek výpočtu (sekce E dle vyhl. 141/2021)",
        key="okrajove_podminky",
        height=120,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Helper functions for conditionally-rendered tabs
# ══════════════════════════════════════════════════════════════════════════════

def _render_plan_ea_tab():
    st.subheader("Plán energetického auditu")
    st.caption(
        "Příloha č. 2 k vyhl. č. 140/2021 Sb. | "
        "Podepsaný plán je povinnou přílohou zprávy EA (§ 10 písm. a))."
    )

    # ── Formální náležitosti ──────────────────────────────────────────────────
    with st.expander("📋 Formální náležitosti", expanded=True):
        col_dat, col_zas = st.columns(2)
        with col_dat:
            st.text_input(
                "Datum zpracování plánu",
                key="plan_ea_datum",
                placeholder="dd.mm.rrrr",
            )
        with col_zas:
            _zas_placeholder = st.session_state.get("zadavatel_kontakt", "")
            st.text_input(
                "Zástupce zadavatele (jméno + funkce)",
                key="plan_ea_zadavatel_zastupce",
                placeholder=_zas_placeholder or "Ing. Jana Nováková, ředitelka",
                help="Osoba oprávněná podepsat plán za zadavatele",
            )
        _spec = st.session_state.get("zpracovatel_zastupce", "–")
        _oprav = st.session_state.get("cislo_opravneni", "–")
        st.info(
            f"Energetický specialista: **{_spec}** | Č. oprávnění: **{_oprav}**  "
            "_(edituje se v záložce 📁 Projekt → Vstupní data)_"
        )

    # ── Oddíl 1: Míra detailu ─────────────────────────────────────────────────
    _UROVNE_POPIS = {
        1: "Přehledový audit (walk-through) – základní prohlídka, identifikace zjevných příležitostí, bez podrobného měření.",
        2: "Úplný audit – revize historické spotřeby, místní šetření, výpočtové hodnocení opatření, ekonomická analýza.",
        3: "Detailní audit – podrobné měření, energetické modelování, analýza citlivosti pro klíčová opatření.",
    }
    with st.expander("1. Míra detailu", expanded=True):
        _uroven = st.radio(
            "Úroveň dle přílohy A3 ČSN ISO 50002",
            options=[1, 2, 3],
            format_func=lambda x: f"Úroveň {x}",
            index=int(st.session_state.get("plan_ea_uroven", 2) or 2) - 1,
            horizontal=True,
            key="plan_ea_uroven",
        )
        st.caption(_UROVNE_POPIS.get(_uroven, ""))

    # ── Oddíl 2: Předmět EA ───────────────────────────────────────────────────
    with st.expander("2. Předmět energetického auditu", expanded=True):
        # Přehled objektů projektu
        _proj_objekty = st.session_state.get("objekty", [])
        _obj_radky = []
        for _oi, _obj in enumerate(_proj_objekty):
            _on = _obj.get("objekt_nazev") or f"Objekt {_oi + 1}"
            _oa = _obj.get("objekt_adresa", "")
            _obj_radky.append(f"**{_on}**" + (f" – {_oa}" if _oa else ""))
        if _obj_radky:
            st.info("Objekty projektu: " + " | ".join(_obj_radky))

        _SYSTEMY_MOZNOSTI = [
            "Vytápění", "Chlazení", "Vzduchotechnika", "Teplá užitková voda",
            "Elektrická energie", "Osvětlení", "Technologie / výroba",
            "Fotovoltaická elektrárna (FVE)", "Kogenerace (KVET)", "Ostatní",
        ]
        st.multiselect(
            "Energetické systémy zahrnuté v auditu",
            options=_SYSTEMY_MOZNOSTI,
            key="plan_ea_systemy",
            help="Vyberte všechny systémy, které budou předmětem hodnocení",
        )

        # Lokalizace – auto-populate z aktivního objektu
        _lokace_hint = st.session_state.get("objekt_adresa", "")
        st.text_input(
            "Lokalizace předmětu EA (adresa / katastr)",
            key="plan_ea_lokalizace",
            placeholder=_lokace_hint or "Ulice, obec, katastrální území, parcelní čísla",
        )
        st.text_area(
            "Doplňující vymezení rozsahu (volitelné)",
            key="plan_ea_predmet_poznamka",
            height=70,
            placeholder="Např.: Systémová hranice zahrnuje pouze vytápění a TUV. Technologie v nájmu jsou vyloučeny.",
        )

    # ── Oddíl 3: Potřeby a cíle ───────────────────────────────────────────────
    _CILE_MOZNOSTI = [
        "Snížení nákladů na energie",
        "Splnění zákonné povinnosti (§ 9 zákona č. 406/2000 Sb.)",
        "Příprava podkladů pro EPC (energetické služby se zárukou)",
        "Žádost o dotaci (OPŽP, NZÚ, EFEKT, MPO)",
        "Příprava průkazu energetické náročnosti budovy (PENB)",
        "Snížení emisí CO₂ / dekarbonizace",
        "Plánování investic do rekonstrukce",
        "Certifikace / ESG reporting",
    ]
    with st.expander("3. Potřeby zadavatele a jeho očekávání", expanded=True):
        st.multiselect(
            "Hlavní cíle zadavatele",
            options=_CILE_MOZNOSTI,
            key="plan_ea_cile_seznam",
        )
        _cil_pct_val = float(st.session_state.get("plan_ea_cil_uspory_pct", 0) or 0)
        _show_pct = "Snížení nákladů na energie" in st.session_state.get("plan_ea_cile_seznam", []) \
                    or _cil_pct_val > 0
        if _show_pct:
            st.number_input(
                "Cílová úspora spotřeby / nákladů [%] (0 = neurčeno)",
                key="plan_ea_cil_uspory_pct",
                min_value=0, max_value=100, step=5,
            )
        st.text_area(
            "Doplňující požadavky (volitelné)",
            key="plan_ea_potreby",
            height=70,
            placeholder="Specifické podmínky, priority nebo omezení zadavatele.",
        )

    # ── Oddíl 4: Kritéria hodnocení ──────────────────────────────────────────
    _UKAZATELE_MOZNOSTI = [
        "NPV", "IRR", "Ts (prostá)", "Tsd (reálná)",
        "LCOE [Kč/MWh]", "Úspora CO₂ [t/rok]", "Specifická cena úspory [Kč/MWh]",
    ]
    _MKH_MOZNOSTI = [
        "Ekonomická efektivnost (NPV)",
        "Technická proveditelnost a spolehlivost",
        "Úspora CO₂ a vliv na klima",
        "Vliv na energetickou třídu budovy (PENB)",
        "Provozní dostupnost / minimální výpadky",
        "Sociální přijatelnost / vliv na komfort",
        "Soulad se strategickými dokumenty",
    ]
    with st.expander("4. Kritéria pro hodnocení příležitostí", expanded=True):
        st.multiselect(
            "Ekonomické ukazatele hodnocení",
            options=_UKAZATELE_MOZNOSTI,
            key="plan_ea_ukazatele_seznam",
        )
        _h = st.session_state.get("horizont_let", 20)
        _d = st.session_state.get("diskontni_sazba", 4.0)
        _i = st.session_state.get("inflace_energie", 3.0)
        _kc1, _kc2, _kc3 = st.columns(3)
        _kc1.metric("Horizont hodnocení", f"{_h} let")
        _kc2.metric("Diskontní sazba", f"{_d:.1f} %")
        _kc3.metric("Inflace cen energií", f"{_i:.1f} %")
        st.caption("Parametry se nastavují v levém panelu a platí pro celý projekt.")
        st.checkbox(
            "Zahrnout možnosti finanční podpory (dotace, úvěry SFŽP)",
            key="plan_ea_dotace",
        )
        st.multiselect(
            "Kritéria MKH (příloha č. 9 vyhl. 140/2021)",
            options=_MKH_MOZNOSTI,
            key="plan_ea_mkh_seznam",
        )

    # ── Oddíl 5: Součinnost a harmonogram ────────────────────────────────────
    _SOUC_MOZNOSTI = [
        "Zajistit přístup do všech prostor objektu",
        "Přidělit kontaktní osobu odpovědnou za součinnost",
        "Dodat podklady dle přiloženého seznamu",
        "Zajistit přítomnost správce / provozovatele při místním šetření",
        "Poskytnout fakturační data za energii (min. 3 roky)",
        "Informovat o plánovaných rekonstrukcích a investicích",
        "Zpřístupnit výkresovou dokumentaci a revizní zprávy",
    ]
    with st.expander("5. Součinnost zadavatele a harmonogram"):
        st.multiselect(
            "Požadavky na součinnost",
            options=_SOUC_MOZNOSTI,
            key="plan_ea_soucinnost_seznam",
        )
        st.caption("Harmonogram – klíčové milníky:")
        _hc1, _hc2 = st.columns(2)
        with _hc1:
            st.text_input("Zahájení auditu", key="plan_ea_datum_zahajeni_plan",
                          placeholder="MM/RRRR")
            st.text_input("Předání návrhu zprávy", key="plan_ea_datum_navrhu",
                          placeholder="MM/RRRR")
        with _hc2:
            st.text_input("Místní šetření", key="plan_ea_datum_setreni",
                          placeholder="MM/RRRR")
            st.text_input("Finalizace a předání", key="plan_ea_datum_finalizace",
                          placeholder="MM/RRRR")

    # ── Oddíl 6: Strategické dokumenty ───────────────────────────────────────
    with st.expander("6. Strategické dokumenty zadavatele"):
        st.caption(
            "Dokumenty, které ovlivňují zadání nebo výstupy EA "
            "(územní energetické koncepce, SEAP/SECAP, strategické plány apod.)."
        )
        _dok_list = list(st.session_state.get("plan_ea_strategicke_dok_list", []))
        _dok_to_remove = None
        for _di, _dok in enumerate(_dok_list):
            _dcol1, _dcol2 = st.columns([10, 1])
            with _dcol1:
                _dok_list[_di] = st.text_input(
                    f"Dokument {_di + 1}", value=_dok,
                    key=f"_plan_dok_{_di}",
                    label_visibility="collapsed",
                    placeholder="Název dokumentu / instituce",
                )
            with _dcol2:
                if st.button("✕", key=f"_rm_dok_{_di}", help="Odebrat"):
                    _dok_to_remove = _di
        if _dok_to_remove is not None:
            _dok_list.pop(_dok_to_remove)
            st.session_state["plan_ea_strategicke_dok_list"] = _dok_list
            st.rerun()
        if st.button("+ Přidat dokument", key="_add_dok"):
            _dok_list.append("")
            st.session_state["plan_ea_strategicke_dok_list"] = _dok_list
            st.rerun()
        st.session_state["plan_ea_strategicke_dok_list"] = _dok_list

    # ── Oddíl 7: Formát zprávy ───────────────────────────────────────────────
    with st.expander("7. Formát zprávy"):
        st.selectbox(
            "Požadovaný formát a počet výtisků",
            options=[
                "Elektronicky (PDF)",
                "Elektronicky (PDF) + 1× tisk vázaný",
                "Elektronicky (PDF) + 2× tisk vázaný",
                "Dle dohody",
            ],
            key="plan_ea_format_typ",
        )

    # ── Oddíl 8: Projednání výstupů ──────────────────────────────────────────
    with st.expander("8. Projednání výstupů"):
        st.selectbox(
            "Způsob projednání",
            options=[
                "Zaslání návrhu zprávy e-mailem k připomínkám",
                "Prezentace výsledků + zaslání e-mailem",
                "Osobní projednání na místě + zaslání e-mailem",
                "Online meeting + zaslání e-mailem",
                "Dle dohody",
            ],
            key="plan_ea_projednani_typ",
        )
        st.text_input(
            "Upřesnění (volitelné)",
            key="plan_ea_projednani_poznamka",
            placeholder="Např.: do 10 pracovních dnů od předání návrhu",
        )

    # ── Dodatky ───────────────────────────────────────────────────────────────
    with st.expander("Dodatky k plánu EA (§ 4 odst. 3 vyhl. 140/2021)"):
        st.caption(
            "Dodatky se pořizují, pokud v průběhu auditu dojde ke změně "
            "předmětu, podkladů nebo harmonogramu."
        )
        _dodatky = list(st.session_state.get("plan_ea_dodatky", []))
        for _di, _dad in enumerate(_dodatky):
            _dad_new = st.text_area(
                f"Dodatek č. {_di + 1}",
                value=_dad,
                key=f"_plan_ea_dodatek_{_di}",
                height=80,
            )
            _dodatky[_di] = _dad_new
            if st.button(f"🗑️ Smazat dodatek č. {_di + 1}", key=f"_del_dad_{_di}"):
                _dodatky.pop(_di)
                st.session_state["plan_ea_dodatky"] = _dodatky
                st.rerun()
        if st.button("➕ Přidat dodatek"):
            _dodatky.append("")
            st.session_state["plan_ea_dodatky"] = _dodatky
            st.rerun()
        st.session_state["plan_ea_dodatky"] = _dodatky

    # ── Stav připravenosti ────────────────────────────────────────────────────
    st.divider()
    _plan_kompletni = all([
        st.session_state.get("plan_ea_datum"),
        st.session_state.get("plan_ea_zadavatel_zastupce"),
        st.session_state.get("plan_ea_systemy"),
        st.session_state.get("plan_ea_cile_seznam"),
        st.session_state.get("cislo_opravneni"),
    ])
    if _plan_kompletni:
        st.success(
            "Plán EA je připraven k exportu – bude zařazen jako příloha 7.1 v dokumentu EA."
        )
    else:
        _chybejici = []
        if not st.session_state.get("plan_ea_datum"):
            _chybejici.append("datum plánu")
        if not st.session_state.get("plan_ea_zadavatel_zastupce"):
            _chybejici.append("zástupce zadavatele")
        if not st.session_state.get("plan_ea_systemy"):
            _chybejici.append("systémy v rozsahu EA (oddíl 2)")
        if not st.session_state.get("plan_ea_cile_seznam"):
            _chybejici.append("cíle zadavatele (oddíl 3)")
        if not st.session_state.get("cislo_opravneni"):
            _chybejici.append("číslo oprávnění specialisty (záložka 📁 Projekt)")
        st.warning(
            "Plán EA bude do dokumentu vložen i bez kompletního vyplnění. "
            "Chybí: " + ", ".join(_chybejici) + "."
        )


def _render_ea_rozsireni_tab():
    st.subheader("EA – přídavný modul (vyhl. č. 140/2021 Sb.)")
    st.caption(
        "Tato záložka obsahuje data specifická pro Energetický audit. "
        "Ostatní data (budova, spotřeby, opatření, ekonomika) se přebírají ze záložek výše."
    )

    # ── Sekce 1: Administrativní údaje EA ────────────────────────────────────
    st.subheader("1. Administrativní údaje")
    _ea_col1, _ea_col2 = st.columns(2)
    with _ea_col1:
        st.text_input("Evidenční číslo EA (ENEX)", key="ea_evidencni_cislo")
        st.text_input("Datum zahájení EA", key="ea_datum_zahajeni", placeholder="DD.MM.RRRR")
        st.text_input("Datum ukončení EA", key="ea_datum_ukonceni", placeholder="DD.MM.RRRR")
    with _ea_col2:
        st.text_area(
            "Cíl energetického auditu",
            key="ea_cil",
            height=100,
            placeholder="Identifikace příležitostí ke snížení energetické náročnosti...",
        )
    st.text_area(
        "Plán EA – shrnutí (§4 vyhl. 140/2021)",
        key="ea_plan_text",
        height=80,
        placeholder="Stručný popis rozsahu, metodiky a způsobu spolupráce se zadavatelem...",
    )
    st.text_area(
        "Program realizace – způsob měření přínosů (§6 odst. 5)",
        key="ea_program_realizace",
        height=80,
        placeholder="Přínosy realizovaných opatření budou průběžně vyhodnocovány na základě fakturovaných spotřeb...",
    )

    st.divider()

    # ── Sekce 2: Klasifikace energonositelů (příl. 3) ─────────────────────────
    st.subheader("2. Klasifikace energonositelů (příl. 3 vyhl. 140/2021)")
    st.caption(
        "Pro každý použitý energonositel zvolte kategorii (NOZE/OZE/Druhotné) "
        "a oblast užití. Data o spotřebách se přebírají ze záložky Vstupní data."
    )
    import pandas as pd
    _ea_en_schema = {
        "nazev": st.column_config.TextColumn("Energonositel", width="medium"),
        "kategorie": st.column_config.SelectboxColumn(
            "Kategorie", options=["NOZE", "OZE", "Druhotné"], width="small"
        ),
        "oblast": st.column_config.SelectboxColumn(
            "Oblast užití", options=["Budovy", "Výrobní procesy", "Doprava"], width="small"
        ),
    }
    _ea_en_default = [
        {"nazev": "Zemní plyn", "kategorie": "NOZE", "oblast": "Budovy"},
        {"nazev": "Elektrická energie", "kategorie": "NOZE", "oblast": "Budovy"},
        {"nazev": "Teplo (CZT)", "kategorie": "NOZE", "oblast": "Budovy"},
    ]
    _ea_en_raw = st.session_state.get("ea_energonositele") or []
    _ea_en_df = pd.DataFrame(_ea_en_raw if _ea_en_raw else _ea_en_default)
    _ea_en_edited = st.data_editor(
        _ea_en_df,
        column_config=_ea_en_schema,
        num_rows="dynamic",
        use_container_width=True,
        key="_ea_en_editor",
    )
    st.session_state["ea_energonositele"] = _ea_en_edited.to_dict("records")

    st.divider()

    # ── Sekce 3: Multikriteriální hodnocení (příl. 9) ─────────────────────────
    st.subheader("3. Váhy kritérií multikriteriálního hodnocení (příl. 9 vyhl. 140/2021)")
    st.caption(
        "Nastavte váhy pro každé kritérium (0–100). Součet aktivních kritérií by měl být 100. "
        "Hodnocení se automaticky vypočítá při generování EA dokumentu."
    )
    _mkh_celkem_vaha = 0
    for _mi, _mk in enumerate(_MKH_DEFAULTS):
        _mk_col1, _mk_col2, _mk_col3 = st.columns([3, 1, 1])
        with _mk_col1:
            st.checkbox(
                f"{_mk['nazev']} [{_mk['jednotka']}] – {_mk['typ']}",
                key=f"ea_mkh_{_mi}_aktivni",
            )
        with _mk_col2:
            _mk_vaha = st.number_input(
                "Váha",
                min_value=0,
                max_value=100,
                step=5,
                key=f"ea_mkh_{_mi}_vaha",
                label_visibility="collapsed",
            )
        with _mk_col3:
            st.caption(f"{_mk['typ']}imalizace")
        if st.session_state.get(f"ea_mkh_{_mi}_aktivni", True):
            _mkh_celkem_vaha += int(st.session_state.get(f"ea_mkh_{_mi}_vaha", 0) or 0)

    if _mkh_celkem_vaha != 100:
        st.warning(f"Součet aktivních vah: **{_mkh_celkem_vaha}** (cíl: 100)")
    else:
        st.success(f"Součet vah: {_mkh_celkem_vaha} ✓")

    st.divider()

    # ── Sekce 4: Ukazatele EnPI (příl. 5) ────────────────────────────────────
    st.subheader("4. Ukazatele energetické náročnosti EnPI (příl. 5 vyhl. 140/2021)")
    st.caption(
        "Definujte vlastní ukazatele energetické náročnosti (např. kWh/m²·rok, "
        "kWh/zaměstnanec). Tyto ukazatele budou zahrnuty do EA dokumentu."
    )
    _ea_enpi_schema = {
        "nazev": st.column_config.TextColumn("Název ukazatele EnPI", width="large"),
        "jednotka": st.column_config.TextColumn("Jednotka", width="small"),
        "stavajici": st.column_config.NumberColumn(
            "Stávající hodnota", min_value=0.0, format="%.2f", width="small"
        ),
        "navrhova": st.column_config.NumberColumn(
            "Navrhovaná hodnota", min_value=0.0, format="%.2f", width="small"
        ),
    }
    _ea_enpi_raw = st.session_state.get("ea_enpi") or []
    _ea_enpi_df = pd.DataFrame(
        _ea_enpi_raw if _ea_enpi_raw
        else [{"nazev": "", "jednotka": "", "stavajici": 0.0, "navrhova": 0.0}]
    )
    _ea_enpi_edited = st.data_editor(
        _ea_enpi_df,
        column_config=_ea_enpi_schema,
        num_rows="dynamic",
        use_container_width=True,
        key="_ea_enpi_editor",
    )
    st.session_state["ea_enpi"] = _ea_enpi_edited.to_dict("records")


# ══════════════════════════════════════════════════════════════════════════════
# TAB „Plán EA" – Plán energetického auditu (příloha č. 2 k vyhl. 140/2021 Sb.)
# ══════════════════════════════════════════════════════════════════════════════

with tab_plan_ea:
    if st.session_state.get("typ_dokumentu") != "Energetický audit":
        st.info(
            f"Plán EA je součástí pouze **Energetického auditu**. "
            f"Aktuální typ dokumentu: **{st.session_state.get('typ_dokumentu', '–')}**."
        )
    else:
        _render_plan_ea_tab()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 – EA – přídavný modul (vyhl. 140/2021 Sb.)
# ══════════════════════════════════════════════════════════════════════════════

with tab_ea:
    if st.session_state.get("typ_dokumentu") != "Energetický audit":
        st.info(
            f"Záložka EA – rozšíření je součástí pouze **Energetického auditu**. "
            f"Aktuální typ dokumentu: **{st.session_state.get('typ_dokumentu', '–')}**."
        )
    else:
        _render_ea_rozsireni_tab()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 – Fotodokumentace
# ══════════════════════════════════════════════════════════════════════════════

with tab_foto:
    import io as _io

    st.subheader("Fotodokumentace")
    st.caption(
        "Nahrajte fotografie objektu, konstrukcí a technických zařízení. "
        "Každá fotka se automaticky vloží do dokumentu (EP i EA) na příslušné místo. "
        "Zařazení do sekce určuje, kde fotka v dokumentu skončí."
    )

    _foto_sekce_popis = {
        "budova":   "Obálka budovy – sekce 3.5 / B.3 (exteriér, fasáda, střecha, okna)",
        "technika": "Technické systémy – sekce 3.6 / B.4 (kotel, rozvaděč, schéma)",
        "priloha":  "Přílohy – sekce 7 (ostatní dokumentace)",
    }

    # Inicializace
    if "fotografie_upload" not in st.session_state:
        st.session_state["fotografie_upload"] = []

    # Upload widget
    _uploaded = st.file_uploader(
        "Nahrát fotografie (JPG, PNG)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="foto_uploader",
        help="Lze nahrát více souborů najednou. Duplicitní soubory jsou ignorovány.",
    )

    # Přidat nově nahrané soubory
    _existujici = {f["name"] for f in st.session_state["fotografie_upload"]}
    _pridano = 0
    for _uf in (_uploaded or []):
        if _uf.name not in _existujici:
            st.session_state["fotografie_upload"].append({
                "data": _uf.read(),
                "name": _uf.name,
                "popisek": _uf.name.rsplit(".", 1)[0].replace("_", " "),
                "sekce": "budova",
                "sirka_cm": 14.0,
            })
            _pridano += 1
    if _pridano:
        st.success(f"Přidáno {_pridano} fotografie.")

    st.divider()

    if not st.session_state["fotografie_upload"]:
        st.info("Žádné fotografie zatím nebyly nahrány.")
    else:
        # Souhrn dle sekce
        _pocty = {"budova": 0, "technika": 0, "priloha": 0}
        for _f in st.session_state["fotografie_upload"]:
            _pocty[_f.get("sekce", "budova")] = _pocty.get(_f.get("sekce", "budova"), 0) + 1
        _sc1, _sc2, _sc3 = st.columns(3)
        _sc1.metric("Obálka budovy", _pocty["budova"])
        _sc2.metric("Technické systémy", _pocty["technika"])
        _sc3.metric("Přílohy", _pocty["priloha"])

        st.divider()
        st.markdown(f"**{len(st.session_state['fotografie_upload'])} fotografií – nastavení:**")

        _foto_k_odstraneni = []
        for _fi, _foto in enumerate(st.session_state["fotografie_upload"]):
            with st.expander(f"📷  {_foto['name']}", expanded=False):
                _fc1, _fc2 = st.columns([2, 1])
                with _fc1:
                    # Náhled
                    st.image(_io.BytesIO(_foto["data"]), use_container_width=True)
                with _fc2:
                    _novo_popisek = st.text_input(
                        "Popisek v dokumentu",
                        value=_foto["popisek"],
                        key=f"foto_popisek_{_fi}",
                    )
                    st.session_state["fotografie_upload"][_fi]["popisek"] = _novo_popisek

                    _nova_sekce = st.selectbox(
                        "Zařadit do sekce",
                        options=["budova", "technika", "priloha"],
                        index=["budova", "technika", "priloha"].index(
                            _foto.get("sekce", "budova")),
                        format_func=lambda x: _foto_sekce_popis[x].split(" – ")[0],
                        key=f"foto_sekce_{_fi}",
                    )
                    st.caption(_foto_sekce_popis[_nova_sekce])
                    st.session_state["fotografie_upload"][_fi]["sekce"] = _nova_sekce

                    _nova_sirka = st.slider(
                        "Šířka v dokumentu [cm]",
                        min_value=5.0, max_value=16.0, step=0.5,
                        value=float(_foto.get("sirka_cm", 14.0)),
                        key=f"foto_sirka_{_fi}",
                    )
                    st.session_state["fotografie_upload"][_fi]["sirka_cm"] = _nova_sirka

                    if st.button("🗑️ Odstranit", key=f"foto_del_{_fi}", type="secondary"):
                        _foto_k_odstraneni.append(_fi)

        for _idx in sorted(_foto_k_odstraneni, reverse=True):
            st.session_state["fotografie_upload"].pop(_idx)
        if _foto_k_odstraneni:
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 10 – Dotace
# ══════════════════════════════════════════════════════════════════════════════

with tab_dotace:
    st.subheader("Přehled dotačních titulů a podmínek")
    st.caption(
        "Referenční přehled podmínek hlavních dotačních programů pro energetické úspory budov. "
        "Podmínky se průběžně mění – vždy ověřte aktuální výzvu na webu poskytovatele."
    )

    import pandas as _pd_dotace

    # ── Přepínač dotačního titulu ─────────────────────────────────────────────
    _dotace_vyber = st.selectbox(
        "Vyberte dotační program",
        options=["OPŽP 2021–2027 (SC 1.3)", "Nová zelená úsporám (NZÚ)", "MPO EFEKT", "Obecný přehled"],
        key="_dotace_vyber",
    )

    # ── Data dotačních titulů ─────────────────────────────────────────────────
    _DOTACE_DATA = {
        "OPŽP 2021–2027 (SC 1.3)": {
            "poskytovatel": "Státní fond životního prostředí ČR (SFŽP)",
            "web": "https://opzp.cz",
            "popis": (
                "Operační program Životní prostředí, specifický cíl 1.3 – Podpora energetické účinnosti. "
                "Zaměřen na snižování energetické náročnosti veřejných budov, bytových domů a podniků."
            ),
            "podminky": [
                ("Min. úspora PE,nOZE", "≥ 30 % oproti výchozímu stavu (bytové domy ≥ 20 %)"),
                ("Dosažená třída EP", "Třída C nebo lepší po realizaci (veřejné budovy)"),
                ("Energetický posudek", "Povinný pro všechny projekty nad 5 mil. Kč"),
                ("PENB", "Povinný – stávající stav i po realizaci"),
                ("Hydraulické vyvážení", "Povinné při čerpání podpory na vytápění"),
                ("U-hodnoty výplní", "Okna ≤ 0,9 W/m²K (= 0,6 × UN,20 = 0,6 × 1,5)"),
                ("Synantropní druhy", "Posudek ornitologa / zoologa při zateplení fasády nebo střechy"),
                ("Stavební povolení", "Nutné pro stavební změny – zajistit před podáním žádosti"),
                ("Veřejná zakázka", "Povinné VŘ dle zákona č. 134/2016 Sb. pro veřejné zadavatele"),
                ("Způsobilé výdaje", "Stavební práce, technologie, projektová dokumentace, dozor, EP/PENB"),
                ("Nezpůsobilé výdaje", "DPH (pokud je plátce), pozemky, přípojky mimo pozemek"),
            ],
            "sazby": [
                ("Veřejné budovy (obce, kraje, stát)", "až 85 % způsobilých výdajů"),
                ("Bytové domy", "až 50 % způsobilých výdajů"),
                ("Podniky (MSP)", "až 45 % způsobilých výdajů"),
                ("Maximální dotace na projekt", "bez stropu (dle výzvy)"),
            ],
        },
        "Nová zelená úsporám (NZÚ)": {
            "poskytovatel": "Státní fond životního prostředí ČR (SFŽP) / MMR",
            "web": "https://novazelenausporam.cz",
            "popis": (
                "Program podpory energetických úspor v rodinných a bytových domech. "
                "Zahrnuje podprogramy pro zateplení, výměnu zdrojů tepla, FVE, VZT a kombinované projekty."
            ),
            "podminky": [
                ("Způsobilý žadatel", "Vlastníci nebo spoluvlastníci RD / BD"),
                ("Výchozí stav", "Budova dokončena před více než 2 lety"),
                ("Oblast A – zateplení", "Splnit doporučené U-hodnoty dle NZÚ (přísnější než ČSN)"),
                ("Oblast C – zdroj tepla", "Pouze ekologické zdroje (TČ, kotel na biomasu, FVE)"),
                ("Oblast D – FVE", "Min. výkon 1 kWp, nesmí přesáhnout 50 % spotřeby"),
                ("Odborný dodavatel", "Práce musí provést registrovaný dodavatel NZÚ"),
                ("PENB", "Povinný pro komplexní zateplení (podprogram B)"),
                ("Souběh dotací", "Nelze kombinovat s OPŽP na stejné výdaje"),
            ],
            "sazby": [
                ("Zateplení fasády (A.1)", "550–1 650 Kč/m² dle dosažené U-hodnoty"),
                ("Zateplení střechy (A.3)", "550–1 650 Kč/m²"),
                ("Výměna oken (A.5)", "1 000–3 800 Kč/m²"),
                ("Tepelné čerpadlo (C.3)", "35 000–70 000 Kč/kW (dle COP)"),
                ("FVE (D.1)", "až 50 % způsobilých výdajů, max. 200 000 Kč"),
                ("Komplexní zateplení (B)", "až 50 % způsobilých výdajů"),
            ],
        },
        "MPO EFEKT": {
            "poskytovatel": "Ministerstvo průmyslu a obchodu ČR",
            "web": "https://www.mpo.cz/efekt",
            "popis": (
                "Program na podporu úspor energie a využití obnovitelných zdrojů. "
                "Zaměřen na energetické audity, poradenství a pilotní projekty. "
                "Aktuálně vypisuje výzvy pro energetické audity podniků a veřejných budov."
            ),
            "podminky": [
                ("Způsobilý žadatel", "Podniky (MSP i velké), veřejné instituce, obce"),
                ("Energetický audit", "Povinný dle zákona č. 406/2000 Sb. pro velké podniky"),
                ("Min. rozsah EA", "Dle vyhlášky 140/2021 Sb. – komplexní posouzení všech energetických systémů"),
                ("Způsobilé výdaje", "Zpracování EA, studie proveditelnosti, poradenství"),
                ("Realizace doporučení", "Není podmínkou pro dotaci na EA, ale zvyšuje hodnocení"),
            ],
            "sazby": [
                ("Energetický audit (MSP)", "až 50 % způsobilých výdajů, max. 350 000 Kč"),
                ("Energetický audit (velký podnik)", "až 30 % způsobilých výdajů, max. 350 000 Kč"),
                ("Poradenství", "až 50 % způsobilých výdajů, max. 200 000 Kč"),
            ],
        },
        "Obecný přehled": {
            "poskytovatel": "Různí poskytovatelé",
            "web": "",
            "popis": "Srovnávací přehled hlavních programů.",
            "podminky": [],
            "sazby": [],
        },
    }

    _d = _DOTACE_DATA.get(_dotace_vyber, {})

    if _dotace_vyber == "Obecný přehled":
        _prehled_rows = [
            {"Program": "OPŽP 2021–2027 SC 1.3", "Poskytovatel": "SFŽP", "Zaměření": "Veřejné budovy, BD, podniky", "Max. dotace": "až 85 %", "Povinný EA/EP": "Ano (> 5 mil. Kč)"},
            {"Program": "Nová zelená úsporám", "Poskytovatel": "SFŽP / MMR", "Zaměření": "RD a BD", "Max. dotace": "fixní sazby / až 50 %", "Povinný EA/EP": "Jen komplex. zateplení"},
            {"Program": "MPO EFEKT", "Poskytovatel": "MPO", "Zaměření": "EA, poradenství", "Max. dotace": "až 50 % (EA)", "Povinný EA/EP": "EA je předmět dotace"},
            {"Program": "Kotlíkové dotace", "Poskytovatel": "Kraje / SFŽP", "Zaměření": "Výměna kotlů v domácnostech", "Max. dotace": "až 95 % (nízkopříjmoví)", "Povinný EA/EP": "Ne"},
            {"Program": "OP TAK (MSP)", "Poskytovatel": "MPO / API", "Zaměření": "Průmysl, podnikání", "Max. dotace": "až 45 %", "Povinný EA/EP": "Ano"},
        ]
        st.dataframe(_pd_dotace.DataFrame(_prehled_rows), use_container_width=True, hide_index=True)

    else:
        st.markdown(f"**Poskytovatel:** {_d.get('poskytovatel', '')}  \n**Popis:** {_d.get('popis', '')}")

        if _d.get("web"):
            st.caption(f"Web: {_d['web']}")

        st.divider()

        if _d.get("podminky"):
            st.markdown("#### Klíčové podmínky")
            _pod_df = _pd_dotace.DataFrame(_d["podminky"], columns=["Podmínka", "Specifikace"])
            st.dataframe(_pod_df, use_container_width=True, hide_index=True)

        if _d.get("sazby"):
            st.divider()
            st.markdown("#### Výše podpory")
            _saz_df = _pd_dotace.DataFrame(_d["sazby"], columns=["Kategorie", "Výše dotace"])
            st.dataframe(_saz_df, use_container_width=True, hide_index=True)

    # ── Relevance pro tento objekt ────────────────────────────────────────────
    st.divider()
    st.markdown("#### Poznámky k objektu")
    st.text_area(
        "Vlastní poznámky k dotačnímu titulu pro tento objekt",
        key="dotace_poznamky",
        height=120,
        placeholder="Např.: Objekt splňuje podmínku 30 % úspory PE – vhodný pro OPŽP. Žadatel: Město XY (IČO …). Kontakt na SFŽP: …",
    )



# ══════════════════════════════════════════════════════════════════════════════
# TAB 9 – Export Word dokumentů (EP / EA)
# ══════════════════════════════════════════════════════════════════════════════

with tab_export:
    from epc_engine.reports import generuj_ep, generuj_ea

    st.subheader("Generování výstupních dokumentů")

    _exp_result = build_project().vypocitej()
    _exp_budova = build_building_info()
    _nazev_souboru = (
        (_exp_budova.objekt_nazev or "objekt")
        .replace(" ", "_")
        .replace("/", "-")
    )

    _typ_dok = st.session_state.get("typ_dokumentu", "Energetický audit")

    if _typ_dok == "Energetický audit":
        col_ea, col_ep = st.columns(2)
        with col_ea:
            st.markdown("**Energetický audit (EA)**")
            st.caption("Vyhláška 140/2021 Sb.")
            _buf_ea = generuj_ea(_exp_budova, _exp_result)
            st.download_button(
                "⬇️ Stáhnout EA (.docx)",
                data=_buf_ea,
                file_name=f"EA_{_nazev_souboru}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
            )
        with col_ep:
            st.markdown("**Energetický posudek (EP)**")
            st.caption("Vyhláška 141/2021 Sb. – vedlejší výstup")
            _buf_ep = generuj_ep(_exp_budova, _exp_result)
            st.download_button(
                "⬇️ Stáhnout EP (.docx)",
                data=_buf_ep,
                file_name=f"EP_{_nazev_souboru}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="secondary",
            )

    elif _typ_dok == "Energetický posudek":
        col_ep, col_ea = st.columns(2)
        with col_ep:
            st.markdown("**Energetický posudek (EP)**")
            st.caption("Vyhláška 141/2021 Sb.")
            _buf_ep = generuj_ep(_exp_budova, _exp_result)
            st.download_button(
                "⬇️ Stáhnout EP (.docx)",
                data=_buf_ep,
                file_name=f"EP_{_nazev_souboru}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
            )
        with col_ea:
            st.markdown("**Energetický audit (EA)**")
            st.caption("Není vyžadován pro tento typ dokumentu.")
            _buf_ea = generuj_ea(_exp_budova, _exp_result)
            st.download_button(
                "⬇️ Stáhnout EA (.docx)",
                data=_buf_ea,
                file_name=f"EA_{_nazev_souboru}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="secondary",
            )

    else:
        # Obecná studie / Podrobná analýza – nabídnout oba formáty jako volitelné
        st.info(
            f"Typ dokumentu **{_typ_dok}** nemá závazný formát výstupu. "
            "Exportujte jako EP nebo EA dle potřeby."
        )
        col_ep, col_ea = st.columns(2)
        with col_ep:
            st.markdown("**Export jako EP (.docx)**")
            st.caption("Formát energetického posudku")
            _buf_ep = generuj_ep(_exp_budova, _exp_result)
            st.download_button(
                "⬇️ Stáhnout EP (.docx)",
                data=_buf_ep,
                file_name=f"EP_{_nazev_souboru}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="secondary",
            )
        with col_ea:
            st.markdown("**Export jako EA (.docx)**")
            st.caption("Formát energetického auditu")
            _buf_ea = generuj_ea(_exp_budova, _exp_result)
            st.download_button(
                "⬇️ Stáhnout EA (.docx)",
                data=_buf_ea,
                file_name=f"EA_{_nazev_souboru}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="secondary",
            )

    st.caption(
        "PDF: Otevřete soubor ve Wordu a uložte jako PDF. "
        "Přímá konverze v Pythonu je plánována v budoucí verzi."
    )

    # ── Technické přílohy VŘ ──────────────────────────────────────────────────
    st.divider()
    st.subheader("Přílohy k zadávací dokumentaci výběrového řízení (VŘ)")
    st.caption(
        "Generuje Word dokument se třemi přílohami: minimální technické požadavky na opatření, "
        "referenční a okrajové podmínky pro M&V, agregovaný položkový rozpočet."
    )

    from epc_engine.reports import generuj_hpr

    # Zjistit seznam aktivních OP z session state
    _vr_aktivni_op = [
        op_id for op_id in [
            "OP1a", "OP1b", "OP2", "OP3", "OP4", "OP5", "OP6",
            "OP7", "OP8", "OP9", "OP10", "OP11", "OP12", "OP13",
            "OP14", "OP15", "OP16", "OP17", "OP18", "OP19", "OP20", "OP21", "OP22",
        ]
        if st.session_state.get(f"{op_id.lower()}_on", False)
    ]

    if _vr_aktivni_op:
        st.markdown(f"**Aktivní opatření:** {', '.join(_vr_aktivni_op)}")
        try:
            _buf_hpr = generuj_hpr(
                _exp_budova,
                _exp_result,
                _vr_aktivni_op,
                dict(st.session_state),
            )
            st.download_button(
                "⬇️ Stáhnout slepý výkaz výměr (.xlsx)",
                data=_buf_hpr,
                file_name=f"HPR_{_nazev_souboru}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )
        except Exception as _e_hpr:
            st.error(f"Chyba při generování HPR: {_e_hpr}")
    else:
        st.info("Žádné opatření není aktivní – aktivujte alespoň jedno v záložce Opatření.")

    # ── Přílohy SES (Smlouva o energetických službách) ────────────────────────
    st.divider()
    st.subheader("Přílohy ke Smlouvě o energetických službách (SES)")

    _ses_variant = st.radio(
        "Varianta příloh SES",
        options=["apes", "dpu"],
        format_func=lambda v: "APES standard – 9 příloh (P01–P09)" if v == "apes"
                              else "DPU standard – 10 příloh (P01–P10, vč. inflační doložky)",
        horizontal=True,
        key="ses_variant",
    )
    _ses_popis = (
        "9 Word dokumentů (ZIP): výchozí stav, popis opatření, cena, harmonogram, "
        "garantovaná úspora, M&V plán, energetický management, oprávněné osoby, poddodavatelé."
    ) if _ses_variant == "apes" else (
        "10 Word dokumentů (ZIP): totéž + P10 Inflační doložka; "
        "P04–P09 dle DPU standardu (detailnější harmonogram, 6-sloupcová úspora, "
        "IPMVP tabulky, textové oprávněné osoby)."
    )
    st.caption(_ses_popis)

    from epc_engine.reports import generuj_ses_prilohy
    try:
        _buf_ses = generuj_ses_prilohy(
            _exp_budova,
            _exp_result,
            _vr_aktivni_op,
            dict(st.session_state),
            variant=_ses_variant,
        )
        _ses_count = "10" if _ses_variant == "dpu" else "9"
        st.download_button(
            f"⬇️ Stáhnout přílohy SES (.zip – {_ses_count}× .docx)",
            data=_buf_ses,
            file_name=f"SES_{_ses_variant}_{_nazev_souboru}.zip",
            mime="application/zip",
            type="primary",
        )
    except Exception as _e_ses:
        st.error(f"Chyba při generování příloh SES: {_e_ses}")
