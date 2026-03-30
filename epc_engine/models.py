"""
Datové třídy EPC engine.

Odpovídají listy Excelu:
  BuildingInfo  ← Titulka, Identifikace, Stávající stav
  EnergyInputs  ← Teplo, Zemní plyn, EE, Voda, Referenční spotřeby, Ovládání
  ChainState    ← průběžný stav spotřeb procházející řetězem opatření
  MeasureResult ← jeden řádek listu Celková bilance
  ProjectResult ← souhrnný řádek + výpočty návratnosti

Sprint 4 rozšíření:
  Vrstva, Konstrukce     ← tepelně technické vlastnosti obálky (ČSN EN ISO 6946)
  TechnickySytem,
  TechnickeSystemy       ← pasport technických systémů (ÚT, TUV, VZT, osvětlení)
  BilancePouzitiEnergie  ← rozpad spotřeby dle účelu (příloha č. 4 vyhl. 141/2021)
  PenbData               ← data PENB z externího SW (vyhl. 264/2020 Sb.)

Sprint 5 EA rozšíření:
  EnergonositelEA        ← klasifikace energonosiče NOZE/OZE/Druhotné (příl. 3 vyhl. 140/2021)
  MKHKriterium           ← kritérium multikriteriálního hodnocení (příl. 9 vyhl. 140/2021)
  EnPIUkazatel           ← ukazatel energetické náročnosti EnPI (příl. 5 vyhl. 140/2021)
  EAData                 ← přídavný EA modul k EP datům

Sprint 6 rozšíření:
  Fotografie             ← fotografie / snímek vložená do dokumentu

Sprint 7 rozšíření:
  PlanEA                 ← Plán energetického auditu (příloha č. 2 k vyhl. 140/2021 Sb.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .economics import EkonomickeBilance, EkonomickeParametry
    from .emissions import EmiseBilance
    from .building_class import KlasifikaceObaly


# ══════════════════════════════════════════════════════════════════════════════
# Tepelně technické vlastnosti – Sprint 4
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Vrstva:
    """
    Jedna vrstva stavební konstrukce.
    Slouží k výpočtu U dle ČSN EN ISO 6946 v epc_engine.tepelna_technika.
    """
    nazev: str = ""
    tloustka_m: float = 0.0    # tloušťka [m]
    lambda_wm: float = 0.0     # tepelná vodivost [W/(m·K)]


@dataclass
class Konstrukce:
    """
    Stavební konstrukce na systémové hranici budovy.
    U se počítá z vrstev, nebo lze zadat přímo (pro okna, dveře).
    """
    nazev: str = ""
    typ: str = "stena"          # stena / strecha / podlaha / okno / dvere
    plocha_m2: float = 0.0      # plocha [m²]
    vrstvy: list[Vrstva] = field(default_factory=list)
    u_zadane: Optional[float] = None   # přímé zadání U [W/(m²K)] – přebije výpočet
    un_value: float = 0.0              # normová hodnota UN [W/(m²K)]

    @property
    def u_effective(self) -> float:
        """Výsledná U-hodnota: přímé zadání nebo výpočet z vrstev."""
        if self.u_zadane is not None:
            return self.u_zadane
        from .tepelna_technika import vypocitej_u_z_vrstev
        return vypocitej_u_z_vrstev(self.vrstvy, self.typ)


# ══════════════════════════════════════════════════════════════════════════════
# Technické systémy – Sprint 4
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TechnickySytem:
    """Jeden technický systém (zdroj tepla, VZT, osvětlení…)."""
    typ: str = ""              # např. "Horkovod CZT", "Plynový kondenzační kotel"
    vykon_kw: float = 0.0     # instalovaný výkon [kW]
    ucinnost_pct: float = 0.0  # účinnost [%] (0 = nezadáno)
    rok_instalace: int = 0    # rok instalace (0 = nezadáno)
    popis: str = ""            # volný text


@dataclass
class TechnickeSystemy:
    """
    Pasport technických systémů objektu.
    Každý systém kombinuje strukturovaná pole + volný text popis.
    """
    vytapeni: TechnickySytem = field(default_factory=TechnickySytem)
    tuv: TechnickySytem = field(default_factory=TechnickySytem)
    vzt: TechnickySytem = field(default_factory=TechnickySytem)
    osvetleni: TechnickySytem = field(default_factory=TechnickySytem)
    mereni_ridici: str = ""    # popis MaR a měření spotřeb


# ══════════════════════════════════════════════════════════════════════════════
# Bilance dle účelu a PENB – Sprint 4
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class BilancePouzitiEnergie:
    """
    Rozpad celkové spotřeby energie dle způsobu užití.
    Odpovídá tabulce dle přílohy č. 4 k vyhlášce č. 141/2021 Sb.
    """
    vytapeni_mwh: float = 0.0
    chlazeni_mwh: float = 0.0
    tuv_mwh: float = 0.0
    vetrání_mwh: float = 0.0
    osvetleni_mwh: float = 0.0
    technologie_mwh: float = 0.0
    phm_mwh: float = 0.0

    vytapeni_kc: float = 0.0
    chlazeni_kc: float = 0.0
    tuv_kc: float = 0.0
    vetrání_kc: float = 0.0
    osvetleni_kc: float = 0.0
    technologie_kc: float = 0.0
    phm_kc: float = 0.0

    @property
    def celkem_mwh(self) -> float:
        return (self.vytapeni_mwh + self.chlazeni_mwh + self.tuv_mwh
                + self.vetrání_mwh + self.osvetleni_mwh
                + self.technologie_mwh + self.phm_mwh)

    @property
    def celkem_kc(self) -> float:
        return (self.vytapeni_kc + self.chlazeni_kc + self.tuv_kc
                + self.vetrání_kc + self.osvetleni_kc
                + self.technologie_kc + self.phm_kc)


@dataclass
class PenbData:
    """
    Data průkazu energetické náročnosti budovy (PENB).
    Vyplňují se ručně z výstupu externího softwaru (Energie+, TechCon…).
    Dle vyhlášky č. 264/2020 Sb.
    """
    trida_stavajici: str = ""           # A–G (stávající stav)
    trida_navrhovy: str = ""            # A–G (po opatřeních)
    merná_potreba_tepla: float = 0.0    # kWh/(m²·rok)
    celkova_dodana_energie: float = 0.0  # kWh/(m²·rok)
    primarni_neobnovitelna: float = 0.0  # kWh/(m²·rok)
    energeticka_vztazna_plocha: float = 0.0  # m²
    poznamka: str = ""                  # zpracovatel PENB, datum, číslo


# ══════════════════════════════════════════════════════════════════════════════
# Historie spotřeby a klimatická data – Sprint 4
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class HistorieRok:
    """Jeden rok historické spotřeby pro sekci B.2 (3letá historie)."""
    rok: int = 0
    energonosic: str = ""        # "Teplo (CZT)", "Zemní plyn", "Elektrická energie"
    spotreba_mwh: float = 0.0    # MWh/rok – roční součet
    naklady_kc: float = 0.0      # Kč/rok – roční náklady
    stupnodni: float = 0.0       # skutečné denostupně daného roku (pro klimatickou korekci)
    mesicni_mwh: list[float] = field(default_factory=lambda: [0.0] * 12)  # spotřeba po měsících


@dataclass
class KlimatickaData:
    """Klimatická data lokality pro klimatickou korekci spotřeby dle denostupňů."""
    lokalita: str = ""
    stupnodni_normovane: float = 3600.0  # D – normované denostupně [°C·dny/rok]
    teplota_vnitrni: float = 19.0        # ti [°C] – převažující vnitřní návrhová teplota
    teplota_exterieru: float = -12.0     # te [°C] – výpočtová venkovní teplota


# ══════════════════════════════════════════════════════════════════════════════
# Systém managementu hospodaření s energií (EnMS) – ČSN EN ISO 50001
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class EnMSOblast:
    """Jedna oblast hodnocení dle ČSN EN ISO 50001."""
    nazev: str = ""            # název oblasti (např. „Energetická politika")
    stav: str = ""             # popis stávajícího stavu (volný text)
    hodnoceni: int = 0         # 1 = nesplnění, 2 = částečné splnění, 3 = plné splnění


@dataclass
class EnMSHodnoceni:
    """
    Hodnocení úrovně systému managementu hospodaření s energií.
    Dle ČSN EN ISO 50001, hodnocení škálou 1–3.
    """
    certifikovan: bool = False
    oblasti: list[EnMSOblast] = field(default_factory=lambda: [
        EnMSOblast("Energetická politika", "", 0),
        EnMSOblast("Energetické plánování", "", 0),
        EnMSOblast("Implementace a provoz", "", 0),
        EnMSOblast("Kontrola a měření", "", 0),
        EnMSOblast("Interní audit EnMS", "", 0),
        EnMSOblast("Přezkoumání vedením", "", 0),
        EnMSOblast("Neustálé zlepšování", "", 0),
    ])
    komentar: str = ""


# ══════════════════════════════════════════════════════════════════════════════
# Sprint 6 – fotografie a vizualizace
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Fotografie:
    """
    Fotografie nebo jiný obrázek vkládaný do dokumentu.

    Pole sekce určuje, kam se fotka zařadí:
      'budova'   → sekce 3.5 Tepelně technické vlastnosti (exteriér, obálka)
      'technika' → sekce 3.6 Technické systémy (kotle, rozvaděče, schémata)
      'priloha'  → sekce 7 Přílohy
    """
    data: bytes = field(default_factory=bytes)
    popisek: str = ""
    sekce: str = "budova"   # "budova" | "technika" | "priloha"
    sirka_cm: float = 14.0  # šířka v dokumentu [cm]


# ══════════════════════════════════════════════════════════════════════════════
# EA-specifické datové třídy – Sprint 5
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class EnergonositelEA:
    """
    Energonositel s klasifikací pro bilanci energetických vstupů EA.
    Dle přílohy č. 3 k vyhlášce č. 140/2021 Sb.
    """
    nazev: str = ""           # "Zemní plyn", "Elektrická energie", "Teplo (CZT)"
    kategorie: str = "NOZE"   # NOZE / OZE / Druhotné
    oblast: str = "Budovy"    # Budovy / Výrobní procesy / Doprava


@dataclass
class MKHKriterium:
    """
    Jedno kritérium multikriteriálního hodnocení opatření.
    Dle přílohy č. 9 k vyhlášce č. 140/2021 Sb. (metoda váženého součtu).
    """
    nazev: str = ""
    jednotka: str = ""
    typ: str = "max"    # "max" = maximalizační, "min" = minimalizační
    vaha: float = 0.0   # váha 0–100; součet vah by měl být 100
    key: str = ""       # interní klíč: "npv" / "td" / "mwh" / "kc"


@dataclass
class EnPIUkazatel:
    """
    Ukazatel energetické náročnosti (EnPI).
    Dle přílohy č. 5 k vyhlášce č. 140/2021 Sb.
    """
    nazev: str = ""
    jednotka: str = ""
    hodnota_stavajici: float = 0.0
    hodnota_navrhova: float = 0.0
    popis_stanoveni: str = ""  # Popis způsobu stanovení ukazatele (příl. 5 sloupec)
    je_stavajici: bool = True   # True = stávající ukazatel; False = navrhovaný nový


@dataclass
class EAData:
    """
    EA-specifická data – přídavný modul k EP datům.
    Obsahuje administrativní a metodické informace potřebné pouze pro EA.
    Používá se při generování EA dokumentu (vyhl. č. 140/2021 Sb.).
    """
    evidencni_cislo_ea: str = ""
    cil: str = ""
    datum_zahajeni: str = ""
    datum_ukonceni: str = ""
    plan_text: str = ""
    program_realizace: str = ""
    energonositele: list[EnergonositelEA] = field(default_factory=list)
    mkh_kriteria: list[MKHKriterium] = field(
        default_factory=lambda: [
            MKHKriterium("Čistá současná hodnota (NPV)", "tis. Kč", "max", 30.0, "npv"),
            MKHKriterium("Prostá doba návratnosti", "roky", "min", 25.0, "td"),
            MKHKriterium("Úspora energie", "MWh/rok", "max", 25.0, "mwh"),
            MKHKriterium("Úspora nákladů na energii", "tis. Kč/rok", "max", 20.0, "kc"),
        ]
    )
    enpi: list[EnPIUkazatel] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
# Identifikace projektu a popis budovy
# Odpovídá listům Titulka, Identifikace a Stávající stav v Excel šabloně.
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Budova:
    """
    Parametry jedné vytápěné budovy v areálu.
    Odpovídá tabulce „Seznam budov" v listu Stávající stav.
    """
    nazev: str = ""
    objem_m3: float = 0.0                  # m³ – obestavěný objem
    podlahova_plocha_m2: float = 0.0       # m² – vytápěná podlahová plocha
    ochlazovana_plocha_m2: float = 0.0     # m² – plocha ochlazovaných konstrukcí

    @property
    def faktor_tvaru(self) -> float:
        """A/V [m²/m³] – faktor tvaru budovy."""
        if self.objem_m3 == 0:
            return 0.0
        return self.ochlazovana_plocha_m2 / self.objem_m3


@dataclass
class Prostor:
    """Jeden řádek tabulky „Seznam a využití prostor"."""
    nazev: str = ""
    ucel: str = ""
    provoz: str = ""   # např. „Po–Pá 6:00–16:30"


