"""
Pasport technických soustav – strukturovaný přehled stávajícího stavu.

Sdílí session_state s hlavní aplikací.
Data se automaticky propisují do Word reportu a do kalkulace OP10 (osvětlení).
"""

import sys
from pathlib import Path
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from epc_engine.pasport_xlsx_parser import parse_pasport_xlsx
from epc_engine.ai_popis import generuj_popis, ma_api_klic
from epc_engine.podklady_scanner import scan_folder, extract_text, extract_text_scan, sestavit_kontext

st.set_page_config(page_title="Popis stávajícího stavu", page_icon="📋", layout="wide")

# ── Inicializace výchozích hodnot (pro případ přímého přístupu bez hlavní app) ─
_PASPORT_DEFAULTS: dict = {
    "sys_vyt_zdroje": [
        {"typ": "Kondenzační plynový kotel", "vykon_kw": 0.0,
         "pocet": 1, "rok": 2000, "stav": "Uspokojivý"},
    ],
    "sys_vyt_vetvi": [
        {"typ": "Dvoutrubková", "popis": "", "pocet_ot": 0,
         "trv": True, "rok": 2000, "stav": "Uspokojivý"},
    ],
    "sys_vyt_regulace": [
        {"typ": "Ekvitermní regulace", "rok": 2000, "stav": "Uspokojivý"},
    ],
    "sys_tuv_zdroje": [
        {"typ": "Plynový zásobníkový ohřívač", "objem_l": 0.0,
         "rok": 2000, "stav": "Uspokojivý"},
    ],
    "sys_tuv_rozvody_cirkulace": False,
    "sys_tuv_rozvody_rok": 2000,
    "sys_tuv_rozvody_stav": "Uspokojivý",
    "sys_chl_instalovano": False,
    "sys_chl_jednotky": [],
    "sys_vzt_jednotky": [
        {"nazev": "", "prut_m3h": 0.0, "zzt": False,
         "zzt_ucinnost_pct": 75.0, "rok": 2000, "stav": "Uspokojivý"},
    ],
    "sys_osv_zony": [
        {"nazev": "", "typ": "Lineární fluorescenční (T8/T5)",
         "prikon_kw": 0.0, "pocet": 0, "rok": 2000, "hodiny_rok": 2000,
         "rizeni": "Ruční spínání", "stav": "Uspokojivý"},
    ],
    "sys_sta_rok_vystavby": 1980,
    "sys_sta_zatepleno": False,
    "sys_sta_rok_zatepleni": 2010,
    "sys_sta_stav_steny": "Uspokojivý",
    "sys_sta_stav_strecha": "Uspokojivý",
    "sys_sta_stav_okna": "Uspokojivý",
    "sys_ele_rok_rozvadece": 2000,
    "sys_ele_rok_revize": 2020,
    "sys_ele_mereni_podružne": False,
    "sys_ele_stav_rozvadece": "Uspokojivý",
    "sys_vod_material_sv": "Ocelové",
    "sys_vod_material_tv": "Ocelové",
    "sys_vod_cirkulace_tv": False,
    "sys_vod_rok": 2000,
    "sys_vod_stav": "Uspokojivý",
    "op10_ee_cap_pct": 50.0,
    "ee": 0.0,
    # popisné texty
    "popis_vytapeni": "",
    "popis_tuv": "",
    "popis_chlazeni": "",
    "popis_vzt": "",
    "popis_osvetleni": "",
    "popis_stavba": "",
    "popis_elektro": "",
    "popis_voda_rozv": "",
}
for _k, _v in _PASPORT_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Záhlaví ───────────────────────────────────────────────────────────────────
st.title("📋 Popis stávajícího stavu")
st.caption(
    "Strukturovaný popis technických soustav a stavebního stavu objektu. "
    "Volný text v každé záložce přechází přímo do Word reportu. "
    "Data z Osvětlení se použijí v kalkulaci OP10. "
    "Pasportová data lze načíst z Excel souboru níže."
)
st.page_link("app.py", label="Zpět do hlavní aplikace")
st.divider()

