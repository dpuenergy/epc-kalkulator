"""
Generátor demo EA dokumentu se vzorkovými daty.
Spustit: python generate_demo_ea.py
Výstup: demo_EA_ZS_Vzor.docx (ve stejné složce)
"""
from epc_engine.models import (
    BuildingInfo, EnergyInputs, Budova, Prostor, Podklad,
    EnergonositelEA, MKHKriterium, EnPIUkazatel, EAData,
    Vrstva, Konstrukce, TechnickySytem, TechnickeSystemy,
    BilancePouzitiEnergie, PenbData, EnMSOblast, EnMSHodnoceni,
    HistorieRok, KlimatickaData, MeasureResult,
    ProjectResult, Fotografie,
)
from epc_engine.economics import EkonomickeBilance, EkonomickeParametry
from epc_engine.building_class import obalkova_klasifikace
from epc_engine.emissions import vypocitej_emise
from epc_engine.reports.ea_generator import generuj_ea


# ──────────────────────────────────────────────────────────────────────────────
# Budova
# ──────────────────────────────────────────────────────────────────────────────

budova = BuildingInfo(
    nazev_zakazky="EA-2026-ZS-Vzor",
    objekt_nazev="Základní škola Vzorová",
    objekt_adresa="Školní 15, 123 45 Vzorové Město",
    objekt_ku="Vzorové Město",
    objekt_parcelni_cislo="1234/1",
    evidencni_cislo="EA-2026-001",
    cislo_opravneni="ESP-0001",
    ucel_ep="MPO EFEKT",

    zadavatel_nazev="Město Vzorové Město",
    zadavatel_adresa="Náměstí Svobody 1, 123 45 Vzorové Město",
    zadavatel_ico="00123456",
    zadavatel_kontakt="Ing. Jana Krátká, referentka investic, jana.kratka@vzor.cz",

    druh_cinnosti="Základní škola – vzdělávání žáků 1.–9. ročníku",
    pocet_zamestnancu="52 zaměstnanců / 420 žáků",
    provozni_rezim="Výukový provoz Po–Pá 7:00–17:00, prázdninový provoz omezený",

    datum="2026-03-27",
    program_efekt=True,
    ceny_bez_dph=True,

    budovy=[
        Budova(
            nazev="Hlavní školní budova (blok A)",
            objem_m3=8_500,
            podlahova_plocha_m2=2_100,
            ochlazovana_plocha_m2=3_200,
        ),
        Budova(
            nazev="Tělocvična (blok B)",
            objem_m3=2_800,
            podlahova_plocha_m2=620,
            ochlazovana_plocha_m2=950,
        ),
    ],
    prostory=[
        Prostor("Učebny (1.–9. tř.)", "Výuka", "Po–Pá 8:00–16:00"),
        Prostor("Tělocvična", "Sport / TV", "Po–Pá 8:00–17:00"),
        Prostor("Školní jídelna + kuchyně", "Stravování", "Po–Pá 7:00–14:00"),
        Prostor("Kabinety a sborovna", "Administrativa", "Po–Pá 7:00–17:00"),
    ],
    podklady=[
        Podklad("Faktury za ZP 2022–2024 (3 roky)", True),
        Podklad("Faktury za EE 2022–2024 (3 roky)", True),
        Podklad("Projektová dokumentace – původní (1985)", True),
        Podklad("Pasport budovy – aktualizace 2018", True),
        Podklad("Regulační schéma ÚT a TUV", True),
        Podklad("Výkresová dokumentace obálky", False),
    ],

    # Klimatická data (D° dle TNI 73 0331)
    klimaticka_data=KlimatickaData(
        lokalita="Vzorové Město (nadm. výška 310 m)",
        stupnodni_normovane=3_422.0,
        teplota_vnitrni=20.0,
        teplota_exterieru=-15.0,
    ),

    # Historie spotřeby (3 roky, HistorieRok per energonositel)
    # Sezónní profil ZP [Led–Pro]: topná sezóna + TUV celoročně
    # Profil EE: plochý s mírným poklesem v létě (méně osvětlení)
    historie_spotreby=[
        HistorieRok(rok=2022, energonosic="Zemní plyn",
                    spotreba_mwh=510.0, naklady_kc=765_000, stupnodni=3_210,
                    mesicni_mwh=[82, 74, 61, 38, 18, 8, 6, 7, 18, 42, 68, 88]),
        HistorieRok(rok=2022, energonosic="Elektrická energie",
                    spotreba_mwh=92.0, naklady_kc=368_000, stupnodni=3_210,
                    mesicni_mwh=[8.5, 7.8, 8.0, 7.6, 7.2, 6.8, 6.5, 6.8, 7.2, 7.8, 8.2, 9.6]),
        HistorieRok(rok=2023, energonosic="Zemní plyn",
                    spotreba_mwh=495.0, naklady_kc=832_500, stupnodni=3_380,
                    mesicni_mwh=[80, 72, 59, 37, 17, 8, 6, 7, 17, 40, 66, 86]),
        HistorieRok(rok=2023, energonosic="Elektrická energie",
                    spotreba_mwh=88.0, naklady_kc=396_000, stupnodni=3_380,
                    mesicni_mwh=[8.2, 7.5, 7.7, 7.3, 6.9, 6.5, 6.2, 6.5, 6.9, 7.5, 7.9, 9.2]),
        HistorieRok(rok=2024, energonosic="Zemní plyn",
                    spotreba_mwh=430.0, naklady_kc=774_000, stupnodni=2_950,
                    mesicni_mwh=[69, 63, 51, 32, 15, 7, 5, 6, 15, 35, 57, 75]),
        HistorieRok(rok=2024, energonosic="Elektrická energie",
                    spotreba_mwh=80.0, naklady_kc=360_000, stupnodni=2_950,
                    mesicni_mwh=[7.5, 6.8, 7.0, 6.6, 6.3, 5.9, 5.6, 5.9, 6.3, 6.8, 7.2, 8.4]),
    ],

    # Tepelná obálka
    konstrukce=[
        Konstrukce("Obvodová stěna – panel 30 cm (nezateplená)", "stena", 1_850.0,
                   vrstvy=[
                       Vrstva("Železobetonový panel", 0.30, 1.58),
                       Vrstva("Omítka vnitřní", 0.015, 0.88),
                   ]),
        Konstrukce("Střecha plochá (původní)", "strecha", 850.0,
                   vrstvy=[
                       Vrstva("Železobetonová deska", 0.20, 1.58),
                       Vrstva("Tepelná izolace EPS 80mm", 0.08, 0.037),
                       Vrstva("Hydroizolace", 0.005, 0.17),
                   ]),
        Konstrukce("Podlaha na zemině (1. NP)", "podlaha", 700.0,
                   vrstvy=[
                       Vrstva("Betonová mazanina", 0.10, 1.30),
                       Vrstva("Tepelná izolace EPS 50mm", 0.05, 0.037),
                   ]),
        Konstrukce("Okna zdvojená (původní dřevěná)", "okno", 420.0,
                   u_zadane=2.8),
        Konstrukce("Vstupní dveře (kovové)", "dvere", 24.0,
                   u_zadane=3.5),
    ],

    # Technické systémy
    technicke_systemy=TechnickeSystemy(
        vytapeni=TechnickySytem(
            typ="Plynový kondenzační kotel Viessmann Vitodens 200",
            vykon_kw=120.0,
            ucinnost_pct=96.0,
            rok_instalace=2015,
            popis=(
                "Centrální plynový kondenzační kotel o výkonu 120 kW zásobuje celý "
                "objekt teplem pro vytápění a přípravu TUV. Rozvody ÚT jsou dvoutrubkové, "
                "ocelové, bez izolace (část rozvodů). Otopná soustava je převážně "
                "článkových radiátorů, bez termostatických ventilů. Regulace je "
                "ekvitermní s modulem pro letní/zimní provoz."
            ),
        ),
        tuv=TechnickySytem(
            typ="Zásobníkový ohřívač – nepřímotopný 500 l (Dražice OKC 500)",
            vykon_kw=30.0,
            ucinnost_pct=88.0,
            rok_instalace=2015,
            popis=(
                "TUV je připravována v zásobníkovém ohřívači 500 l nepřímotopném, "
                "napojeném na kondenzační kotel. Cirkulace TUV je zajištěna oběhovým "
                "čerpadlem s časovačem (provoz 7:00–16:00). Rozvody TUV jsou "
                "neizolované, délka cirkulačního okruhu cca 80 m."
            ),
        ),
        vzt=TechnickySytem(
            typ="Přirozené větrání + částečná nucená ventilace kuchyně",
            vykon_kw=2.2,
            ucinnost_pct=0.0,
            rok_instalace=2005,
            popis=(
                "Učebny a kanceláře jsou větrány přirozeně okny. Školní kuchyně "
                "je vybavena digestoří s odtahovým ventilátorem (2,2 kW). "
                "Rekuperace tepla z odpadního vzduchu není instalována."
            ),
        ),
        osvetleni=TechnickySytem(
            typ="Lineární zářivky T8 (učebny), halogenové svítidla (chodby)",
            vykon_kw=18.0,
            ucinnost_pct=0.0,
            rok_instalace=2000,
            popis=(
                "Osvětlení učeben je zajištěno lineárními zářivkami T8 (2×36 W / svítidlo), "
                "celkem cca 280 svítidel. Chodby a schodiště jsou osvětleny halogenovými "
                "svítidly. Spínání je manuální, bez přítomnostních čidel ani denního řízení. "
                "Průměrná intenzita osvětlení v učebnách 280–320 lux (požadavek 300–500 lux)."
            ),
        ),
        mereni_ridici=(
            "Měření spotřeby ZP: 1× průmyslový plynoměr na vstupu do kotelny (G16). "
            "Měření EE: 1× elektroměr na hlavním rozvaděči. Podružné měření není. "
            "Řídicí systém ÚT: ekvitermní regulátor s týdenním programem. "
            "Dálkové monitorování není k dispozici."
        ),
    ),

    # Bilance dle účelu (příl. 4 vyhl. 141/2021 – pro EP, sdílená i pro EA)
    bilance_pouziti=BilancePouzitiEnergie(
        vytapeni_mwh=380.0, vytapeni_kc=684_000,
        tuv_mwh=50.0,       tuv_kc=90_000,
        vetrání_mwh=0.0,    vetrání_kc=0,
        osvetleni_mwh=35.0, osvetleni_kc=157_500,
        technologie_mwh=40.0, technologie_kc=180_000,
        chlazeni_mwh=0.0,   chlazeni_kc=0,
        phm_mwh=5.0,        phm_kc=22_500,
    ),

    # PENB data (výsledky z certifikovaného SW)
    penb=PenbData(
        trida_stavajici="D",
        trida_navrhovy="C",
        merná_potreba_tepla=125.0,
        celkova_dodana_energie=158.0,
        primarni_neobnovitelna=185.0,
        energeticka_vztazna_plocha=2_100.0,
        poznamka="PENB zpracován v SW NKN III v. 3.6.4, zpracovatel Ing. Pavel Beneš, ESP-0042.",
    ),

    # EnMS hodnocení (hodnoceni: 1=nesplnění, 2=částečné, 3=plné)
    enms=EnMSHodnoceni(oblasti=[
        EnMSOblast("Energetická politika",
                   "Energetická politika není formálně vyhlášena. "
                   "Vedení školy se informálně zavazuje ke snižování spotřeb energií.",
                   1),
        EnMSOblast("Energetické plánování",
                   "Energetický audit je zpracováván poprvé. Pravidelný monitoring "
                   "spotřeb probíhá dle faktur. Výhledový plán úspor není formalizován.",
                   1),
        EnMSOblast("Implementace a provoz",
                   "Základní provozní předpisy pro obsluhu kotlů jsou k dispozici. "
                   "Energetická odpovědnost není formálně přidělena.",
                   2),
        EnMSOblast("Kontrola a měření",
                   "Spotřeba ZP a EE je sledována z ročních faktur. Podružné měření "
                   "neexistuje. Klimatická korekce není prováděna.",
                   1),
        EnMSOblast("Interní audit EnMS",
                   "Interní audity EnMS nebyly prováděny. Systém ISO 50001 není zaveden.",
                   1),
        EnMSOblast("Přezkoumání vedením",
                   "Spotřeby energií jsou projednávány na poradách vedení 1× ročně.",
                   2),
        EnMSOblast("Neustálé zlepšování",
                   "V minulosti proběhla výměna kotle (2015). Systémový přístup "
                   "k průběžnému zlepšování není zaveden.",
                   1),
    ]),

    okrajove_podminky=(
        "Výpočty jsou provedeny pro klimatickou oblast odpovídající lokalitě Vzorové Město "
        "(D = 3 422 den·K, te = –15 °C, ti = 20 °C). Referenčním rokem pro hodnocení "
        "úspor je průměr let 2022–2024 korigovaný na normální denostupně. "
        "Ceny energií odpovídají aktuálním smlouveným tarifům zadavatele (bez DPH). "
        "Ekonomické hodnocení je zpracováno pro hodnotící horizont 20 let, diskontní "
        "sazba 4 % p.a., inflace cen energií 3 % p.a."
    ),

    # EA rozšíření
    ea_data=EAData(
        evidencni_cislo_ea="EA-2026-001",
        cil=(
            "Cílem energetického auditu je identifikace a posouzení příležitostí ke "
            "snížení energetické náročnosti budovy ZŠ Vzorová. Audit je zpracován "
            "v souladu s § 9 odst. 1 zákona č. 406/2000 Sb. a vyhláškou č. 140/2021 Sb."
        ),
        datum_zahajeni="03.01.2026",
        datum_ukonceni="28.03.2026",
        plan_text=(
            "Plán energetického auditu byl předán zadavateli dne 10.01.2026 "
            "(příloha č. 7.1). Sběr podkladů proběhl v lednu a únoru 2026, "
            "prohlídka objektu dne 15.02.2026."
        ),
        program_realizace=(
            "Doporučuje se realizovat příležitosti v pořadí daném multikriteriálním "
            "hodnocením. Prioritně zateplení obálky (OP1a + OP1b + OP1c) v rámci "
            "jedné realizační etapy pro maximalizaci synergií. Výměna osvětlení (OP3) "
            "je vhodná jako samostatná rychlá akce s krátkou dobou návratnosti. "
            "Výsledky budou vyhodnocovány ročně dle fakturovaných spotřeb "
            "korigovaných na denostupně."
        ),
        energonositele=[
            EnergonositelEA("Zemní plyn (ZP)", "NOZE", "Budovy"),
            EnergonositelEA("Elektrická energie (EE)", "NOZE", "Budovy"),
        ],
        mkh_kriteria=[
            MKHKriterium("Čistá současná hodnota (NPV)", "tis. Kč", "max", 30.0, "npv"),
            MKHKriterium("Prostá doba návratnosti (Td)", "roky", "min", 30.0, "td"),
            MKHKriterium("Roční úspora energie", "MWh/rok", "max", 25.0, "mwh"),
            MKHKriterium("Roční úspora nákladů na energii", "tis. Kč/rok", "max", 15.0, "kc"),
        ],
        enpi=[
            EnPIUkazatel(
                nazev="Měrná spotřeba tepla na vytápění",
                jednotka="kWh/m²·rok",
                hodnota_stavajici=181.0,
                hodnota_navrhova=105.0,
                popis_stanoveni="Spotřeba ZP na ÚT / podlahová plocha (2 100 m²), průměr 2022–2024",
                je_stavajici=True,
            ),
            EnPIUkazatel(
                nazev="Měrná spotřeba elektrické energie",
                jednotka="kWh/m²·rok",
                hodnota_stavajici=38.1,
                hodnota_navrhova=22.0,
                popis_stanoveni="Celková spotřeba EE / podlahová plocha (2 100 m²)",
                je_stavajici=True,
            ),
            EnPIUkazatel(
                nazev="Celková měrná spotřeba energie budovy",
                jednotka="kWh/m²·rok",
                hodnota_stavajici=243.8,
                hodnota_navrhova=152.0,
                popis_stanoveni="Celková spotřeba (ZP+EE) / podlahová plocha",
                je_stavajici=True,
            ),
            EnPIUkazatel(
                nazev="Spotřeba energie na žáka",
                jednotka="MWh/žák·rok",
                hodnota_stavajici=1.21,
                hodnota_navrhova=0.76,
                popis_stanoveni="Celková spotřeba / počet žáků (420)",
                je_stavajici=False,
            ),
        ],
    ),
)

