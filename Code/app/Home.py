"""greendash · Home."""
import streamlit as st

import client
import theme as T
from components import shell

T.setup("Home")
persona = shell.sidebar()

T.render('<span class="gd-tag">Megathon X · Problem Statement 1 · Lloyds</span>')
st.title("Green, with receipts.")
T.render('<p class="gd-muted" style="font-size:17px;max-width:760px">One evidence engine, two audiences. Customers get a next green step they can check. '
         'Relationship teams get a ranked pipeline they can defend. Every number has a source, every refusal is explained, '
         'and every AI-written sentence is checked before anyone sees it.</p>')
T.banner(T.CORE_RULE, "ok")

st.subheader("Where to go")
c1, c2, c3 = st.columns(3)
with c1, st.container(key="gd-panel-home-hub"):
    st.markdown("**Customer Hub**")
    st.caption("Four pathways, always visible. Proof Cards with three separate verdicts, evidence with dates, impact ranges, Claim-Check. Scenario Lab.")
    st.page_link("pages/1_Customer_Hub.py", label="Open Customer Hub", icon=":material/eco:")
with c2, st.container(key="gd-panel-home-cockpit"):
    st.markdown("**Cockpit**")
    st.caption("Portfolio tiles reported separately, funnel, opportunity quadrant, segments, and drill-down from customer to evidence to action.")
    st.page_link("pages/2_Cockpit.py", label="Open Cockpit", icon=":material/monitoring:")
with c3, st.container(key="gd-panel-home-receipts"):
    st.markdown("**Receipts**")
    st.caption("Baselines, calibration, confidence terciles, categoriser, LLM evaluation, scenario suite and data-quality gates.")
    st.page_link("pages/3_Receipts.py", label="Open Receipts", icon=":material/receipt_long:")

st.subheader("Customers")
st.caption("Pick one in the sidebar.")
for p in client.personas():
    T.render(f'<p style="margin:2px 0"><b>{T.esc(p["display_name"])}</b> <span class="gd-tag gd-tag--code">{T.esc(p["customer_id"])}</span> '
             f'<span class="gd-muted">{T.esc(p["summary"])}</span></p>')

T.footer()