# ── Import z Excelu ───────────────────────────────────────────────────────────
with st.expander("Nahrát pasport z Excelu (.xlsx)", expanded=True):
    _uploaded = st.file_uploader(
        "Vyberte pasportový soubor (šablona DPU Energy)",
        type=["xlsx"],
        key="pasport_upload",
        label_visibility="collapsed",
    )
    if _uploaded is not None:
        _cache_key = f"_pasport_parsed_v2_{_uploaded.name}_{_uploaded.size}"
        if _cache_key not in st.session_state:
            with st.spinner("Načítám pasport…"):
                try:
                    st.session_state[_cache_key] = parse_pasport_xlsx(_uploaded)
                except Exception as _e:
                    st.error(f"Chyba při parsování: {_e}")
                    st.session_state[_cache_key] = None

        _parsed = st.session_state.get(_cache_key)
        if _parsed is not None:
            # Náhled výsledků
            st.success(f"Soubor přečten: **{_uploaded.name}**")
            if _parsed.nazev_objektu:
                st.caption(f"Objekt: {_parsed.nazev_objektu}  |  {_parsed.adresa}")

            if _parsed.warnings:
                for _w in _parsed.warnings:
                    st.warning(_w)

            # Náhled nalezených dat
            import pandas as _pd
            _preview_cols = st.columns(3)
            with _preview_cols[0]:
                if _parsed.vyt_zdroje:
                    st.caption(f"Zdroje tepla: {len(_parsed.vyt_zdroje)}")
                if _parsed.tuv_zdroje:
                    st.caption(f"Zdroje TUV: {len(_parsed.tuv_zdroje)}")
            with _preview_cols[1]:
                if _parsed.vzt_jednotky:
                    st.caption(f"VZT jednotky: {len(_parsed.vzt_jednotky)}")
                if _parsed.chl_instalovano:
                    st.caption("Chlazení: instalováno")
            with _preview_cols[2]:
                if _parsed.osv_zony:
                    st.caption(f"Osvětlovací zóny: {len(_parsed.osv_zony)}")

            if _parsed.osv_zony:
                _df = _pd.DataFrame([{
                    "Zóna": z["nazev"],
                    "Typ": z["typ"],
                    "Příkon [kW]": z["prikon_kw"],
                    "Počet [ks]": z["pocet"],
                    "Hodiny/rok": z["hodiny_rok"],
                } for z in _parsed.osv_zony])
                st.dataframe(_df, use_container_width=True, hide_index=True)

            def _do_import(force: bool) -> None:
                """Zapíše všechna data z PasportData do session_state."""
                ss = st.session_state
                # Identifikace
                if force or not ss.get("objekt_nazev"):
                    if _parsed.nazev_objektu:
                        ss["objekt_nazev"] = _parsed.nazev_objektu
                if force or not ss.get("objekt_adresa"):
                    if _parsed.adresa:
                        ss["objekt_adresa"] = _parsed.adresa
                # Rok výstavby
                if _parsed.rok_vystavby and (force or ss.get("sys_sta_rok_vystavby", 0) == 1980):
                    ss["sys_sta_rok_vystavby"] = _parsed.rok_vystavby
                # Stav obálky
                if force or ss.get("sys_sta_stav_steny") == "Uspokojivý":
                    ss["sys_sta_stav_steny"] = _parsed.stav_steny
                if force or ss.get("sys_sta_stav_okna") == "Uspokojivý":
                    ss["sys_sta_stav_okna"] = _parsed.stav_okna
                if force or ss.get("sys_sta_stav_strecha") == "Uspokojivý":
                    ss["sys_sta_stav_strecha"] = _parsed.stav_strecha
                # Stav TZB
                if force or ss.get("sys_ele_stav_rozvadece") == "Uspokojivý":
                    ss["sys_ele_stav_rozvadece"] = _parsed.stav_elektro
                if force or ss.get("sys_vod_stav") == "Uspokojivý":
                    ss["sys_vod_stav"] = _parsed.stav_voda
                # Vytápění
                if _parsed.vyt_zdroje and (force or ss.get("sys_vyt_zdroje") == _PASPORT_DEFAULTS["sys_vyt_zdroje"]):
                    ss["sys_vyt_zdroje"] = _parsed.vyt_zdroje
                if _parsed.vyt_vetvi and (force or ss.get("sys_vyt_vetvi") == _PASPORT_DEFAULTS["sys_vyt_vetvi"]):
                    ss["sys_vyt_vetvi"] = _parsed.vyt_vetvi
                if _parsed.vyt_regulace and (force or ss.get("sys_vyt_regulace") == _PASPORT_DEFAULTS["sys_vyt_regulace"]):
                    ss["sys_vyt_regulace"] = _parsed.vyt_regulace
                # TUV
                if _parsed.tuv_zdroje and (force or ss.get("sys_tuv_zdroje") == _PASPORT_DEFAULTS["sys_tuv_zdroje"]):
                    ss["sys_tuv_zdroje"] = _parsed.tuv_zdroje
                if force:
                    ss["sys_tuv_rozvody_cirkulace"] = _parsed.tuv_cirkulace
                # Chlazení
                if force or _parsed.chl_instalovano:
                    ss["sys_chl_instalovano"] = _parsed.chl_instalovano
                if _parsed.chl_jednotky and (force or not ss.get("sys_chl_jednotky")):
                    ss["sys_chl_jednotky"] = _parsed.chl_jednotky
                # VZT
                if _parsed.vzt_jednotky and (force or ss.get("sys_vzt_jednotky") == _PASPORT_DEFAULTS["sys_vzt_jednotky"]):
                    ss["sys_vzt_jednotky"] = _parsed.vzt_jednotky
                # Osvětlení
                if _parsed.osv_zony and (force or ss.get("sys_osv_zony") == _PASPORT_DEFAULTS["sys_osv_zony"]):
                    ss["sys_osv_zony"] = _parsed.osv_zony
                # Rozvody vody
                if force or ss.get("sys_vod_material_sv") == "Ocelové":
                    ss["sys_vod_material_sv"] = _parsed.vod_material_sv
                if force or ss.get("sys_vod_material_tv") == "Ocelové":
                    ss["sys_vod_material_tv"] = _parsed.vod_material_tv
                if force:
                    ss["sys_vod_cirkulace_tv"] = _parsed.vod_cirkulace
                # Popisné texty (přepsat jen pokud jsou v pasportu)
                for _field, _key in [
                    ("popis_stavba", "popis_stavba"),
                    ("popis_vytapeni", "popis_vytapeni"),
                    ("popis_tuv", "popis_tuv"),
                    ("popis_chlazeni", "popis_chlazeni"),
                    ("popis_vzt", "popis_vzt"),
                    ("popis_osvetleni", "popis_osvetleni"),
                    ("popis_elektro", "popis_elektro"),
                    ("popis_voda_rozv", "popis_voda_rozv"),
                ]:
                    _val = getattr(_parsed, _field, "")
                    if _val and (force or not ss.get(_key)):
                        ss[_key] = _val

            _col_imp1, _col_imp2, _ = st.columns([2, 2, 3])
            with _col_imp1:
                if st.button("Importovat vše do pasportu", type="primary",
                             key="pasport_import_all"):
                    _do_import(force=False)
                    st.success("Importováno! Stávající data nebyla přepsána.")
                    st.rerun()
            with _col_imp2:
                if st.button("Importovat a přepsat stávající data", type="secondary",
                             key="pasport_import_all_force"):
                    _do_import(force=True)
                    st.success("Přepsáno a importováno.")
                    st.rerun()
            if not _parsed.osv_zony:
                st.info("V souboru nebyla nalezena žádná svítidla.")

