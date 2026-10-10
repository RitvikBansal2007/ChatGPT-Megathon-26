"""Cockpit — portfolio dashboard for Relationship Managers and Analysts.

Four SEPARATE metric tiles (never summed), funnel, scatter quadrant,
segment table, and a governance strip. All data from client.get_portfolio().
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

import theme
import client
from components.chrome import banner, current_role

st.set_page_config(page_title="GreenProof – Cockpit", layout="wide")
st.markdown(theme.css(), unsafe_allow_html=True)

banner()
st.title("Cockpit")
role = current_role()
st.caption(f"Viewing as: {role}")

# ── Load data ────────────────────────────────────────────────────────────────
with st.spinner("Loading portfolio…"):
    try:
        portfolio = client.get_portfolio()
    except Exception as exc:
        st.error(f"Could not load portfolio data: {exc}", icon=":material/error:")
        st.stop()

metrics = portfolio.get("metrics", {})
funnel  = portfolio.get("funnel", [])
scatter = portfolio.get("scatter", [])
segments = portfolio.get("segments", [])
gov = portfolio.get("governance", {})
as_of = portfolio.get("as_of", "—")

st.caption(f"Data as of {as_of} · Synthetic data · Estimates only")

# ── 1. Four SEPARATE metric tiles (never summed) ─────────────────────────────
st.subheader("Portfolio metrics")
m_cols = st.columns(4, gap="small")
_M_CONFIG = [
    ("co2e_kg",     "CO₂e",              "kg CO₂e", theme.METRICS["CO2E"]),
    ("energy_kwh",  "Energy",            "kWh",     theme.METRICS["ENERGY"]),
    ("paper_sheets","Paper sheets avoided","sheets", theme.METRICS["PAPER"]),
    ("digital_pct", "Digital adoption",  "%",       theme.METRICS["DIGITAL"]),
]
for col, (key, label, unit, m_token) in zip(m_cols, _M_CONFIG):
    m = metrics.get(key, {})
    val = m.get("value", "—")
    note = m.get("note", "Estimated")
    with col:
        st.markdown(
            f'<div class="gd-metric gd-metric--{key.replace("_","").replace("kwh","energy").replace("pct","digital")}" '
            f'style="border-left-color:{m_token["chart"]};">'
            f'<div class="gd-tag" style="color:{m_token["text"]};">{label}</div>'
            f'<div class="gd-metric-value" style="color:{m_token["text"]};">'
            f'{val:,}{"%" if key=="digital_pct" else ""}</div>'
            f'<div class="gd-tag" style="margin-top:4px;">{note}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.divider()

# ── 2. Funnel ────────────────────────────────────────────────────────────────
col_funnel, col_scatter = st.columns([1, 2], gap="medium")
with col_funnel:
    st.subheader("Opportunity funnel")
    if funnel:
        fig_funnel = go.Figure(go.Funnel(
            y=[f["stage"] for f in funnel],
            x=[f["count"] for f in funnel],
            textinfo="value+percent initial",
            marker_color=theme.METRICS["CO2E"]["chart"],
        ))
        fig_funnel.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_family="Inter, system-ui, sans-serif",
            margin=dict(l=0, r=0, t=0, b=0),
            height=320,
        )
        st.plotly_chart(fig_funnel, use_container_width=True, config={"displayModeBar": False})

# ── 3. Scatter quadrant ──────────────────────────────────────────────────────
with col_scatter:
    st.subheader("Opportunity quadrant")
    if scatter:
        _PRODUCT_COLORS = {
            "GP01": theme.METRICS["CO2E"]["chart"],
            "GP02": theme.METRICS["ENERGY"]["chart"],
            "GP03": theme.METRICS["PAPER"]["chart"],
            "GP04": theme.METRICS["DIGITAL"]["chart"],
        }
        fig_scatter = go.Figure()
        for row in scatter:
            fig_scatter.add_trace(go.Scatter(
                x=[row["propensity"]],
                y=[row["impact"]],
                mode="markers",
                marker=dict(
                    size=max(10, row.get("size", 100) / 30),
                    color=_PRODUCT_COLORS.get(row["product"], "#888"),
                    opacity=0.85,
                    line=dict(width=1, color="white"),
                ),
                name=row["product"],
                hovertemplate=(
                    f"<b>{row.get('product','')}</b><br>"
                    f"Propensity: {row['propensity']:.0%}<br>"
                    f"Impact: {row['impact']:,} kg CO₂e<br>"
                    f"Confidence: {row.get('confidence', 0):.0%}<br>"
                    f"Status: {row.get('status','')}"
                    "<extra></extra>"
                ),
            ))

        # Zone annotation labels
        for txt, x, y in [
            ("RM call list", 0.85, 1650),
            ("Get more data", 0.15, 1650),
            ("Digital nudge", 0.85, 250),
            ("Educate", 0.15, 250),
        ]:
            fig_scatter.add_annotation(
                x=x, y=y, text=txt, showarrow=False,
                font=dict(size=10, color="#6B8A7C", family="JetBrains Mono, monospace"),
                opacity=0.7,
            )
        # Centre cross lines
        fig_scatter.add_hline(y=800, line_dash="dot", line_color="#6B8A7C", line_width=1, opacity=0.4)
        fig_scatter.add_vline(x=0.5, line_dash="dot", line_color="#6B8A7C", line_width=1, opacity=0.4)
        fig_scatter.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(241,248,244,0.5)",
            xaxis_title="Propensity →", yaxis_title="Estimated impact (kg CO₂e) →",
            xaxis=dict(range=[0, 1], tickformat=".0%", gridcolor="rgba(11,31,24,0.06)"),
            yaxis=dict(gridcolor="rgba(11,31,24,0.06)"),
            font_family="Inter, system-ui, sans-serif",
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            height=320,
        )
        st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})

st.divider()

# ── 4. Segment table (k-anonymity: <10 shown as "<10") ──────────────────────
st.subheader("Segment breakdown")
st.caption("Groups with fewer than 10 customers are shown as '<10' to protect privacy.")
if segments:
    import pandas as pd
    df = pd.DataFrame(segments).set_index("region")
    # Ensure <10 strings are preserved
    st.dataframe(df, use_container_width=True)

st.divider()

# ── 5. Governance strip ──────────────────────────────────────────────────────
st.subheader("Governance")
g_cols = st.columns(4, gap="small")
with g_cols[0]:
    st.metric("Abstention rate", f"{gov.get('abstention_rate', 0):.0%}")
with g_cols[1]:
    st.metric("Claims blocked", gov.get("claims_blocked", 0))
with g_cols[2]:
    st.metric("Recommendation rate", f"{gov.get('recommendation_rate', {}).get('all', 0):.0%}")
with g_cols[3]:
    audit_ok = gov.get("audit_chain_ok", False)
    if audit_ok:
        st.success("✓ Audit chain intact", icon=":material/verified:")
    else:
        st.error("✗ Audit chain broken — check logs", icon=":material/error:")

st.caption("Not a credit decision. All impact figures are estimates, not guarantees.")