@dataclass
class Podklad:
    """Jeden řádek seznamu obdržených podkladů."""
    nazev: str = ""
    k_dispozici: bool = True


@dataclass
class BuildingInfo:
    """
    Kompletní identifikace projektu a popis objektu.

    Titulka
    -------
    nazev_zakazky    ← název nadřazené zakázky (může zahrnovat více objektů)
    datum            ← datum vypracování analýzy
    program_efekt    ← zda je dílo podpořeno programem EFEKT

    Zadavatel (klient)
    ------------------
    zadavatel_*

    Zpracovatel (DPU ENERGY)
    -------------------
    zpracovatel_zastupce  ← odpovědná osoba za analýzu

    Identifikace objektu
    --------------------
    objekt_nazev, objekt_adresa, predmet_analyzy

    Základní parametry
    ------------------
    druh_cinnosti, pocet_zamestnancu, provozni_rezim
    budovy        ← seznam instancí Budova
    prostory      ← seznam instancí Prostor

    Vstupní podklady
    ----------------
    podklady      ← seznam instancí Podklad
    poznamka_podklady  ← volný text za seznam podkladů
    """

    # ── Titulka ───────────────────────────────────────────────────────────────
    nazev_zakazky: str = ""
    datum: str = ""
    program_efekt: bool = False

    # ── Zadavatel ─────────────────────────────────────────────────────────────
    zadavatel_nazev: str = ""
    zadavatel_adresa: str = ""
    zadavatel_ico: str = ""
    zadavatel_kontakt: str = ""        # jméno kontaktní osoby
    zadavatel_telefon: str = ""
    zadavatel_email: str = ""

    # ── Zpracovatel ───────────────────────────────────────────────────────────
    zpracovatel_zastupce: str = "Ing. Jakub Hřídel"

    # ── Identifikace objektu ─────────────────────────────────────────────────
    objekt_nazev: str = ""
    objekt_adresa: str = ""
    predmet_analyzy: str = (
        "Předmětem analýzy je zjištění stavu a potenciálu energetických úspor "
        "a vhodnosti realizace úsporných opatření pomocí EPC metody."
    )

    # ── Základní parametry budovy ─────────────────────────────────────────────
    druh_cinnosti: str = ""            # např. „Základní škola", „Administrativní budova"
    pocet_zamestnancu: str = ""        # volný text – „84 / 678 žáků"
    provozni_rezim: str = ""           # volný popis provozu
    budovy: list[Budova] = field(default_factory=lambda: [Budova()])
    prostory: list[Prostor] = field(default_factory=list)

    # ── Vstupní podklady ──────────────────────────────────────────────────────
    podklady: list[Podklad] = field(default_factory=lambda: [
        Podklad("Spotřeby a platby za elektrickou energii, teplo, vodu"),
        Podklad("Původní projektová dokumentace", False),
        Podklad("Energetický audit", False),
        Podklad("Průkaz energetické náročnosti budovy (PENB)", False),
        Podklad("Pasport objektu", False),
        Podklad("Revizní zprávy", False),
        Podklad("Informace od provozovatele"),
        Podklad("Informace z technické prohlídky objektu"),
    ])
    poznamka_podklady: str = (
        "Pokud není v analýze uvedeno jinak, jsou všechny ceny a náklady "
        "uváděny včetně DPH."
    )

    # ── Sprint 4: doplňující identifikační pole ───────────────────────────────
    objekt_ku: str = ""                 # katastrální území
    objekt_parcelni_cislo: str = ""     # parcelní číslo
    evidencni_cislo: str = ""           # evidenční číslo v systému ENEX
    cislo_opravneni: str = ""           # číslo oprávnění energetického specialisty
    ucel_ep: str = ""                   # účel EP dle §9a zák. 406/2000 Sb.
    ceny_bez_dph: bool = True           # True = ceny v EP bez DPH

    # ── Sprint 4: tepelná obálka ──────────────────────────────────────────────
    konstrukce: list[Konstrukce] = field(default_factory=list)

    # ── Sprint 4: technické systémy ───────────────────────────────────────────
    technicke_systemy: TechnickeSystemy = field(default_factory=TechnickeSystemy)

    # ── Sprint 4: bilance dle účelu (příloha č. 4 vyhl. 141/2021) ────────────
    bilance_pouziti: Optional[BilancePouzitiEnergie] = None

    # ── Sprint 4: PENB data (z externího SW) ──────────────────────────────────
    penb: Optional[PenbData] = None

    # ── Sprint 4: historie spotřeby (sekce B.2) ──────────────────────────────
    klimaticka_data: Optional[KlimatickaData] = None
    historie_spotreby: list[HistorieRok] = field(default_factory=list)

    # ── Sprint 4: EnMS (sekce B.5.2, C.3) ────────────────────────────────────
    enms: Optional[EnMSHodnoceni] = None

    # ── Sprint 5: EA-specifická data ──────────────────────────────────────────
    ea_data: Optional["EAData"] = None

    # ── Sprint 6: fotografie a schémata ──────────────────────────────────────
    fotografie: list[Fotografie] = field(default_factory=list)

    # ── Sprint 7: plán energetického auditu (příloha č. 2 k vyhl. 140/2021) ──
    plan_ea: Optional["PlanEA"] = None

    # ── Sprint 4: okrajové podmínky (volný text, sekce E) ─────────────────────
    okrajove_podminky: str = (
        "Pro dosažení kalkulovaných úspor je nezbytné dodržet navržené technické "
        "parametry při výběru dodavatele, provádět pravidelnou údržbu a servis "
        "instalovaných zařízení a zachovat stávající způsob užívání objektu."
    )

    # ── Odvozené vlastnosti ───────────────────────────────────────────────────
    @property
    def celkova_plocha_m2(self) -> float:
        return sum(b.podlahova_plocha_m2 for b in self.budovy)

    @property
    def celkovy_objem_m3(self) -> float:
        return sum(b.objem_m3 for b in self.budovy)