st.divider()

# ── Složka s podklady ─────────────────────────────────────────────────────────
if "podklady_extracts" not in st.session_state:
    st.session_state["podklady_extracts"] = {}   # {filename: text}

with st.expander("Složka s podklady projektu", expanded=True):
    _folder_path = st.text_input(
        "Cesta ke složce s podklady",
        key="podklady_folder",
        placeholder=r"C:\Projekty\1031002_Čakovice\Podklady",
    )

    if _folder_path:
        _files = scan_folder(_folder_path)
        if not _files:
            st.warning("Ve složce nebyly nalezeny žádné podporované soubory (PDF, Word, Excel).")
        else:
            st.caption(f"Nalezeno {len(_files)} souborů.")

            # Výběr souborů
            _file_labels = {
                f["rel_path"]: f"{f['name']}  ({f['size_kb']} kB)"
                for f in _files
            }
            _selected_paths = st.multiselect(
                "Vyberte soubory k načtení",
                options=list(_file_labels.keys()),
                format_func=lambda p: _file_labels[p],
                key="podklady_selected",
            )

            # Načíst vybrané soubory
            if _selected_paths:
                _selected_files = [f for f in _files if f["rel_path"] in _selected_paths]
                _scan_files = []

                _col_load, _col_clear = st.columns([2, 1])
                with _col_load:
                    if st.button("Načíst a extrahovat text", key="podklady_load", type="primary"):
                        _extracts = dict(st.session_state.get("podklady_extracts", {}))
                        _progress = st.progress(0)
                        for _idx, _fi in enumerate(_selected_files):
                            _progress.progress((_idx + 1) / len(_selected_files), text=f"Čtu: {_fi['name']}")
                            if _fi["name"] not in _extracts:
                                _text, _is_scan = extract_text(_fi)
                                if _is_scan:
                                    _scan_files.append(_fi)
                                elif _text:
                                    _extracts[_fi["name"]] = _text
                                else:
                                    _extracts[_fi["name"]] = "(Nepodařilo se extrahovat text)"
                        _progress.empty()
                        st.session_state["podklady_extracts"] = _extracts
                        if _scan_files:
                            st.session_state["podklady_scan_pending"] = _scan_files
                        st.rerun()
                with _col_clear:
                    if st.button("Vymazat vše", key="podklady_clear"):
                        st.session_state["podklady_extracts"] = {}
                        st.session_state.pop("podklady_scan_pending", None)
                        st.rerun()

            # Zobrazit načtené soubory + skenované čekající na OCR
            _extracts = st.session_state.get("podklady_extracts", {})
            _scan_pending = st.session_state.get("podklady_scan_pending", [])

            if _scan_pending and ma_api_klic():
                st.warning(
                    f"{len(_scan_pending)} soubor(ů) je pravděpodobně skenované PDF bez textu. "
                    "Lze je extrahovat přes Claude vision (každá stránka = 1 AI volání)."
                )
                if st.button("Extrahovat skenovaná PDF pomocí AI", key="podklady_ocr"):
                    _extracts = dict(_extracts)
                    _progress = st.progress(0)
                    for _idx, _fi in enumerate(_scan_pending):
                        _progress.progress((_idx + 1) / len(_scan_pending), text=f"OCR: {_fi['name']}")
                        try:
                            from epc_engine.ai_popis import _api_key
                            _text = extract_text_scan(_fi, _api_key())
                            _extracts[_fi["name"]] = _text
                        except Exception as _e:
                            _extracts[_fi["name"]] = f"(Chyba OCR: {_e})"
                    _progress.empty()
                    st.session_state["podklady_extracts"] = _extracts
                    st.session_state.pop("podklady_scan_pending", None)
                    st.rerun()

            if _extracts:
                st.markdown(f"**Načteno {len(_extracts)} souborů** — použijí se při generování popisů (AI).")
                for _fname, _txt in _extracts.items():
                    with st.expander(f"Náhled: {_fname}", expanded=False):
                        st.text(_txt[:800] + ("…" if len(_txt) > 800 else ""))

st.divider()

# ── Pomocné ───────────────────────────────────────────────────────────────────
_STAV = ["Dobrý", "Uspokojivý", "Vyžaduje rekonstrukci", "Není instalováno"]

def _stav_sel(label: str, key: str):
    idx = _STAV.index(st.session_state.get(key, "Uspokojivý"))
    st.selectbox(label, _STAV, index=idx, key=key)


def _ai_btn(sekce: str) -> None:
    """Tlačítko pro AI generování popisu. Výsledek vloží do session_state[sekce]."""
    _c1, _c2 = st.columns([2, 5])
    with _c1:
        if st.button("Generovat popis (AI)", key=f"_ai_{sekce}", use_container_width=True):
            if not ma_api_klic():
                st.warning(
                    "API klíč Anthropic není nastaven. "
                    "Doplň `ANTHROPIC_API_KEY` do souboru `.streamlit/secrets.toml`."
                )
            else:
                with st.spinner("Generuji…"):
                    try:
                        _podklady = sestavit_kontext(
                            st.session_state.get("podklady_extracts", {})
                        )
                        st.session_state[sekce] = generuj_popis(
                            sekce, dict(st.session_state), podklady=_podklady
                        )
                        st.rerun()
                    except Exception as _e:
                        st.error(str(_e))

