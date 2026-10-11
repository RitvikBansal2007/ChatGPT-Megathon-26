"""Customer Hub: four pathway tiles (always visible), the Proof Card, Scenario Lab and red-team."""
import streamlit as st

import importlib
import client
import theme as T
from components import proof_card, shell
from components.scenario_lab import redteam, scenario_lab
importlib.reload(shell)

T.setup("Customer Hub")
shell.auth_gate()
persona = shell.sidebar()

shell.gate("hub", "the Customer Hub")

doc = client.opportunities(persona["customer_id"], client.role())
opps = {o["opportunity_id"]: o for o in doc["opportunities"]}

# Default card: the most prominent status (RECOMMEND > REVIEW > ABSTAIN > SOFT_SURFACE > RULED_OUT)
ORDER = {"RECOMMEND": 0, "REVIEW": 1, "ABSTAIN": 2, "SOFT_SURFACE": 3, "RULED_OUT": 4}
sel_key = f"pathway::{persona['customer_id']}"
if sel_key not in st.session_state:
    st.session_state[sel_key] = sorted(opps.values(), key=lambda o: ORDER[o["status"]])[0]["opportunity_id"]

user = client.current_user()
if not user:
    T.banner(f"Previewing sample profile: {doc['display_name']} ({persona['customer_id']}). Sign In or Sign Up in the sidebar to access your verified account.", "info")

st.markdown(f"## Hi {T.esc(doc['display_name'])}")
T.render(f'<div class="gd-row"><span class="gd-chip">Data as of 30 Jun 2026</span><span class="gd-chip">{T.esc(doc["region"])}</span>'
         + "".join(f'<span class="gd-chip">{T.esc(t)}</span>' for t in doc.get("tags", [])) + "</div>")


if all(o["status"] == "RULED_OUT" for o in opps.values()):
    T.banner("You're all set. Every pathway is ruled out for a plain reason: open any tile to see why.", "ok")

st.markdown("#### Your four green pathways")
cols = st.columns(4)
for col, gp in zip(cols, ["GP01", "GP02", "GP03", "GP04"]):
    with col:
        T.render(T.tile(opps[gp], st.session_state[sel_key] == gp))
        if st.button("Open", key=f"open-{gp}", width="stretch", help=f"Open {opps[gp]['opportunity_name']}"):
            st.session_state[sel_key] = gp
            st.rerun()

left, right = st.columns([3, 2], gap="large")
with left:
    if st.session_state.get("insights-on", True):
        proof_card.render(doc, opps[st.session_state[sel_key]], key=f"{persona['customer_id']}-{st.session_state[sel_key]}")
    else:
        T.banner("Insights are off. Switch them back on in Your data whenever you like.", "info")

with right:
    names = ["Your data", "Customer Memory"] + (["Scenario Lab"] if shell.can("lab") else []) + (["Claim-Check"] if shell.can("redteam") else [])
    tabs = dict(zip(names, st.tabs(names)))
    with tabs["Your data"]:
        for f in doc.get("data_freshness", []):
            T.render(f'<p style="margin:4px 0;display:flex;justify-content:space-between;gap:8px"><span>{T.esc(f["source"])}</span>'
                     f'<span class="gd-date">{T.esc(f["asOf"]).upper()} · {"DECLARED" if f["kind"] == "declared" else "INFERRED"}</span></p>')
        st.caption("We use spending categories, products, energy and digital usage. "
                   "We do not use age, income or fine-grained postcode to drive recommendations.")
        st.toggle("Show me green insights", value=True, key="insights-on", help="Switching this off replaces every card with one placeholder.")
    with tabs["Customer Memory"]:
        st.caption("Persistent preferences and declared facts remembered for this customer.")
        m_items = client.get_customer_memory(persona["customer_id"])
        if m_items:
            for item in m_items:
                cat_tag = item.get("category", "preference").replace("_", " ").title()
                src_tag = item.get("source", "declared").replace("_", " ").title()
                T.render(f'<div class="gd-card gd-card--flat" style="padding:10px;margin-bottom:8px">'
                         f'<div class="gd-row" style="margin-bottom:4px"><span class="gd-tag">{T.esc(cat_tag)}</span>'
                         f'<span class="gd-date">{T.esc(src_tag)}</span></div>'
                         f'<p style="margin:0;font-size:13px">{T.esc(item.get("value", ""))}</p></div>')
        else:
            T.banner("No memory items recorded yet for this customer.", "info")

        with st.expander("Add preference or declared fact", expanded=False):
            m_text = st.text_input("Fact / Preference", placeholder="e.g. Planning to install heat pump in autumn", key=f"mem-txt-{persona['customer_id']}")
            m_cat = st.selectbox("Category", ["preference", "declared_fact", "goal", "agent_note"], format_func=lambda s: s.replace("_", " ").title(), key=f"mem-cat-{persona['customer_id']}")
            if st.button("Save to Memory", key=f"mem-save-{persona['customer_id']}", type="primary"):
                if m_text.strip():
                    client.add_customer_memory(persona["customer_id"], "note", m_text.strip(), m_cat, "customer_declared")
                    st.success("Saved to customer memory.")
                    st.rerun()
    if "Scenario Lab" in tabs:
        with tabs["Scenario Lab"]:
            scenario_lab(persona["customer_id"])
    if "Claim-Check" in tabs:
        with tabs["Claim-Check"]:
            redteam()

T.footer()
