"""Receipts: every claim we make, checkable on one page."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import client
import theme as T
from components import shell

T.setup("Receipts")
persona = shell.sidebar()
shell.gate("receipts", "Receipts")

E = client.eval_summary(client.role())
st.markdown("## Receipts")
# Shown until the eval payload says it was measured ("measured": true).
if not E.get("measured"):
    T.banner("Illustrative figures, not measured results. They show what this page reports; they do not come from an evaluation run.", "warn")

LAYOUT = dict(plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter", color=T.C["ink_soft"]), margin=dict(l=0, r=0, t=10, b=0))

# --------------------------------------------------------------- models vs baselines
st.markdown("### Propensity models against two baselines")
rows = []
for m in E["models"]:
    for name, k in (("LightGBM, calibrated", "lgbm"), ("Logistic regression", "logreg"), ("Rule heuristic", "rule")):
        v = m[k]
        rows.append({"Product": m["product"], "Model": name, "ROC-AUC": v["auc"], "PR-AUC": v["prauc"],
                     "Brier": "–" if v["brier"] is None else f'{v["brier"]:.3f}', "Lift at top 10%": f'{v["lift"]:.1f}×'})
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("#### Calibration curve")
    pts = E["calibration"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Perfect calibration", line=dict(color=T.C["slate_sage"], dash="dot")))
    fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines+markers", name="Calibrated LightGBM", line=dict(color=T.C["verdant"], width=2)))
    fig.update_layout(height=320, xaxis_title="Predicted propensity", yaxis_title="Observed take-up", legend=dict(orientation="h", y=1.12), **LAYOUT)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
with c2:
    st.markdown("#### Confidence is validated")
    st.caption("Brier score (lower is better) should fall as confidence rises.")
    t = E["terciles"]
    fig = go.Figure(go.Bar(x=[r["band"] for r in t], y=[r["brier"] for r in t], marker_color=T.C["aqua"], text=[f'{r["brier"]:.3f}' for r in t], textposition="outside"))
    fig.update_layout(height=320, yaxis_title="Brier score", **LAYOUT)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

# --------------------------------------------------------------- categoriser
st.markdown("### Transaction categoriser (merchants unseen in training)")
cat = E["categoriser"]
a, b = st.columns(2)
a.metric("Macro-F1", f'{cat["macroF1"]:.2f}', delta=f'{cat["macroF1"] - cat["rulesOnlyF1"]:+.2f} vs rules only')
b.metric("Rules-only baseline", f'{cat["rulesOnlyF1"]:.2f}')
z = [[v / max(1, sum(r)) for v in r] for r in cat["matrix"]]
fig = go.Figure(go.Heatmap(z=z, x=cat["labels"], y=cat["labels"], text=cat["matrix"], texttemplate="%{text}",
                           colorscale=[[0, "#FFFFFF"], [1, T.C["canopy"]]], showscale=False, hovertemplate="True %{y} → predicted %{x}: %{text}<extra></extra>"))
fig.update_layout(height=420, xaxis_title="Predicted", yaxis_title="True category", yaxis=dict(autorange="reversed"), **LAYOUT)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

# --------------------------------------------------------------- LLM evaluation
st.markdown("### LLM explanations: governed pipeline against a naive prompt")
st.caption("150-case evaluation set: 8 personas × perturbations, 20 adversarial sentences and prompt-injection cases.")
st.dataframe(pd.DataFrame([{"Metric": r["metric"], "greendash (governed)": r["governed"], "Naive prompt": r["naive"]} for r in E["llm"]]),
             hide_index=True, width="stretch")

# --------------------------------------------------------------- scenario suite, carbon tests, gates
s1, s2 = st.columns(2, gap="large")
with s1:
    sc = E["scenarios"]
    st.markdown(f"### Scenario suite · {sc['passed']}/{sc['total']} passed")
    st.dataframe(pd.DataFrame([{"Organiser scenario type": g["name"], "Passed": f'{g["passed"]}/{g["total"]}'} for g in sc["groups"]]),
                 hide_index=True, width="stretch")
    ct = E["carbonTests"]
    st.metric("Carbon engine hand-calculation tests", f'{ct["passed"]}/{ct["total"]}')
with s2:
    st.markdown("### Data-quality gates")
    st.dataframe(pd.DataFrame([{"Gate": g["gate"], "Result": g["result"], "Pass": "✓" if g["ok"] else "✗"} for g in E["gates"]]),
                 hide_index=True, width="stretch")

st.metric("Claims blocked so far", f'{st.session_state.get("blocked_total", client.portfolio(client.role())["governance"]["claims_blocked"]):,}')
T.banner("Labels are synthetic, so these metrics show the pipeline is honest (leak-free, calibrated, beats baselines), not real-world accuracy.", "info")
T.footer()