# ── Záložky ───────────────────────────────────────────────────────────────────
(
    _pt_vyt, _pt_tuv, _pt_chl, _pt_vzt,
    _pt_osv, _pt_sta, _pt_ele, _pt_vod,
) = st.tabs([
    "Vytápění", "TUV", "Chlazení", "VZT",
    "Osvětlení", "Stavba", "Elektroinstalace", "Rozvody vody",
])


# ── TAB: Vytápění ─────────────────────────────────────────────────────────────
with _pt_vyt:
    st.markdown("**Zdroje tepla**")
    _VYT_TYPY = [
        "Plynový kotel", "Kondenzační plynový kotel",
        "Tepelné čerpadlo vzduch/voda", "Tepelné čerpadlo země/voda",
        "CZT / horkovod", "Elektrický kotel",
        "Kotel na tuhá paliva", "Jiný",
    ]
    _vyt_zdroje = list(st.session_state.get("sys_vyt_zdroje", []))
    _vyt_updated = []
    for _i, _z in enumerate(_vyt_zdroje):
        _c1, _c2, _c3, _c4, _c5, _crm = st.columns([2, 1, 1, 1, 1, 0.3])
        _lv = "visible" if _i == 0 else "hidden"
        with _c1:
            _typ = st.selectbox("Typ" if _i == 0 else " ", _VYT_TYPY,
                index=_VYT_TYPY.index(_z.get("typ", _VYT_TYPY[0])),
                key=f"vyt_zdroj_{_i}_typ", label_visibility=_lv)
        with _c2:
            _vyk = st.number_input("Výkon [kW]" if _i == 0 else " ",
                min_value=0.0, step=10.0,
                value=float(_z.get("vykon_kw", 0.0)),
                key=f"vyt_zdroj_{_i}_vykon", label_visibility=_lv)
        with _c3:
            _poc = st.number_input("Počet [ks]" if _i == 0 else " ",
                min_value=1, step=1, value=int(_z.get("pocet", 1)),
                key=f"vyt_zdroj_{_i}_pocet", label_visibility=_lv)
        with _c4:
            _rok = st.number_input("Rok" if _i == 0 else " ",
                min_value=1900, max_value=2035, step=1,
                value=int(_z.get("rok", 2000)),
                key=f"vyt_zdroj_{_i}_rok", label_visibility=_lv)
        with _c5:
            _stv = st.selectbox("Stav" if _i == 0 else " ", _STAV,
                index=_STAV.index(_z.get("stav", "Uspokojivý")),
                key=f"vyt_zdroj_{_i}_stav", label_visibility=_lv)
        with _crm:
            st.markdown("&nbsp;" if _i == 0 else "")
            _rm = st.button("✕", key=f"vyt_zdroj_{_i}_rm")
        if not _rm:
            _vyt_updated.append({"typ": _typ, "vykon_kw": _vyk,
                                 "pocet": _poc, "rok": _rok, "stav": _stv})
    if st.button("+ Přidat zdroj tepla", key="vyt_zdroj_add"):
        _vyt_updated.append({"typ": _VYT_TYPY[0], "vykon_kw": 0.0,
                              "pocet": 1, "rok": 2000, "stav": "Uspokojivý"})
    st.session_state["sys_vyt_zdroje"] = _vyt_updated

    st.markdown("**Větve otopné soustavy**")
    _VYT_SOUSTAVA_TYPY = [
        "Dvoutrubková", "Jednotrubková", "Podlahové vytápění", "Mix",
    ]
    _vetvi = list(st.session_state.get("sys_vyt_vetvi", []))
    _vetvi_upd = []
    for _i, _v in enumerate(_vetvi):
        _c1, _c2, _c3, _c4, _c5, _c6, _crm = st.columns([1.5, 1.5, 1, 1, 1, 1, 0.3])
        _lv = "visible" if _i == 0 else "hidden"
        with _c1:
            _typ = st.selectbox("Typ soustavy" if _i == 0 else " ", _VYT_SOUSTAVA_TYPY,
                index=_VYT_SOUSTAVA_TYPY.index(_v.get("typ", _VYT_SOUSTAVA_TYPY[0])),
                key=f"vyt_vetev_{_i}_typ", label_visibility=_lv)
        with _c2:
            _pop = st.text_input("Větev / popis" if _i == 0 else " ",
                value=_v.get("popis", ""), key=f"vyt_vetev_{_i}_popis",
                placeholder="např. Jih, Sever, Tělocvična", label_visibility=_lv)
        with _c3:
            _pot = st.number_input("Počet OT" if _i == 0 else " ",
                min_value=0, step=10, value=int(_v.get("pocet_ot", 0)),
                key=f"vyt_vetev_{_i}_ot", label_visibility=_lv)
        with _c4:
            _trv = st.checkbox("TRV" if _i == 0 else " ",
                value=bool(_v.get("trv", True)),
                key=f"vyt_vetev_{_i}_trv", label_visibility=_lv)
        with _c5:
            _rok = st.number_input("Rok" if _i == 0 else " ",
                min_value=1900, max_value=2035, step=1,
                value=int(_v.get("rok", 2000)),
                key=f"vyt_vetev_{_i}_rok", label_visibility=_lv)
        with _c6:
            _stv = st.selectbox("Stav" if _i == 0 else " ", _STAV,
                index=_STAV.index(_v.get("stav", "Uspokojivý")),
                key=f"vyt_vetev_{_i}_stav", label_visibility=_lv)
        with _crm:
            st.markdown("&nbsp;" if _i == 0 else "")
            _rm = st.button("✕", key=f"vyt_vetev_{_i}_rm")
        if not _rm:
            _vetvi_upd.append({"typ": _typ, "popis": _pop, "pocet_ot": _pot,
                               "trv": _trv, "rok": _rok, "stav": _stv})
    if st.button("+ Přidat větev", key="vyt_vetev_add"):
        _vetvi_upd.append({"typ": _VYT_SOUSTAVA_TYPY[0], "popis": "",
                            "pocet_ot": 0, "trv": True, "rok": 2000, "stav": "Uspokojivý"})
    st.session_state["sys_vyt_vetvi"] = _vetvi_upd

    st.markdown("**Regulace**")
    _REG_TYPY = [
        "Ekvitermní regulace", "Ekvitermní + TRV",
        "Ekvitermní + TRV + individuální regulace (IRC)",
        "Prostorový termostat", "Zónová regulace",
        "BMS / nadřazená regulace", "Bez regulace",
    ]
    _regulace = list(st.session_state.get("sys_vyt_regulace", []))
    _reg_upd = []
    for _i, _r in enumerate(_regulace):
        _lv = "visible" if _i == 0 else "hidden"
        _c1, _c2, _c3, _crm = st.columns([2, 1, 1, 0.3])
        with _c1:
            _rtyp_val = _r.get("typ", _REG_TYPY[0])
            _rtyp_idx = _REG_TYPY.index(_rtyp_val) if _rtyp_val in _REG_TYPY else 0
            _typ = st.selectbox("Typ" if _i == 0 else " ", _REG_TYPY,
                index=_rtyp_idx,
                key=f"vyt_reg_{_i}_typ", label_visibility=_lv)
        with _c2:
            _rok = st.number_input("Rok" if _i == 0 else " ",
                min_value=1900, max_value=2035, step=1,
                value=int(_r.get("rok", 2000)),
                key=f"vyt_reg_{_i}_rok", label_visibility=_lv)
        with _c3:
            _stv = st.selectbox("Stav" if _i == 0 else " ", _STAV,
                index=_STAV.index(_r.get("stav", "Uspokojivý")),
                key=f"vyt_reg_{_i}_stav", label_visibility=_lv)
        with _crm:
            st.markdown("&nbsp;" if _i == 0 else "")
            _rm = st.button("✕", key=f"vyt_reg_{_i}_rm")
        if not _rm:
            _reg_upd.append({"typ": _typ, "rok": _rok, "stav": _stv})
    if st.button("+ Přidat regulaci", key="vyt_reg_add"):
        _reg_upd.append({"typ": _REG_TYPY[0], "rok": 2000, "stav": "Uspokojivý"})
    st.session_state["sys_vyt_regulace"] = _reg_upd

    _ai_btn("popis_vytapeni")
    st.text_area("Popis vytápění pro report", key="popis_vytapeni", height=320,
        placeholder=(
            "Popište celkový stav vytápění, hlavní nedostatky a potenciál pro EPC.\n"
            "Text přejde přímo do Word reportu."
        ),
    )