@dataclass
class EnergyInputs:
    """
    Referenční spotřeby (normované denostupni) a jednotkové ceny.

    Kde vzít hodnoty:
      teplo_ut, teplo_tuv  ← list Denostupně (normovaná spotřeba ÚT a TUV)
      zp_ut, zp_tuv        ← list Denostupně (normovaná spotřeba ZP pro ÚT a TUV)
      ee                   ← EE!F25 – roční spotřeba EE
      voda, srazky         ← Voda!H25, Voda!M25
      cena_*               ← Teplo!G24, ZP!G24, EE!G25, Voda!I25, Voda!N25

    Příznaky pouzit_* odpovídají listu Ovládání (D11–D14, F11–F13).
    Objekt zastupuje jeden řetěz výpočtů (= jeden energonosič pro vytápění).
    """

    # ── Spotřeby ──────────────────────────────────────────────────────────────
    teplo_ut: float = 0.0       # MWh/rok – teplo pro ústřední vytápění (CZT)
    teplo_tuv: float = 0.0      # MWh/rok – teplo pro přípravu TUV (CZT)
    zp_ut: float = 0.0          # MWh/rok – zemní plyn pro ÚT
    zp_tuv: float = 0.0         # MWh/rok – zemní plyn pro TUV
    ee: float = 0.0             # MWh/rok – elektrická energie
    voda: float = 0.0           # m3/rok  – vodné a stočné
    srazky: float = 0.0         # m3/rok  – poplatek za odvod srážkové vody

    # ── Ceny ─────────────────────────────────────────────────────────────────
    cena_teplo: float = 0.0     # Kč/MWh
    cena_zp: float = 0.0        # Kč/MWh
    cena_ee: float = 0.0        # Kč/MWh
    cena_voda: float = 0.0      # Kč/m3
    cena_srazky: float = 0.0    # Kč/m3
    cena_ee_vykup: float = 0.0  # Kč/MWh – výkupní cena přetoků z FVE do sítě

    # ── Příznaky aktivních energonosičů (Ovládání D11–D14, F11–F13) ──────────
    pouzit_teplo: bool = False       # True = teplo ze SZTE / CZT
    pouzit_zp: bool = False          # True = zemní plyn pro ÚT
    pouzit_tuv_teplo: bool = False   # True = TUV ohřívána teplem z CZT
    pouzit_tuv_zp: bool = False      # True = TUV ohřívána zemním plynem
    pouzit_tuv_ee: bool = False      # True = TUV ohřívána elektřinou

    # ── Odvozené vlastnosti ──────────────────────────────────────────────────
    @property
    def teplo_total(self) -> float:
        """Celková referenční spotřeba tepla ze CZT (ÚT + TUV) v MWh/rok."""
        return self.teplo_ut + self.teplo_tuv

    @property
    def zp_total(self) -> float:
        """Celková referenční spotřeba zemního plynu (ÚT + TUV) v MWh/rok."""
        return self.zp_ut + self.zp_tuv

    @property
    def celkove_naklady(self) -> float:
        """
        Celkové roční náklady na energie (Kč/rok).

        Použito jako jmenovatel při výpočtu procentuální úspory (sloupec AM
        v listu Celková bilance Excel šablony).
        """
        return (
            (self.teplo_total * self.cena_teplo if self.pouzit_teplo else 0.0)
            + (self.zp_total * self.cena_zp if self.pouzit_zp else 0.0)
            + self.ee * self.cena_ee
            + self.voda * self.cena_voda
            + self.srazky * self.cena_srazky
        )


