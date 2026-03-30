"""
Emisní bilance a faktory primární energie.

Výpočty dle vyhlášky 140/2021 Sb. (EA) a 141/2021 Sb. (EP).

════════════════════════════════════════════════════════════════
EMISNÍ FAKTORY CO₂ – vyhl. 140/2021 Sb., příloha 8
════════════════════════════════════════════════════════════════
Příloha 8 vyhlášky 140/2021 Sb. obsahuje POUZE emisní faktory CO₂
[t CO₂/MWh vztaženo k výhřevnosti].
NOₓ, SO₂, TZL vyhláška 140/2021 nestanoví – nejsou předmětem
povinného ekologického hodnocení dle této vyhlášky.

Zákonné hodnoty CO₂ z přílohy 8 [t CO₂/MWh × 1 000 = kg CO₂/MWh]:
  Zemní plyn:                     0,200 t/MWh =  200 kg/MWh
  Elektřina:                      0,860 t/MWh =  860 kg/MWh
  LPG (zkapalněný ropný plyn):    0,237 t/MWh =  237 kg/MWh
  Topný olej (plynový + ostatní): 0,267 t/MWh =  267 kg/MWh
  Topný olej nízkosirný ≤1% S:   0,279 t/MWh =  279 kg/MWh
  Topný olej vysokosirný >1% S:   0,279 t/MWh =  279 kg/MWh
  Černé uhlí:                     0,330 t/MWh =  330 kg/MWh
  Hnědé uhlí:                     0,352 t/MWh =  352 kg/MWh
  Hnědouhelné brikety:            0,346 t/MWh =  346 kg/MWh
  Koks:                           0,385 t/MWh =  385 kg/MWh
  Dálkové teplo (CZT):            nestanoveno   – dle § 7 vyhl. 140/2021
                                  a ČSN EN 15316-4-5; výchozí 180 kg/MWh
                                  (kotel ZP ≈ 200, biomasa ≈ 15,
                                   kogenerace ≈ 70–140 kg/MWh)

════════════════════════════════════════════════════════════════
FAKTORY PRIMÁRNÍ ENERGIE – vyhl. 264/2020 Sb., příloha 3
ve znění novely č. 222/2024 Sb. (platnost od 1. 9. 2024)
════════════════════════════════════════════════════════════════
Vyhláška 264/2020 definuje POUZE fpe,nOZE (faktor neobnovitelné
složky primární energie). Celkový faktor primární energie fpe
(včetně OZE) tato vyhláška nestanoví.

  Energonositel                          fpe,nOZE (-)
  ──────────────────────────────────────────────────
  Zemní plyn                             1,0
  Tuhá fosilní paliva                    1,0
  LPG / propan-butan                     1,2
  Topný olej                             1,2
  Elektřina                              2,1   ← novela 222/2024 (dříve 2,6)
  Dřevěné peletky                        0,1   ← novela 222/2024 (dříve 0,2)
  Kusové dřevo, dřevní štěpka            0,1
  Energie okolního prostředí             0,0
  CZT – ostatní (nezařazené)             1,3
  CZT – účinná soustava, ≤80 % OZE      0,7   ← novela 222/2024 (dříve 0,9)
  CZT – účinná soustava, >80 % OZE      0,1   ← novela 222/2024 (dříve 0,2)
  Odpadní teplo z technologie            0,0
  Ostatní neuvedené energonositele       1,2
"""

from __future__ import annotations

from dataclasses import dataclass


# ──────────────────────────────────────────────────────────────────────────────
# Emisní faktory CO₂ [kg/MWh] – vyhl. 140/2021 Sb., příloha 8
# (zákonné hodnoty, t CO₂/MWh × 1 000)
# Příloha 8 nestanoví NOₓ/SO₂/TZL – tyto složky jsou informativní.
# ──────────────────────────────────────────────────────────────────────────────