# ── TAB: TUV ──────────────────────────────────────────────────────────────────
with _pt_tuv:
    st.markdown("**Zdroje ohřevu TUV**")
    _TUV_TYPY = [
        "Plynový zásobníkový ohřívač", "Elektrický bojler",
        "Ohřev z CZT", "Tepelné čerpadlo (vzduch/voda)",
        "Průtokový ohřívač", "Jiný",
    ]
    _tuv_zdroje = list(st.session_state.get("sys_tuv_zdroje", []))
    _tuv_updated = []
    for _i, _z in enumerate(_tuv_zdroje):
        _c1, _c2, _c3, _c4, _crm = st.columns([2, 1, 1, 1, 0.3])
        _lv = "visible" if _i == 0 else "hidden"
        with _c1:
            _typ = st.selectbox("Typ" if _i == 0 else " ", _TUV_TYPY,
                index=_TUV_TYPY.index(_z.get("typ", _TUV_TYPY[0])),
                key=f"tuv_zdroj_{_i}_typ", label_visibility=_lv)
        with _c2:
            _obj = st.number_input("Objem zásobníku [l]" if _i == 0 else " ",
                min_value=0.0, step=50.0,
                value=float(_z.get("objem_l", 0.0)),
                key=f"tuv_zdroj_{_i}_objem", label_visibility=_lv,
                help="0 = průtokový ohřívač")
        with _c3:
            _rok = st.number_input("Rok" if _i == 0 else " ",
                min_value=1900, max_value=2035, step=1,
                value=int(_z.get("rok", 2000)),
                key=f"tuv_zdroj_{_i}_rok", label_visibility=_lv)
        with _c4:
            _stv = st.selectbox("Stav" if _i == 0 else " ", _STAV,
                index=_STAV.index(_z.get("stav", "Uspokojivý")),
                key=f"tuv_zdroj_{_i}_stav", label_visibility=_lv)
        with _crm:
            st.markdown("&nbsp;" if _i == 0 else "")
            _rm = st.button("✕", key=f"tuv_zdroj_{_i}_rm")
        if not _rm:
            _tuv_updated.append({"typ": _typ, "objem_l": _obj,
                                 "rok": _rok, "stav": _stv})
    if st.button("+ Přidat zdroj TUV", key="tuv_zdroj_add"):
        _tuv_updated.append({"typ": _TUV_TYPY[0], "objem_l": 0.0,
                              "rok": 2000, "stav": "Uspokojivý"})
    st.session_state["sys_tuv_zdroje"] = _tuv_updated

    st.markdown("**Rozvody TUV**")
    _c1, _c2, _c3 = st.columns([1, 1, 1])
    with _c1:
        st.checkbox("Cirkulace TUV", key="sys_tuv_rozvody_cirkulace")
    with _c2:
        st.number_input("Rok instalace rozvodů", min_value=1900, max_value=2035,
                        step=1, key="sys_tuv_rozvody_rok")
    with _c3:
        _stav_sel("Stav rozvodů", "sys_tuv_rozvody_stav")

    _ai_btn("popis_tuv")
    st.text_area("Popis TUV pro report", key="popis_tuv", height=320,
        placeholder="Popište způsob přípravy TUV, zásobníky, cirkulaci a hlavní nedostatky.")


