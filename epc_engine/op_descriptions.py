"""
Textace opatření OP1a–OP22 extrahované z Excel šablony.

Použití::
    from epc_engine.op_descriptions import OP_INFO
    info = OP_INFO["OP1a"]
    print(info["title"])
    print(info["popis"])   # hlavní odstavec
"""

OP_INFO: dict[str, dict] = {
    "OP1a": {
        "title": "Zateplení obvodových stěn systémem ETICS",
        "popis": (
            "Z rešerše podkladů a absolvovaných prohlídek objektů vyplynula potřeba realizovat "
            "kompletní, případně dodatečné zateplení obvodových stěn. Při návrhu opatření je třeba "
            "dbát aktuálně platných předpisů v oblasti energetické náročnosti budov."
        ),
        "dotace": (
            "Součinitel prostupu tepla pro měněné stavební prvky vyjma oken, na něž se vztahuje "
            "podpora, musí být ≤ URj dle přílohy č. 1, vyhl. 264/2020 Sb. (= UN,20 dle ČSN 73 0540-2). "
            "V případě realizace metodou EPC není nutné tyto požadavky dodržet."
        ),
    },
    "OP1b": {
        "title": "Obnova zateplení pomocí termoizolačního omítkového systému",
        "popis": (
            "Při stavebně-technickém průzkumu bylo zjištěno, že stav obvodového pláště je zateplen, "
            "avšak zateplení bylo realizováno před přibližně 15 lety a ztrácí původní technické vlastnosti. "
            "Navrhuje se ošetření stávajícího pláště termoizolačním omítkovým systémem: "
            "λ ≈ 0,05 W/(m·K), zbavuje materiály vlhkosti, má termoreflexní vlastnosti, "
            "prodlužuje životnost ETICS a snižuje přehřívání v létě. "
            "Četnost výmalby při použití kvalitního systému max. 1× za 10 let."
        ),
        "dotace": (
            "Dle pravidel aktuálně známých výzev není třeba dodržet požadavky vyhlášky "
            "v případě realizace metodou EPC."
        ),
    },
    "OP2": {
        "title": "Výměna otvorových výplní",
        "popis": (
            "S ohledem na postupující trendy a zpřísňování podmínek v oblasti energetické náročnosti "
            "je doporučena postupná výměna otvorových výplní na ty splňující nejnovější standardy."
        ),
        "dotace": (
            "Součinitel prostupu tepla oken musí být ≤ 0,6 × URj dle přílohy č. 1, vyhl. 264/2020 Sb. "
            "Hodnota UN,20,W pro okna činí 1,500 W/(m²·K), tzn. požadavek ≤ 0,9 W/(m²·K)."
        ),
    },
    "OP3": {
        "title": "Rekonstrukce střechy (zateplení)",
        "popis": (
            "Z rešerše podkladů a absolvovaných prohlídek objektů vyplynula potřeba realizovat "
            "kompletní, případně dodatečné zateplení střech. Při návrhu opatření je třeba dbát "
            "aktuálně platných předpisů. U památkově chráněných objektů a projektů metodou EPC "
            "není nutné dodržet požadavky vyhlášky."
        ),
        "dotace": (
            "Součinitel prostupu tepla střechy musí být ≤ URj dle přílohy č. 1, vyhl. 264/2020 Sb. "
            "(= UN,20 dle ČSN 73 0540-2 pro daný typ střešní konstrukce)."
        ),
    },
    "OP4": {
        "title": "Zateplení podlahy půdy",
        "popis": (
            "Z rešerše podkladů a absolvovaných prohlídek objektů vyplynula potřeba realizovat "
            "zateplení podlahy půdy. V případě realizace metodou EPC není nutné dodržet "
            "požadavky vyhlášky."
        ),
        "dotace": (
            "Součinitel prostupu tepla musí být ≤ URj dle přílohy č. 1, vyhl. 264/2020 Sb."
        ),
    },
    "OP5": {
        "title": "Zateplení podlahy na terénu",
        "popis": (
            "Z rešerše podkladů a absolvovaných prohlídek objektů vyplynula potřeba realizovat "
            "zateplení podlahy na terénu. V případě realizace metodou EPC není nutné dodržet "
            "požadavky vyhlášky."
        ),
        "dotace": (
            "Součinitel prostupu tepla musí být ≤ URj dle přílohy č. 1, vyhl. 264/2020 Sb."
        ),
    },
    "OP6": {
        "title": "Výmalba interiérů termoreflexními nátěry",
        "popis": (
            "Objekty dostávají každoročně prostředky na obnovu výmalby interiérů. Navrhuje se "
            "využití kvalitnějšího interiérového nátěru s funkcemi: omyvatelnost, zamezení tvorby "
            "plísní, regulace vlhkosti, rovnoměrná distribuce tepla a tepelný komfort, "
            "termoreflexní vlastnosti (snížení přehřívání v létě). "
            "Četnost výmalby max. 1× za 10 let."
        ),
        "dotace": None,
    },
    "OP7": {
        "title": "Výměna zdroje tepla",
        "popis": (
            "Jako hlavní zdroj topné vody se navrhuje kaskáda tepelných čerpadel vzduch/voda "
            "(výkon = 80 % tepelné ztráty, A7W55). Jako bivalentní zdroj zůstane stávající plynová "
            "kotelna (100 % záloha). Budou osazeny dva akumulační zásobníky TV – jeden pro předehřev "
            "TČ, druhý pro dohřev plynovým kotlem. Nová nadřazená regulace s kaskádovým chodem TČ "
            "a kotlů, ekvitermní okruhy a řízení ohřevu TV."
        ),
        "dotace": (
            "Tepelné čerpadlo musí plnit třídu energetické účinnosti A++ dle nařízení Komise (EU) č. 811/2013."
        ),
    },
    "OP8": {
        "title": "Instalace nadřazené regulace, nová výzbroj rozdělovače/sběrače",
        "popis": (
            "Instalace nadřazené regulace umožní optimalizaci chodu zdroje tepla v závislosti "
            "na aktuální potřebě objektu. Nová výzbroj rozdělovače/sběrače zajistí správnou "
            "distribuci tepelné energie do jednotlivých otopných větví."
        ),
        "dotace": None,
    },
    "OP9": {
        "title": "Zavedení IRC systému (individuální regulace topení)",
        "popis": (
            "Systém IRC (Individual Room Control) propojuje zdroj tepla s otopnými tělesy. "
            "Monitoruje teplotu v místnosti, uzavírá těleso při otevřeném okně, "
            "odstavuje větev/zdroj při nulové potřebě. V pokročilejší podobě generuje přehledy "
            "spotřeby a slouží pro rozúčtování nákladů na vytápění nájemcům."
        ),
        "dotace": None,
    },
    "OP10": {
        "title": "Instalace LED osvětlení",
        "popis": (
            "Stávající osvětlení bude nahrazeno svítidly pro-kognitivního osvětlení – "
            "plnospektrální zdroj (450–670 nm, ±10 %), CRI Ra > 95, teplota chromatičnosti "
            "4600–4800 K, min. podíl Harmful blue light (< 8 % v pásmu 415–455 nm). "
            "Zlepšuje komfort a kognitivní výkon uživatelů budov."
        ),
        "dotace": None,
    },
    "OP11": {
        "title": "Instalace fotovoltaické elektrárny (FVE)",
        "popis": (
            "FVE je instalována za účelem pokrytí části vlastní spotřeby objektu. "
            "Přebytky (přetoky) jsou prodávány do distribuční sítě za výkupní cenu."
        ),
        "dotace": None,
    },
    "OP12": {
        "title": "Instalace bateriového uložiště",
        "popis": (
            "Bateriové uložiště omezuje přetoky FVE do sítě tím, že ukládá přebytky "
            "pro pozdější vlastní spotřebu. Zvyšuje míru vlastní spotřeby FVE."
        ),
        "dotace": None,
    },
    "OP13": {
        "title": "Využití přebytků FVE pro ohřev TUV",
        "popis": (
            "Akumulační nádrž na TUV s elektrickým topným tělesem absorbuje přebytky z FVE. "
            "Snižuje spotřebu primárního paliva pro ohřev teplé vody."
        ),
        "dotace": None,
    },
    "OP14": {
        "title": "Instalace spořičů vody",
        "popis": (
            "Osazení spořičů průtoku na výtokové armatury umyvadel, sprchových hlavic a "
            "úsporných splachovacích systémů na toaletách. "
            "Snižuje spotřebu vody i energie na její ohřev."
        ),
        "dotace": None,
    },
    "OP15": {
        "title": "Instalace retenční nádrže na dešťovou vodu",
        "popis": (
            "Podzemní retenční nádrž zachycuje dešťovou vodu ze střechy pro zálivku zahrady. "
            "Snižuje poplatek za odvod srážkové vody z pozemku."
        ),
        "dotace": None,
    },
    "OP16": {
        "title": "Hydraulické vyvážení otopné soustavy",
        "popis": (
            "Nastavení ventilů dle vypočtené tlakové ztráty otopných těles v kombinaci s "
            "oběhovými čerpadly s plynulými otáčkami vede k ideální distribuci tepla, "
            "vychlazení zpátečky a úsporám na vytápění. "
            "Podmínkou jsou funkční termoregulační ventily – počítá se s jejich kompletní výměnou."
        ),
        "dotace": (
            "Dotační tituly stanovují povinnost realizovat hydraulické vyvážení při čerpání "
            "podpory na úsporná opatření."
        ),
    },
    "OP17": {
        "title": "Instalace vzduchotechniky se zpětným získáváním tepla (ZZT)",
        "popis": (
            "Vyhláška č. 146/2024 Sb. (od 1. 7. 2024) zpřísňuje max. koncentraci CO₂ na 1 200 ppm. "
            "Při zpřísňujících se požadavcích na energetickou náročnost budov nelze pobytové místnosti "
            "vyvětrat jinak než vzduchotechnickou jednotkou s rekuperací. "
            "Pro školy se doporučuje decentrální nebo semicentrální řešení (max. 5 tříd / jednotka)."
        ),
        "dotace": (
            "Při financování z dotace je podmínkou zajistit větrání dle Konceptu větrání "
            "vydaného Českou komorou lehkých obvodových plášťů."
        ),
    },
    "OP18": {
        "title": "Instalace venkovních stínicích prvků",
        "popis": (
            "Vnější žaluzie zamezují přestupu tepla zářením – nejefektivnější ochrana před "
            "přehříváním v létě. Dle ČSN 73 0540-2:2007 nesmí nejvyšší letní teplota "
            "v exponované místnosti překročit 27 °C."
        ),
        "dotace": None,
    },
    "OP19": {
        "title": "Zavedení energetického managementu",
        "popis": (
            "Systém managementu hospodaření s energiemi (EnMS) využívá data z měření a regulace "
            "pro stanovení výchozího stavu, ukazatelů energetické náročnosti, cílů a akčních plánů. "
            "Vede ke snižování nákladů na energie a emisí GHG."
        ),
        "dotace": None,
    },
    "OP20": {
        "title": "Rekonstrukce otopné soustavy",
        "popis": (
            "Životnost potrubí z černé oceli je 30–50 let. Zanášení potrubí snižuje účinnost "
            "systému vytápění. Doporučuje se pravidelná kontrola soustavy; rekonstrukce je "
            "vhodná jen při prokázaném dožití. Úspory jsou z praktického hlediska zanedbatelné "
            "ve srovnání s investicí."
        ),
        "dotace": None,
    },
    "OP21": {
        "title": "Rekonstrukce elektroinstalace",
        "popis": (
            "Rekonstrukce elektroinstalace sama o sobě není úsporným opatřením, ale technicky "
            "nutnou záležitostí pro bezpečný provoz ostatních opatření. "
            "Životnost hliníkových rozvodů je 30–40 let – u objektů z éry minulého režimu "
            "může být překročena."
        ),
        "dotace": None,
    },
    "OP22": {
        "title": "Rekonstrukce rozvodů teplé a studené vody",
        "popis": (
            "Rekonstrukce rozvodů není primárně úsporným opatřením, ale může být součástí "
            "komplexní rekonstrukce. Životnost: černá ocel 30–50 let, PPR 50+ let, měď 30+ let "
            "(náchylná na usazeniny). U objektů z éry minulého režimu může být životnost za hranou."
        ),
        "dotace": None,
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Podklady k opatřením
#
# Zdroj: „Podklady k D&B.xlsx" (DPU Energy – General/Koncepty)
# Struktura každé položky:
#   cinnost    – název požadovaného podkladu
#   zajisteni  – kdo primárně zajišťuje (Zákazník / DPU ENERGY / Ventia / externě)
#   nahradni   – kdo zajistí, pokud zákazník nemá (DPU REVIT / externě / —)
#   role       – odborná role zajišťující podklad
#   dotace_only – True = vyžadováno pouze při čerpání dotace, False = vždy
# ──────────────────────────────────────────────────────────────────────────────

# Obecné podklady platné pro VŠECHNA opatření
OP_PODKLADY_OBECNE: list[dict] = [
    {
        "cinnost": "Studie stavebně-technologického řešení (projektová studie)",
        "zajisteni": "Ventia",
        "nahradni": "—",
        "role": "Projektant TZB",
        "dotace_only": False,
    },
    {
        "cinnost": "Hrubé položkové rozpočty",
        "zajisteni": "Ventia",
        "nahradni": "—",
        "role": "Projektant TZB",
        "dotace_only": False,
    },
    {
        "cinnost": "Energetický posudek",
        "zajisteni": "DPU ENERGY",
        "nahradni": "—",
        "role": "Energetický specialista",
        "dotace_only": True,
    },
    {
        "cinnost": "Průkaz energetické náročnosti budovy (PENB)",
        "zajisteni": "DPU ENERGY",
        "nahradni": "—",
        "role": "Energetický specialista",
        "dotace_only": True,
    },
]

# Podklady per opatření (mapování: klíč = OP ID shodný s OP_INFO)
OP_PODKLADY: dict[str, list[dict]] = {
    "OP1a": [
        {"cinnost": "Dokumentace stávajícího stavu (stavební výkresy)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant staveb", "dotace_only": False},
        {"cinnost": "Stavebně-technický průzkum – zpráva",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant staveb", "dotace_only": False},
        {"cinnost": "Sondy u kritických míst (na základě STI průzkumu)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Stavební firma", "dotace_only": False},
        {"cinnost": "Posudek synantropních druhů (hnízdění ptáků, netopýři)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Ornitolog / zoolog", "dotace_only": True},
    ],
    "OP1b": [
        {"cinnost": "Dokumentace stávajícího stavu (stavební výkresy)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant staveb", "dotace_only": False},
        {"cinnost": "Stavebně-technický průzkum – zpráva",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant staveb", "dotace_only": False},
    ],
    "OP2": [
        {"cinnost": "Dokumentace stávajícího stavu (stavební výkresy)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant staveb", "dotace_only": False},
        {"cinnost": "Stavebně-technický průzkum – zpráva",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant staveb", "dotace_only": False},
    ],
    "OP3": [  # Zateplení střechy (rekonstrukce střechy)
        {"cinnost": "Dokumentace stávajícího stavu (stavební výkresy)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant staveb", "dotace_only": False},
        {"cinnost": "Stavebně-technický průzkum – zpráva",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant staveb", "dotace_only": False},
        {"cinnost": "Sondy u kritických míst (na základě STI průzkumu)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Stavební firma", "dotace_only": False},
        {"cinnost": "Posouzení dřevěné konstrukce (mykologie, hmyz, dřevokazný hmyz)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Mykolog / entomolog", "dotace_only": False},
        {"cinnost": "Statický posudek střešní konstrukce",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Statik", "dotace_only": False},
        {"cinnost": "Posudek synantropních druhů (hnízdění ptáků, netopýři)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Ornitolog / zoolog", "dotace_only": True},
    ],
    "OP4": [  # Zateplení podlahy půdy
        {"cinnost": "Dokumentace stávajícího stavu (stavební výkresy)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant staveb", "dotace_only": False},
        {"cinnost": "Stavebně-technický průzkum – zpráva",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant staveb", "dotace_only": False},
        {"cinnost": "Sondy u kritických míst (na základě STI průzkumu)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Stavební firma", "dotace_only": False},
    ],
    "OP5": [  # Zateplení podlahy na terénu
        {"cinnost": "Dokumentace stávajícího stavu (stavební výkresy)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant staveb", "dotace_only": False},
        {"cinnost": "Stavebně-technický průzkum – zpráva",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant staveb", "dotace_only": False},
        {"cinnost": "Sondy u kritických míst (na základě STI průzkumu)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Stavební firma", "dotace_only": False},
    ],
    "OP6": [],  # Termoreflexní nátěry – bez zvláštních požadavků na podklady
    "OP7": [  # Výměna zdroje tepla (zahrnuje podtypy – vyberte relevantní)
        {"cinnost": "Dokumentace stávajícího stavu zdroje tepla (schéma kotelny / strojovny)",
         "zajisteni": "Zákazník", "nahradni": "Ventia", "role": "Projektant TZB", "dotace_only": False},
        {"cinnost": "Zpráva o stavu otopné soustavy",
         "zajisteni": "Zákazník", "nahradni": "DPU ENERGY", "role": "Energetický specialista", "dotace_only": False},
        {"cinnost": "Revize plynového zařízení (pro plynový kotel / kogeneraci)",
         "zajisteni": "Zákazník", "nahradni": "—", "role": "Revizní technik plynu", "dotace_only": False},
        {"cinnost": "Revize spalinových cest (pro plynový kotel)",
         "zajisteni": "Zákazník", "nahradni": "—", "role": "Kominík / revizní technik", "dotace_only": False},
        {"cinnost": "Požárně-bezpečnostní řešení",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Autorizovaný technik PBŘ", "dotace_only": False},
        {"cinnost": "Dokumentace stávajícího stavu elektroinstalace (pro TČ / kogeneraci)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Projektant elektro", "dotace_only": False},
        {"cinnost": "Diagram spotřeby tepelné energie (profil)",
         "zajisteni": "Zákazník", "nahradni": "DPU ENERGY", "role": "Energetický specialista", "dotace_only": False},
        {"cinnost": "Diagram spotřeby elektrické energie (profil, pro kogeneraci / TČ)",
         "zajisteni": "Zákazník", "nahradni": "DPU ENERGY", "role": "Energetický specialista", "dotace_only": False},
        {"cinnost": "Hluková studie (pro TČ vzduch-voda / kogeneraci)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Certifikovaný akustik", "dotace_only": False},
        {"cinnost": "Hydrogeologický posudek (pro TČ voda-voda / země-voda)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Hydrogeolog", "dotace_only": False},
        {"cinnost": "Dokumentace ke stávajícímu systému měření a regulace",
         "zajisteni": "Zákazník", "nahradni": "Ventia", "role": "Projektant TZB", "dotace_only": False},
    ],
    "OP8": [  # Nadřazená regulace, nová výzbroj R/S
        {"cinnost": "Dokumentace stávajícího stavu zdroje tepla",
         "zajisteni": "Zákazník", "nahradni": "Ventia", "role": "Projektant TZB", "dotace_only": False},
        {"cinnost": "Dokumentace ke stávajícímu systému měření a regulace",
         "zajisteni": "Zákazník", "nahradni": "Ventia", "role": "Projektant TZB", "dotace_only": False},
        {"cinnost": "Stavebně-technický průzkum – zpráva (stav otopné soustavy)",
         "zajisteni": "Zákazník", "nahradni": "Ventia", "role": "Projektant TZB", "dotace_only": False},
        {"cinnost": "Pasportizace objektu (počty těles, větvení soustavy)",
         "zajisteni": "Zákazník", "nahradni": "DPU ENERGY", "role": "Kdokoliv", "dotace_only": False},
    ],
    "OP9": [  # IRC systém
        {"cinnost": "Dokumentace stávajícího stavu – půdorysy (rozmístění otopných těles)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant stavby", "dotace_only": False},
        {"cinnost": "Pasport otopných těles (počty, typ, výkon)",
         "zajisteni": "Zákazník", "nahradni": "DPU ENERGY", "role": "Kdokoliv", "dotace_only": False},
        {"cinnost": "Požadavky na zabezpečení sítě (IT/OT bezpečnost objektu)",
         "zajisteni": "Zákazník", "nahradni": "—", "role": "IT správce zákazníka", "dotace_only": False},
    ],
    "OP10": [  # LED osvětlení
        {"cinnost": "Dokumentace stávajícího stavu – půdorysy, řezy (výšky místností)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant stavby", "dotace_only": False},
        {"cinnost": "Dokumentace stávajícího stavu elektroinstalace",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Projektant elektro", "dotace_only": False},
        {"cinnost": "Pasport svítidel (zatřídění místností, stávající příkony)",
         "zajisteni": "Zákazník", "nahradni": "DPU ENERGY", "role": "Kdokoliv", "dotace_only": False},
        {"cinnost": "Revize elektrických zařízení (platná)",
         "zajisteni": "Zákazník", "nahradni": "—", "role": "Revizní technik EZ", "dotace_only": False},
    ],
    "OP11": [  # FVE
        {"cinnost": "Dokumentace stávajícího stavu střechy (výkresy, orientace, sklony)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant stavby", "dotace_only": False},
        {"cinnost": "Stavebně-technický průzkum – zpráva (stav střechy)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant stavby", "dotace_only": False},
        {"cinnost": "Sondy u kritických míst (na základě STI průzkumu)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Stavební firma", "dotace_only": False},
        {"cinnost": "Posouzení dřevěné konstrukce sedlových střech (mykologie, hmyz)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Mykolog / entomolog", "dotace_only": False},
        {"cinnost": "Statický posudek střešní konstrukce",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Statik", "dotace_only": False},
        {"cinnost": "Platná smlouva o připojení výrobny k distribuční soustavě",
         "zajisteni": "Zákazník", "nahradni": "DPU ENERGY", "role": "Inženýring", "dotace_only": False},
        {"cinnost": "Požárně-bezpečnostní řešení",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Autorizovaný technik PBŘ", "dotace_only": False},
        {"cinnost": "Diagram spotřeby elektrické energie (hodinový nebo čtvrthodinový profil)",
         "zajisteni": "Zákazník", "nahradni": "DPU ENERGY", "role": "Energetický specialista", "dotace_only": False},
    ],
    "OP12": [  # Bateriové uložiště
        {"cinnost": "Dokumentace stávajícího stavu stavby (umístění uložiště)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant stavby", "dotace_only": False},
        {"cinnost": "Dokumentace stávajícího stavu elektroinstalace",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Projektant elektro", "dotace_only": False},
        {"cinnost": "Požárně-bezpečnostní řešení",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Autorizovaný technik PBŘ", "dotace_only": False},
    ],
    "OP13": [  # Přebytky FVE pro ohřev TUV
        {"cinnost": "Pasport zásobníku TUV (objem, výkon topného tělesa)",
         "zajisteni": "Zákazník", "nahradni": "DPU ENERGY", "role": "Kdokoliv", "dotace_only": False},
    ],
    "OP14": [  # Spořiče vody
        {"cinnost": "Pasport výtokových armatur (počty, typy, průtoky)",
         "zajisteni": "Zákazník", "nahradni": "DPU ENERGY", "role": "Kdokoliv", "dotace_only": False},
    ],
    "OP15": [  # Retenční nádrž
        {"cinnost": "Hydrogeologický posudek (vsak, hladina podzemní vody)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Hydrogeolog", "dotace_only": False},
        {"cinnost": "Situační plán (plochy střech, svody, místo umístění nádrže)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant stavby", "dotace_only": False},
    ],
    "OP16": [  # Hydraulické vyvážení
        {"cinnost": "Pasportizace otopných těles (odhadovaný počet v objektu)",
         "zajisteni": "Zákazník", "nahradni": "DPU ENERGY", "role": "Kdokoliv", "dotace_only": False},
        {"cinnost": "Dokumentace ke stávajícímu systému měření a regulace",
         "zajisteni": "Zákazník", "nahradni": "Ventia", "role": "Projektant TZB", "dotace_only": False},
    ],
    "OP17": [  # VZT se ZZT
        {"cinnost": "Dokumentace stávajícího stavu stavby (půdorysy, řezy – vedení VZT)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant stavby", "dotace_only": False},
        {"cinnost": "Dokumentace stávajícího stavu elektroinstalace",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Projektant elektro", "dotace_only": False},
        {"cinnost": "Požárně-bezpečnostní řešení",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Autorizovaný technik PBŘ", "dotace_only": False},
    ],
    "OP18": [  # Venkovní stínění
        {"cinnost": "Dokumentace stávajícího stavu stavby (půdorysy, pohledy fasády)",
         "zajisteni": "Zákazník", "nahradni": "DPU REVIT", "role": "Projektant stavby", "dotace_only": False},
    ],
    "OP19": [  # Energetický management
        {"cinnost": "Přehled instalovaných měřidel energií (stávající stav)",
         "zajisteni": "Zákazník", "nahradni": "DPU ENERGY", "role": "Kdokoliv", "dotace_only": False},
        {"cinnost": "Přístup k fakturám a odečtům (historická data min. 3 roky)",
         "zajisteni": "Zákazník", "nahradni": "—", "role": "Správce budovy", "dotace_only": False},
        {"cinnost": "Organizační schéma provozu (odpovědné osoby za energie)",
         "zajisteni": "Zákazník", "nahradni": "—", "role": "Správce budovy", "dotace_only": False},
    ],
    "OP20": [  # Rekonstrukce otopné soustavy
        {"cinnost": "Dokumentace stávajícího stavu otopné soustavy",
         "zajisteni": "Zákazník", "nahradni": "Ventia", "role": "Projektant TZB", "dotace_only": False},
        {"cinnost": "Stavebně-technický průzkum – zpráva (stav potrubí)",
         "zajisteni": "Zákazník", "nahradni": "Ventia", "role": "Projektant TZB", "dotace_only": False},
    ],
    "OP21": [  # Rekonstrukce elektroinstalace
        {"cinnost": "Dokumentace stávajícího stavu elektroinstalace",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Projektant elektro", "dotace_only": False},
        {"cinnost": "Stavebně-technický průzkum – zpráva (stav rozvodů)",
         "zajisteni": "Zákazník", "nahradni": "Externě", "role": "Projektant elektro", "dotace_only": False},
        {"cinnost": "Revize elektrických zařízení (platná)",
         "zajisteni": "Zákazník", "nahradni": "—", "role": "Revizní technik EZ", "dotace_only": False},
    ],
    "OP22": [  # Rekonstrukce rozvodů TV a SV
        {"cinnost": "Dokumentace stávajícího stavu rozvodů TV/SV",
         "zajisteni": "Zákazník", "nahradni": "Ventia", "role": "Projektant ZTI", "dotace_only": False},
        {"cinnost": "Stavebně-technický průzkum – zpráva (stav potrubí)",
         "zajisteni": "Zákazník", "nahradni": "Ventia", "role": "Projektant ZTI", "dotace_only": False},
    ],
}

# ──────────────────────────────────────────────────────────────────────────────
# Minimální technické podmínky pro zadávací dokumentaci VŘ
#
# Slouží pro generování Přílohy č. 1 zadávací dokumentace EPC výběrového řízení.
# Každá položka: (parametr, požadavek, norma_reference)
# ──────────────────────────────────────────────────────────────────────────────

OP_TECHNICKE_PODMINKY: dict[str, list[tuple[str, str, str]]] = {
    "OP1a": [
        ("Součinitel prostupu tepla stěny",
         "U ≤ 0,18 W/(m²·K) (doporučená hodnota)",
         "ČSN 73 0540-2:2011, tab. 3"),
        ("Tepelná izolace – minimální tloušťka",
         "Min. 140 mm EPS 70F nebo 120 mm MW (λ ≤ 0,038 W/(m·K))",
         "Výpočet dle ČSN EN ISO 6946"),
        ("Reakce na oheň – kontaktní zateplovací systém ETICS",
         "Třída B-s1,d0 nebo lepší (EPS s minerálními pásy u otvorů, MW)",
         "ČSN EN 13501-1; vyhl. č. 23/2008 Sb."),
        ("Délka kotvení hmoždinek do nosné části",
         "Min. 60 mm; kotvící plán dle statického posudku",
         "ETAG 004 / ETA"),
        ("Paropropustnost systému",
         "Sd (omítka + stěrka) ≤ 2 m; difúzní otevřenost musí být prokázána výpočtem",
         "ČSN EN ISO 13788"),
        ("Záruka za provedení a materiál",
         "Min. 10 let (systémová záruka výrobce ETICS)",
         "NOZ § 2113"),
    ],
    "OP1b": [
        ("Součinitel tepelné vodivosti termoizolační omítky",
         "λ ≤ 0,05 W/(m·K) – doložit technickým listem výrobce",
         "ČSN EN 1745"),
        ("Minimální tloušťka vrstvy",
         "≥ 2 mm (dle technologického předpisu výrobce)",
         "Technický list výrobce"),
        ("Reakce na oheň",
         "Min. třída B-s1,d0",
         "ČSN EN 13501-1"),
        ("Záruka za provedení",
         "Min. 10 let",
         "NOZ § 2113"),
    ],
    "OP2": [
        ("Součinitel prostupu tepla oknem",
         "U_w ≤ 0,9 W/(m²·K) (= 0,6 × U_N,20 = 0,6 × 1,5)",
         "Vyhl. č. 264/2020 Sb. příloha 1; ČSN 73 0540-2"),
        ("Součinitel prostupu tepla rámem / rámeček",
         "U_f ≤ 1,3 W/(m²·K); distanční rámeček Ψ_g ≤ 0,04 W/(m·K)",
         "ČSN EN ISO 10077-1"),
        ("Vzduchová neprůvzdušnost",
         "Třída vzduchové propustnosti ≥ 3 (q_100 ≤ 1,5 m³/(h·m))",
         "ČSN EN 12207"),
        ("Odolnost vůči zatížení větrem",
         "Třída ≥ C3 (tlak 800 Pa) dle lokace objektu",
         "ČSN EN 12210"),
        ("Podíl otevíratelných křídel",
         "Min. 30 % celkové plochy zasklení (pro přirozené větrání)",
         "Vyhl. č. 160/2024 Sb."),
        ("Záruka za provedení a materiál",
         "Min. 5 let (profily, kování, těsnění)",
         "NOZ § 2113"),
    ],
    "OP3": [
        ("Součinitel prostupu tepla střechy",
         "U ≤ 0,16 W/(m²·K) (doporučená hodnota pro ploché střechy)",
         "ČSN 73 0540-2:2011, tab. 3"),
        ("Tepelná izolace – minimální tloušťka",
         "Min. 200 mm EPS 100S nebo 160 mm PIR/PUR; λ ≤ 0,038 W/(m·K)",
         "Výpočet dle ČSN EN ISO 6946"),
        ("Hydroizolační souvrství",
         "Min. 2× modifikovaný asfaltový pás (SBS) nebo PVC/TPO fólie; záruka hydroizolace min. 15 let",
         "ČSN 73 1901; EN 13707"),
        ("Spád střechy",
         "Min. 1,75 % (pro ploché střechy) – nutno ověřit spádovými klíny",
         "ČSN 73 1901"),
        ("Záruka za provedení",
         "Min. 10 let (hydroizolace min. 15 let)",
         "NOZ § 2113"),
    ],
    "OP4": [
        ("Součinitel prostupu tepla podlahy půdy",
         "U ≤ 0,15 W/(m²·K)",
         "ČSN 73 0540-2:2011, tab. 3"),
        ("Parotěsná zábrana",
         "Sd ≥ 100 m (PE fólie 0,2 mm nebo asfaltový pás); pokládat na strop pod TI",
         "ČSN EN ISO 13788"),
        ("Tepelná izolace – minimální tloušťka",
         "Min. 200 mm EPS 70S nebo 160 mm MW (λ ≤ 0,038 W/(m·K))",
         "Výpočet dle ČSN EN ISO 6946"),
        ("Záruka za provedení",
         "Min. 10 let",
         "NOZ § 2113"),
    ],
    "OP5": [
        ("Součinitel prostupu tepla podlahy na terénu",
         "U ≤ 0,22 W/(m²·K)",
         "ČSN 73 0540-2:2011, tab. 3"),
        ("Tepelná izolace – mechanická odolnost",
         "EPS 100 nebo EPS 150 (zatížení ≥ 100 kPa při 10% stlačení)",
         "ČSN EN 826"),
        ("Tepelná izolace – minimální tloušťka",
         "Min. 120 mm EPS 100 nebo ekvivalent",
         "Výpočet dle ČSN EN ISO 6946"),
    ],
    "OP6": [
        ("Součinitel tepelné vodivosti nátěru",
         "λ ≤ 0,05 W/(m·K) – doložit technickým listem",
         "ČSN EN 1745"),
        ("Reflexní koeficient (světlost barvy)",
         "Reflexní koeficient ≥ 0,70 pro snížení letního přehřívání",
         "Technický list výrobce"),
        ("Záruka za nátěr",
         "Min. 10 let (četnost přetírání max. 1× za 10 let)",
         "NOZ § 2113"),
    ],
    "OP7": [
        ("Třída energetické účinnosti tepelného čerpadla",
         "Min. A++ při vytápění (nař. Komise (EU) č. 811/2013)",
         "Nař. (EU) č. 811/2013"),
        ("Sezónní topný výkon (SCOP)",
         "SCOP ≥ 3,5 při A7/W55 (vzduch/voda), resp. W10/W55 (voda/voda)",
         "ČSN EN 14511; ČSN EN 14825"),
        ("Hladina akustického výkonu",
         "L_WA ≤ 65 dB(A) (venkovní jednotka) – doložit měřením dle EN 12102",
         "ČSN EN 12102; NV č. 272/2011 Sb."),
        ("Chladivo",
         "Chladivo s GWP ≤ 675 (R32, R290 nebo ekvivalent) dle nař. (EU) č. 517/2014",
         "Nař. (EU) č. 517/2014"),
        ("Bivalentní provoz",
         "Záložní zdroj (plynový kotel) s výkonem min. 100 % tepelné ztráty objektu",
         "ČSN EN 12831"),
        ("Záruka",
         "Min. 5 let na TČ, min. 3 roky na kompresor",
         "NOZ § 2113"),
    ],
    "OP8": [
        ("Řídící systém",
         "Ekvitermní regulace pro každý topný okruh; podpora protokolu Modbus RTU/TCP nebo BACnet",
         "ČSN EN ISO 16484"),
        ("Vzdálený přístup a vizualizace",
         "Webové rozhraní nebo mobilní aplikace; záznamy spotřeby min. 24 měsíců",
         "Technická specifikace"),
        ("Energetická třída oběhových čerpadel",
         "Min. třída A (Energy Efficiency Index EEI ≤ 0,23)",
         "Nař. Komise (EU) č. 622/2012"),
        ("Záruka",
         "Min. 2 roky na řídicí systém a čerpadla",
         "NOZ § 2113"),
    ],
    "OP9": [
        ("Termoregulační hlavice / elektronické termostaty",
         "Elektronické termostaty s programovatelným nočním poklesem; detekce otevřeného okna (volitelně)",
         "ČSN EN 215"),
        ("Rozsah nastavení teploty",
         "5–30 °C; protimrazová ochrana na 7 °C",
         "ČSN EN 215"),
        ("Napájení",
         "Bateriové (výdrž min. 2 roky) nebo sběrnicové (KNX, Zigbee, LoRa)",
         "Technická specifikace"),
        ("Záruka",
         "Min. 2 roky",
         "NOZ § 2113"),
    ],
    "OP10": [
        ("Hladina osvětlenosti",
         "Dle ČSN EN 12464-1 pro daný typ prostoru (kanceláře: 500 lx, chodby: 100 lx, apod.)",
         "ČSN EN 12464-1:2021"),
        ("Světelná účinnost svítidla",
         "≥ 120 lm/W (systémová účinnost včetně DALI ovladače)",
         "ČSN EN 62722-2-1"),
        ("Index podání barev",
         "CRI Ra ≥ 80 (doporučeno Ra ≥ 90 pro pracovní prostory)",
         "ČSN EN 12464-1"),
        ("Životnost světelného zdroje",
         "L80B10 ≥ 50 000 h při 25 °C",
         "ČSN EN 62612"),
        ("Řízení osvětlení",
         "DALI-2 nebo 1–10 V stmívání; přítomnostní čidla tam, kde je to technicky možné",
         "ČSN EN 62386"),
        ("Záruka",
         "Min. 5 let na svítidla a světelné zdroje",
         "NOZ § 2113"),
    ],
    "OP11": [
        ("Jmenovitý výkon FVE",
         "Min. dle projektu (viz příloha – agregovaný rozpočet); tolerance ±5 %",
         "Technická specifikace"),
        ("Minimální účinnost panelů",
         "≥ 20 % (monokrystalický Si) nebo ≥ 18 % (polykrystalický Si)",
         "ČSN EN IEC 61215"),
        ("Záruka na výkon panelů",
         "Min. 80 % jmenovitého výkonu po 25 letech provozu",
         "ČSN EN IEC 61215"),
        ("Záruka na výrobek (panely)",
         "Min. 10 let",
         "NOZ § 2113"),
        ("Střídač – účinnost",
         "Evropská (EURO) účinnost ≥ 97 %",
         "ČSN EN IEC 62109"),
        ("Střídač – záruka",
         "Min. 5 let (možnost prodloužení na 10 let)",
         "NOZ § 2113"),
        ("Ochranné prvky",
         "DC odpojovač, přepěťová ochrana T2 na AC i DC straně, zemnění soustavy",
         "ČSN EN 62548; PNE 33 0000-1"),
        ("Záruka za montáž a provedení",
         "Min. 5 let",
         "NOZ § 2113"),
    ],
    "OP12": [
        ("Kapacita uložiště",
         "Min. dle projektu (viz agregovaný rozpočet); použitelná kapacita ≥ 80 % nominální",
         "Technická specifikace"),
        ("Počet cyklů / životnost",
         "≥ 3 000 cyklů při 80 % DoD nebo záruka 10 let na kapacitu",
         "IEC 62619"),
        ("Chemie baterií",
         "LFP (Li-Fe-P) nebo jiná technologie s integrovaným BMS",
         "IEC 62619; IEC 62620"),
        ("Záruka",
         "Min. 10 let nebo 3 000 cyklů (podle toho, co nastane dříve)",
         "NOZ § 2113"),
    ],
    "OP13": [
        ("Zásobník TUV s elektrickým topným tělesem",
         "Nerezový zásobník, min. objem dle projektu; tepelná ztráta zásobníku ≤ 1,5 W/l",
         "ČSN EN 12897"),
        ("Řídicí systém – integrace s FVE",
         "Automatické přepínání ohřevu podle výkonu FVE (přebytkový ohřev); manuální override",
         "Technická specifikace"),
        ("Záruka",
         "Min. 5 let na zásobník, min. 2 roky na řídicí systém",
         "NOZ § 2113"),
    ],
    "OP14": [
        ("Průtok výtokových armatur – umyvadla",
         "≤ 6 l/min při tlaku 300 kPa (perlátory nebo spořicí armatury)",
         "ČSN EN 817; EU ekoznačka"),
        ("Průtok výtokových armatur – sprchy",
         "≤ 8 l/min při tlaku 300 kPa",
         "ČSN EN 817"),
        ("Splachovací systémy – WC",
         "Dual-flush: 3/6 l nebo 2/4 l; jednorázové splachování max. 6 l",
         "ČSN EN 14055"),
        ("Záruka",
         "Min. 2 roky na veškeré armatury",
         "NOZ § 2113"),
    ],
    "OP15": [
        ("Kapacita retenční nádrže",
         "Min. dle projektu (viz agregovaný rozpočet)",
         "Technická specifikace"),
        ("Materiál nádrže",
         "PE (polyetylen) nebo beton s PE výstelkou; odolný vůči podzemní vodě",
         "ČSN 75 6081"),
        ("Filtr a přečerpávací sada",
         "Vstupní filtr (hrubý a jemný), plováčkový ventil, ponorné čerpadlo s ovládáním",
         "Technická specifikace"),
        ("Přepadový systém",
         "Napojení na kanalizaci nebo vsakovací prvek",
         "ČSN 75 6081"),
    ],
    "OP16": [
        ("Regulační ventily a termostatické ventily",
         "Přednastavitelná regulační šroubení nebo termostatické ventily na všech otopných tělesech",
         "ČSN EN 215; ČSN EN 1854"),
        ("Oběhová čerpadla",
         "Energetická třída A (EEI ≤ 0,23); plynulá regulace otáček",
         "Nař. (EU) č. 622/2012"),
        ("Protokol hydraulického vyvážení",
         "Doložit protokol nastavení každého ventilu s hodnotami průtoku a tlakové ztráty",
         "ČSN EN 14336"),
        ("Záruka",
         "Min. 2 roky na regulační armatury a čerpadla",
         "NOZ § 2113"),
    ],
    "OP17": [
        ("Účinnost zpětného získávání tepla (ZZT)",
         "η_ZZT ≥ 70 % (teplotní faktor při standardních podmínkách dle ČSN EN 308)",
         "ČSN EN 308; Vyhl. č. 264/2020 Sb."),
        ("Třída filtrace přiváděného vzduchu",
         "Min. M5 (ISO ePM10 ≥ 50 %); filtr nahradit min. 2× ročně",
         "ČSN EN ISO 16890"),
        ("Hladina akustického tlaku v obsluhovaném prostoru",
         "≤ 40 dB(A) (v učebně nebo kanceláři při jmenovitém průtoku)",
         "NV č. 272/2011 Sb.; ČSN EN 16798-1"),
        ("Regulace průtoku vzduchu",
         "Automatická regulace dle koncentrace CO₂ (čidlo v každé obsluhované místnosti); max. CO₂ 1 200 ppm",
         "Vyhl. č. 146/2024 Sb.; Metodický pokyn SFŽP"),
        ("Specifický příkon ventilátorů (SFP)",
         "SFP ≤ 1 000 W/(m³/s) pro lokální jednotky; SFP ≤ 1 500 W/(m³/s) pro centrální jednotky",
         "ČSN EN 16798-3"),
        ("Průtok venkovního vzduchu",
         "Min. dle Metodického pokynu pro návrh větrání škol (SFŽP/MPO): MŠ 10, ZŠ1 12, ZŠ2 18, SŠ 20 m³/(h·žák)",
         "Metodický pokyn SFŽP; Vyhl. č. 160/2024 Sb."),
        ("Záruka",
         "Min. 3 roky na VZT jednotky a příslušenství",
         "NOZ § 2113"),
    ],
    "OP18": [
        ("Stínící faktor (Fc)",
         "Fc ≤ 0,20 pro vnější žaluzie nebo markýzy (účinné vnější stínění)",
         "ČSN 73 0540-4; ČSN EN 13363-1"),
        ("Odolnost vůči větru",
         "Min. třída 4 dle ČSN EN 13561 (pro výšku do 10 m nad terénem)",
         "ČSN EN 13561"),
        ("Ovládání",
         "Elektromotorické ovládání; automatické zatažení při nárazu větru > 10 m/s (anemometr)",
         "Technická specifikace"),
        ("Záruka",
         "Min. 3 roky na mechanismus a pohon",
         "NOZ § 2113"),
    ],
    "OP19": [
        ("Systém energetického managementu",
         "Splňuje požadavky ČSN EN ISO 50001; zahrnuje výchozí přezkum, cíle, akční plány a interní audity",
         "ČSN EN ISO 50001:2018"),
        ("Měření a podružné měření",
         "Podružné elektroměry a kalorimetry pro každou budovu / odběrné místo; data dostupná online",
         "Vyhl. č. 141/2021 Sb.; ČSN EN ISO 50006"),
        ("Reportování",
         "Měsíční přehledy spotřeb energií; roční zpráva o hospodaření s energií",
         "ČSN EN ISO 50015"),
        ("Záruka / servisní smlouva",
         "Min. 2 roky na SW a HW; servisní smlouva po dobu EPC kontraktu",
         "NOZ § 2113"),
    ],
    "OP20": [
        ("Materiál potrubí",
         "Ocel bezešvá ČSN EN 10255 nebo měď ČSN EN 1057; případně jiný materiál dle projektu",
         "ČSN 06 0310"),
        ("Tlaková zkouška",
         "Min. 1,5× pracovního tlaku soustavy; výsledky zaznamenat do protokolu",
         "ČSN 06 0310"),
        ("Tepelná izolace rozvodů",
         "Dle ČSN EN 12828 a ČSN EN 15316-2-1 (min. tloušťka dle průměru potrubí)",
         "ČSN EN 12828"),
        ("Záruka",
         "Min. 5 let na potrubí a izolaci",
         "NOZ § 2113"),
    ],
    "OP21": [
        ("Projektová dokumentace a provedení",
         "Dle ČSN 33 2000-1 (HD 60364) a platných předpisů; Cu vodiče pro silnoproud",
         "ČSN 33 2000"),
        ("Jistící a ochranné prvky",
         "Selektivní ochrana (koordinace jističů); RCD ≤ 30 mA v mokrých prostorách",
         "ČSN 33 2000-4-41"),
        ("Revizní zpráva",
         "Výchozí revize elektroinstalace dle ČSN 33 1500 po dokončení prací",
         "ČSN 33 1500"),
        ("Záruka",
         "Min. 3 roky na provedení elektroinstalace",
         "NOZ § 2113"),
    ],
    "OP22": [
        ("Materiál potrubí",
         "PPR PN20, měď nebo nerez (výběr dle projektu); Cu bez olova pro pitnou vodu",
         "ČSN EN 1057; ČSN EN 12201"),
        ("Tlaková zkouška",
         "Min. 1,5× pracovního tlaku; výsledky zaznamenat do protokolu",
         "ČSN 73 6660"),
        ("Tepelná izolace teplé vody",
         "Dle ČSN EN 12828; min. tloušťka izolace = průměr potrubí (do DN 35)",
         "ČSN EN 12828"),
        ("Dezinfekce a proplach",
         "Proplach a dezinfekce rozvodů dle ČSN EN 806-4 před uvedením do provozu",
         "ČSN EN 806-4"),
        ("Záruka",
         "Min. 5 let na potrubí a montáž",
         "NOZ § 2113"),
    ],
}

# ── Položkový rozpočet – typické položky pro slepý výkaz výměr ───────────────
# Formát: (popis_položky, MJ)
# Množství a ceny vyplňuje uchazeč ve výběrovém řízení.

OP_ROZPOCET_POLOZKY: dict[str, list[tuple[str, str]]] = {
    "OP1a": [
        ("Lešení – dodávka, montáž a demontáž", "m²"),
        ("Kontaktní zateplovací systém ETICS – tepelná izolace EPS/MW, lepení, kotvení", "m²"),
        ("Soklová část – XPS nebo perimetrická izolace", "m²"),
        ("Omítková vrstva s výztužnou tkaninou a finální povrchová úprava", "m²"),
        ("Nové oplechování parapetů, atik a říms", "m"),
        ("Nová oplechování prostupů a detailů", "paušál"),
        ("Začištění ostění okenních a dveřních otvorů", "m"),
        ("Projektová dokumentace a inženýring", "paušál"),
        ("Uvedení do provozu, předání díla", "paušál"),
    ],
    "OP1b": [
        ("Demontáž stávající omítky / obkladu fasády", "m²"),
        ("Termoizolační omítkový systém – podkladní vrstva a tepelněizolační omítka", "m²"),
        ("Finální fasádní omítka nebo nátěr", "m²"),
        ("Nové oplechování parapetů a detailů", "m"),
        ("Projektová dokumentace a inženýring", "paušál"),
        ("Uvedení do provozu, předání díla", "paušál"),
    ],
    "OP2": [
        ("Demontáž stávajících oken vč. odvoz a likvidace", "ks"),
        ("Okna plastová / dřevěná / AL – dodávka a montáž (vč. kování, těsnění)", "ks"),
        ("Balkónové nebo terénní dveře – dodávka a montáž", "ks"),
        ("Vnitřní parapety – dodávka a montáž", "ks"),
        ("Vnější parapety – dodávka a montáž", "ks"),
        ("Začištění ostění – interiér / exteriér", "m"),
        ("Projektová dokumentace a inženýring", "paušál"),
        ("Předání díla", "paušál"),
    ],
    "OP3": [
        ("Demontáž střešního pláště / krytiny", "m²"),
        ("Tepelná izolace střechy – minerální vlna nebo PIR (spádové klíny)", "m²"),
        ("Parozábrana / pojistná hydroizolace", "m²"),
        ("Hydroizolační souvrství nebo nová krytina", "m²"),
        ("Klempířské práce – oplechování, okapnice, oplechování atiky", "m"),
        ("Odvodnění střechy – vpusti, svody (oprava / nové)", "ks"),
        ("Projektová dokumentace a inženýring", "paušál"),
        ("Předání díla", "paušál"),
    ],
    "OP4": [
        ("Demontáž stávajícího násypu / podlahové skladby na půdě", "m²"),
        ("Tepelná izolace podlahy půdy – minerální vlna foukaná nebo rohože", "m²"),
        ("Doplňkové klempířské práce", "paušál"),
        ("Projektová dokumentace a inženýring", "paušál"),
        ("Předání díla", "paušál"),
    ],
    "OP5": [
        ("Demontáž stávající podlahové skladby na terénu (bourání)", "m²"),
        ("Tepelná izolace podlahy – XPS / EPS 150S", "m²"),
        ("Nová podlahová skladba – betonová mazanina, potěr, nášlapná vrstva", "m²"),
        ("Izolace soklu / spodní stavby", "m²"),
        ("Projektová dokumentace a inženýring", "paušál"),
        ("Předání díla", "paušál"),
    ],
    "OP6": [
        ("Termoreflexní nátěr interiéru – příprava povrchu a nátěr 2× nástřik", "m²"),
        ("Předání díla", "paušál"),
    ],
    "OP7": [
        ("Demontáž stávajícího zdroje tepla vč. odvoz a ekologická likvidace", "ks"),
        ("Nový zdroj tepla (TČ vzduch-voda / TČ voda-voda / kotel na biomasu / CZT předávací stanice) – dodávka a montáž", "ks"),
        ("Zásobník tepla / akumulační nádrž", "ks"),
        ("Zásobník teplé užitkové vody", "ks"),
        ("Primární okruh – potrubní rozvody, armatury, izolace", "paušál"),
        ("Sekundární okruh – připojení na otopnou soustavu, regulační armatury", "paušál"),
        ("Elektroinstalace silnoproudá a řídicí", "paušál"),
        ("Stavební práce (prostupyd zdivem, základ, strojovna)", "paušál"),
        ("Uvedení do provozu, seřízení, předání díla", "paušál"),
        ("Projektová dokumentace a inženýring", "paušál"),
    ],
    "OP8": [
        ("Nadřazená regulace (řídicí jednotka DDC/PLC) – dodávka a programování", "ks"),
        ("Nová výzbroj rozdělovače/sběrače – regulační armatury, vyvažovací ventily", "paušál"),
        ("Čidla teploty, průtoku a tlaku", "ks"),
        ("Kabeláž a komunikační infrastruktura (BACnet / Modbus)", "paušál"),
        ("Integrace se stávajícím řídicím systémem", "paušál"),
        ("Oživení a programování řídicí logiky", "paušál"),
        ("Školení obsluhy", "paušál"),
        ("Projektová dokumentace a inženýring", "paušál"),
    ],
    "OP9": [
        ("Termostatické ventily na otopných tělesech – dodávka a montáž", "ks"),
        ("Termostatické hlavice", "ks"),
        ("Regulační a vyvažovací ventily na stoupačkách", "ks"),
        ("Hydraulické vyvážení otopné soustavy – měření a nastavení průtoků", "paušál"),
        ("Oběhová čerpadla s plynulou regulací otáček – dodávka a montáž", "ks"),
        ("Projektová dokumentace a inženýring", "paušál"),
        ("Předání protokolu o hydraulickém vyvážení", "paušál"),
    ],
    "OP10": [
        ("Demontáž stávajících svítidel vč. odvoz", "ks"),
        ("Svítidla LED – dodávka a montáž (interiér)", "ks"),
        ("Svítidla LED – venkovní osvětlení", "ks"),
        ("Systém řízení osvětlení – pohybová čidla, stmívání, časové spínání", "paušál"),
        ("Elektroinstalační práce – napájení, kabeláž", "paušál"),
        ("Úprava rozvaděčů osvětlení", "paušál"),
        ("Revize elektroinstalace", "paušál"),
        ("Projektová dokumentace a inženýring", "paušál"),
    ],
    "OP11": [
        ("FV panely monokrystalické – dodávka a montáž", "kWp"),
        ("Střídač síťový (on-grid) – dodávka a montáž", "ks"),
        ("Nosná konstrukce na střeše / fasádě", "paušál"),
        ("DC kabeláž, konektory a ochranné prvky", "paušál"),
        ("AC kabeláž a rozvaděč FVE vč. jištění a přepěťové ochrany", "paušál"),
        ("Monitoring výroby a spotřeby (datalogger, webový portál)", "paušál"),
        ("Připojení k distribuční soustavě – žádost, projekt, jistič", "paušál"),
        ("Stavební práce (prostupy, kotvy, těsnění)", "paušál"),
        ("Projektová dokumentace a inženýring", "paušál"),
        ("Uvedení do provozu, předání díla", "paušál"),
    ],
    "OP12": [
        ("Bateriový systém BESS (LFP) – dodávka a montáž", "kWh"),
        ("Energetický řídicí systém EMS – dodávka a programování", "ks"),
        ("Rozvaděč BESS vč. jištění a přepěťové ochrany", "ks"),
        ("Elektroinstalační práce a kabeláž", "paušál"),
        ("Integrace s FVE a odběrným místem", "paušál"),
        ("Uvedení do provozu, parametrizace, školení", "paušál"),
        ("Projektová dokumentace a inženýring", "paušál"),
    ],
    "OP13": [
        ("Zásobník TUV pro přebytky FVE – dodávka a montáž", "ks"),
        ("Elektrokotel / topné těleso pro přebytky FVE – dodávka a montáž", "ks"),
        ("Řídicí jednotka přebytků – dodávka, montáž a naprogramování", "ks"),
        ("Elektroinstalační práce", "paušál"),
        ("Uvedení do provozu", "paušál"),
    ],
    "OP14": [
        ("Spořiče vody na výtocích (perlátor, regulátor průtoku) – dodávka a montáž", "ks"),
        ("Spořiče vody na sprchách – limitery průtoku", "ks"),
        ("Instalatérské práce", "paušál"),
        ("Předání díla", "paušál"),
    ],
    "OP15": [
        ("Retenční nádrž na dešťovou vodu – dodávka a osazení", "ks"),
        ("Zemní práce a uložení nádrže", "paušál"),
        ("Přívod dešťové vody ze střechy – žlaby, svody, filtrace", "paušál"),
        ("Rozvod užitkové vody (zálivka, WC) vč. armatur", "paušál"),
        ("Přepad do kanalizace", "paušál"),
        ("Projektová dokumentace a inženýring", "paušál"),
        ("Uvedení do provozu", "paušál"),
    ],
    "OP16": [
        ("Hydraulické vyvážení otopné soustavy – měření a seřízení průtoků", "paušál"),
        ("Vyvažovací ventily na stoupačkách – dodávka a montáž", "ks"),
        ("Termostatické ventily s přednastavením – dodávka a montáž", "ks"),
        ("Termostatické hlavice – dodávka a montáž", "ks"),
        ("Protokol o hydraulickém vyvážení", "paušál"),
        ("Projektová dokumentace", "paušál"),
    ],
    "OP17": [
        ("Vzduchotechnická jednotka se ZZT (rekuperace / regenerace) – dodávka a montáž", "ks"),
        ("Vzduchovody přívodní – dodávka a montáž", "m"),
        ("Vzduchovody odvodní – dodávka a montáž", "m"),
        ("Distribuční prvky (vyústky, mřížky, difuzory)", "ks"),
        ("Regulační klapky a požární klapky", "ks"),
        ("Čidla CO₂ a teploty pro regulaci průtoku vzduchu (DCV)", "ks"),
        ("Protihluková opatření (tlumiče hluku)", "ks"),
        ("Řídicí systém VZT – dodávka, montáž a programování", "paušál"),
        ("Stavební práce (prostupy, drážky, zakrytí)", "paušál"),
        ("Uvedení do provozu, zaregulování, měření průtoků", "paušál"),
        ("Projektová dokumentace a inženýring", "paušál"),
    ],
    "OP18": [
        ("Venkovní stínicí prvky (žaluzie, rolety, markýzy) – dodávka a montáž", "ks"),
        ("Kotvení a nosné prvky", "paušál"),
        ("Elektroinstalace pro motorické ovládání", "paušál"),
        ("Řídicí systém (sluneční automat, integrace do BMS)", "paušál"),
        ("Uvedení do provozu", "paušál"),
    ],
    "OP19": [
        ("Dálkově odečitatelný elektroměr (HDO/pulsní výstup / M-Bus)", "ks"),
        ("Dálkově odečitatelný plynoměr", "ks"),
        ("Dálkově odečitatelný tepelný měřič (průtokoměr + čidla teploty)", "ks"),
        ("Dálkově odečitatelný vodoměr", "ks"),
        ("Komunikační brána / datalogger – sběr dat ze všech měřidel", "ks"),
        ("Software pro energetický management (licence, cloud)", "paušál"),
        ("Kabeláž a instalace", "paušál"),
        ("Zprovoznění, konfigurace a školení energetického manažera", "paušál"),
        ("Projektová dokumentace", "paušál"),
    ],
    "OP20": [
        ("Demontáž stávajících otopných těles vč. odvoz", "ks"),
        ("Nová otopná tělesa – dodávka a montáž", "ks"),
        ("Demontáž stávajícího potrubí ÚT", "m"),
        ("Nové potrubní rozvody ÚT – ocel / Cu / PEX-AL-PEX", "m"),
        ("Tepelná izolace potrubí", "m"),
        ("Armatury, uzavírací ventily, vypouštěcí kohouty", "paušál"),
        ("Tlakové zkoušky potrubí, napuštění soustavy", "paušál"),
        ("Stavební práce (drážky, prostupy, zakrytí)", "paušál"),
        ("Projektová dokumentace a inženýring", "paušál"),
        ("Uvedení do provozu, předání díla", "paušál"),
    ],
    "OP21": [
        ("Demontáž stávající elektroinstalace", "paušál"),
        ("Nové kabely a vodiče – dodávka a montáž", "m"),
        ("Nový rozvaděč nebo rekonstrukce stávajícího", "ks"),
        ("Zásuvky, vypínače, datové prvky – dodávka a montáž", "ks"),
        ("Osvětlovací obvody", "paušál"),
        ("Uzemnění a ochrana před bleskem", "paušál"),
        ("Výchozí revize elektroinstalace", "paušál"),
        ("Projektová dokumentace a inženýring", "paušál"),
        ("Předání díla", "paušál"),
    ],
    "OP22": [
        ("Demontáž stávajícího potrubí TV/SV vč. odvoz", "m"),
        ("Nové potrubní rozvody teplé vody – Cu / PPR PN20", "m"),
        ("Nové potrubní rozvody studené vody", "m"),
        ("Cirkulační potrubí TV – dodávka a montáž", "m"),
        ("Tepelná izolace potrubí TV", "m"),
        ("Cirkulační čerpadlo TV", "ks"),
        ("Armatury – uzávěry, zpětné klapky, pojistné ventily", "paušál"),
        ("Tlaková zkouška, proplach, dezinfekce", "paušál"),
        ("Stavební práce (drážky, prostupy)", "paušál"),
        ("Projektová dokumentace a inženýring", "paušál"),
        ("Předání díla", "paušál"),
    ],
}