@dataclass
class ChainState:
    """
    Průběžný stav spotřeb procházející řetězem opatření.

    Každé aktivní opatření sníží příslušné hodnoty IN-PLACE.
    Chain prochází opatřeními v pořadí OP1a → OP1b → ... → OP22.

    Tepelný řetěz (ÚT): opatření OP1a–OP6 snižují zbývající spotřebu.
    OP7–OP9, OP16–OP17 počítají úsporu jako procento ze zbývajícího ÚT.
    EE, voda a srážky mají vlastní průběžné hodnoty.
    """

    zbyvajici_teplo: float   # MWh/rok – zbývající spotřeba tepla (CZT)
    zbyvajici_zp: float      # MWh/rok – zbývající spotřeba zemního plynu
    zbyvajici_ee: float      # MWh/rok – zbývající spotřeba EE
    zbyvajici_voda: float    # m3/rok
    zbyvajici_srazky: float  # m3/rok
    # Reference TUV (nemění se – potřebná pro výpočet úspor pouze z ÚT části)
    ref_teplo_tuv: float = 0.0
    ref_zp_tuv: float = 0.0

    @classmethod
    def from_inputs(cls, energie: EnergyInputs) -> ChainState:
        """Vytvoří počáteční stav z referenčních vstupů."""
        return cls(
            zbyvajici_teplo=energie.teplo_total if energie.pouzit_teplo else 0.0,
            zbyvajici_zp=energie.zp_total if energie.pouzit_zp else 0.0,
            zbyvajici_ee=energie.ee,
            zbyvajici_voda=energie.voda,
            zbyvajici_srazky=energie.srazky,
            ref_teplo_tuv=energie.teplo_tuv,
            ref_zp_tuv=energie.zp_tuv,
        )

    def zbyvajici_teplo_ut(self) -> float:
        """Zbývající spotřeba tepla pouze pro ÚT (bez TUV)."""
        return max(0.0, self.zbyvajici_teplo - self.ref_teplo_tuv)

    def zbyvajici_zp_ut(self) -> float:
        """Zbývající spotřeba ZP pouze pro ÚT (bez TUV)."""
        return max(0.0, self.zbyvajici_zp - self.ref_zp_tuv)