# ── TAB: Chlazení ─────────────────────────────────────────────────────────────
with _pt_chl:
    _instalovano = st.checkbox("Chlazení je v objektu instalováno",
                               key="sys_chl_instalovano")
    _CHL_TYPY = [
        "Klimatizace split / multi-split", "VRF systém",
        "Chiller + fancoily", "Adiabatické chlazení", "Jiný",
    ]
    if _instalovano:
        _chl_jed = list(st.session_state.get("sys_chl_jednotky", []))
        _chl_upd = []
        for _i, _j in enumerate(_chl_jed):
            _lv = "visible" if _i == 0 else "hidden"
            _c1, _c2, _c3, _c4, _crm = st.columns([2, 1, 1, 1, 0.3])
            with _c1:
                _typ = st.selectbox("Typ" if _i == 0 else " ", _CHL_TYPY,
                    index=_CHL_TYPY.index(_j.get("typ", _CHL_TYPY[0])),
                    key=f"chl_{_i}_typ", label_visibility=_lv)
            with _c2:
                _vyk = st.number_input("Výkon [kW]" if _i == 0 else " ",
                    min_value=0.0, step=5.0,
                    value=float(_j.get("vykon_kw", 0.0)),
                    key=f"chl_{_i}_vykon", label_visibility=_lv)
            with _c3:
                _rok = st.number_input("Rok" if _i == 0 else " ",
                    min_value=1900, max_value=2035, step=1,
                    value=int(_j.get("rok", 2010)),
                    key=f"chl_{_i}_rok", label_visibility=_lv)
            with _c4:
                _stv = st.selectbox("Stav" if _i == 0 else " ", _STAV,
                    index=_STAV.index(_j.get("stav", "Uspokojivý")),
                    key=f"chl_{_i}_stav", label_visibility=_lv)
            with _crm:
                st.markdown("&nbsp;" if _i == 0 else "")
                _rm = st.button("✕", key=f"chl_{_i}_rm")
            if not _rm:
                _chl_upd.append({"typ": _typ, "vykon_kw": _vyk,
                                 "rok": _rok, "stav": _stv})
        if st.button("+ Přidat chladicí jednotku", key="chl_add"):
            _chl_upd.append({"typ": _CHL_TYPY[0], "vykon_kw": 0.0,
                              "rok": 2010, "stav": "Uspokojivý"})
        st.session_state["sys_chl_jednotky"] = _chl_upd
    _ai_btn("popis_chlazeni")
    st.text_area("Popis chlazení pro report", key="popis_chlazeni", height=320,
        placeholder=(
            "Popište zdroje chladu, chlazené prostory a hlavní nedostatky.\n"
            "Pokud není instalováno: Objekt není vybaven chladicím systémem."
        ),
    )


# ── TAB: VZT ──────────────────────────────────────────────────────────────────
with _pt_vzt:
    st.markdown("**VZT jednotky**")
    _vzt_jednotky = list(st.session_state.get("sys_vzt_jednotky", []))
    _vzt_updated = []
    for _i, _j in enumerate(_vzt_jednotky):
        _c1, _c2, _c3, _c4, _c5, _crm = st.columns([2, 1, 1, 1, 1, 0.3])
        _lv = "visible" if _i == 0 else "hidden"
        with _c1:
            _naz = st.text_input("Název / umístění" if _i == 0 else " ",
                value=_j.get("nazev", ""), key=f"vzt_j_{_i}_nazev",
                placeholder="např. VZT kuchyně, Třídní větrání...",
                label_visibility=_lv)
        with _c2:
            _prt = st.number_input("Průtok [m³/h]" if _i == 0 else " ",
                min_value=0.0, step=500.0,
                value=float(_j.get("prut_m3h", 0.0)),
                key=f"vzt_j_{_i}_prut", label_visibility=_lv)
        with _c3:
            _rok = st.number_input("Rok" if _i == 0 else " ",
                min_value=1900, max_value=2035, step=1,
                value=int(_j.get("rok", 2000)),
                key=f"vzt_j_{_i}_rok", label_visibility=_lv)
        with _c4:
            _zzt = st.checkbox("ZZT" if _i == 0 else " ",
                value=bool(_j.get("zzt", False)),
                key=f"vzt_j_{_i}_zzt", label_visibility=_lv)
            if _zzt:
                _zzt_uc = st.number_input("Účinnost [%]",
                    min_value=0.0, max_value=100.0, step=5.0,
                    value=float(_j.get("zzt_ucinnost_pct", 75.0)),
                    key=f"vzt_j_{_i}_zzt_uc")
            else:
                _zzt_uc = 0.0
        with _c5:
            _stv = st.selectbox("Stav" if _i == 0 else " ", _STAV,
                index=_STAV.index(_j.get("stav", "Uspokojivý")),
                key=f"vzt_j_{_i}_stav", label_visibility=_lv)
        with _crm:
            st.markdown("&nbsp;" if _i == 0 else "")
            _rm = st.button("✕", key=f"vzt_j_{_i}_rm")
        if not _rm:
            _vzt_updated.append({"nazev": _naz, "prut_m3h": _prt,
                                 "rok": _rok, "zzt": _zzt,
                                 "zzt_ucinnost_pct": _zzt_uc, "stav": _stv})
    if st.button("+ Přidat VZT jednotku", key="vzt_add"):
        _vzt_updated.append({"nazev": "", "prut_m3h": 0.0, "rok": 2000,
                              "zzt": False, "zzt_ucinnost_pct": 75.0, "stav": "Uspokojivý"})
    st.session_state["sys_vzt_jednotky"] = _vzt_updated

    _ai_btn("popis_vzt")
    st.text_area("Popis VZT pro report", key="popis_vzt", height=320,
        placeholder="Popište větrací systémy, průtoky vzduchu, rekuperaci, stáří zařízení a hlavní nedostatky.")


