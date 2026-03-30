"""
AI generátor popisných textů pro pasport budovy.

Volá Claude API (claude-haiku) a vrací odborný popis stávajícího stavu
dané technické soustavy na základě dat ze session_state.

Nastavení API klíče – jedna z možností:
  1. .streamlit/secrets.toml:  ANTHROPIC_API_KEY = "sk-ant-..."
  2. Proměnná prostředí:        ANTHROPIC_API_KEY=sk-ant-...
"""
from __future__ import annotations

import os


# ─────────────────────────────────────────────────────────────────────────────
# API klíč
# ─────────────────────────────────────────────────────────────────────────────

def _api_key() -> str | None:
    try:
        import streamlit as st
        val = st.secrets.get("ANTHROPIC_API_KEY")
        if val:
            return val
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


def ma_api_klic() -> bool:
    return bool(_api_key())


# ─────────────────────────────────────────────────────────────────────────────
# Pomocné
# ─────────────────────────────────────────────────────────────────────────────

def _ser(items: list, fields: list[str]) -> str:
    if not items:
        return "(žádné záznamy)"
    lines = []
    for item in items:
        parts = [f"{k}: {item.get(k, '–')}" for k in fields if k in item]
        lines.append(", ".join(parts))
    return "\n".join(f"  - {l}" for l in lines)


# ─────────────────────────────────────────────────────────────────────────────
# Prompty pro jednotlivé sekce
# ─────────────────────────────────────────────────────────────────────────────

def _p_vytapeni(ss: dict) -> str:
    zdroje = _ser(ss.get("sys_vyt_zdroje", []), ["typ", "vykon_kw", "pocet", "rok", "stav"])
    vetvi = _ser(ss.get("sys_vyt_vetvi", []), ["typ", "pocet_ot", "trv", "rok", "stav"])
    regulace = _ser(ss.get("sys_vyt_regulace", []), ["typ", "rok", "stav"])
    return (
        "Napiš popis stávajícího stavu vytápění pro technickou zprávu (pasport budovy).\n\n"
        f"Zdroje tepla:\n{zdroje}\n\n"
        f"Otopné větve:\n{vetvi}\n\n"
        f"Regulace:\n{regulace}"
    )


def _p_tuv(ss: dict) -> str:
    zdroje = _ser(ss.get("sys_tuv_zdroje", []), ["typ", "objem_l", "rok", "stav"])
    cir = "ano" if ss.get("sys_tuv_rozvody_cirkulace") else "ne"
    rok = ss.get("sys_tuv_rozvody_rok", "–")
    stav = ss.get("sys_tuv_rozvody_stav", "–")
    return (
        "Napiš popis stávajícího stavu přípravy teplé užitkové vody (TUV) "
        "pro technickou zprávu (pasport budovy).\n\n"
        f"Zdroje TUV:\n{zdroje}\n\n"
        f"Rozvody TUV: rok instalace {rok}, stav: {stav}, cirkulace: {cir}"
    )


def _p_chlazeni(ss: dict) -> str:
    if not ss.get("sys_chl_instalovano"):
        return (
            "Napiš jednu větu do technické zprávy: "
            "objekt není vybaven strojním chladicím systémem."
        )
    jednotky = _ser(ss.get("sys_chl_jednotky", []), ["typ", "vykon_kw", "rok", "stav"])
    return (
        "Napiš popis stávajícího chladicího systému pro technickou zprávu (pasport budovy).\n\n"
        f"Chladicí jednotky:\n{jednotky}"
    )


def _p_vzt(ss: dict) -> str:
    jed = _ser(
        ss.get("sys_vzt_jednotky", []),
        ["nazev", "prut_m3h", "zzt", "zzt_ucinnost_pct", "rok", "stav"],
    )
    return (
        "Napiš popis stávajícího větracího systému (VZT) pro technickou zprávu (pasport budovy).\n\n"
        f"VZT jednotky:\n{jed}"
    )


def _p_osvetleni(ss: dict) -> str:
    zony = _ser(
        ss.get("sys_osv_zony", []),
        ["nazev", "typ", "prikon_kw", "pocet", "hodiny_rok", "rizeni", "stav"],
    )
    return (
        "Napiš popis stávajícího osvětlení budovy pro technickou zprávu (pasport budovy).\n\n"
        f"Osvětlovací zóny:\n{zony}"
    )


def _p_stavba(ss: dict) -> str:
    rok = ss.get("sys_sta_rok_vystavby", "–")
    steny = ss.get("sys_sta_stav_steny", "–")
    strecha = ss.get("sys_sta_stav_strecha", "–")
    okna = ss.get("sys_sta_stav_okna", "–")
    zat = ss.get("sys_sta_zatepleno", False)
    rok_zat = ss.get("sys_sta_rok_zatepleni", "–")
    zatepleni = f"ano (rok {rok_zat})" if zat else "ne"
    return (
        "Napiš popis stavebně-technického stavu budovy pro technickou zprávu (pasport budovy).\n\n"
        f"Rok výstavby: {rok}\n"
        f"Stav obvodových stěn: {steny}\n"
        f"Stav střechy/stropu: {strecha}\n"
        f"Stav oken a dveří: {okna}\n"
        f"Zatepleno: {zatepleni}"
    )


