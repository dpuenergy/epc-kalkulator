"""
Databáze denostupňů a délky otopného období pro české lokality.

Zdroj: list Pomocné_Denostupně v šabloně Výpočet potřeby tepla pro větrání.xltx
       (72 lokalit, ČSN EN ISO 15927-6 / TNI 73 0331)

Denostupně D [K·day] = d × (θi − tes), kde:
  d   = délka otopného období [dny]
  θi  = vnitřní výpočtová teplota [°C] (obvykle 21 °C)
  tes = průměrná teplota venkovního vzduchu v otopném období [°C]

Použití::

    from epc_engine.physics.degree_days import lokalita, LOKALITY

    lok = lokalita("Praha")
    d, tes = lok.d13, lok.tes13   # délka sezóny a prům. teplota pro tem=13 °C
    D = d * (21 - tes)            # vytápěcí denostupně
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Lokalita:
    nazev: str
    h: float          # nadmořská výška [m n. m.]
    te: float         # venkovní výpočtová teplota [°C]
    # tem = 12 °C
    tes12: float      # průměrná teplota v otopném období [°C]
    d12: int          # délka otopného období [dny]
    # tem = 13 °C
    tes13: float
    d13: int
    # tem = 15 °C
    tes15: float
    d15: int

    def denostupne(self, theta_i: float = 21.0, tem: int = 13) -> float:
        """
        Vytápěcí denostupně D [K·day] pro danou vnitřní teplotu a práh tem.

        D = d × (θi − tes)
        """
        if tem == 12:
            return self.d12 * (theta_i - self.tes12)
        elif tem == 15:
            return self.d15 * (theta_i - self.tes15)
        else:  # default tem=13
            return self.d13 * (theta_i - self.tes13)


LOKALITY: list[Lokalita] = [
    Lokalita("Benešov", 327, -15, 3.5, 234, 3.9, 245, 5.2, 280),
    Lokalita("Beroun (Králův Dvůr)", 229, -12, 3.7, 225, 4.1, 236, 5.3, 268),
    Lokalita("Blansko (Dolní Lhota)", 273, -15, 3.3, 229, 3.7, 241, 5.1, 275),
    Lokalita("Brno", 227, -12, 3.6, 222, 4.0, 232, 5.1, 263),
    Lokalita("Bruntál", 546, -18, 2.7, 255, 3.3, 271, 4.8, 315),
    Lokalita("Břeclav (Lednice)", 159, -12, 4.1, 215, 4.4, 224, 5.2, 253),
    Lokalita("Česká Lípa", 276, -15, 3.3, 232, 3.8, 245, 5.1, 282),
    Lokalita("České Budějovice", 384, -15, 3.4, 232, 3.8, 244, 5.1, 279),
    Lokalita("Český Krumlov", 489, -18, 3.1, 243, 3.5, 254, 4.6, 288),
    Lokalita("Děčín (Březiny, Libverda)", 141, -12, 3.8, 225, 4.2, 236, 5.5, 269),
    Lokalita("Domažlice", 428, -15, 3.4, 235, 3.8, 247, 5.1, 284),
    Lokalita("Frýdek-Místek", 300, -15, 3.4, 225, 3.8, 236, 5.1, 269),
    Lokalita("Havlíčkův Brod", 422, -15, 2.8, 239, 3.3, 253, 4.9, 294),
    Lokalita("Hodonín", 162, -12, 3.9, 208, 4.2, 215, 5.1, 240),
    Lokalita("Hradec Králové", 244, -12, 3.4, 229, 3.9, 242, 5.2, 279),
    Lokalita("Cheb", 448, -15, 3.0, 246, 3.6, 262, 5.2, 306),
    Lokalita("Chomutov (Ervěnice)", 330, -12, 3.7, 223, 4.1, 233, 5.2, 264),
    Lokalita("Chrudim", 276, -12, 3.6, 225, 4.1, 238, 5.9, 276),
    Lokalita("Jablonec nad Nisou (Liberec)", 502, -18, 3.1, 241, 3.6, 256, 5.1, 298),
    Lokalita("Jičín (Libáň)", 278, -15, 3.5, 223, 3.9, 234, 5.2, 268),
    Lokalita("Jihlava", 516, -15, 3.0, 243, 3.5, 257, 4.8, 296),
    Lokalita("Jindřichův Hradec", 478, -15, 3.0, 242, 3.5, 256, 5.0, 296),
    Lokalita("Karlovy Vary", 379, -15, 3.3, 240, 3.8, 254, 5.1, 293),
    Lokalita("Karviná", 230, -15, 3.6, 223, 4.0, 234, 5.3, 267),
    Lokalita("Kladno (Lány)", 380, -15, 4.0, 243, 4.5, 258, 5.0, 300),
    Lokalita("Klatovy", 409, -15, 3.4, 235, 3.9, 248, 5.2, 286),
    Lokalita("Kolín", 223, -12, 4.0, 216, 4.4, 226, 5.9, 257),
    Lokalita("Kroměříž", 207, -12, 3.5, 217, 3.9, 227, 5.1, 258),
    Lokalita("Kutná Hora (Kolín)", 253, -12, 4.0, 216, 4.4, 226, 5.9, 257),
    Lokalita("Liberec", 357, -18, 3.1, 241, 3.6, 256, 5.1, 298),
    Lokalita("Litoměřice", 171, -12, 3.7, 222, 4.1, 232, 5.2, 263),
    Lokalita("Louny (Lenešice)", 201, -12, 3.7, 219, 4.1, 229, 5.2, 260),
    Lokalita("Mělník", 155, -12, 3.7, 219, 4.1, 229, 5.3, 261),
    Lokalita("Mladá Boleslav", 230, -12, 3.5, 225, 3.9, 235, 5.1, 267),
    Lokalita("Most (Ervěnice)", 230, -12, 3.7, 223, 4.1, 233, 5.2, 264),
    Lokalita("Náchod (Kleny)", 344, -15, 3.1, 235, 3.7, 250, 4.8, 292),
    Lokalita("Nový Jičín", 284, -15, 3.3, 229, 3.8, 242, 5.2, 280),
    Lokalita("Nymburk (Poděbrady)", 186, -12, 3.8, 217, 4.2, 228, 5.5, 262),
    Lokalita("Olomouc", 226, -15, 3.4, 221, 3.8, 231, 5.0, 262),
    Lokalita("Opava", 258, -15, 3.5, 228, 3.9, 232, 5.2, 274),
    Lokalita("Ostrava", 217, -15, 3.6, 219, 4.0, 229, 5.2, 260),
    Lokalita("Pardubice", 223, -12, 3.7, 224, 4.1, 234, 5.2, 265),
    Lokalita("Pelhřimov", 499, -15, 3.0, 241, 3.6, 257, 5.1, 300),
    Lokalita("Písek", 348, -15, 3.2, 235, 3.7, 247, 5.0, 284),
    Lokalita("Plzeň", 311, -12, 3.3, 233, 3.6, 242, 4.8, 272),
    Lokalita("Praha (Karlov)", 181, -12, 4.0, 216, 4.3, 225, 5.1, 254),
    Lokalita("Prachatice", 574, -18, 3.3, 253, 3.8, 267, 5.1, 307),
    Lokalita("Prostějov", 226, -15, 3.4, 220, 3.9, 228, 5.0, 261),
    Lokalita("Přerov", 212, -12, 3.5, 218, 3.5, 252, 5.1, 259),
    Lokalita("Příbram", 502, -15, 3.0, 239, 3.8, 230, 4.9, 290),
    Lokalita("Rakovník", 332, -15, 3.4, 232, 4.0, 250, 5.7, 297),
    Lokalita("Rokycany (Příbram)", 363, -15, 3.0, 239, 3.5, 252, 4.9, 290),
    Lokalita("Rychnov n. Kněžnou (Slatina)", 325, -15, 3.0, 241, 3.5, 254, 4.8, 291),
    Lokalita("Semily (Libštát)", 334, -18, 2.8, 243, 3.4, 259, 4.7, 303),
    Lokalita("Sokolov", 405, -15, 3.4, 239, 3.9, 254, 5.4, 297),
    Lokalita("Strakonice", 392, -15, 3.3, 236, 3.8, 249, 5.2, 288),
    Lokalita("Svitavy (Moravská Třebová)", 447, -15, 2.9, 235, 3.4, 248, 4.8, 286),
    Lokalita("Šumperk", 317, -15, 3.0, 230, 3.5, 242, 5.2, 277),
    Lokalita("Tábor", 480, -15, 3.0, 236, 3.5, 250, 5.0, 289),
    Lokalita("Tachov (Stříbro)", 496, -15, 3.1, 237, 3.6, 250, 5.0, 289),
    Lokalita("Teplice", 205, -12, 3.8, 221, 4.1, 230, 5.3, 261),
    Lokalita("Trutnov", 428, -18, 2.8, 242, 3.3, 257, 5.0, 298),
    Lokalita("Třebíč (Bítovánky)", 406, -15, 2.5, 247, 3.1, 263, 4.6, 306),
    Lokalita("Uherské Hradiště (Buchlovice)", 181, -12, 3.2, 222, 3.6, 233, 5.0, 266),
    Lokalita("Ústí nad Labem", 145, -12, 3.6, 221, 3.9, 229, 5.0, 256),
    Lokalita("Ústí nad Orlicí", 332, -15, 3.1, 238, 3.6, 251, 4.9, 289),
    Lokalita("Vsetín", 346, -15, 3.2, 225, 3.6, 236, 4.9, 270),
    Lokalita("Vyškov", 245, -12, 3.3, 219, 3.7, 229, 4.9, 260),
    Lokalita("Zlín (Napajedla)", 234, -12, 3.6, 216, 4.0, 226, 5.1, 257),
    Lokalita("Znojmo", 289, -12, 3.6, 217, 3.9, 226, 5.2, 256),
    Lokalita("Žďár nad Sázavou", 572, -15, 2.4, 252, 3.1, 270, 4.7, 318),
]

_LOOKUP: dict[str, Lokalita] = {lok.nazev.lower(): lok for lok in LOKALITY}


def lokalita(nazev: str) -> Lokalita:
    """
    Vrátí Lokalita pro dané město (přibližná shoda).
    Vyvolá ValueError, pokud nenalezne.
    """
    key = nazev.strip().lower()
    if key in _LOOKUP:
        return _LOOKUP[key]
    matches = [lok for lok in LOKALITY if key in lok.nazev.lower()]
    if matches:
        return matches[0]
    raise ValueError(f"Lokalita '{nazev}' nenalezena v databázi denostupňů.")


def nazvy_lokalit() -> list[str]:
    """Vrátí seřazený seznam názvů lokalit pro výběrový seznam v UI."""
    return [lok.nazev for lok in LOKALITY]


# ══════════════════════════════════════════════════════════════════════════════
# Roční korekce denostupňů
# ══════════════════════════════════════════════════════════════════════════════
#
# Korekční faktory k_rok = D_skutečné_rok / D_dlouhodobý_průměr.
# Platí pro celé území ČR (regionální odchylky do ±3 %).
#
# Zdroj: Odhadní hodnoty odvozené z ročních teplotních anomálií ČR
#   publikovaných ČHMÚ (Zpráva o podnebí ČR) a srovnání s měřenými
#   denostupni pro Praha-Karlov a Brno-Tuřany.
#   Hodnoty jsou orientační; pro přesnou normalizaci doporučujeme ověřit
#   na www.chmi.cz → Klimatologie → Normály → Denostupně.
#
# Roky bez záznamu → faktor 1,0 (= dlouhodobý průměr).
#
ROCNI_KOREKCE_D: dict[int, float] = {
    # Kalendářní rok → korekční faktor (podíl skutečných a průměrných D)
    2015: 0.97,
    2016: 0.96,
    2017: 0.98,
    2018: 0.92,   # teplejší rok (teplá zima 2017/18, velmi teplé léto)
    2019: 0.94,   # teplý rok (teplá zima 2018/19)
    2020: 0.90,   # velmi teplo (zima 2019/20 nejmirnější za 100 let)
    2021: 0.97,   # blízko průměru (zima 2020/21 normální)
    2022: 0.93,   # teplejší (teplá zima 2021/22, vysoké ceny → úspory?)
    2023: 0.91,   # teplý rok (2022/23 teplá zima, rekordní teploty 2023)
    2024: 0.88,   # velmi teplý (zima 2023/24 rekordně teplá)
}


def denostupne_rok(
    nazev_lokality: str,
    rok: int,
    theta_i: float = 21.0,
    tem: int = 13,
) -> float:
    """
    Odhadované denostupně D [K·day] pro konkrétní lokalitu a kalendářní rok.

    D = D_ref × k_rok, kde D_ref je dlouhodobý průměr dle TNI 73 0331
    a k_rok je roční korekční faktor z ROCNI_KOREKCE_D.

    Pro roky mimo tabulku ROCNI_KOREKCE_D vrátí D_ref (k_rok = 1,0).
    """
    lok = lokalita(nazev_lokality)
    D_ref = lok.denostupne(theta_i, tem)
    k = ROCNI_KOREKCE_D.get(rok, 1.0)
    return round(D_ref * k, 0)
