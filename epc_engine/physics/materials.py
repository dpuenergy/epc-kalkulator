"""
Databáze stavebních materiálů – součinitel tepelné vodivosti λ [W/m·K].

Zdroj: list Pomocné_Součinitele v šabloně Výpočet ochlazovaných konstrukcí.xltx
       (293 materiálů, ČSN 73 0540-4 / EN ISO 10456)

Použití::

    from epc_engine.physics.materials import lambda_materialu, MATERIALY

    lam = lambda_materialu("Pěnový polystyren - PPS")   # vybere první shodu
    lam = lambda_materialu("Pěnový polystyren - PPS", rho=30)  # nebo podle hustoty
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Material:
    nazev: str
    lambda_: float   # W/(m·K)
    c: float         # J/(kg·K)
    rho: float       # kg/m³


# (nazev, lambda [W/m·K], c [J/kg·K], rho [kg/m³])
_DATA: list[tuple[str, float, float, float]] = [
    ("2x Asfaltový nátěr", 0.2, 1470.0, 1200.0),
    ("Al fólie", 204.0, 870.0, 2700.0),
    ("Arabit", 0.2, 1470.0, 1072.0),
    ("Asfaltový nátěr", 0.2, 0.2, 900.0),
    ("Averbit", 0.2, 1470.0, 1110.0),
    ("Azbestocementové desky", 0.45, 960.0, 1800.0),
    ("B 400 SH", 0.2, 1470.0, 900.0),
    ("Bitagit R", 0.2, 1470.0, 1210.0),
    ("Bitagit S", 0.2, 1470.0, 1235.0),
    ("Bitagit SI", 0.2, 1470.0, 1245.0),
    ("Butylkaučuk", 0.2, 1470.0, 1360.0),
    ("CD 32 tl. 240", 0.88, 960.0, 1400.0),
    ("CD 32 tl. 320", 0.64, 960.0, 1400.0),
    ("CD 36 tl. 240", 0.67, 960.0, 1250.0),
    ("CD 36 tl. 360", 0.62, 960.0, 1300.0),
    ("CD INA-A", 0.34, 960.0, 1000.0),
    ("CD INA-L", 0.37, 960.0, 1150.0),
    ("CD IVA-A", 0.35, 960.0, 1100.0),
    ("CD IVA-C+IVA-B", 0.41, 960.0, 1100.0),
    ("CD TYN tl. 190", 0.64, 960.0, 1300.0),
    ("CD TYN tl. 290", 0.53, 960.0, 1300.0),
    ("CD TYN tl. 365", 0.36, 960.0, 1000.0),
    ("CDM tl. 115", 0.6, 960.0, 1400.0),
    ("CDM tl. 240", 0.72, 960.0, 1450.0),
    ("CDM tl. 375", 0.73, 960.0, 1550.0),
    ("Celuloid, tuhý nepěněný", 0.21, 1260.0, 1400.0),
    ("Cihelná hmota (800 kg/m³)", 0.51, 920.0, 800.0),
    ("Cihelná hmota (1400 kg/m³)", 0.64, 920.0, 1400.0),
    ("Cihelná hmota (2000 kg/m³)", 1.01, 920.0, 2000.0),
    ("Climatizer Plus + lepidlo", 0.049, 2000.0, 60.0),
    ("Climatizer Plus + voda", 0.042, 2000.0, 36.9),
    ("Climatizer Plus, hutný", 0.04, 2000.0, 59.0),
    ("Climatizer Plus, volný", 0.039, 2000.0, 26.8),
    ("CpD8 tl. 140", 0.55, 960.0, 850.0),
    ("CpD8 tl. 290", 0.6, 960.0, 850.0),
    ("Čedič", 4.2, 920.0, 3200.0),
    ("Desky dřevovláknité, lisované (200 kg/m³)", 0.075, 1630.0, 200.0),
    ("Desky dřevovláknité, lisované (400 kg/m³)", 0.098, 1630.0, 400.0),
    ("Desky dřevovláknité, lisované (600 kg/m³)", 0.13, 1630.0, 600.0),
    ("Desky dřevovláknité, lisované (800 kg/m³)", 0.15, 1630.0, 800.0),
    ("Desky dřevovláknité, lisované (1000 kg/m³)", 0.17, 1630.0, 1000.0),
    ("Desky z dřevitého odpadu s cementem (300 kg/m³)", 0.11, 1580.0, 300.0),
    ("Desky z dřevitého odpadu s cementem (400 kg/m³)", 0.15, 1580.0, 400.0),
    ("Desky z dřevitého odpadu s cementem (500 kg/m³)", 0.17, 1580.0, 500.0),
    ("Desky z dřevitého odpadu s cementem (600 kg/m³)", 0.19, 1580.0, 600.0),
    ("Desky z dřevitého odpadu s cementem (800 kg/m³)", 0.24, 1580.0, 800.0),
    ("Desky z dřevitého odpadu s cementem (1000 kg/m³)", 0.29, 1580.0, 1000.0),
    ("Desky z dřevitého odpadu s cementem (1200 kg/m³)", 0.35, 1580.0, 1200.0),
    ("Desky z korku, lisované", 0.064, 1880.0, 150.0),
    ("Desky z PE", 0.34, 1470.0, 930.0),
    ("Desky z pěnového skla (140 kg/m³)", 0.06, 840.0, 140.0),
    ("Desky z pěnového skla (180 kg/m³)", 0.069, 840.0, 180.0),
    ("Desky z polyesterového skelného laminátu", 0.21, 1050.0, 1600.0),
    ("Desky z PVC", 0.16, 1100.0, 1400.0),
    ("Dřevo měkké, tepelný tok // s vlákny", 0.41, 2510.0, 400.0),
    ("Dřevo měkké, tepelný tok kolmo k vláknům", 0.18, 2510.0, 400.0),
    ("Dřevo tvrdé, tepelný tok // s vlákny", 0.49, 2510.0, 600.0),
    ("Dřevo tvrdé, tepelný tok kolmo k vláknům", 0.22, 2510.0, 600.0),
    ("Dřevotřískové desky", 0.11, 1500.0, 800.0),
    ("Dřevovláknité desky, měkké", 0.046, 1380.0, 230.0),
    ("Foalbit", 0.2, 1470.0, 1270.0),
    ("Foalbit R", 0.2, 1470.0, 1225.0),
    ("Foalbit S", 0.2, 1470.0, 850.0),
    ("Fólie polyetylénová", 0.2, 1470.0, 900.0),
    ("Fólie PVC", 0.2, 960.0, 1400.0),
    ("Formaldehydová pěnová pryskyřice, otevřená (20 kg/m³)", 0.037, 1250.0, 20.0),
    ("Formaldehydová pěnová pryskyřice, otevřená (30 kg/m³)", 0.041, 1250.0, 30.0),
    ("Formaldehydová pěnová pryskyřice, otevřená (40 kg/m³)", 0.045, 1250.0, 40.0),
    ("Formaldehydová pěnová pryskyřice, otevřená (50 kg/m³)", 0.061, 1250.0, 50.0),
    ("Formaldehydová pěnová pryskyřice, uzavřená (25 kg/m³)", 0.041, 1250.0, 25.0),
    ("Formaldehydová pěnová pryskyřice, uzavřená (30 kg/m³)", 0.05, 1510.0, 30.0),
    ("Formaldehydová pěnová pryskyřice, uzavřená (50 kg/m³)", 0.06, 1510.0, 50.0),
    ("Hlína suchá", 0.7, 920.0, 1600.0),
    ("Hliník", 204.0, 870.0, 2700.0),
    ("Chloroprenový tmel", 0.26, 1350.0, 1440.0),
    ("Igelit", 0.2, 1470.0, 1500.0),
    ("IPA 1x", 0.2, 1470.0, 1280.0),
    ("IPA 400 SH", 0.2, 1470.0, 1280.0),
    ("IPA 500 SH (940 kg/m³)", 0.2, 1470.0, 940.0),
    ("IPA 500 SH (1100 kg/m³)", 0.2, 1470.0, 1100.0),
    ("IPA 500 SH (1280 kg/m³)", 0.2, 1470.0, 1280.0),
    ("Isofol B", 0.2, 1470.0, 1330.0),
    ("Keramická dlažba", 1.01, 840.0, 2000.0),
    ("Keramzit / Expandovaná břidlice / Strusková pemza (400 kg/m³)", 0.13, 1260.0, 400.0),
    ("Keramzit / Expandovaná břidlice / Strusková pemza (500 kg/m³)", 0.14, 1260.0, 500.0),
    ("Keramzit / Expandovaná břidlice / Strusková pemza (600 kg/m³)", 0.16, 1260.0, 600.0),
    ("Keramzit / Expandovaná břidlice / Strusková pemza (700 kg/m³)", 0.17, 1260.0, 700.0),
    ("Keramzit / Expandovaná břidlice / Strusková pemza (800 kg/m³)", 0.21, 1260.0, 800.0),
    ("Keramzit / Expandovaná břidlice / Strusková pemza (900 kg/m³)", 0.23, 1260.0, 900.0),
    ("Keramzit / Expandovaná břidlice / Strusková pemza (1000 kg/m³)", 0.24, 1260.0, 1000.0),
    ("Koberec", 0.065, 1880.0, 160.0),
    ("Korková drť", 0.04, 1880.0, 45.0),
    ("Křemelina", 0.19, 1050.0, 600.0),
    ("Led", 2.3, 2093.4, 900.0),
    ("Lepenka A 400H", 0.2, 1470.0, 900.0),
    ("Lepenka A 500H", 0.2, 1470.0, 1070.0),
    ("Lepenka A 50SH", 0.2, 1470.0, 660.0),
    ("Lepenka B 500", 0.2, 1470.0, 845.0),
    ("Linoleum, tuhé nepěněné", 0.19, 1880.0, 1200.0),
    ("Malta cementová", 1.16, 840.0, 2000.0),
    ("Malta vápenná", 0.87, 840.0, 1600.0),
    ("Malta vápennocementová", 0.97, 840.0, 1850.0),
    ("Materiály z minerální plsti (100 kg/m³)", 0.056, 880.0, 100.0),
    ("Materiály z minerální plsti (200 kg/m³)", 0.064, 880.0, 200.0),
    ("Materiály z minerální plsti (300 kg/m³)", 0.079, 880.0, 300.0),
    ("Materiály z minerálních vln, lisované (150 kg/m³)", 0.095, 1150.0, 150.0),
    ("Materiály z minerálních vln, lisované (250 kg/m³)", 0.079, 1150.0, 250.0),
    ("Materiály z minerálních vln, lisované (350 kg/m³)", 0.054, 1150.0, 350.0),
    ("Materiály z minerálních vln, lisované (450 kg/m³)", 0.073, 1150.0, 450.0),
    ("Materiály z minerálních vln, lisované (500 kg/m³)", 0.088, 1150.0, 500.0),
    ("Materiály ze skleněné plsti (15 kg/m³)", 0.046, 940.0, 15.0),
    ("Materiály ze skleněné plsti (35 kg/m³)", 0.05, 940.0, 35.0),
    ("Měď", 372.0, 380.0, 8800.0),
    ("Mramor", 3.5, 920.0, 2800.0),
    ("Novodur, tuhý nepěněný", 0.17, 1465.0, 1380.0),
    ("Ocel", 50.0, 440.0, 7850.0),
    ("Omítka perlitová (250 kg/m³)", 0.1, 850.0, 250.0),
    ("Omítka perlitová (300 kg/m³)", 0.11, 850.0, 300.0),
    ("Omítka perlitová (350 kg/m³)", 0.11, 850.0, 350.0),
    ("Omítka perlitová (400 kg/m³)", 0.12, 850.0, 400.0),
    ("Omítka perlitová (450 kg/m³)", 0.15, 850.0, 450.0),
    ("Omítka perlitová (500 kg/m³)", 0.18, 850.0, 500.0),
    ("Omítka perlitová s PPS granulátem", 0.051, 1000.0, 120.0),
    ("Omítka vápenná", 0.88, 840.0, 1600.0),
    ("Omítka vápennocementová", 0.99, 790.0, 2000.0),
    ("Optifol C", 0.2, 1470.0, 1600.0),
    ("Optifol E", 0.2, 1470.0, 1700.0),
    ("Optifol K", 0.2, 1470.0, 1300.0),
    ("ORSIL L", 0.044, 960.0, 50.0),
    ("ORSIL M", 0.04, 960.0, 75.0),
    ("ORSIL N", 0.039, 960.0, 100.0),
    ("ORSIL P", 0.041, 960.0, 120.0),
    ("ORSIL S", 0.044, 960.0, 200.0),
    ("ORSIL T", 0.041, 960.0, 150.0),
    ("ORSIL X", 0.043, 960.0, 175.0),
    ("Pebit", 0.2, 1470.0, 1350.0),
    ("Pebit R", 0.2, 1470.0, 985.0),
    ("Pebit S", 0.2, 1470.0, 1780.0),
    ("Pěnový polystyren - PPS (10 kg/m³)", 0.051, 1270.0, 10.0),
    ("Pěnový polystyren - PPS (20 kg/m³)", 0.044, 1270.0, 20.0),
    ("Pěnový polystyren - PPS (30 kg/m³)", 0.039, 1270.0, 30.0),
    ("Pěnový polystyren - PPS (40 kg/m³)", 0.037, 1270.0, 40.0),
    ("Pěnový polystyren - PPS (50 kg/m³)", 0.037, 1270.0, 50.0),
    ("Pěnový polystyren - PPS (60 kg/m³)", 0.039, 1270.0, 60.0),
    ("Pěnový polystyren extrudovaný - EXP", 0.034, 2060.0, 30.0),
    ("Pěnový polyuretan měkký", 0.048, 800.0, 35.0),
    ("Pěnový polyuretan tuhý, neplášťovaný", 0.032, 1500.0, 35.0),
    ("Pěnový polyuretan tuhý, plášťovaný", 0.029, 1510.0, 35.0),
    ("Perbitagit", 0.2, 1470.0, 1100.0),
    ("Pertinax, tuhý nepěněný", 0.22, 1590.0, 1400.0),
    ("Piliny", 0.12, 2510.0, 200.0),
    ("Písek", 0.95, 960.0, 1750.0),
    ("Pískovec", 1.7, 920.0, 2600.0),
    ("Pískový pórobeton / plynobeton (480 kg/m³)", 0.19, 840.0, 480.0),
    ("Pískový pórobeton / plynobeton (580 kg/m³)", 0.21, 840.0, 580.0),
    ("Pískový pórobeton / plynobeton (680 kg/m³)", 0.24, 840.0, 680.0),
    ("Plastbeton", 0.74, 1200.0, 1400.0),
    ("Plexisklo, tuhý nepěněný", 0.19, 1465.0, 1180.0),
    ("Polyetylén, tuhý nepěněný", 0.35, 1470.0, 930.0),
    ("Polymercementový potěr", 0.95, 840.0, 1200.0),
    ("Polystyren, tuhý nepěněný", 0.13, 1340.0, 1050.0),
    ("Popílek (85 kg/m³)", 0.23, 1010.0, 85.0),
    ("Popílek (1050 kg/m³)", 0.36, 1010.0, 1050.0),
    ("Popílkový pórobeton / plynosilikát (480 kg/m³)", 0.18, 840.0, 480.0),
    ("Popílkový pórobeton / plynosilikát (580 kg/m³)", 0.2, 840.0, 580.0),
    ("Popílkový pórobeton / plynosilikát (680 kg/m³)", 0.23, 840.0, 680.0),
    ("Porfyr", 1.7, 920.0, 2800.0),
    ("POROTHERM 11,5 P+D - P10 příčka", 0.44, 960.0, 1000.0),
    ("POROTHERM 11,5 P+D - P8 příčka", 0.44, 960.0, 1000.0),
    ("POROTHERM 17,5 P+D - P10 vnitřní nosná stěna", 0.45, 960.0, 1000.0),
    ("POROTHERM 17,5 P+D - P8 vnitřní nosná stěna", 0.42, 960.0, 900.0),
    ("POROTHERM 24 P+D - P10 vnitřní nosná stěna", 0.39, 960.0, 800.0),
    ("POROTHERM 24 P+D - P15 vnitřní nosná stěna", 0.41, 960.0, 900.0),
    ("POROTHERM 30 P+D - P10 nosná stěna", 0.23, 960.0, 800.0),
    ("POROTHERM 30 P+D - P15 nosná stěna", 0.25, 960.0, 900.0),
    ("POROTHERM 36,5 N P+D - P10 tepelně izolační", 0.149, 960.0, 800.0),
    ("POROTHERM 36,5 N P+D - P8 tepelně izolační", 0.174, 960.0, 800.0),
    ("POROTHERM 36,5 P+D - P10 tepelně izolační", 0.149, 960.0, 800.0),
    ("POROTHERM 36,5 P+D - P8 tepelně izolační", 0.174, 960.0, 800.0),
    ("POROTHERM 40 P+D - P10 tepelně izolační", 0.15, 960.0, 800.0),
    ("POROTHERM 40 P+D - P8 tepelně izolační", 0.174, 960.0, 800.0),
    ("POROTHERM 44 N P+D - P10 tepelně izolační", 0.149, 960.0, 800.0),
    ("POROTHERM 44 N P+D - P8 tepelně izolační", 0.174, 960.0, 800.0),
    ("POROTHERM 44 P+D - P10 tepelně izolační", 0.149, 960.0, 800.0),
    ("POROTHERM 44 P+D - P8 tepelně izolační", 0.174, 960.0, 800.0),
    ("POROTHERM 44 Si - P6 super izolační", 0.137, 960.0, 650.0),
    ("POROTHERM 44 Si - P8 super izolační", 0.112, 960.0, 700.0),
    ("POROTHERM 6,5 P+D - P10 příčka", 0.65, 960.0, 1000.0),
    ("POROTHERM 6,5 P+D - P15 příčka", 0.65, 960.0, 1000.0),
    ("Pryž pěnová (150 kg/m³)", 0.048, 1510.0, 150.0),
    ("Pryž pěnová (230 kg/m³)", 0.059, 1510.0, 230.0),
    ("Pryž tvrdá", 0.16, 1420.0, 1200.0),
    ("PVC", 0.16, 1100.0, 1400.0),
    ("PVC pěněné", 0.051, 1350.0, 60.0),
    ("PVC, tuhý nepěněný", 0.2, 1100.0, 1380.0),
    ("R 380SH", 0.2, 1470.0, 700.0),
    ("R 400SH", 0.2, 1470.0, 900.0),
    ("Rostlá půda", 2.3, 920.0, 2000.0),
    ("Ruberoid", 0.2, 1470.0, 1155.0),
    ("Ruberoid R 400", 0.2, 1470.0, 950.0),
    ("Sádrokarton", 0.22, 1060.0, 750.0),
    ("Sadurit", 0.16, 1600.0, 1600.0),
    ("Silon, tuhý nepěněný", 0.26, 1100.0, 1150.0),
    ("Sklo stavební", 0.76, 840.0, 2600.0),
    ("Sklobit", 0.2, 1470.0, 1100.0),
    ("Sklobit 169", 0.2, 1470.0, 1170.0),
    ("Sklobit A", 0.2, 1470.0, 1195.0),
    ("Sklobit extra", 0.2, 1470.0, 1170.0),
    ("Sklobit V", 0.2, 1470.0, 1200.0),
    ("Sníh", 0.26, 2090.0, 300.0),
    ("Škvára", 0.27, 750.0, 750.0),
    ("Štěrk", 0.65, 750.0, 1650.0),
    ("Tatrafan", 0.2, 1470.0, 1500.0),
    ("Teflon, tuhý nepěněný", 0.24, 1100.0, 2100.0),
    ("Tmely pro stavební použití", 0.22, 1300.0, 1500.0),
    ("Trocal A", 0.2, 1470.0, 1265.0),
    ("Trocal B", 0.2, 1470.0, 1280.0),
    ("Trocal DS", 0.2, 1470.0, 1325.0),
    ("Vápenec", 1.4, 920.0, 2500.0),
    ("Vlysy", 0.18, 2510.0, 600.0),
    ("Voda 20 °C", 0.6, 4180.0, 998.0),
    ("Xylolit", 0.26, 2090.0, 1250.0),
    ("YTONG P2-400 (tl. 300)", 0.11, 1000.0, 550.0),
    ("YTONG P2-400 (tl. 375)", 0.11, 1000.0, 550.0),
    ("YTONG P2-500 (tl. 200)", 0.15, 1000.0, 650.0),
    ("YTONG P2-500 (tl. 250)", 0.15, 1000.0, 650.0),
    ("YTONG P3-550 (tl. 100) příčka", 0.17, 1000.0, 700.0),
    ("YTONG P3-550 (tl. 125) příčka", 0.17, 1000.0, 700.0),
    ("YTONG P3-550 (tl. 150) příčka", 0.17, 1000.0, 700.0),
    ("YTONG P3-550 (tl. 175) příčka", 0.17, 1000.0, 700.0),
    ("YTONG P3-550 (tl. 50) vnitřní výstavba", 0.18, 1000.0, 700.0),
    ("YTONG P3-550 (tl. 75) vnitřní výstavba", 0.18, 1000.0, 700.0),
    ("YTONG P4-500 (tl. 200)", 0.15, 1000.0, 650.0),
    ("YTONG P4-500 (tl. 250)", 0.15, 1000.0, 650.0),
    ("YTONG P4-500 (tl. 300)", 0.15, 1000.0, 650.0),
    ("YTONG P4-500 (tl. 375)", 0.15, 1000.0, 650.0),
    ("YTONG P6-700 (tl. 250)", 0.21, 1000.0, 850.0),
    ("YTONG P6-700 (tl. 300)", 0.21, 1000.0, 850.0),
    ("YTONG P6-700 (tl. 375)", 0.21, 1000.0, 850.0),
    ("YTONG sádrová omítka", 0.6, 1000.0, 1100.0),
    ("YTONG silikonová omítka", 0.7, 1000.0, 1200.0),
    ("YTONG strukturální omítka", 0.6, 1000.0, 1100.0),
    ("YTONG univerzální omítka", 0.8, 1000.0, 1200.0),
    ("YTONG venkovní omítka", 0.8, 1000.0, 1200.0),
    ("Zdivo-CP (1700 kg/m³)", 0.8, 900.0, 1700.0),
    ("Zdivo-CP (1800 kg/m³)", 0.86, 900.0, 1800.0),
    ("Železo", 58.0, 440.0, 7850.0),
    ("Žula", 3.1, 920.0, 2500.0),
]

# Sestavit seznam objektů a vyhledávací slovník (normalizovaný název → list)
MATERIALY: list[Material] = [Material(n, l, c, r) for n, l, c, r in _DATA]

_LOOKUP: dict[str, list[Material]] = {}
for _m in MATERIALY:
    _key = _m.nazev.lower()
    _LOOKUP.setdefault(_key, []).append(_m)


def lambda_materialu(nazev: str, rho: Optional[float] = None) -> float:
    """
    Vrátí součinitel tepelné vodivosti λ [W/(m·K)] pro daný materiál.

    Pokud existuje více variant (různé hustoty), lze zpřesnit parametrem rho.
    Pokud materiál není v databázi, vyvolá ValueError.
    """
    key = nazev.strip().lower()
    candidates = _LOOKUP.get(key)
    if not candidates:
        # Zkusit částečnou shodu
        candidates = [m for m in MATERIALY if key in m.nazev.lower()]
        if not candidates:
            raise ValueError(f"Materiál '{nazev}' nenalezen v databázi.")
    if rho is not None:
        closest = min(candidates, key=lambda m: abs(m.rho - rho))
        return closest.lambda_
    return candidates[0].lambda_


def nazvy_materialu() -> list[str]:
    """Vrátí seřazený seznam názvů všech materiálů pro výběr v UI."""
    return [m.nazev for m in MATERIALY]