def _p_elektro(ss: dict) -> str:
    rok_rozv = ss.get("sys_ele_rok_rozvadece", "–")
    rok_rev = ss.get("sys_ele_rok_revize", "–")
    stav = ss.get("sys_ele_stav_rozvadece", "–")
    podružne = "ano" if ss.get("sys_ele_mereni_podružne") else "ne"
    return (
        "Napiš popis stavu elektroinstalace budovy pro technickou zprávu (pasport budovy).\n\n"
        f"Rok instalace rozvaděčů: {rok_rozv}\n"
        f"Rok poslední revize: {rok_rev}\n"
        f"Stav rozvaděčů: {stav}\n"
        f"Podružné měření odběrů: {podružne}"
    )


def _p_voda(ss: dict) -> str:
    mat_sv = ss.get("sys_vod_material_sv", "–")
    mat_tv = ss.get("sys_vod_material_tv", "–")
    cir = "ano" if ss.get("sys_vod_cirkulace_tv") else "ne"
    rok = ss.get("sys_vod_rok", "–")
    stav = ss.get("sys_vod_stav", "–")
    return (
        "Napiš popis stavu rozvodů vody budovy pro technickou zprávu (pasport budovy).\n\n"
        f"Materiál SV: {mat_sv}\n"
        f"Materiál TV/cirkulace: {mat_tv}\n"
        f"Cirkulace TV: {cir}\n"
        f"Rok instalace: {rok}\n"
        f"Stav: {stav}"
    )


_PROMPTS = {
    "popis_vytapeni": _p_vytapeni,
    "popis_tuv": _p_tuv,
    "popis_chlazeni": _p_chlazeni,
    "popis_vzt": _p_vzt,
    "popis_osvetleni": _p_osvetleni,
    "popis_stavba": _p_stavba,
    "popis_elektro": _p_elektro,
    "popis_voda_rozv": _p_voda,
}

_SYSTEM = (
    "Jsi zkušený energetický specialista s více než 15 lety praxe v oblasti EPC studií, "
    "energetických auditů a pasportizace budov pro veřejný sektor v ČR. "
    "Píšeš podrobné popisy stávajícího stavu technických soustav budovy pro technickou zprávu / pasport budovy, "
    "která je určena zástupcům měst a obcí – tedy lidem bez technického vzdělání."
    "\n\nPravidla pro výstup:"
    "\n- Piš jako zkušený odborník, ale srozumitelně pro netechnického čtenáře (starosta, zastupitel, ekonom obce)."
    "\n- Odborné pojmy vždy krátce vysvětli nebo uveď v kontextu, aby jim porozuměl i laik."
    "\n- Strukturuj text do 3–5 odstavců (bez nadpisů, jen prázdný řádek mezi odstavci)."
    "\n- Celková délka: 200–350 slov – text má být košatý a čtivý, ne telegrafický."
    "\n- 1. odstavec: celkový charakter a stav soustavy, co to je a k čemu slouží."
    "\n- Prostřední odstavce: stáří a technický stav zařízení, způsob ovládání a regulace, případné slabiny nebo specifika provozu."
    "\n- Poslední odstavec: shrnutí celkového dojmu ze soustavy z pohledu energetické hospodárnosti."
    "\n- Pokud jsou vstupní data neúplná, odvoď pravděpodobný stav z kontextu (typ budovy, rok výstavby, typ zařízení)."
    "\n- Nepoužívej odrážky, nadpisy ani výčty – pouze plné odstavce textu."
    "\n- Jazyk: čeština, věcný ale přístupný tón."
)


# ─────────────────────────────────────────────────────────────────────────────
# Veřejné API
# ─────────────────────────────────────────────────────────────────────────────

def generuj_popis(sekce: str, ss: dict, podklady: str = "") -> str:
    """
    Vygeneruje odborný popis dané sekce pasportu pomocí Claude API.

    podklady: volitelný kontextový text sestavený přes podklady_scanner.sestavit_kontext()
    """
    if sekce not in _PROMPTS:
        raise ValueError(f"Neznámá sekce: {sekce!r}")
    key = _api_key()
    if not key:
        raise RuntimeError(
            "API klíč Anthropic není nastaven. "
            "Přidej ANTHROPIC_API_KEY do .streamlit/secrets.toml nebo env proměnných."
        )
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("Balíček 'anthropic' není nainstalován (pip install anthropic).") from exc

    prompt = _PROMPTS[sekce](ss)
    if podklady:
        prompt = podklady + "\n\n" + prompt

    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()