@dataclass
class MeasureResult:
    """
    Výsledky jednoho opatření.

    Odpovídá jednomu řádku v listu Celková bilance Excel šablony
    (sloupce A–AO, ale bez zdrojových sloupců W–AO – ty jsou jen mezikroky).
    """

    id: str
    nazev: str
    aktivni: bool

    investice: float = 0.0          # Kč vč. DPH
    uspora_teplo: float = 0.0       # MWh/rok (teplo ze CZT)
    uspora_zp: float = 0.0          # MWh/rok (zemní plyn)
    uspora_ee: float = 0.0          # MWh/rok (kladné = úspora, záporné = navýšení spotřeby)
    vynos_pretoky: float = 0.0      # Kč/rok  (příjmy z prodeje přetoků FVE do sítě)
    uspora_voda: float = 0.0        # m3/rok
    uspora_srazky: float = 0.0      # m3/rok
    uspora_kc: float = 0.0          # Kč/rok – celková finanční úspora vč. výnosů
    uspora_pct: float = 0.0         # podíl z celkových nákladů (0–1)
    servisni_naklady: float = 0.0   # Kč/rok – roční servisní náklady po realizaci
    prosta_navratnost: Optional[float] = None
    # None = záporná nebo nulová čistá úspora (v Excelu zobrazeno jako „∞")

    # Ekonomická analýza (NPV/IRR/Tsd) – doplněna kalkulátorem pokud jsou k dispozici parametry
    ekonomika: Optional["EkonomickeBilance"] = None


