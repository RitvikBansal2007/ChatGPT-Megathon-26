"""Scenario Lab — seven mutation toggles, diff view, invariance badge, red-team button.

Only shown to Evaluator and Relationship Manager roles.
All calls go through client.py. No engine imports.
"""

import html
import streamlit as st

import theme
import client

# ── Mutation catalogue (mirrors architecture §1.6) ─────────────────────────
MUTATIONS = [
    ("SET_VEHICLE_BEV",   "Set vehicle to EV"),
    ("REMOVE_MILEAGE",    "Remove annual mileage"),
    ("REMOVE_ENERGY",     "Remove energy data"),
    ("ADD_CONFLICT_FUEL", "Add conflicting fuel signal"),
    ("MAKE_STALE",        "Make data stale"),
    ("SET_RENTER",        "Mark as renter"),
    ("SELL_CAR",          "Sell the car"),
]

# Roles that can access the lab
LAB_ROLES = {"Evaluator", "Relationship Manager"}

# Fixed sentence for red-team (hardcoded per playbook §3.6)
_REDTEAM_SENTENCE = (
    "Switching will save you 4,000 kg a year and you're pre-approved."
)


def _role_allowed(role: str) -> bool:
    return any(r in role for r in LAB_ROLES)


def render(customer_id: str, opportunity_id: str, role: str) -> None:
    """Render the Scenario Lab side panel. Call once per page."""
    if not _role_allowed(role):
        return

    with st.sidebar:
        st.markdown(
            '<div class="gd-card" style="padding:16px;">'
            '<div class="gd-tag" style="margin-bottom:8px;">SCENARIO LAB</div>'
            '<p class="gd-muted" style="font-size:12px;margin-bottom:12px;">'
            'Toggle inputs to see how the recommendation changes. '
            'Results mirror the live engine — only inputs are mutated.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── Seven mutation toggles ─────────────────────────────────────────
        active_mutations: list[str] = []
        for mut_id, mut_label in MUTATIONS:
            key = f"lab_toggle_{mut_id}"
            if st.toggle(mut_label, key=key):
                active_mutations.append(mut_id)

        st.divider()

        # ── Run scenario on any toggle change ─────────────────────────────
        if active_mutations:
            with st.spinner("Re-computing…"):
                try:
                    result = client.run_scenario(customer_id, active_mutations)
                    _render_scenario_result(result)
                except Exception as exc:
                    st.error(f"Scenario failed: {exc}", icon=":material/error:")
        else:
            st.caption("Enable a toggle to see what changes.")

        # ── Reset button ───────────────────────────────────────────────────
        if st.button("↺ Reset to original", key="lab_reset", use_container_width=True):
            for mut_id, _ in MUTATIONS:
                st.session_state[f"lab_toggle_{mut_id}"] = False
            st.rerun()

        st.divider()

        # ── Red-team button ────────────────────────────────────────────────
        st.markdown(
            '<div class="gd-tag" style="color:#B4232A;margin-bottom:8px;">RED-TEAM</div>',
            unsafe_allow_html=True,
        )
        st.caption("Inject a known-bad claim and see Claim-Check catch it.")
        if st.button(
            "🔴 Inject fake claim",
            key="lab_redteam",
            use_container_width=True,
        ):
            with st.spinner("Running Claim-Check…"):
                try:
                    cc = client.claimcheck(
                        customer_id,
                        opportunity_id,
                        [_REDTEAM_SENTENCE],
                    )
                    _render_redteam_result(cc)
                except Exception as exc:
                    st.error(f"Claim-Check failed: {exc}", icon=":material/error:")


def _render_scenario_result(result: dict) -> None:
    """Show before/after transition badges, diff table, cause, invariance."""
    before = result.get("before", {})
    after  = result.get("after",  {})
    diff   = result.get("diff",   [])
    cause  = result.get("cause",  "—")
    inv_ok = result.get("invariance_ok", True)
    elapsed = result.get("elapsed_ms", 0)

    # Status transitions per product
    all_products = set(before.keys()) | set(after.keys())
    for pid in sorted(all_products):
        b_status = (before.get(pid) or {}).get("status", "—")
        a_status = (after.get(pid)  or {}).get("status", "—")
        if b_status == a_status:
            continue
        b_tok = theme.STATUS.get(b_status, {})
        a_tok = theme.STATUS.get(a_status, {})
        b_col = b_tok.get("fg", "#888")
        a_col = a_tok.get("fg", "#888")
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">'
            f'<span class="gd-tag">{html.escape(pid)}</span>'
            f'<span style="color:{b_col};font-weight:700;">{html.escape(b_status)}</span>'
            f'<span style="color:#6B8A7C;">→</span>'
            f'<span style="color:{a_col};font-weight:700;">{html.escape(a_status)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Cause line
    if cause:
        st.caption(f"**Cause:** {cause}")

    # Diff table
    if diff:
        import pandas as pd
        df = pd.DataFrame(diff)
        st.dataframe(df, use_container_width=True, height=min(200, 36 + 36 * len(df)))

    # Invariance badge
    if inv_ok:
        st.success(f"✓ Invariance OK · {elapsed} ms", icon=":material/check_circle:")
    else:
        st.error("✗ Invariance failed — lab output differs from fresh run", icon=":material/error:")


def _render_redteam_result(cc: dict) -> None:
    """Highlight violations, show rule IDs, fallback text, blocked count."""
    sentence   = cc.get("sentence", _REDTEAM_SENTENCE)
    violations = cc.get("violations", [])
    fallback   = cc.get("fallback_text", "")
    blocked    = cc.get("blocked_total", 0)
    passed     = cc.get("pass", False)

    st.markdown("**Claim-Check result:**")

    # Highlight violating spans in the sentence
    highlighted = html.escape(sentence)
    for v in violations:
        span    = html.escape(v.get("span", ""))
        rule_id = html.escape(v.get("rule_id", ""))
        highlighted = highlighted.replace(
            span,
            f'<mark style="background:#FDECEA;color:#B4232A;border-radius:3px;padding:0 2px;">'
            f'{span}</mark>'
            f'<sup class="gd-tag" style="color:#B4232A;margin-left:2px;">{rule_id}</sup>',
            1,
        )

    st.markdown(
        f'<div class="gd-well" style="font-size:13px;line-height:20px;">{highlighted}</div>',
        unsafe_allow_html=True,
    )

    # Rule ID list
    if violations:
        rule_ids = " · ".join(v.get("rule_id", "") for v in violations)
        st.markdown(
            f'<p class="gd-tag" style="color:#B4232A;">Rules fired: {html.escape(rule_ids)}</p>',
            unsafe_allow_html=True,
        )
        for v in violations:
            st.caption(f"**{v.get('rule_id','')}:** {v.get('reason','')}")

    # Fallback text
    if fallback:
        st.markdown("**Fallback sentence used instead:**")
        st.info(fallback, icon=":material/verified_user:")

    # Blocked counter
    if passed:
        st.success(f"PASS — {blocked} total claims blocked in system", icon=":material/check_circle:")
    else:
        st.error(
            f"BLOCKED — {blocked} total claims blocked in system",
            icon=":material/block:",
        )
