"""
Výpočet potřeby tepla pro větrání.

Odpovídá šabloně Výpočet potřeby tepla pro větrání.xltx

Vzorec bez rekuperace:
    Q_větr [MWh] = V / 3600 × 1.2 × 1010 × h_provoz × (d_provoz / 7) × D / 10⁶

Vzorec s rekuperací (ZZT):
    Q_zzt [MWh] = 1.05 × (1 − η_rec) × Q_větr

kde:
    V          = objem větrané místnosti [m³]
    n          = intenzita výměny vzduchu [h⁻¹]  → průtok = V × n [m³/h]
    h_provoz   = počet provozních hodin za den [h/den]
    d_provoz   = počet provozních dní v týdnu [dny/týden]
    D          = vytápěcí denostupně [K·day]
    η_rec      = účinnost rekuperace [-]

Použití::

    from epc_engine.physics.ventilation import vypocet_vetrani
    from epc_engine.physics.degree_days import lokalita

    lok = lokalita("Praha")
    D = lok.denostupne()   # K·day

    Q_bez, Q_se_zzt = vypocet_vetrani(V=480, n=0.25, h_provoz=8, d_provoz=5, D=D, eta_rec=0.9)
    uspora = Q_bez - Q_se_zzt   # MWh/rok ušetřené díky ZZT
"""
from __future__ import annotations


def vypocet_vetrani(
    V: float,
    n: float,
    h_provoz: float,
    d_provoz: float,
    D: float,
    eta_rec: float = 0.0,
) -> tuple[float, float]:
    """
    Potřeba tepla pro větrání [MWh/rok].

    Parametry
    ---------
    V         : objem větrané místnosti [m³]
    n         : intenzita výměny vzduchu [h⁻¹]
    h_provoz  : provozní hodiny za den [h/den]
    d_provoz  : provozní dny v týdnu [dny/týden]
    D         : vytápěcí denostupně [K·day]
    eta_rec   : účinnost rekuperace [-], 0 = bez ZZT

    Vrátí
    -----
    (Q_bez_zzt, Q_se_zzt) – obě hodnoty v [MWh/rok]
    Pokud eta_rec = 0, pak Q_se_zzt == Q_bez_zzt.
    """
    # Průtok vzduchu [m³/h]
    V_prietok = V * n  # m³/h (interní, nepoužívá se přímo)

    # Tepelná ztráta bez rekuperace
    Q_bez = V / 3_600.0 * 1.2 * 1_010.0 * h_provoz * (d_provoz / 7.0) * D / 1_000_000.0

    if eta_rec <= 0:
        return Q_bez, Q_bez

    # Tepelná ztráta s ZZT (10% příplatek na reálné podmínky provozu)
    Q_se_zzt = 1.05 * (1.0 - eta_rec) * Q_bez
    return Q_bez, Q_se_zzt


def uspora_vetrani_mwh(
    V: float,
    n: float,
    h_provoz: float,
    d_provoz: float,
    D: float,
    eta_rec: float,
) -> float:
    """
    Roční úspora tepla díky instalaci ZZT [MWh/rok].

    Zkratková funkce: Q_bez − Q_se_zzt.
    """
    Q_bez, Q_se = vypocet_vetrani(V, n, h_provoz, d_provoz, D, eta_rec)
    return max(0.0, Q_bez - Q_se)
