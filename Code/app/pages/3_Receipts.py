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

D = T.chart_colours()
LAYOUT = dict(plot_bgcolor=D["plot"], paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter", color=D["text"]), margin=dict(l=0, r=0, t=10, b=0),
              xaxis=dict(gridcolor=D["grid"]), yaxis=dict(gridcolor=D["grid"]))


def fmt(v, spec="{:.3f}"):
    return "–" if v is None else spec.format(v)


t_models, t_cat, t_llm, t_checks = st.tabs(["Models", "Categoriser", "Explanations", "Scenarios"])

with t_models:
    sp = E["split"]
    if sp:
        st.caption(f"Propensity models against two baselines, scored once on a held-out test set: "
                   f"{sp.get('train', 0):,} customers to train, {sp.get('val', 0):,} to calibrate, {sp.get('test', 0):,} to test.")
    rows = []
    for m in E["models"]:
        for name, k in (("LightGBM, calibrated", "lgbm"), ("Logistic regression", "logreg"), ("Rule heuristic", "rule")):
            v = m[k]
            rows.append({"Product": m["product"], "Model": name, "ROC-AUC": fmt(v["auc"]), "PR-AUC": fmt(v["prauc"]),
                         "Brier": fmt(v["brier"], "{:.4f}"), "Lift at top 10%": fmt(v["lift"], "{:.1f}×")})
    st.table(pd.DataFrame(rows).set_index("Product"))  # HTML table: follows dark mode (st.dataframe draws on a light canvas)
    T.banner("Take-up is rare (3 to 5% of customers), so each test set has only a few dozen positives. "
             "Differences of a few AUC points between LightGBM and logistic regression are within noise.", "info")

    st.markdown("#### Calibration")
    pts = E["calibration"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 0.6], y=[0, 0.6], mode="lines", name="Perfect calibration", line=dict(color=T.C["slate_sage"], dash="dot")))
    fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines+markers", name="Calibrated LightGBM",
                             text=[f"{p[2]:,} predictions" if p[2] else "" for p in pts], hovertemplate="Predicted %{x:.3f}, observed %{y:.3f}<br>%{text}<extra></extra>",
                             line=dict(color=T.C["verdant"], width=2)))
    fig.update_layout(height=320, xaxis_title="Predicted propensity", yaxis_title="Observed take-up", legend=dict(orientation="h", y=1.12), **LAYOUT)
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})

with t_cat:
    st.caption("Transaction categoriser, 5-fold test on merchants unseen in training.")
    cat = E["categoriser"]
    a, b = st.columns(2)
    a.metric("Macro-F1, rules + model", fmt(cat["macroF1"], "{:.2f}"))
    b.metric("Macro-F1, rules only", fmt(cat["rulesOnlyF1"], "{:.2f}"))
    T.banner("Synthetic merchant names follow a small set of patterns, which is why the combined score is this high. Real statements will be harder.", "info")

with t_llm:
    llm = E["llm"]
    st.caption("Every explanation is written from an evidence pack, checked sentence by sentence, and replaced by fixed wording if any check fails.")
    a, b, c, d = st.columns(4)
    a.metric("Explanations tested", f'{llm["evaluated"]:,}')
    b.metric("Written by the model", "–" if llm["written"] is None else f'{llm["written"]:,}')
    c.metric("Faithful to the pack", llm["faithfulness"] or "–")
    d.metric("Canary leakage", llm["canary"] or "–")
    REASONS = {"INPUT_UNSAFE": "Input rejected before the model saw it (planted instruction or unsafe text)",
               "INPUT_PII": "Input rejected: personal data found", "CLAIMCHECK_FAIL": "Model reply failed Claim-Check twice",
               "OUTPUT_SCHEMA": "Model reply was not in the required format", "PROVIDER_ERROR": "Model unavailable or rate-limited",
               "STATUS_FIXED_WORDING": "Ruled out or under review: explained by the rule, by design",
               "NONE": "Fixed wording used"}
    if llm["reasons"]:
        st.markdown("#### When fixed wording was used instead")
        st.table(pd.DataFrame([{"Reason": REASONS.get(k, k.replace("_", " ").capitalize()), "Explanations": v} for k, v in llm["reasons"].items()]).set_index("Reason"))
    if llm["judged_by_model"] is not None:
        st.caption(f'{llm["judged_by_model"]:,} of {llm["evaluated"]:,} were scored by a second model acting as judge; the rest by the rule checks alone.')
    if llm["fallback"] == "100%":
        T.banner("This run had no language-model key, so every explanation came from the checked template. The figures describe the template path only.", "warn")

with t_checks:
    sc = E["scenarios"]
    st.metric("Scenario suite", f'{sc["passed"]}/{sc["total"]} passed')
    st.caption("Each case changes one fact about a customer (sells the car, becomes a renter, data goes stale) and checks the status, rule and impact that should follow.")
    for f in sc.get("failures", []):
        st.markdown(f"- {f}")

T.banner("Labels are synthetic, so these metrics check the pipeline (held-out split, calibration, rule behaviour), not real-world accuracy.", "info")
T.footer()