@dataclass
class PlanEA:
    """
    Plán energetického auditu – příloha č. 2 k vyhl. 140/2021 Sb.

    Dokument se dohodne před zahájením auditu (§ 4 odst. 1), podepíší ho
    obě strany a stává se povinnou přílohou zprávy EA (§ 10 písm. a)).
    Ekonomické parametry (diskont, horizont, inflace) jsou zároveň
    vstupem do ekonomické analýzy opatření.
    """

    # Formální náležitosti (příloha č. 2 – závěr dokumentu)
    datum_planu: str = ""                  # datum podpisu plánu
    zadavatel_zastupce: str = ""           # jméno + funkce zástupce zadavatele
    # specialista + č. oprávnění se přebírají z BuildingInfo

    # 1. Požadavky na míru detailu
    mira_detailu: str = (
        "Úplný energetický audit dle přílohy A3 normy ČSN ISO 50002 (úroveň 2). "
        "Zahrnuje revizi historické spotřeby, místní šetření, měření a výpočtové "
        "hodnocení úsporných opatření."
    )

    # 2. Předmět EA – rámcové vymezení (podrobnosti dle § 7)
    predmet_ea: str = ""
    lokalizace_predmetu: str = ""

    # 3. Potřeby a očekávání zadavatele
    potreby_a_cile: str = ""

    # 4. Kritéria hodnocení – ekonomická + MKH (příloha č. 9)
    ekonomicke_ukazatele: str = "NPV, IRR, prostá a reálná doba návratnosti (Ts, Tsd)"
    horizont_hodnoceni_let: int = 20
    diskontni_sazba_pct: float = 4.0      # % – reálná diskontní sazba
    inflace_energie_pct: float = 3.0       # % – roční změna cen energií
    zahrnout_financni_podporu: bool = False
    mkh_kriteria_popis: str = (
        "Vícekriteriální hodnocení dle přílohy č. 9 vyhl. 140/2021 Sb. zahrnuje: "
        "NPV, dobu návratnosti, úsporu CO₂ a technickou proveditelnost."
    )

    # 5. Součinnost zadavatele
    soucinnost_pozadavky: str = (
        "Zadavatel zajistí přístup do všech částí předmětu auditu, přidělí "
        "kontaktní osobu odpovědnou za součinnost a poskytne podklady dle "
        "přiloženého seznamu požadovaných dokumentů."
    )
    harmonogram: str = ""

    # 6. Strategické dokumenty
    strategicke_dokumenty: str = ""

    # 7. Formát zprávy
    format_zpravy: str = "Elektronicky ve formátu PDF; 1× tištěný výtisk vázaný"

    # 8. Projednání dílčích výstupů
    projednani_vystupu: str = (
        "Návrh zprávy bude předán zadavateli k připomínkám před finalizací. "
        "Případné změny předmětu nebo harmonogramu budou řešeny písemným "
        "dodatkem k plánu EA dle § 4 odst. 3 vyhl. 140/2021 Sb."
    )

    # Dodatky (§ 4 odst. 3) – volný text každého dodatku
    dodatky: list[str] = field(default_factory=list)


