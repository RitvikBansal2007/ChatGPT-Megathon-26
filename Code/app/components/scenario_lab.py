"""Scenario Lab — aligned to real contracts.py ScenarioResponse + ClaimCheckResponse.

ScenarioResponse fields (Akshit):
  before / after: dict[ProductId, StatusSnapshot]
  diff[].product / .field / .from / .to / .cause
  invariance_ok, elapsed_ms

ClaimCheckResponse fields:
  verdict: "BLOCKED" | "PASS"
  sentences[].violations[].rule / .span / .detail
  fallback_text
  blocked_total
"""

import html
import streamlit as st

import theme
import client

MUTATIONS = [
    ("SET_VEHICLE_BEV",   "Set vehicle to EV"),
    ("REMOVE_MILEAGE",    "Remove annual mileage"),
    ("REMOVE_ENERGY",     "Remove energy data"),
    ("ADD_CONFLICT_FUEL", "Add conflicting fuel signal"),
    ("MAKE_STALE",        "Make data stale"),
    ("SET_RENTER",        "Mark as renter"),
    ("SELL_CAR",          "Sell the car"),
]

LAB_ROLES = {"Evaluator", "Relationship Manager"}
_REDTEAM_SENTENCE = "Switching will save you 4,000 kg a year and you're pre-approved."


def _role_allowed(role: str) -> bool:
    return any(r in role for r in LAB_ROLES)


def render(customer_id: str, opportunity_id: str, role: str) -> None:
    if not _role_allowed(role):
        return

    with st.sidebar:
        st.markdown(
            '<div style="background:#F1F8F4;border:1px solid #C8E6D4;border-radius:12px;'
            'padding:14px 16px;margin-bottom:12px;">'
            '<div style="font-size:10px;font-family:monospace;font-weight:700;'
            'color:#0F7A55;margin-bottom:6px;">SCENARIO LAB</div>'
            '<p style="font-size:11px;color:#6B8A7C;margin:0;">Toggle inputs to see how '
            'the recommendation changes.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        active_mutations: list[str] = []
        for mut_id, mut_label in MUTATIONS:
            if st.toggle(mut_label, key=f"lab_toggle_{mut_id}"):
                active_mutations.append(mut_id)

        st.divider()

        if active_mutations:
            with st.spinner("Re-computing…"):
                try:
                    result = client.run_scenario(customer_id, active_mutations)
                    _render_scenario_result(result)
                except Exception as exc:
                    st.error(f"Scenario failed: {exc}", icon=":material/error:")
        else:
            st.caption("Enable a toggle to see what changes.")

        if st.button("↺ Reset", key="lab_reset", use_container_width=True):
            for mut_id, _ in MUTATIONS:
                st.session_state[f"lab_toggle_{mut_id}"] = False
            st.rerun()

        st.divider()

        st.markdown(
            '<div style="font-size:10px;font-family:monospace;font-weight:700;'
            'color:#B4232A;margin-bottom:6px;">RED-TEAM</div>',
            unsafe_allow_html=True,
        )
        st.caption("Inject a known-bad claim and see Claim-Check catch it.")
        if st.button("🔴 Inject fake claim", key="lab_redteam", use_container_width=True):
            with st.spinner("Running Claim-Check…"):
                try:
                    cc = client.claimcheck(customer_id, opportunity_id, [_REDTEAM_SENTENCE])
                    _render_redteam_result(cc)
                except Exception as exc:
                    st.error(f"Claim-Check failed: {exc}", icon=":material/error:")


def _render_scenario_result(result: dict) -> None:
    before   = result.get("before", {})
    after    = result.get("after",  {})
    diff     = result.get("diff",   [])
    inv_ok   = result.get("invariance_ok", True)
    elapsed  = result.get("elapsed_ms", 0)

    products = sorted(set(list(before.keys()) + list(after.keys())))
    for pid in products:
        b_status = (before.get(pid) or {}).get("status", "—")
        a_status = (after.get(pid)  or {}).get("status", "—")
        if b_status == a_status:
            continue
        b_tok = theme.STATUS.get(b_status, {})
        a_tok = theme.STATUS.get(a_status, {})
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;flex-wrap:wrap;">'
            f'<span style="font-size:10px;font-family:monospace;background:#E3EFE9;'
            f'padding:2px 6px;border-radius:4px;">{html.escape(pid)}</span>'
            f'<span style="color:{b_tok.get("fg","#888")};font-weight:700;font-size:12px;">{html.escape(b_status)}</span>'
            f'<span style="color:#8AA79A;">→</span>'
            f'<span style="color:{a_tok.get("fg","#888")};font-weight:700;font-size:12px;">{html.escape(a_status)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Diff rows — contract uses .from (aliased to from_) and .to
    if diff:
        import pandas as pd
        rows = []
        for d in diff:
            rows.append({
                "Product": d.get("product", ""),
                "Field":   d.get("field", ""),
                "Before":  d.get("from", d.get("from_", "")),
                "After":   d.get("to", ""),
                "Cause":   d.get("cause", ""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if inv_ok:
        st.success(f"✓ Invariance OK · {elapsed} ms", icon=":material/check_circle:")
    else:
        st.error("✗ Invariance failed", icon=":material/error:")


def _render_redteam_result(cc: dict) -> None:
    """Aligned to claimcheck_response.json contract:
       sentences[].violations[].rule / .span / .detail
    """
    verdict   = cc.get("verdict", "BLOCKED")
    sentences = cc.get("sentences", [])
    fallback  = cc.get("fallback_text", "")
    blocked   = cc.get("blocked_total", 0)

    st.markdown("**Claim-Check result:**")

    for sent in sentences:
        text = sent.get("text", _REDTEAM_SENTENCE)
        violations = sent.get("violations", [])

        # Highlight each violating span
        highlighted = html.escape(text)
        for v in violations:
            span    = html.escape(v.get("span", ""))
            rule_id = html.escape(v.get("rule", ""))
            if span in highlighted:
                highlighted = highlighted.replace(
                    span,
                    f'<mark style="background:#FDECEA;color:#B4232A;border-radius:3px;'
                    f'padding:0 2px;">{span}</mark>'
                    f'<sup style="font-family:monospace;font-size:9px;color:#B4232A;'
                    f'margin-left:1px;">{rule_id}</sup>',
                    1,
                )

        st.markdown(
            f'<div style="background:#FFF8F8;border:1px solid #F5C6C6;border-radius:10px;'
            f'padding:10px 14px;font-size:13px;line-height:1.6;">{highlighted}</div>',
            unsafe_allow_html=True,
        )

        if violations:
            rule_ids = " · ".join(v.get("rule", "") for v in violations)
            st.markdown(
                f'<p style="font-size:11px;font-family:monospace;color:#B4232A;margin:4px 0 0;">'
                f'Rules fired: {html.escape(rule_ids)}</p>',
                unsafe_allow_html=True,
            )
            for v in violations:
                st.caption(f"**{v.get('rule','')}:** {v.get('detail', v.get('span',''))}")

    if fallback:
        st.markdown("**Fallback text used instead:**")
        st.info(fallback, icon=":material/verified_user:")

    if verdict == "PASS":
        st.success(f"PASS — {blocked} total claims blocked in system", icon=":material/check_circle:")
    else:
        st.error(f"BLOCKED — {blocked} total claims blocked in system", icon=":material/block:")
