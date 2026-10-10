"""Customer Hub: four pathway tiles (always visible), the Proof Card, Scenario Lab and red-team."""
import streamlit as st

import client
import theme as T
from components import proof_card, shell
from components.scenario_lab import redteam, scenario_lab

T.setup("Customer Hub")
persona = shell.sidebar()
shell.gate("hub", "the Customer Hub")

doc = client.opportunities(persona["customer_id"], client.role())
opps = {o["opportunity_id"]: o for o in doc["opportunities"]}

# Default card: the most prominent status (RECOMMEND > REVIEW > ABSTAIN > SOFT_SURFACE > RULED_OUT)
ORDER = {"RECOMMEND": 0, "REVIEW": 1, "ABSTAIN": 2, "SOFT_SURFACE": 3, "RULED_OUT": 4}
sel_key = f"pathway::{persona['customer_id']}"
if sel_key not in st.session_state:
    st.session_state[sel_key] = sorted(opps.values(), key=lambda o: ORDER[o["status"]])[0]["opportunity_id"]

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
        if st.button(f"Open {opps[gp]['opportunity_name']}", key=f"open-{gp}", width="stretch"):
            st.session_state[sel_key] = gp
            st.rerun()

left, right = st.columns([3, 2], gap="large")
with left:
    if st.session_state.get("insights-on", True):
        proof_card.render(doc, opps[st.session_state[sel_key]], key=f"{persona['customer_id']}-{st.session_state[sel_key]}")
    else:
        T.banner("Insights are off. Switch them back on in Your data whenever you like.", "info")

with right:
    with st.container(key="gd-panel-data"):
        st.markdown("#### Your data")
        for f in doc.get("data_freshness", []):
            T.render(f'<p style="margin:4px 0;display:flex;justify-content:space-between;gap:8px"><span>{T.esc(f["source"])}</span>'
                     f'<span class="gd-date">{T.esc(f["asOf"]).upper()} · {"DECLARED" if f["kind"] == "declared" else "INFERRED"}</span></p>')
        st.markdown("**What we used / what we didn't**")
        st.caption("Used: spending categories, products, energy and digital usage. "
                   "Not used to drive recommendations: age, income or fine-grained postcode.")
        st.toggle("Show me green insights", value=True, key="insights-on", help="Switching this off replaces every card with one placeholder.")
    if shell.can("lab"):
        scenario_lab(persona["customer_id"])
    if shell.can("redteam"):
        redteam()

T.footer()