# ── TAB: Osvětlení ────────────────────────────────────────────────────────────
with _pt_osv:
    st.markdown("**Zóny osvětlení**")
    _OSV_TYPY = [
        "LED", "Lineární fluorescenční (T8/T5)",
        "Kompaktní fluorescenční (CFL)", "Halogenové / výbojkové",
        "Mix (LED + fluorescenční)", "Jiný",
    ]
    _OSV_RIZENI = [
        "Ruční spínání", "Časové spínání",
        "Přítomnostní čidla (PIR)", "Čidla denního světla",
        "Kombinace PIR + denní světlo", "BMS",
    ]
    _OSV_HOD_REF = {
        "— vyberte typ provozu —": None,
        "Třídy / učebny (1 800 h/rok)": 1_800,
        "Kanceláře / administrativa (2 500 h/rok)": 2_500,
        "Chodby / schodiště (3 500 h/rok)": 3_500,
        "Tělocvična / sportovní hala (1 500 h/rok)": 1_500,
        "Hygienické zázemí, WC (2 000 h/rok)": 2_000,
        "Sklady / technické místnosti (1 000 h/rok)": 1_000,
        "Výrobní / průmyslové prostory (4 000 h/rok)": 4_000,
        "Restaurace / společenské prostory (2 500 h/rok)": 2_500,
        "Venkovní osvětlení / parkoviště (4 000 h/rok)": 4_000,
    }

    _hod_preset_col, _ = st.columns([2, 3])
    with _hod_preset_col:
        _hod_preset_sel = st.selectbox(
            "Rychlá předvolba hodin provozu (vyplní všechny zóny)",
            list(_OSV_HOD_REF.keys()), index=0, key="osv_hod_preset",
        )
    _hod_preset_val = _OSV_HOD_REF[_hod_preset_sel]

    _osv_zony = list(st.session_state.get("sys_osv_zony", []))
    _osv_upd = []
    for _i, _z in enumerate(_osv_zony):
        _lv = "visible" if _i == 0 else "hidden"
        _c1, _c2, _c3, _c4, _c5, _c6, _c7, _c8, _crm = st.columns(
            [1.4, 1.4, 0.8, 0.7, 0.7, 1.0, 1.3, 0.9, 0.3])
        with _c1:
            _naz = st.text_input("Zóna / prostor" if _i == 0 else " ",
                value=_z.get("nazev", ""), key=f"osv_{_i}_nazev",
                placeholder="Třídy, Chodby…", label_visibility=_lv)
        with _c2:
            _typ = st.selectbox("Typ svítidel" if _i == 0 else " ", _OSV_TYPY,
                index=_OSV_TYPY.index(_z.get("typ", _OSV_TYPY[0])),
                key=f"osv_{_i}_typ", label_visibility=_lv)
        with _c3:
            _prk = st.number_input("Příkon [kW]" if _i == 0 else " ",
                min_value=0.0, step=0.5,
                value=float(_z.get("prikon_kw", 0.0)),
                key=f"osv_{_i}_prikon", label_visibility=_lv)
        with _c4:
            _poc = st.number_input("Počet [ks]" if _i == 0 else " ",
                min_value=0, step=10, value=int(_z.get("pocet", 0)),
                key=f"osv_{_i}_pocet", label_visibility=_lv)
        with _c5:
            _rok = st.number_input("Rok" if _i == 0 else " ",
                min_value=1900, max_value=2035, step=1,
                value=int(_z.get("rok", 2000)),
                key=f"osv_{_i}_rok", label_visibility=_lv)
        with _c6:
            _hod_default = _hod_preset_val if _hod_preset_val else int(_z.get("hodiny_rok", 2000))
            _hod = st.number_input(
                "Hodiny/rok" if _i == 0 else " ",
                min_value=0, max_value=8760, step=100,
                value=_hod_default,
                key=f"osv_{_i}_hod",
                help=(
                    "Referenční hodnoty:\n"
                    "Třídy 1 800 · Kanceláře 2 500 · Chodby 3 500 · "
                    "Tělocvična 1 500 · WC 2 000 · Sklady 1 000 · Výroba 4 000"
                ),
                label_visibility=_lv,
            )
        with _c7:
            _riz = st.selectbox("Řízení" if _i == 0 else " ", _OSV_RIZENI,
                index=_OSV_RIZENI.index(_z.get("rizeni", _OSV_RIZENI[0])),
                key=f"osv_{_i}_rizeni", label_visibility=_lv)
        with _c8:
            _stv = st.selectbox("Stav" if _i == 0 else " ", _STAV,
                index=_STAV.index(_z.get("stav", "Uspokojivý")),
                key=f"osv_{_i}_stav", label_visibility=_lv)
        with _crm:
            st.markdown("&nbsp;" if _i == 0 else "")
            _rm = st.button("✕", key=f"osv_{_i}_rm")
        if not _rm:
            _osv_upd.append({"nazev": _naz, "typ": _typ, "prikon_kw": _prk,
                              "pocet": _poc, "rok": _rok, "hodiny_rok": _hod,
                              "rizeni": _riz, "stav": _stv})
    if st.button("+ Přidat zónu osvětlení", key="osv_add"):
        _osv_upd.append({"nazev": "", "typ": _OSV_TYPY[0], "prikon_kw": 0.0,
                          "pocet": 0, "rok": 2000, "hodiny_rok": 2000,
                          "rizeni": _OSV_RIZENI[0], "stav": "Uspokojivý"})
    st.session_state["sys_osv_zony"] = _osv_upd

    # ── Souhrn EE osvětlení ───────────────────────────────────────────────────
    _osv_total_mwh = sum(
        z.get("prikon_kw", 0) * z.get("hodiny_rok", 0) / 1000
        for z in _osv_upd
    )
    _ee_total = st.session_state.get("ee", 0.0)
    if _osv_total_mwh > 0:
        _osv_pct = (_osv_total_mwh / _ee_total * 100) if _ee_total > 0 else None
        _osv_cap = st.session_state.get("op10_ee_cap_pct", 50.0)
        _cols_osv = st.columns(3)
        _cols_osv[0].metric("Odhadovaná spotřeba EE – osvětlení", f"{_osv_total_mwh:.1f} MWh/rok")
        if _osv_pct is not None:
            _cols_osv[1].metric("Podíl z celkové EE", f"{_osv_pct:.0f} %")
            if _osv_pct > _osv_cap:
                st.warning(
                    f"Odhadovaná spotřeba osvětlení ({_osv_pct:.0f} %) překračuje "
                    f"nastavenou hranici {_osv_cap:.0f} % z celkové EE. "
                    "Zkontrolujte příkony nebo hodiny provozu."
                )
        else:
            _cols_osv[1].metric("Podíl z celkové EE", "–",
                help="Zadejte celkovou spotřebu EE v záložce Vstupní data.")

    _ai_btn("popis_osvetleni")
    st.text_area("Popis osvětlení pro report", key="popis_osvetleni", height=320,
        placeholder="Popište typ svítidel, příkony, řízení a rozsah plánované rekonstrukce.")


