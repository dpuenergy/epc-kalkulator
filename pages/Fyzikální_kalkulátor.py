"""
Fyzikální kalkulátor – pomocný nástroj pro výpočet úspor stavebních opatření.

Sdílí session_state s hlavní aplikací (theta_i, theta_e, phi_total_kw, lokalita_projekt).
Výsledky lze přenést do příslušného opatření kliknutím na tlačítko.
"""

import io
import streamlit as st
from epc_engine.physics import (
    nazvy_materialu, lambda_materialu,
    typy_konstrukci, u_hodnoty_konstrukce,
    nazvy_lokalit, lokalita,
    Vrstva, Konstrukce,
    vypocet_vytapeni, vypocet_tuv, druhy_budov,
    vypocet_vetrani,
)
from epc_engine.physics.heat_demand import vw_faktor

st.set_page_config(page_title="Fyzikální kalkulátor", page_icon="🔬", layout="wide")

# ── Inicializace sdílených klíčů (pokud přichází přímo, ne přes hlavní app) ──
for _k, _v in [
    ("theta_i", 21.0), ("theta_e", -13.0),
    ("phi_total_kw", 0.0), ("lokalita_projekt", "Praha (Karlov)"),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Inicializace OP phi_kw klíčů ─────────────────────────────────────────────
for _op in ["op1a", "op1b", "op2", "op3", "op4", "op5", "op6"]:
    if f"{_op}_phi_kw" not in st.session_state:
        st.session_state[f"{_op}_phi_kw"] = 0.0

# ── Banner okrajových podmínek ────────────────────────────────────────────────
st.title("🔬 Fyzikální kalkulátor")

_ti = st.session_state["theta_i"]
_te = st.session_state["theta_e"]
_phi = st.session_state["phi_total_kw"]
_lok_nazev = st.session_state["lokalita_projekt"]

with st.container(border=True):
    _bc1, _bc2, _bc3, _bc4, _bc5 = st.columns(5)
    _bc1.metric("θi", f"{_ti:.0f} °C", help="Vnitřní výpočtová teplota (nastavit v hlavní app → sidebar)")
    _bc2.metric("θe", f"{_te:.0f} °C", help="Venkovní výpočtová teplota")
    _bc3.metric("ΔT", f"{_ti - _te:.0f} K")
    _bc4.metric("Lokalita", _lok_nazev.split(" (")[0])
    if _phi > 0:
        _bc5.metric("Φ celkem", f"{_phi:.0f} kW", help="Celková tepelná ztráta objektu")
    else:
        _bc5.metric("Φ celkem", "–", help="Zadejte v záložce Potřeba tepla – vytápění pro aktivaci korekce")

st.caption("θi, θe a lokalita se nastavují v **hlavní aplikaci** (sidebar). Φ celkem se zadává v záložce Potřeba tepla – vytápění níže.")
st.divider()

# ── Záložky kalkulátoru ───────────────────────────────────────────────────────
tab_u, tab_teplo, tab_tuv, tab_vetrani, tab_import = st.tabs([
    "Součinitel prostupu tepla U",
    "Potřeba tepla – vytápění",
    "Potřeba tepla – TUV",
    "Větrání a ZZT",
    "Import z PDF",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – VÝPOČET U-HODNOTY + TLOUŠŤKA IZOLANTU + KOREKCE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_u:
    st.subheader("Výpočet U-hodnoty a tloušťky zateplení")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        materialy_list = nazvy_materialu()
        konstrukce_nazev = st.text_input("Název konstrukce", value="Obvodová stěna", key="u_nazev")
        plocha = st.number_input("Plocha konstrukce [m²]", min_value=0.0, value=100.0, step=10.0, key="u_plocha")

        st.markdown("**Vrstvy stávající konstrukce** (od interiéru k exteriéru)")

        if "u_vrstvy" not in st.session_state:
            st.session_state.u_vrstvy = [
                {"mat": "Omítka vápenná", "d": 0.02, "lambda_manual": None},
                {"mat": "Zdivo-CP (1700 kg/m³)", "d": 0.45, "lambda_manual": None},
                {"mat": "Omítka vápenná", "d": 0.02, "lambda_manual": None},
            ]

        for i, vrstva in enumerate(st.session_state.u_vrstvy):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 0.4])
            with c1:
                mat = st.selectbox(
                    f"Materiál #{i+1}",
                    options=["(zadat λ ručně)"] + materialy_list,
                    index=(materialy_list.index(vrstva["mat"]) + 1)
                          if vrstva["mat"] in materialy_list else 0,
                    key=f"u_mat_{i}", label_visibility="collapsed",
                )
                st.session_state.u_vrstvy[i]["mat"] = mat if mat != "(zadat λ ručně)" else vrstva["mat"]
            with c2:
                d = st.number_input(
                    "d [m]", min_value=0.001, max_value=2.0,
                    value=float(vrstva["d"]), step=0.01, format="%.3f",
                    key=f"u_d_{i}", label_visibility="collapsed",
                )
                st.session_state.u_vrstvy[i]["d"] = d
            with c3:
                if mat == "(zadat λ ručně)":
                    lam_val = st.number_input(
                        "λ [W/mK]", min_value=0.001, max_value=500.0,
                        value=float(vrstva.get("lambda_manual") or 0.5),
                        step=0.01, format="%.3f",
                        key=f"u_lam_{i}", label_visibility="collapsed",
                    )
                    st.session_state.u_vrstvy[i]["lambda_manual"] = lam_val
                else:
                    try:
                        lam_val = lambda_materialu(mat)
                    except Exception:
                        lam_val = 1.0
                    st.number_input(
                        "λ [W/mK]", value=lam_val, disabled=True,
                        key=f"u_lam_auto_{i}", label_visibility="collapsed",
                    )
                    st.session_state.u_vrstvy[i]["lambda_manual"] = None
            with c4:
                if st.button("✕", key=f"u_del_{i}", help="Odebrat vrstvu") and len(st.session_state.u_vrstvy) > 1:
                    st.session_state.u_vrstvy.pop(i)
                    st.rerun()

        if st.button("+ Přidat vrstvu", key="u_add"):
            st.session_state.u_vrstvy.append({"mat": "Omítka vápenná", "d": 0.02, "lambda_manual": None})
            st.rerun()

    with col_right:
        st.markdown("**Referenční U-hodnoty (ČSN 73 0540-2)**")
        typ_k = st.selectbox("Typ konstrukce", typy_konstrukci(), key="u_ref_typ")
        ref = u_hodnoty_konstrukce(typ_k)
        st.metric("UN,20 – požadovaná", f"{ref.UN} W/(m²·K)" if ref.UN else "–")
        st.metric("Urec,20 – doporučená", f"{ref.Urec} W/(m²·K)" if ref.Urec else "–")
        st.metric("Upas,20 – pasivní", f"{ref.Upas} W/(m²·K)" if ref.Upas else "–")

    # ── Výpočet U stávající konstrukce ───────────────────────────────────────
    st.divider()
    vrstvy_obj = []
    ok = True
    for i, v in enumerate(st.session_state.u_vrstvy):
        mat_name = v["mat"]
        d_v = float(v["d"])
        lam_manual = v.get("lambda_manual")
        if lam_manual is not None:
            lam = float(lam_manual)
        else:
            try:
                lam = lambda_materialu(mat_name)
            except Exception:
                st.error(f"Materiál vrstvy #{i+1} nebyl nalezen.")
                ok = False
                break
        if lam > 0 and d_v > 0:
            vrstvy_obj.append(Vrstva(mat_name, d_v, lam))

    if ok and vrstvy_obj:
        k_pred = Konstrukce(
            nazev=konstrukce_nazev,
            plocha_m2=float(plocha),
            vrstvy=vrstvy_obj,
        )
        U_pred = k_pred.U
        R_pred = k_pred.R_tot
        delta_T = _ti - _te   # z okrajových podmínek projektu
        Q_pred_kw = k_pred.tepelna_ztrata_kw(delta_T)

        st.markdown("**Stávající stav**")
        c1, c2, c3 = st.columns(3)
        c1.metric("R_tot [m²·K/W]", f"{R_pred:.3f}")
        c2.metric("U [W/(m²·K)]", f"{U_pred:.3f}")
        c3.metric("Tepelná ztráta Q [kW]", f"{Q_pred_kw:.2f}")

        # ── Tloušťka izolantu pro dosažení cílové U-hodnoty ──────────────────
        st.divider()
        st.markdown("**Potřebná tloušťka zateplení**")
        st.caption(
            "Kolik cm izolantu je třeba přidat k stávající konstrukci, "
            "aby byla dosažena požadovaná/doporučená/pasivní U-hodnota."
        )

        # Odpor stávající konstrukce bez povrchových odporů = tepelný odpor vrstev
        R_vrstvy = sum(v.R for v in vrstvy_obj)  # = R_tot - Rsi - Rse

        izol_typy = {
            "Minerální vata (λ = 0.040 W/mK)": 0.040,
            "Minerální vata – lepší třída (λ = 0.035 W/mK)": 0.035,
            "EPS polystyren (λ = 0.039 W/mK)": 0.039,
            "EPS – grafitový (λ = 0.031 W/mK)": 0.031,
            "Termoizolační omítka (λ = 0.051 W/mK)": 0.051,
            "PIR / PUR (λ = 0.022 W/mK)": 0.022,
        }
        izol_vyber = st.selectbox("Typ izolantu", list(izol_typy.keys()), key="u_izol_typ")
        lam_izol = izol_typy[izol_vyber]

        cile = {}
        if ref.UN:
            cile["Požadovaná UN"] = ref.UN
        if ref.Urec:
            cile["Doporučená Urec"] = ref.Urec
        if ref.Upas:
            cile["Pasivní Upas"] = ref.Upas

        if cile:
            iz_cols = st.columns(len(cile))
            for col, (label, U_cil) in zip(iz_cols, cile.items()):
                R_cil = 1.0 / U_cil
                # R_cil = Rsi + R_vrstvy + d/λ_izol + Rse
                # d = (R_cil - Rsi - R_vrstvy - Rse) * λ_izol
                d_izol = (R_cil - k_pred.Rsi - R_vrstvy - k_pred.Rse) * lam_izol
                if d_izol <= 0:
                    col.metric(label, "Splněno ✓", help=f"Stávající U={U_pred:.3f} ≤ {U_cil}")
                else:
                    col.metric(label, f"{d_izol*100:.0f} cm", help=f"Cílová U = {U_cil} W/(m²·K)")

        # ── Výpočet úspory po zateplení ────────────────────────────────────────
        st.divider()
        st.markdown("**Úspora tepelné ztráty po zateplení**")

        col_u_po, col_nebo = st.columns([2, 1])
        with col_u_po:
            U_po_val = st.number_input(
                "Nová U-hodnota po opatření [W/(m²·K)]",
                min_value=0.01, max_value=5.0,
                value=float(ref.Urec or U_pred * 0.4),
                step=0.01, format="%.3f", key="u_po",
            )
        with col_nebo:
            st.caption("nebo vyberte cíl:")
            for label, U_cil in cile.items():
                if st.button(f"→ {label} ({U_cil})", key=f"u_btn_{label}"):
                    st.session_state["u_po"] = U_cil
                    st.rerun()

        Q_po_kw = float(plocha) * float(U_po_val) * delta_T / 1_000.0
        delta_phi_kw = max(0.0, Q_pred_kw - Q_po_kw)

        r1, r2, r3 = st.columns(3)
        r1.metric("Q před [kW]", f"{Q_pred_kw:.2f}")
        r2.metric("Q po [kW]", f"{Q_po_kw:.2f}")
        r3.metric("ΔΦ – úspora tep. ztráty [kW]", f"{delta_phi_kw:.2f}",
                  delta=f"−{delta_phi_kw:.2f} kW")

        # ── Korekce na skutečnou spotřebu ─────────────────────────────────────
        st.divider()
        st.markdown("**Korekce na skutečnou spotřebu**")

        phi_total = st.session_state.get("phi_total_kw", 0.0)
        if phi_total > 0 and delta_phi_kw > 0:
            ratio = delta_phi_kw / phi_total

            _nosic = st.session_state.get("nosic", "Zemní plyn")
            spotreba_teplo = (
                st.session_state.get("zp_ut", 0.0) + st.session_state.get("zp_tuv", 0.0)
                if _nosic == "Zemní plyn"
                else st.session_state.get("teplo_ut", 0.0) + st.session_state.get("teplo_tuv", 0.0)
            )
            uspora_korigovana = ratio * spotreba_teplo

            kc1, kc2, kc3 = st.columns(3)
            kc1.metric("ΔΦ / Φ_total", f"{ratio*100:.1f} %",
                       help=f"{delta_phi_kw:.1f} kW / {phi_total:.0f} kW")
            kc2.metric("Skutečná spotřeba tepla", f"{spotreba_teplo:.0f} MWh/rok")
            kc3.metric("Korigovaná úspora", f"{uspora_korigovana:.1f} MWh/rok",
                       help="= (ΔΦ / Φ_total) × skutečná spotřeba")

            st.success(
                f"**Výsledek: {uspora_korigovana:.1f} MWh/rok**  \n"
                f"ΔΦ = {delta_phi_kw:.2f} kW tvoří {ratio*100:.1f} % celkové ztráty "
                f"({phi_total:.0f} kW), tolik % ušetříme ze skutečné spotřeby {spotreba_teplo:.0f} MWh."
            )

            # Přenos výsledku do příslušného opatření
            st.markdown("**Přenést do projektu**")
            _ops = {
                "OP1a – Zateplení stěn (ETICS)": ("op1a_phi_kw", "op1a_uspora"),
                "OP1b – Termoizolační omítka": ("op1b_phi_kw", "op1b_uspora"),
                "OP2 – Výměna otvorových výplní": ("op2_phi_kw", "op2_uspora"),
                "OP3 – Rekonstrukce střechy": ("op3_phi_kw", "op3_uspora"),
                "OP4 – Zateplení podlahy půdy": ("op4_phi_kw", "op4_uspora"),
                "OP5 – Zateplení podlahy na terénu": ("op5_phi_kw", "op5_uspora"),
                "OP6 – Termoreflexní nátěry": ("op6_phi_kw", "op6_uspora"),
            }
            prenest_col, btn_col = st.columns([2, 1])
            with prenest_col:
                op_vyber = st.selectbox("Přenést jako", list(_ops.keys()), key="u_op_vyber")
            with btn_col:
                st.write("")
                st.write("")
                if st.button("✓ Přenést ΔΦ a MWh do projektu", type="primary"):
                    phi_key, uspora_key = _ops[op_vyber]
                    st.session_state[phi_key] = round(delta_phi_kw, 2)
                    st.session_state[uspora_key] = round(uspora_korigovana, 1)
                    st.success(
                        f"Přeneseno do **{op_vyber}**: "
                        f"ΔΦ = {delta_phi_kw:.2f} kW, "
                        f"úspora = {uspora_korigovana:.1f} MWh/rok"
                    )
        elif phi_total == 0:
            st.info(
                "Zadejte **Φ celkem [kW]** v záložce **Potřeba tepla – vytápění** výše "
                "pro aktivaci korekce na skutečnou spotřebu."
            )
        else:
            st.info("Zadejte tloušťku nové U-hodnoty pro výpočet ΔΦ.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 – POTŘEBA TEPLA PRO VYTÁPĚNÍ
# ═══════════════════════════════════════════════════════════════════════════════
with tab_teplo:
    st.subheader("Výpočet potřeby tepla pro vytápění")
    st.caption(
        "Slouží ke stanovení referenční spotřeby tepla (pro záložku Vstupní data). "
        "θi a θe jsou přebírány z okrajových podmínek projektu."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Lokalita a denostupně**")
        lok_nazvy = nazvy_lokalit()
        lok_idx = lok_nazvy.index(_lok_nazev) if _lok_nazev in lok_nazvy else 45
        lok_vybrana = st.selectbox("Lokalita", lok_nazvy, index=lok_idx, key="teplo_lokalita")
        lok = lokalita(lok_vybrana)
        tem_vol = st.radio("Práh otopného období tem", [12, 13, 15], index=1,
                           format_func=lambda x: f"{x} °C", horizontal=True, key="teplo_tem")

        if tem_vol == 12:
            d_val, tes_val = lok.d12, lok.tes12
        elif tem_vol == 15:
            d_val, tes_val = lok.d15, lok.tes15
        else:
            d_val, tes_val = lok.d13, lok.tes13

        D_val = d_val * (_ti - tes_val)
        st.info(f"d = {d_val} dní, tes = {tes_val} °C, **D = {D_val:.0f} K·day** (dlouhodobý průměr)")

        _D_manual = st.checkbox(
            "Zadat D ručně (konkrétní rok)",
            key="teplo_D_manual",
            help="Zadejte skutečné denostupně z klimatické stanice pro konkrétní rok. "
                 "Odpovídá hodnotě D ve sloupci Vstupní data → tabulka po rocích.",
        )
        if _D_manual:
            D_val = st.number_input(
                "D [K·day] – skutečné denostupně daného roku",
                min_value=0.0, value=float(D_val), step=10.0,
                key="teplo_D_val",
            )

        phi_kw = st.number_input(
            "Tepelná ztráta objektu Φ [kW]",
            min_value=0.0,
            value=float(_phi) if _phi > 0 else 120.0,
            step=5.0,
            help="Celková tepelná ztráta – z výpočtu obálky nebo z PENB.",
            key="teplo_phi",
        )
        # Sync zpět do sdíleného klíče phi_total_kw (používá hlavní app + korekce)
        st.session_state["phi_total_kw"] = float(phi_kw)

    with col2:
        st.markdown("**Opravné součinitele a účinnosti**")

        def _sub(label: str, help_text: str = "") -> None:
            """Vykreslí label s HTML dolním indexem jako markdown nad widgetem."""
            _h = f" <span title='{help_text}' style='cursor:help'>ⓘ</span>" if help_text else ""
            st.markdown(f"<span style='font-size:0.875rem;font-weight:600'>{label}</span>{_h}",
                        unsafe_allow_html=True)

        # ── e_i – přerušování provozu ────────────────────────────────────────
        _EI = {
            "Trvalý provoz – nemocnice, hotely, bytové domy":      1.00,
            "Noční útlum – obytné domy, penziony":                 0.90,
            "Víkendový útlum – administrativa":                    0.85,
            "Noční i víkendový útlum – školy, úřady":              0.80,
            "Intenzivní útlum – prázdniny, sezónní přestávky":     0.70,
            "Minimální provoz – sklady, sezónní objekty":          0.60,
        }
        _sub("e<sub>i</sub> – přerušování provozu",
             "Korekční součinitel přerušovaného vytápění (TNI 73 0331).")
        _ei_key = st.selectbox(
            "e_i", list(_EI.keys()), index=3, key="teplo_ei_sel",
            label_visibility="collapsed",
        )
        ei = _EI[_ei_key]

        # ── e_t – způsob regulace ────────────────────────────────────────────
        _ET = {
            "Bez regulace – ruční obsluha":                        1.00,
            "Ekvitermní regulace kotelny":                         0.97,
            "Ekvitermní + termostatické ventily (TRV)":            0.93,
            "Ekvitermní + TRV + hydraulické vyvážení":             0.89,
            "Ekvitermní + TRV + individuální regulace (IRC)":      0.84,
        }
        _sub("e<sub>t</sub> – způsob regulace",
             "Korekční součinitel způsobu regulace teploty (TNI 73 0331).")
        _et_key = st.selectbox(
            "e_t", list(_ET.keys()), index=2, key="teplo_et_sel",
            label_visibility="collapsed",
        )
        et = _ET[_et_key]

        # ── e_d – distribuce / zátopu ────────────────────────────────────────
        _ED = {
            "Lokální zdroj (přímý ohřev, krátké rozvody)":        1.00,
            "Krátké dobře izolované rozvody":                      0.95,
            "Standardní rozvody":                                  0.90,
            "Starší nebo hůře izolované rozvody":                  0.85,
            "Rozvody ve venkovním prostředí nebo bez izolace":     0.80,
        }
        _sub("e<sub>d</sub> – stav rozvodů a zátopu",
             "Korekční součinitel tepelných ztrát rozvodů a doby zátopu (TNI 73 0331).")
        _ed_key = st.selectbox(
            "e_d", list(_ED.keys()), index=2, key="teplo_ed_sel",
            label_visibility="collapsed",
        )
        ed = _ED[_ed_key]

        # ── η_o a η_r – účinnosti ────────────────────────────────────────────
        _ETA_O = {
            "Automatická regulace a MaR":                          0.98,
            "Standardní obsluha (výchozí)":                        0.95,
            "Ruční obsluha bez automatizace":                      0.90,
        }
        _ETA_R = {
            "Rozvody v interiéru, dobře izolované":                0.98,
            "Standardní stav rozvodů (výchozí)":                   0.95,
            "Starší rozvody s viditelnými tepelnými ztrátami":     0.90,
            "Nevyhovující stav – plánovaná rekonstrukce":          0.85,
        }
        _sub("η<sub>o</sub> – účinnost obsluhy zdroje",
             "Účinnost obsluhy a regulace zdroje tepla.")
        _eta_o_key = st.selectbox(
            "η_o", list(_ETA_O.keys()), index=1, key="teplo_etao_sel",
            label_visibility="collapsed",
        )
        _sub("η<sub>r</sub> – účinnost rozvodu tepla",
             "Účinnost přenosu tepla od zdroje k otopným tělesům.")
        _eta_r_key = st.selectbox(
            "η_r", list(_ETA_R.keys()), index=1, key="teplo_etar_sel",
            label_visibility="collapsed",
        )
        eta_o = _ETA_O[_eta_o_key]
        eta_r = _ETA_R[_eta_r_key]

        # ── Ruční přepsání ───────────────────────────────────────────────────
        if st.checkbox("Přepsat hodnoty ručně", key="teplo_rucni"):
            _rc1, _rc2, _rc3 = st.columns(3)
            with _rc1:
                _sub("e<sub>i</sub>")
                ei    = st.number_input("e_i", 0.1, 1.0, ei,    0.01, "%.2f", key="teplo_ei",    label_visibility="collapsed")
            with _rc2:
                _sub("e<sub>t</sub>")
                et    = st.number_input("e_t", 0.1, 1.0, et,    0.01, "%.2f", key="teplo_et",    label_visibility="collapsed")
            with _rc3:
                _sub("e<sub>d</sub>")
                ed    = st.number_input("e_d", 0.1, 1.0, ed,    0.01, "%.2f", key="teplo_ed",    label_visibility="collapsed")
            _rc4, _rc5, _ = st.columns(3)
            with _rc4:
                _sub("η<sub>o</sub>")
                eta_o = st.number_input("η_o", 0.5, 1.0, eta_o, 0.01, "%.2f", key="teplo_etao",  label_visibility="collapsed")
            with _rc5:
                _sub("η<sub>r</sub>")
                eta_r = st.number_input("η_r", 0.5, 1.0, eta_r, 0.01, "%.2f", key="teplo_etar",  label_visibility="collapsed")

        # ── Souhrn ───────────────────────────────────────────────────────────
        eps = ei * et * ed
        _m1, _m2, _m3 = st.columns(3)
        with _m1:
            _sub("e<sub>i</sub>")
            st.markdown(f"<span style='font-size:2rem;font-weight:700'>{ei:.2f}</span>",
                        unsafe_allow_html=True)
        with _m2:
            _sub("e<sub>t</sub> · e<sub>d</sub>")
            st.markdown(f"<span style='font-size:2rem;font-weight:700'>{et * ed:.3f}</span>",
                        unsafe_allow_html=True)
        with _m3:
            _sub("ε = e<sub>i</sub>·e<sub>t</sub>·e<sub>d</sub>",
                 f"η_o = {eta_o:.2f}, η_r = {eta_r:.2f}")
            st.markdown(f"<span style='font-size:2rem;font-weight:700'>{eps:.3f}</span>",
                        unsafe_allow_html=True)

    st.divider()
    Q_UT = vypocet_vytapeni(
        phi_kw=float(phi_kw), D=D_val,
        theta_i=_ti, theta_e=_te,
        ei=float(ei), et=float(et), ed=float(ed),
        eta_o=float(eta_o), eta_r=float(eta_r),
    )
    c1, c2 = st.columns(2)
    c1.metric("Q_UT [MWh/rok]", f"{Q_UT:.1f}")
    c2.metric("Q_UT [GJ/rok]", f"{Q_UT * 3.6:.1f}")
    st.caption(f"→ Zadejte **{Q_UT:.1f} MWh/rok** do záložky Vstupní data (ÚT spotřeba)")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – POTŘEBA TEPLA PRO TUV
# ═══════════════════════════════════════════════════════════════════════════════
with tab_tuv:
    st.subheader("Výpočet potřeby tepla pro přípravu teplé vody")

    col1, col2 = st.columns(2)

    with col1:
        druhy = druhy_budov()
        druh = st.selectbox("Druh budovy", druhy,
                             index=druhy.index("Škola") if "Škola" in druhy else 0,
                             key="tuv_druh")
        vwf, jednotka = vw_faktor(druh)
        st.info(f"Specifická potřeba TV: **{vwf} l / ({jednotka} · den)**")
        pocet = st.number_input(f"Počet {jednotka}", min_value=1, value=300, step=10, key="tuv_pocet")

        lok_nazvy2 = nazvy_lokalit()
        lok_idx2 = lok_nazvy2.index(_lok_nazev) if _lok_nazev in lok_nazvy2 else 45
        lok_vybrana2 = st.selectbox("Lokalita", lok_nazvy2, index=lok_idx2, key="tuv_lokalita")
        lok2 = lokalita(lok_vybrana2)
        tem_vol2 = st.radio("Práh otopného období", [12, 13, 15], index=1,
                             format_func=lambda x: f"{x} °C", horizontal=True, key="tuv_tem")
        d_tuv = lok2.d12 if tem_vol2 == 12 else (lok2.d15 if tem_vol2 == 15 else lok2.d13)
        st.caption(f"Délka otopného období: {d_tuv} dní")

    with col2:
        T_v = st.number_input("Výstupní teplota TV [°C]", value=55.0, step=1.0, key="tuv_tv")
        T_sv = st.number_input("Teplota studené vody [°C]", value=10.0, step=1.0, key="tuv_tsv")
        T_leto = st.number_input("Teplota SV v létě [°C]", value=15.0, step=1.0, key="tuv_tleto")
        T_zima = st.number_input("Teplota SV v zimě [°C]", value=5.0, step=1.0, key="tuv_tzima")
        k_ztraty = st.number_input("Koeficient ztrát systému", min_value=0.0, max_value=2.0,
                                    value=1.0, step=0.1, key="tuv_kztraty")

    st.divider()
    Q_TUV = vypocet_tuv(
        druh_budovy=druh, pocet=float(pocet), d=d_tuv,
        k_ztraty=float(k_ztraty),
        T_v=float(T_v), T_sv=float(T_sv),
        T_leto=float(T_leto), T_zima=float(T_zima),
    )
    # Uložit výsledek do session_state – hlavní app ho přečte v pomůcce na split ZP→ÚT+TUV
    st.session_state["_tuv_calc_mwh"] = float(Q_TUV)

    V_den = vwf * pocet / 1_000.0
    c1, c2, c3 = st.columns(3)
    c1.metric("Objem TV [m³/den]", f"{V_den:.3f}")
    c2.metric("Q_TUV [MWh/rok]", f"{Q_TUV:.1f}")
    c3.metric("Q_TUV [GJ/rok]", f"{Q_TUV * 3.6:.1f}")
    st.caption(f"→ Výsledek je dostupný v hlavní aplikaci: Vstupní data → pomůcka pro rozdělení ZP na ÚT a TUV.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 – VĚTRÁNÍ A ZZT
# ═══════════════════════════════════════════════════════════════════════════════
with tab_vetrani:
    st.subheader("Výpočet potřeby tepla pro větrání a úspory ZZT")

    col1, col2 = st.columns(2)

    with col1:
        V_vetrani = st.number_input("Objem větrané místnosti [m³]", min_value=1.0,
                                     value=480.0, step=10.0, key="vet_V")
        n_vetrani = st.number_input("Intenzita výměny vzduchu n [h⁻¹]", min_value=0.01,
                                     value=0.25, step=0.05, format="%.2f", key="vet_n")
        h_provoz = st.number_input("Provozní hodiny / den [h]", min_value=1.0,
                                    max_value=24.0, value=8.0, step=0.5, key="vet_h")
        d_provoz = st.number_input("Provozní dny / týden", min_value=1.0,
                                    max_value=7.0, value=5.0, step=1.0, key="vet_d")

    with col2:
        lok_nazvy3 = nazvy_lokalit()
        lok_idx3 = lok_nazvy3.index(_lok_nazev) if _lok_nazev in lok_nazvy3 else 45
        lok_vybrana3 = st.selectbox("Lokalita", lok_nazvy3, index=lok_idx3, key="vet_lokalita")
        lok3 = lokalita(lok_vybrana3)
        tem_vol3 = st.radio("Práh otopného období", [12, 13, 15], index=1,
                             format_func=lambda x: f"{x} °C", horizontal=True, key="vet_tem")

        if tem_vol3 == 12:
            d_v, tes_v = lok3.d12, lok3.tes12
        elif tem_vol3 == 15:
            d_v, tes_v = lok3.d15, lok3.tes15
        else:
            d_v, tes_v = lok3.d13, lok3.tes13

        D_vet = d_v * (_ti - tes_v)
        st.caption(f"D = {D_vet:.0f} K·day  (θi = {_ti} °C, tes = {tes_v} °C, d = {d_v} dní)")
        eta_rec = st.slider("Účinnost rekuperace η [-]", 0.0, 1.0, 0.9, 0.05,
                             key="vet_eta", format="%.2f")

    st.divider()
    Q_bez, Q_se = vypocet_vetrani(
        V=float(V_vetrani), n=float(n_vetrani),
        h_provoz=float(h_provoz), d_provoz=float(d_provoz),
        D=D_vet, eta_rec=float(eta_rec),
    )
    uspora = max(0.0, Q_bez - Q_se)

    c1, c2, c3 = st.columns(3)
    c1.metric("Tepelná ztráta větráním [MWh/rok]", f"{Q_bez:.2f}", help="Bez rekuperace")
    c2.metric("Tepelná ztráta se ZZT [MWh/rok]", f"{Q_se:.2f}")
    c3.metric("Úspora díky ZZT [MWh/rok]", f"{uspora:.2f}", delta=f"−{uspora:.2f} MWh/rok")

    if eta_rec > 0 and uspora > 0:
        st.caption(
            f"→ Zadejte **{uspora:.2f} MWh/rok** jako úsporu tepla u opatření OP17 (VZT+ZZT)"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 – IMPORT Z PDF (PENB / Svoboda SW / Deksoft)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_import:
    st.subheader("Import dat z PDF")
    st.caption(
        "Podporované formáty: **PENB dle vyhl. 264/2020** a **výpočet Svoboda SW / Deksoft (Energie 2021)**. "
        "Starý PENB (skenovaný) není podporován – nemá textovou vrstvu."
    )

    uploaded = st.file_uploader(
        "Nahrajte PDF soubor",
        type=["pdf"],
        key="penb_upload",
        help="Maximální velikost: 200 MB. Zpracování probíhá lokálně, soubor se nikam neodesílá.",
    )

    if uploaded is not None:
        # Parsovat jen pokud se změnil soubor (cache podle jména + velikosti)
        _cache_key = f"{uploaded.name}|{uploaded.size}"
        if st.session_state.get("_penb_cache_key") != _cache_key:
            try:
                from epc_engine.penb_parser import parse_pdf
                _pdf_bytes = uploaded.read()
                _parsed = parse_pdf(io.BytesIO(_pdf_bytes))
                st.session_state["_penb_parsed"] = _parsed
                st.session_state["_penb_cache_key"] = _cache_key
            except Exception as _e:
                st.error(f"Chyba při zpracování PDF: {_e}")
                st.session_state.pop("_penb_parsed", None)
                st.session_state["_penb_cache_key"] = None

    _parsed = st.session_state.get("_penb_parsed")

    if _parsed is None:
        st.info("Nahrajte PDF soubor pro zahájení importu.")
    else:
        _zdroj_label = {
            "penb_264_2020": "PENB dle vyhl. 264/2020",
            "svoboda_sw": "Výpočet Svoboda SW / Deksoft (Energie 2021)",
        }.get(_parsed.zdroj, _parsed.zdroj)
        st.success(f"Rozpoznaný formát: **{_zdroj_label}**")

        # ── Geometrie ─────────────────────────────────────────────────────────
        with st.expander("Geometrie budovy", expanded=True):
            _gc1, _gc2, _gc3 = st.columns(3)
            _gc1.metric("Objem V [m³]", f"{_parsed.objem_m3:.0f}" if _parsed.objem_m3 else "–")
            _gc2.metric(
                "Energeticky vztažná plocha [m²]",
                f"{_parsed.plocha_m2:.0f}" if _parsed.plocha_m2 else "–",
                help="Podlahová plocha vytápěné části budovy (A,n).",
            )
            _gc3.metric(
                "Plocha obálky A [m²]",
                f"{_parsed.ochlazovana_plocha_m2:.0f}" if _parsed.ochlazovana_plocha_m2 else "–",
                help="Součet ploch všech ochlazovaných konstrukcí obálky budovy (stěny + střecha + podlahy + výplně). Slouží pro výpočet faktoru tvaru A/V.",
            )

            _any_geom = _parsed.objem_m3 > 0 or _parsed.plocha_m2 > 0 or _parsed.ochlazovana_plocha_m2 > 0
            if _any_geom:
                if st.button("Importovat geometrii do aktivního objektu", key="imp_geom"):
                    _bud = st.session_state.get("budovy", [{}])
                    if not _bud:
                        _bud = [{}]
                    if _parsed.objem_m3 > 0:
                        _bud[0]["objem_m3"] = _parsed.objem_m3
                    if _parsed.plocha_m2 > 0:
                        _bud[0]["plocha_m2"] = _parsed.plocha_m2
                    if _parsed.ochlazovana_plocha_m2 > 0:
                        _bud[0]["ochlaz_m2"] = _parsed.ochlazovana_plocha_m2
                    st.session_state["budovy"] = _bud
                    st.success("Geometrie importována → záložka Identifikace → Budovy.")

        # ── Tepelná ztráta Φ ──────────────────────────────────────────────────
        with st.expander("Tepelná ztráta a Uem", expanded=True):
            _pc1, _pc2 = st.columns(2)
            _pc1.metric("Φ celkem [kW]", f"{_parsed.phi_total_kw:.1f}" if _parsed.phi_total_kw else "–")
            _pc2.metric("Uem [W/(m²·K)]", f"{_parsed.U_em:.3f}" if _parsed.U_em else "–")

            if _parsed.phi_total_kw > 0:
                if st.button("Importovat Φ", key="imp_phi"):
                    st.session_state["phi_total_kw"] = _parsed.phi_total_kw
                    st.success(f"Φ = {_parsed.phi_total_kw:.1f} kW importováno → aktivní v záložce Potřeba tepla.")

        # ── Energie (teoretické hodnoty EP z výpočtu) ─────────────────────────
        with st.expander("Teoretické hodnoty EP z výpočtu (pro korekci úspor)", expanded=True):
            st.warning(
                "**Pozor – toto nejsou naměřené spotřeby z faktur.**  \n"
                "Hodnoty EP,H a EP,W jsou teoretické, normované výstupy energetického výpočtu "
                "(dle ČSN EN ISO 52016 / TNI 73 0331). Jsou vhodné jako referenční základ "
                "pro korekci úspory tepla (ΔΦ / Φ × EP_ref), "
                "ale **nenahrazují skutečně naměřené spotřeby** ze vstupních dat projektu.",
                icon="⚠️",
            )
            _ec1, _ec2, _ec3, _ec4 = st.columns(4)
            _ec1.metric(
                "EP,H – vytápění [MWh/rok]",
                f"{_parsed.ut_mwh:.1f}" if _parsed.ut_mwh else "–",
                help="Dodaná energie na vytápění (EP,H) z výpočtu.",
            )
            _ec2.metric(
                "EP,W – TUV [MWh/rok]",
                f"{_parsed.tuv_mwh:.1f}" if _parsed.tuv_mwh else "–",
                help="Dodaná energie na přípravu teplé vody (EP,W) z výpočtu.",
            )
            _ec3.metric(
                "ZP celkem [MWh/rok]",
                f"{_parsed.zp_mwh:.1f}" if _parsed.zp_mwh else "–",
                help="Celková dodaná energie – zemní plyn (všechny účely).",
            )
            _ec4.metric(
                "EE [MWh/rok]",
                f"{_parsed.ee_mwh:.1f}" if _parsed.ee_mwh else "–",
                help="Celková dodaná elektrická energie z výpočtu.",
            )

            _has_energy = _parsed.zp_mwh > 0 or _parsed.ut_mwh > 0 or _parsed.ee_mwh > 0
            if _has_energy:
                st.caption(
                    "Použijte import **pouze tehdy**, kdy nemáte skutečné naměřené hodnoty "
                    "(např. nová budova, rekonstrukce bez historických dat). "
                    "V ostatních případech zadejte skutečné spotřeby z faktur ručně v záložce Vstupní data."
                )
                _imp_col1, _imp_col2 = st.columns(2)
                with _imp_col1:
                    _imp_zp = st.checkbox(
                        "EP,H → ZP ÚT (vytápění)", value=False, key="imp_zp_ut_cb",
                        help="Přepíše hodnotu ZP pro ÚT ve Vstupních datech teoretickou hodnotou EP,H.",
                    )
                    _imp_zp_tuv = st.checkbox(
                        "EP,W → ZP TUV", value=False, key="imp_zp_tuv_cb",
                        help="Přepíše hodnotu ZP pro TUV ve Vstupních datech teoretickou hodnotou EP,W.",
                    )
                with _imp_col2:
                    _imp_ee = st.checkbox(
                        "EE (elektrická energie)", value=False, key="imp_ee_cb",
                        help="Přepíše hodnotu EE ve Vstupních datech. Používejte opatrně.",
                    )
                    _imp_theta = st.checkbox(
                        f"Návrhová θe = {_parsed.theta_e:.0f} °C",
                        value=(_parsed.theta_e != -13.0),
                        key="imp_theta_cb",
                        help="Nastaví venkovní výpočtovou teplotu z PDF (odlišná od výchozích −13 °C).",
                    )

                if st.button(
                    "Přepsat Vstupní data vybranými hodnotami EP",
                    key="imp_energie", type="secondary",
                ):
                    if _imp_zp and _parsed.ut_mwh > 0:
                        st.session_state["zp_ut"] = _parsed.ut_mwh
                    elif _imp_zp and _parsed.zp_mwh > 0 and not _parsed.ut_mwh:
                        st.session_state["zp_ut"] = _parsed.zp_mwh
                    if _imp_zp_tuv and _parsed.tuv_mwh > 0:
                        st.session_state["zp_tuv"] = _parsed.tuv_mwh
                    if _imp_ee and _parsed.ee_mwh > 0:
                        st.session_state["ee"] = _parsed.ee_mwh
                    if _imp_theta:
                        st.session_state["theta_e"] = _parsed.theta_e
                    # Měsíční průběh
                    if any(v > 0 for v in _parsed.mesice_zp):
                        st.session_state["zp_ut_mesice"] = list(_parsed.mesice_zp)
                    if any(v > 0 for v in _parsed.mesice_ee):
                        st.session_state["ee_mesice"] = list(_parsed.mesice_ee)
                    st.success("Hodnoty EP importovány → zkontrolujte záložku Vstupní data v hlavní aplikaci.")

        # ── Konstrukce obálky ─────────────────────────────────────────────────
        if _parsed.konstrukce:
            with st.expander(f"Konstrukce obálky budovy ({len(_parsed.konstrukce)} prvků)", expanded=True):
                import pandas as pd
                _TYP_LABEL = {
                    "stena": "Stěna", "strecha": "Střecha",
                    "podlaha_ext": "Podlaha ext.", "podlaha_zem": "Podlaha/zemina",
                    "otvor": "Výplň otvoru",
                }
                _rows = []
                for _k in _parsed.konstrukce:
                    _rows.append({
                        "Označení": _k.ozn,
                        "Typ": _TYP_LABEL.get(_k.typ, _k.typ),
                        "Plocha [m²]": round(_k.plocha_m2, 1),
                        "U [W/(m²·K)]": round(_k.U, 3),
                        "UN,20 [W/(m²·K)]": round(_k.U_ref, 3) if _k.U_ref else "–",
                    })
                _df_kce = pd.DataFrame(_rows)
                st.dataframe(_df_kce, use_container_width=True, hide_index=True)

                st.caption(
                    "Konstrukce jsou pouze pro orientaci. Pro výpočet ΔΦ a úspory opatření "
                    "použijte záložku **Součinitel prostupu tepla U** výše – kliknutím na "
                    "tlačítko níže předvyplníte plochu a stávající U pro vybranou konstrukci."
                )

                _vyber_kce = st.selectbox(
                    "Předvyplnit záložku U-hodnoty konstrukcí z PDF:",
                    options=["– nevybráno –"] + [f"{_k.ozn} – {_TYP_LABEL.get(_k.typ, _k.typ)} – {_k.plocha_m2:.0f} m² – U={_k.U:.3f}" for _k in _parsed.konstrukce],
                    key="imp_kce_vyber",
                )
                if _vyber_kce != "– nevybráno –":
                    _kce_idx = [f"{_k.ozn} – {_TYP_LABEL.get(_k.typ, _k.typ)} – {_k.plocha_m2:.0f} m² – U={_k.U:.3f}" for _k in _parsed.konstrukce].index(_vyber_kce)
                    _sel_kce = _parsed.konstrukce[_kce_idx]
                    if st.button(f"Předvyplnit U-kalkulátor: {_sel_kce.ozn}", key="imp_kce_btn"):
                        st.session_state["u_nazev"] = _sel_kce.nazev
                        st.session_state["u_plocha"] = _sel_kce.plocha_m2
                        # Nastavíme první vrstvu jako "zadat λ ručně" s odvozeným R = 1/U
                        # (orientační – uživatel upřesní skladbu)
                        _R_approx = (1.0 / _sel_kce.U) - 0.17  # odpočet Rsi+Rse ≈ 0.17
                        _d_approx = max(0.10, round(_R_approx * 0.9, 2))  # orientační
                        st.session_state["u_vrstvy"] = [
                            {"mat": "(zadat λ ručně)", "d": _d_approx, "lambda_manual": round(_d_approx / max(0.001, _R_approx), 3)},
                        ]
                        st.success(f"Záložka U-hodnota předvyplněna: plocha={_sel_kce.plocha_m2:.0f} m², U≈{_sel_kce.U:.3f} W/(m²·K).")
                        st.info("Přejděte na záložku **Součinitel prostupu tepla U** a upřesněte skladbu vrstev.")