EMISNI_FAKTORY: dict[str, dict[str, float]] = {
    "zp": {
        "co2": 200.0,   # 0,200 t/MWh – příloha 8 vyhl. 140/2021 Sb. ✓
        # NOₓ/SO₂/TZL: informativní, příloha 8 nestanoví
        "nox": 0.081,
        "so2": 0.000,
        "tzl": 0.001,
        "nh3": 0.000,
    },
    "teplo": {
        "co2": 180.0,   # kg CO₂/MWh – příloha 8 nestanoví; výchozí průměr CZT
                        # dle § 7 vyhl. 140/2021 + ČSN EN 15316-4-5; ověřit dle CZT
        "nox": 0.054,
        "so2": 0.011,
        "tzl": 0.003,
        "nh3": 0.000,
    },
    "ee": {
        "co2": 860.0,   # 0,860 t/MWh – příloha 8 vyhl. 140/2021 Sb. ✓ (zákonná hodnota)
        "nox": 0.108,
        "so2": 0.171,
        "tzl": 0.010,
        "nh3": 0.000,
    },
    "lpg": {
        "co2": 237.0,   # 0,237 t/MWh – příloha 8 vyhl. 140/2021 Sb. ✓
        "nox": 0.085,
        "so2": 0.000,
        "tzl": 0.001,
        "nh3": 0.000,
    },
    "olej": {
        "co2": 267.0,   # 0,267 t/MWh – topný a ostatní plynový olej, příloha 8 ✓
        "nox": 0.092,
        "so2": 0.020,
        "tzl": 0.003,
        "nh3": 0.000,
    },
    "olej_nizkosirnY": {
        "co2": 279.0,   # 0,279 t/MWh – topný olej nízkosirný ≤1 % hm. S, příloha 8 ✓
        "nox": 0.092,
        "so2": 0.005,
        "tzl": 0.003,
        "nh3": 0.000,
    },
    "olej_vysokosirny": {
        "co2": 279.0,   # 0,279 t/MWh – topný olej vysokosirný >1 % hm. S, příloha 8 ✓
        "nox": 0.092,
        "so2": 0.040,
        "tzl": 0.003,
        "nh3": 0.000,
    },
    "cerne_uhli": {
        "co2": 330.0,   # 0,330 t/MWh – příloha 8 vyhl. 140/2021 Sb. ✓
        "nox": 0.200,
        "so2": 0.400,
        "tzl": 0.050,
        "nh3": 0.000,
    },
    "hnede_uhli": {
        "co2": 352.0,   # 0,352 t/MWh – příloha 8 vyhl. 140/2021 Sb. ✓
        "nox": 0.200,
        "so2": 0.600,
        "tzl": 0.060,
        "nh3": 0.000,
    },
    "hnedouhelne_brikety": {
        "co2": 346.0,   # 0,346 t/MWh – příloha 8 vyhl. 140/2021 Sb. ✓
        "nox": 0.200,
        "so2": 0.500,
        "tzl": 0.055,
        "nh3": 0.000,
    },
    "koks": {
        "co2": 385.0,   # 0,385 t/MWh – příloha 8 vyhl. 140/2021 Sb. ✓
        "nox": 0.150,
        "so2": 0.050,
        "tzl": 0.020,
        "nh3": 0.000,
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Faktory primární energie z neobnovitelných zdrojů (fpe,nOZE)
# Vyhl. 264/2020 Sb. příloha 3, ve znění novely č. 222/2024 Sb. (od 1. 9. 2024)
#
# POZOR: vyhláška 264/2020 nedefinuje celkový fpe (vč. OZE) – pouze fpe,nOZE.
# ──────────────────────────────────────────────────────────────────────────────

FAKTORY_PRIMARNI_ENERGIE: dict[str, float] = {
    "zp":                    1.0,   # zemní plyn
    "tuha_fosil":            1.0,   # tuhá fosilní paliva
    "lpg":                   1.2,   # propan-butan / LPG
    "olej":                  1.2,   # topný olej
    "ee":                    2.1,   # elektřina (novela 222/2024; dříve 2,6)
    "pelety":                0.1,   # dřevěné peletky (novela 222/2024; dříve 0,2)
    "drevo":                 0.1,   # kusové dřevo, dřevní štěpka
    "okolni_prostredi":      0.0,   # energie okolního prostředí (TČ apod.)
    "teplo_ostatni":         1.3,   # CZT – ostatní (výchozí pro nespecifikované CZT)
    "teplo_ucinna":          0.7,   # CZT – účinná soustava, ≤80 % OZE (nov. 222/2024)
    "teplo_ucinna_oze":      0.1,   # CZT – účinná soustava, >80 % OZE (nov. 222/2024)
    "odpadni_teplo":         0.0,   # odpadní teplo z technologie
    "ostatni":               1.2,   # ostatní neuvedené energonositele
}

# Aliasy pro zpětnou kompatibilitu
FAKTORY_PRIMARNI_ENERGIE["teplo"] = FAKTORY_PRIMARNI_ENERGIE["teplo_ostatni"]


def fpe_noze(energonosic: str) -> float:
    """
    Faktor primární energie z neobnovitelných zdrojů (fpe,nOZE) dle
    vyhl. 264/2020 Sb. ve znění novely č. 222/2024 Sb.

    Parametr energonosic je libovolný řetězec; funkce hledá shodu
    se klíči FAKTORY_PRIMARNI_ENERGIE.
    Výchozí hodnota: zemní plyn (1,0).
    """
    n = energonosic.lower()
    for k, val in FAKTORY_PRIMARNI_ENERGIE.items():
        if k in n:
            return val
    return FAKTORY_PRIMARNI_ENERGIE["zp"]


# Zpětně kompatibilní alias
def fpe(energonosic: str, noze_only: bool = True) -> float:
    """Zpětně kompatibilní alias pro fpe_noze(). Parametr noze_only ignorován."""
    return fpe_noze(energonosic)


@dataclass
class EmiseBilance:
    """Roční emise ze spotřeby energie [kg/rok].

    Povinná složka dle vyhl. 140/2021 příl. 8: pouze co2_kg.
    Ostatní složky jsou informativní (příloha 8 je nestanoví).
    """

    co2_kg: float = 0.0   # CO₂ [kg/rok] – povinné dle vyhl. 140/2021 příl. 8
    nox_kg: float = 0.0   # NOₓ [kg/rok] – informativní
    so2_kg: float = 0.0   # SO₂ [kg/rok] – informativní
    tzl_kg: float = 0.0   # TZL [kg/rok] – informativní
    eps_kg: float = 0.0   # EPS [kg/rok] – informativní (ekvivalentní prašné škody)


def _eps(tzl: float, nox: float, so2: float, nh3: float = 0.0) -> float:
    """EPS = 1,0×TZL + 0,88×NOₓ + 0,54×SO₂ + 0,64×NH₃ [kg]."""
    return tzl * 1.0 + nox * 0.88 + so2 * 0.54 + nh3 * 0.64


def vypocitej_emise(
    zp_mwh: float,
    teplo_mwh: float,
    ee_mwh: float,
) -> EmiseBilance:
    """
    Vypočítá roční emise ze zadaných spotřeb tří energonosičů.

    CO₂ faktory dle vyhl. 140/2021 Sb., příloha 8 (zákonné hodnoty).
    NOₓ/SO₂/TZL jsou informativní – příloha 8 je nestanoví.

    Parametry:
        zp_mwh    – roční spotřeba zemního plynu [MWh]
        teplo_mwh – roční spotřeba dálkového tepla [MWh]
        ee_mwh    – roční spotřeba elektrické energie [MWh]
    """
    def _sum(key: str) -> float:
        return (
            zp_mwh    * EMISNI_FAKTORY["zp"][key]
            + teplo_mwh * EMISNI_FAKTORY["teplo"][key]
            + ee_mwh    * EMISNI_FAKTORY["ee"][key]
        )

    co2 = _sum("co2")
    nox = _sum("nox")
    so2 = _sum("so2")
    tzl = _sum("tzl")
    nh3 = _sum("nh3")

    return EmiseBilance(
        co2_kg=round(co2, 1),
        nox_kg=round(nox, 3),
        so2_kg=round(so2, 3),
        tzl_kg=round(tzl, 3),
        eps_kg=round(_eps(tzl, nox, so2, nh3), 3),
    )