# ── TAB: Stavba ───────────────────────────────────────────────────────────────
with _pt_sta:
    st.caption("U-hodnoty konstrukcí zadávejte ve Fyzikálním kalkulátoru.")
    _c1, _c2, _c3 = st.columns(3)
    with _c1:
        st.number_input("Rok výstavby", min_value=1800, max_value=2035,
                        step=1, key="sys_sta_rok_vystavby")
    with _c2:
        st.checkbox("Objekt byl zateplen", key="sys_sta_zatepleno")
    with _c3:
        if st.session_state.get("sys_sta_zatepleno"):
            st.number_input("Rok zateplení", min_value=1900, max_value=2035,
                            step=1, key="sys_sta_rok_zatepleni")

    st.markdown("**Stav konstrukcí obálky**")
    _c1, _c2, _c3 = st.columns(3)
    with _c1:
        _stav_sel("Obvodové stěny", "sys_sta_stav_steny")
    with _c2:
        _stav_sel("Střecha / strop", "sys_sta_stav_strecha")
    with _c3:
        _stav_sel("Okna a dveře", "sys_sta_stav_okna")

    _ai_btn("popis_stavba")
    st.text_area("Popis stavby pro report", key="popis_stavba", height=320,
        placeholder=(
            "Popište stav obvodových stěn, střechy, oken a podlah. "
            "Uveďte provedené rekonstrukce a hlavní nedostatky obálky budovy."
        ),
    )


# ── TAB: Elektroinstalace ─────────────────────────────────────────────────────
with _pt_ele:
    st.markdown("**Rozvaděče a silové rozvody**")
    _c1, _c2, _c3, _c4 = st.columns([1, 1, 1, 1])
    with _c1:
        st.number_input("Rok instalace rozvaděčů", min_value=1900, max_value=2035,
                        step=1, key="sys_ele_rok_rozvadece")
    with _c2:
        st.number_input("Rok poslední revize", min_value=1900, max_value=2035,
                        step=1, key="sys_ele_rok_revize")
    with _c3:
        st.checkbox("Podružné měření odběrů", key="sys_ele_mereni_podružne")
    with _c4:
        _stav_sel("Stav rozvaděčů", "sys_ele_stav_rozvadece")

    _ai_btn("popis_elektro")
    st.text_area("Popis elektroinstalace pro report", key="popis_elektro", height=320,
        placeholder=(
            "Popište stav rozvaděčů, silových rozvodů a jistících prvků. "
            "Uveďte rok poslední revize, podružné měření a hlavní nedostatky."
        ),
    )


# ── TAB: Rozvody vody ─────────────────────────────────────────────────────────
with _pt_vod:
    st.markdown("**Potrubí studené a teplé vody**")
    _c1, _c2, _c3, _c4, _c5 = st.columns([1, 1, 1, 1, 1])
    with _c1:
        st.selectbox("Materiál SV", [
            "Ocelové", "Měděné", "Plastové (PE/PPR)", "Pozinkované", "Mix",
        ], key="sys_vod_material_sv")
    with _c2:
        st.selectbox("Materiál TV/cirkulace", [
            "Ocelové", "Měděné", "Plastové (PE/PPR)", "Pozinkované", "Mix",
        ], key="sys_vod_material_tv")
    with _c3:
        st.checkbox("Cirkulace TV", key="sys_vod_cirkulace_tv")
    with _c4:
        st.number_input("Rok instalace", min_value=1900, max_value=2035,
                        step=1, key="sys_vod_rok")
    with _c5:
        _stav_sel("Stav", "sys_vod_stav")

    _ai_btn("popis_voda_rozv")
    st.text_area("Popis rozvodů vody pro report", key="popis_voda_rozv", height=320,
        placeholder=(
            "Popište materiál a stav potrubí SV, TV a cirkulace, "
            "armatury, vodoměry a případné úniky."
        ),
    )
