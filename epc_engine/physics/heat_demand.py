"""
Výpočet potřeby tepla pro vytápění a přípravu teplé vody.

Odpovídá šabloně Výpočet potřeby tepla pro vytápění a přípravu teplé vody.xltx

Vzorce
------
Vytápění (ČSN EN 12831):
    Q_UT [MWh] = (ε / (ηo × ηr)) × 24 × Φ × D / (θi − θe) / 1000

    kde:
      Φ        = tepelná ztráta objektu [kW]
      D        = vytápěcí denostupně [K·day] = d × (θi − tes)
      θi       = vnitřní výpočtová teplota [°C]  (default 21)
      θe       = venkovní výpočtová teplota [°C]  (default −13)
      ε        = ei × et × ed  (opravné součinitele)
      ηo, ηr   = účinnosti systému

Teplá voda (EN 15316):
    Q_den [kWh/den] = (1 + k_ztraty) × 4186 × V_w [m³/den] × (T_v − T_sv) / 3600
    Q_TUV [MWh] = (Q_den × d + 0.8 × Q_den × (T_v − T_leto)/(T_v − T_zima) × (N − d)) / 1000

    kde:
      V_w       = VW_f × pocet [m³/den]  (VW_f z databáze podle druhu budovy)
      d         = délka otopného období [dny]
      T_v       = výstupní teplota TV [°C]   (default 55)
      T_sv      = teplota studené vody [°C]   (default 10)
      T_leto    = teplota SV v létě [°C]      (default 15)
      T_zima    = teplota SV v zimě [°C]      (default 5)
      N         = počet provozních dní soustavy [dny] (default 365)

Použití::

    from epc_engine.physics.heat_demand import vypocet_vytapeni, vypocet_tuv, VW_FAKTORY

    Q_UT = vypocet_vytapeni(phi_kw=120.0, D=3600.0)
    Q_TUV = vypocet_tuv(druh_budovy="Škola", pocet=300, d=225)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ── Databáze specifické potřeby TV dle druhu budovy ──────────────────────────
# (druh_budovy, VW_f [l / (měrná jednotka · den)], měrná jednotka)
_TUV_DATA: list[tuple[str, float, str]] = [
    ("Rodinný dům",                                 45.0,  "obyvatel"),
    ("Bytový dům",                                  40.0,  "obyvatel"),
    ("Ubytovací zařízení",                          28.0,  "lůžek"),
    ("Jednohvězdičkový hotel bez prádelny",         56.0,  "lůžek"),
    ("Jednohvězdičkový hotel s prádelnou",          70.0,  "lůžek"),
    ("Dvouhvězdičkový hotel bez prádelny",          76.0,  "lůžek"),
    ("Dvouhvězdičkový hotel s prádelnou",           90.0,  "lůžek"),
    ("Tříhvězdičkový hotel bez prádelny",           97.0,  "lůžek"),
    ("Tříhvězdičkový hotel s prádelnou",           111.0,  "lůžek"),
    ("Čtyřhvězdičkový hotel bez prádelny",         118.0,  "lůžek"),
    ("Čtyřhvězdičkový hotel s prádelnou",          132.0,  "lůžek"),
    ("Restaurace",                                  15.0,  "jídel"),
    ("Kavárna",                                     25.0,  "míst k sezení"),
    ("Domov mládeže",                               50.0,  "lůžek"),
    ("Domov pro seniory",                           40.0,  "lůžek"),
    ("Nemocnice bez prádelny",                      56.0,  "lůžek"),
    ("Nemocnice s prádelnou",                       88.0,  "lůžek"),
    ("Administrativní budova",                      12.5,  "osob"),
    ("Škola",                                        7.5,  "osob"),
    ("Školní tělocvična",                           20.0,  "sprchových koupelí"),
    ("Sportovní zařízení",                         101.0,  "instalovaných sprch"),
    ("Průmyslový závod",                            30.0,  "sprchových koupelí"),
]

VW_FAKTORY: dict[str, tuple[float, str]] = {
    druh: (vwf, jednotka) for druh, vwf, jednotka in _TUV_DATA
}


def vw_faktor(druh_budovy: str) -> tuple[float, str]:
    """Vrátí (VW_f [l/jedn./den], měrná jednotka) pro daný druh budovy."""
    key = druh_budovy.strip()
    if key in VW_FAKTORY:
        return VW_FAKTORY[key]
    # Částečná shoda
    matches = [(d, v) for d, v in VW_FAKTORY.items() if key.lower() in d.lower()]
    if matches:
        return matches[0][1]
    raise ValueError(f"Druh budovy '{druh_budovy}' nenalezen v databázi TV.")


def druhy_budov() -> list[str]:
    """Vrátí seznam druhů budov pro výběrový seznam v UI."""
    return list(VW_FAKTORY.keys())


# ── Hlavní výpočetní funkce ───────────────────────────────────────────────────

def vypocet_vytapeni(
    phi_kw: float,
    D: float,
    theta_i: float = 21.0,
    theta_e: float = -13.0,
    ei: float = 0.9,
    et: float = 0.9,
    ed: float = 0.8,
    eta_o: float = 0.95,
    eta_r: float = 0.95,
) -> float:
    """
    Potřeba tepla pro vytápění [MWh/rok].

    Parametry
    ---------
    phi_kw  : tepelná ztráta objektu [kW]
    D       : vytápěcí denostupně [K·day]
    theta_i : vnitřní výpočtová teplota [°C]
    theta_e : venkovní výpočtová teplota [°C]
    ei, et, ed : opravné součinitele (default 0.9, 0.9, 0.8 → ε = 0.648)
    eta_o, eta_r : účinnosti soustavy (default 0.95, 0.95)
    """
    delta_T = theta_i - theta_e
    if delta_T <= 0:
        return 0.0
    eps = ei * et * ed
    return (eps / (eta_o * eta_r)) * (24.0 * phi_kw * D) / delta_T / 1_000.0


def vypocet_tuv(
    druh_budovy: str,
    pocet: float,
    d: int,
    k_ztraty: float = 1.0,
    T_v: float = 55.0,
    T_sv: float = 10.0,
    T_leto: float = 15.0,
    T_zima: float = 5.0,
    N: int = 365,
) -> float:
    """
    Potřeba tepla pro přípravu teplé vody [MWh/rok].

    Parametry
    ---------
    druh_budovy : typ objektu (klíč do VW_FAKTORY)
    pocet       : počet měrných jednotek (osob, lůžek, sprch…)
    d           : délka otopného období [dny]
    k_ztraty    : koeficient energetických ztrát systému (0 = bez ztrát)
    T_v         : výstupní teplota teplé vody [°C]
    T_sv        : teplota studené vody v zimě [°C]
    T_leto      : teplota studené vody v létě [°C]
    T_zima      : teplota studené vody v zimě [°C]
    N           : počet provozních dní soustavy v roce [dny]
    """
    vwf, _ = vw_faktor(druh_budovy)
    V_w = vwf * pocet / 1_000.0  # m³/den

    Q_den = (1 + k_ztraty) * 4_186.0 * V_w * (T_v - T_sv) / 3_600.0  # kWh/den
    Q_tuv = (
        Q_den * d
        + 0.8 * Q_den * ((T_v - T_leto) / (T_v - T_zima)) * (N - d)
    ) / 1_000.0  # MWh
    return max(0.0, Q_tuv)


@dataclass
class VypocetTepla:
    """
    Kompletní výpočet potřeby tepla pro vytápění a TUV před a po rekonstrukci.

    Používá se jako výstup kalkulátoru obálky budovy pro OP1a–OP6.
    """
    Q_UT_pred: float   # MWh/rok – potřeba tepla pro ÚT před opatřením
    Q_UT_po: float     # MWh/rok – potřeba tepla pro ÚT po opatření
    Q_TUV: float       # MWh/rok – potřeba tepla pro TUV (nemění se)

    @property
    def uspora_UT_mwh(self) -> float:
        return max(0.0, self.Q_UT_pred - self.Q_UT_po)

    @property
    def Q_celkem_pred(self) -> float:
        return self.Q_UT_pred + self.Q_TUV

    @property
    def Q_celkem_po(self) -> float:
        return self.Q_UT_po + self.Q_TUV