@dataclass
class ProjectResult:
    """
    Celková bilance projektu (souhrnný řádek listu Celková bilance).

    Agreguje výsledky všech aktivních opatření.
    """

    energie: EnergyInputs
    vysledky: list[MeasureResult] = field(default_factory=list)

    # EA/EP rozšíření – doplněno kalkulátorem (None pokud vstupy chybí)
    ekonomika_parametry: Optional["EkonomickeParametry"] = None
    ekonomika_projekt: Optional["EkonomickeBilance"] = None   # NPV/IRR/Tsd celého projektu
    emise_pred: Optional["EmiseBilance"] = None               # emise ve výchozím stavu
    emise_po: Optional["EmiseBilance"] = None                 # emise po opatřeních
    klasifikace_pred: Optional["KlasifikaceObaly"] = None     # A–G stávající stav
    klasifikace_po: Optional["KlasifikaceObaly"] = None       # A–G po opatřeních (TBD)

    @property
    def aktivni(self) -> list[MeasureResult]:
        return [r for r in self.vysledky if r.aktivni]

    @property
    def celkova_investice(self) -> float:
        return sum(r.investice for r in self.aktivni)

    @property
    def celkova_uspora_teplo(self) -> float:
        return sum(r.uspora_teplo for r in self.aktivni)

    @property
    def celkova_uspora_zp(self) -> float:
        return sum(r.uspora_zp for r in self.aktivni)

    @property
    def celkova_uspora_ee(self) -> float:
        return sum(r.uspora_ee for r in self.aktivni)

    @property
    def celkove_vynos_pretoky(self) -> float:
        return sum(r.vynos_pretoky for r in self.aktivni)

    @property
    def celkova_uspora_voda(self) -> float:
        return sum(r.uspora_voda for r in self.aktivni)

    @property
    def celkova_uspora_srazky(self) -> float:
        return sum(r.uspora_srazky for r in self.aktivni)

    @property
    def celkova_uspora_kc(self) -> float:
        return sum(r.uspora_kc for r in self.aktivni)

    @property
    def celkove_servisni_naklady(self) -> float:
        return sum(r.servisni_naklady for r in self.aktivni)

    @property
    def celkova_uspora_pct(self) -> float:
        if self.energie.celkove_naklady == 0:
            return 0.0
        return self.celkova_uspora_kc / self.energie.celkove_naklady

    @property
    def prosta_navratnost_celkem(self) -> Optional[float]:
        net = self.celkova_uspora_kc - self.celkove_servisni_naklady
        if net <= 0:
            return None
        return self.celkova_investice / net