# ──────────────────────────────────────────────────────────────────────────────
# Energie (průměr 2022–2024)
# ──────────────────────────────────────────────────────────────────────────────

energie = EnergyInputs(
    zp_ut=380.0,
    zp_tuv=50.0,
    ee=80.0,
    teplo_ut=0.0,
    teplo_tuv=0.0,
    cena_zp=1_800.0,      # Kč/MWh (bez DPH)
    cena_ee=4_500.0,      # Kč/MWh (bez DPH)
    cena_teplo=0.0,
    pouzit_zp=True,
    pouzit_teplo=False,
    voda=3_200.0,         # m³/rok
)

# ──────────────────────────────────────────────────────────────────────────────
# Výsledky opatření (MeasureResult – ručně sestavené pro demo)
# ──────────────────────────────────────────────────────────────────────────────

op1a = MeasureResult(
    id="OP1a", nazev="Zateplení obvodových stěn ETICS (λ=0,031 W/mK, 160 mm)",
    aktivni=True, investice=4_200_000,
    uspora_zp=155.0, uspora_ee=0.0, uspora_teplo=0.0,
    uspora_kc=279_000, prosta_navratnost=15.1,
    ekonomika=EkonomickeBilance(npv=185_000, irr=0.068, tsd=15.1),
)
op1b = MeasureResult(
    id="OP1b", nazev="Zateplení střechy (PIR deska 200 mm, λ=0,022 W/mK)",
    aktivni=True, investice=1_350_000,
    uspora_zp=62.0, uspora_ee=0.0, uspora_teplo=0.0,
    uspora_kc=111_600, prosta_navratnost=12.1,
    ekonomika=EkonomickeBilance(npv=210_000, irr=0.082, tsd=12.1),
)
op1c = MeasureResult(
    id="OP1c", nazev="Výměna oken za plastová trojskla (Uw=0,9 W/m²K)",
    aktivni=True, investice=1_890_000,
    uspora_zp=48.0, uspora_ee=0.0, uspora_teplo=0.0,
    uspora_kc=86_400, prosta_navratnost=21.9,
    ekonomika=EkonomickeBilance(npv=-125_000, irr=0.028, tsd=21.9),
)
op2 = MeasureResult(
    id="OP2", nazev="Výměna kotle za kondenzační + termostatické ventily + hydraulika",
    aktivni=True, investice=680_000,
    uspora_zp=52.0, uspora_ee=0.0, uspora_teplo=0.0,
    uspora_kc=93_600, prosta_navratnost=7.3,
    ekonomika=EkonomickeBilance(npv=520_000, irr=0.138, tsd=7.3),
)
op3 = MeasureResult(
    id="OP3", nazev="Výměna osvětlení za LED (učebny + chodby + tělocvična)",
    aktivni=True, investice=420_000,
    uspora_zp=0.0, uspora_ee=29.0, uspora_teplo=0.0,
    uspora_kc=130_500, prosta_navratnost=3.2,
    ekonomika=EkonomickeBilance(npv=980_000, irr=0.305, tsd=3.2),
)

# Emise a klasifikace
emise_pred = vypocitej_emise(zp_mwh=430.0, teplo_mwh=0.0, ee_mwh=80.0)
emise_po   = vypocitej_emise(zp_mwh=113.0, teplo_mwh=0.0, ee_mwh=51.0)

result = ProjectResult(
    energie=energie,
    vysledky=[op1a, op1b, op1c, op2, op3],
    ekonomika_parametry=EkonomickeParametry(),
    emise_pred=emise_pred,
    emise_po=emise_po,
    klasifikace_pred=obalkova_klasifikace(1.38, 0.41),
)

# ──────────────────────────────────────────────────────────────────────────────
# Generování dokumentu
# ──────────────────────────────────────────────────────────────────────────────

print("Generuji demo EA dokument...")
buf = generuj_ea(budova, result)

output_path = "demo_EA_ZS_Vzor.docx"
with open(output_path, "wb") as f:
    f.write(buf.getvalue())

print(f"OK Dokument ulozen: {output_path}")
print(f"  Velikost: {len(buf.getvalue()) / 1024:.1f} kB")
