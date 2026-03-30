"""
Referenční hodnoty součinitele prostupu tepla dle ČSN 73 0540-2.

Zdroj: list Pomocné_Součinitele_R v šabloně Výpočet ochlazovaných konstrukcí.xltx

UN,20   = požadovaná hodnota (normová hranice)
Urec,20 = doporučená hodnota (energeticky úsporné řešení)
Upas,20 = doporučená hodnota pro pasivní budovy

Použití::

    from epc_engine.physics.u_values import UHODNOTY, u_hodnoty_konstrukce

    u = u_hodnoty_konstrukce("Stěna vnější")
    print(u.UN, u.Urec, u.Upas)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UHodnoty:
    typ: str
    UN: float                    # W/(m²·K) – požadovaná
    Urec: float                  # W/(m²·K) – doporučená
    Upas: Optional[float]        # W/(m²·K) – pasivní (None = nedefinováno)


UHODNOTY: list[UHodnoty] = [
    UHodnoty("Stěna vnější",                                                    0.30, 0.25, 0.18),
    UHodnoty("Střecha strmá (sklon > 45°)",                                     0.30, 0.20, 0.18),
    UHodnoty("Střecha plochá a šikmá (sklon ≤ 45°)",                           0.24, 0.16, 0.15),
    UHodnoty("Strop s podlahou nad venkovním prostorem",                        0.24, 0.16, 0.15),
    UHodnoty("Strop pod nevytápěnou půdou (střecha bez TI)",                    0.30, 0.20, 0.15),
    UHodnoty("Stěna k nevytápěné půdě (střecha bez TI)",                       0.30, 0.25, 0.18),
    UHodnoty("Podlaha / stěna přilehlá k zemině",                              0.45, 0.30, 0.22),
    UHodnoty("Strop / stěna z vytápěného k nevytápěnému prostoru",             0.60, 0.40, 0.30),
    UHodnoty("Strop / stěna z vytápěného k temperovanému prostoru",            0.75, 0.50, 0.38),
    UHodnoty("Strop / stěna z temperovaného k venkovnímu prostředí",           0.75, 0.50, 0.38),
    UHodnoty("Podlaha / stěna temperovaného prostoru přilehlá k zemině",       0.85, 0.60, 0.45),
    UHodnoty("Stěna mezi sousedními budovami",                                  1.05, 0.70, 0.50),
    UHodnoty("Strop mezi prostory s rozdílem teplot ≤ 10 °C",                  1.05, 0.70, None),
    UHodnoty("Stěna mezi prostory s rozdílem teplot ≤ 10 °C",                  1.30, 0.90, None),
    UHodnoty("Strop vnitřní mezi prostory s rozdílem teplot ≤ 5 °C",           2.20, 1.45, None),
    UHodnoty("Stěna vnitřní mezi prostory s rozdílem teplot ≤ 5 °C",           2.70, 1.80, None),
    UHodnoty("Výplň otvoru ve vnější stěně / strmé střeše (okno, NE dveře)",  1.50, 1.20, 0.70),
    UHodnoty("Šikmá výplň otvoru (sklon ≤ 45°) do venkovního prostředí",      1.40, 1.10, 0.90),
    UHodnoty("Dveřní výplň otvoru do venkovního prostředí",                    1.70, 1.20, 0.90),
    UHodnoty("Výplň otvoru z vytápěného do temperovaného prostoru",            3.50, 2.30, 1.70),
    UHodnoty("Výplň otvoru z temperovaného do venkovního prostředí",           3.50, 2.30, 1.70),
    UHodnoty("Šikmá výplň otvoru (sklon ≤ 45°) z temperovaného do venkovního",2.60, 1.70, 1.40),
    UHodnoty("Kovový rám výplně otvoru",                                        None, 1.80, 1.00),  # type: ignore[arg-type]
    UHodnoty("Nekovový rám výplně otvoru",                                      None, 1.30, 0.80),  # type: ignore[arg-type]
]

_LOOKUP = {u.typ.lower(): u for u in UHODNOTY}


def u_hodnoty_konstrukce(typ: str) -> UHodnoty:
    """
    Vrátí referenční U-hodnoty pro daný typ konstrukce (ČSN 73 0540-2).
    Hledá přibližnou shodu – vyvolá ValueError, pokud nenalezne.
    """
    key = typ.strip().lower()
    if key in _LOOKUP:
        return _LOOKUP[key]
    # Částečná shoda
    matches = [u for u in UHODNOTY if key in u.typ.lower()]
    if matches:
        return matches[0]
    raise ValueError(f"Typ konstrukce '{typ}' nenalezen v tabulce ČSN 73 0540-2.")


def typy_konstrukci() -> list[str]:
    """Vrátí seznam typů konstrukcí pro výběrový seznam v UI."""
    return [u.typ for u in UHODNOTY]
