"""Cockpit: portfolio -> opportunity -> customer -> evidence -> impact -> action.

CO2e, energy, paper and digital adoption are four separate tiles, never summed or netted.
Segments under 10 customers are suppressed. Analysts and auditors see aggregates only.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import client
import theme as T
import importlib
from components import shell
importlib.reload(shell)

T.setup("Cockpit", dark=True)
shell.auth_gate()
persona = shell.sidebar()
shell.gate("cockpit", "the Cockpit")

P = client.portfolio(client.role())
NAMES = {"GP01": "EV Finance", "GP02": "Green Home", "GP03": "Solar Finance", "GP04": "Paperless"}
D = T.DARK


def table(df: pd.DataFrame) -> None:
    """HTML table (follows the dark theme; st.dataframe draws on a light canvas)."""
    st.table(df.set_index(df.columns[0]))


STATUS_COLOUR = {"RECOMMEND": T.C["verdant"], "SOFT_SURFACE": T.C["slate_sage"], "ABSTAIN": T.C["slate_sage"], "REVIEW": T.C["slate_sage"]}

st.markdown("## Portfolio cockpit")

# ------------------------------------------------------------ four separate families, never summed
st.caption(f'Data as of {P["as_of"]} · {P["customers_analysed"]:,} customers analysed · {P["complete_data_share"]:.0%} with complete data · '
           f'{P["abstained_share"]:.1%} abstained (not enough data)')
k = P["tiles"]
for col, key in zip(st.columns(4), ["co2", "energy", "paper", "digital"]):
    with col:
        T.render(T.kpi(k[key]))
st.caption("Four metrics, reported separately and never summed. Realised CO₂e is not yet measurable: it needs post-adoption data.")

# ------------------------------------------------------------ Level 2: funnel + quadrant
product = st.segmented_control("Product", list(NAMES), format_func=lambda g: NAMES[g], default="GP01", key="cockpit-product") or "GP01"
fam_colour = T.C["aqua"] if product == "GP04" else T.C["verdant"]
unit = "sheets a year" if product == "GP04" else "kg CO₂e a year"

t_over, t_seg, t_cust, t_gov = st.tabs(["Overview", "Segments and trend", "Customers", "Governance"])

with t_over:
    c_f, c_q = st.columns([2, 3], gap="large")
    with c_f, st.container(key="gd-panel-funnel"):
        st.markdown(f"#### Opportunity funnel · {NAMES[product]}")
        f = P["funnel"][product]
        fig = go.Figure(go.Bar(x=[v for _, v in f], y=[s for s, _ in f], orientation="h", marker_color=fam_colour,
                               text=[f"{v:,}" for _, v in f], textposition="outside", hovertemplate="%{y}: %{x:,}<extra></extra>"))
        fig.update_layout(height=300, margin=dict(l=0, r=40, t=10, b=0), yaxis=dict(autorange="reversed"), xaxis=dict(visible=False, range=[0, f[0][1] * 1.25]),
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter", color=D["text"]))
        st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})
        drops = [f"{f[i][0]} → {f[i + 1][0]}: −{f[i][1] - f[i + 1][1]:,}" for i in range(len(f) - 1)]
        st.caption(" · ".join(drops))

    cohorts = P["quadrant"][product]
    shown = [c for c in cohorts if not c.get("suppressed")]
    hidden = len(cohorts) - len(shown)
    with c_q, st.container(key="gd-panel-quadrant"):
        st.markdown(f"#### Opportunity quadrant · {NAMES[product]}")
        st.caption(f"Propensity × estimated impact per customer, {P['customers_analysed']:,} customers. Circle size = cohort size, opacity = confidence, whisker = low to high range.")
        max_y = max((c.get("high") or c.get("central") or 1) for c in shown) * 1.15
        fig = go.Figure()
        for c in shown:
            low_conf = c["conf"] < 0.6
            fig.add_trace(go.Scatter(
                x=[c["propensity"]], y=[c.get("central") or 0], mode="markers", name=c["name"], customdata=[c["id"]],
                error_y=dict(type="data", symmetric=False, array=[(c.get("high") or 0) - (c.get("central") or 0)],
                             arrayminus=[(c.get("central") or 0) - (c.get("low") or 0)], color=STATUS_COLOUR.get(c["status"], fam_colour), thickness=2, width=0),
                marker=dict(size=max(12, min(46, c["n"] ** 0.5 * 1.9)), color=fam_colour if c["status"] == "RECOMMEND" else T.C["slate_sage"],
                            opacity=0.35 + 0.6 * c["conf"], line=dict(color=T.C["amber"] if low_conf else D["background"], width=3 if low_conf else 1)),
                hovertemplate=f"<b>{c['name']}</b><br>{c['n']:,} customers<br>Propensity %{{x:.2f}}<br>Confidence {c['conf']:.2f}<br>"
                              + (f"Estimate {c['low']:,}–{c['high']:,} {unit}" if c.get("high") else "Impact not estimated") + "<extra></extra>"))
        fig.add_vline(x=0.5, line_dash="dot", line_color=D["grid"])
        fig.add_hline(y=max_y / 2, line_dash="dot", line_color=D["grid"])
        for x, y, txt, anchor in ((0.02, max_y * 0.97, "EDUCATE, NO HARD SELL", "left"), (0.98, max_y * 0.97, "RM CALL LIST", "right"),
                                  (0.98, max_y * 0.04, "DIGITAL NUDGE", "right"), (0.02, max_y * 0.04, "LOW PRIORITY", "left")):
            fig.add_annotation(x=x, y=y, text=txt, showarrow=False, xanchor=anchor, font=dict(family="JetBrains Mono", size=10, color=D["muted"]))
        fig.update_layout(height=380, showlegend=False, margin=dict(l=64, r=10, t=10, b=48), plot_bgcolor=D["plot"], paper_bgcolor="rgba(0,0,0,0)",
                          xaxis=dict(title="Propensity (low to high)", range=[0, 1], gridcolor=D["grid"], zeroline=False),
                          yaxis=dict(title=f"Estimated impact ({unit})", range=[0, max_y], gridcolor=D["grid"], zeroline=False),
                          font=dict(family="Inter", color=D["text"]))
        event = st.plotly_chart(fig, width="stretch", theme=None, on_select="rerun", selection_mode="points", key=f"quad-{product}", config={"displayModeBar": False})
        if hidden:
            st.caption(f"{hidden} cohort hidden to protect privacy (fewer than 10 customers). Dotted amber outline = low confidence: enrich data.")
        pts = (event or {}).get("selection", {}).get("points", []) if isinstance(event, dict) else getattr(getattr(event, "selection", None), "points", [])
        picked_id = pts[0]["customdata"][0] if pts and pts[0].get("customdata") else None
        names = {c["id"]: c["name"] for c in shown}
        picked_id = st.selectbox("Cohort", list(names), index=list(names).index(picked_id) if picked_id in names else 0, format_func=names.get, key=f"cohort-{product}")
        c = next(x for x in shown if x["id"] == picked_id)
        T.render(f'<div class="gd-card gd-card--flat"><b>{T.esc(c["name"])}</b> · {c["n"]:,} customers · Propensity {c["propensity"]:.2f} · '
                 f'Eligibility {c["eligPass"]:.0%} passed, {c["eligNeeds"]:.0%} need verification · Impact quality {T.esc((c.get("quality") or "not estimated").lower())}'
                 + (f' · Est. {c["low"]:,}–{c["high"]:,} {unit} per customer' if c.get("high") else "")
                 + '<div class="gd-row" style="margin-top:8px">' + "".join(f'<span class="gd-tag gd-tag--code">{T.esc(r)}</span>' for r in c.get("reasons", [])) + "</div></div>")

with t_seg:
    # ------------------------------------------------------------ segments, regions, trends
    s1, s2 = st.columns(2, gap="large")
    with s1:
        st.markdown("#### Segments")
        seg = pd.DataFrame([{"Segment": s["name"], "Customers": "<10" if s.get("suppressed") else f'{s["customers"]:,}',
                             "Recommend rate": "Hidden" if s.get("suppressed") else f'{s["recommend"]:.0%}',
                             "Abstain rate": "Hidden" if s.get("suppressed") else f'{s["abstain"]:.0%}',
                             "Impact (estimate)": "Hidden" if s.get("suppressed") else s["impact"]} for s in P["segments"]])
        table(seg)
    with s2:
        st.markdown("#### Regions")
        reg = pd.DataFrame([{"Region": r["name"], "Customers": r["customers"], "Recommend rate": f'{r["recommend"]:.0%}', "Abstain rate": f'{r["abstain"]:.0%}'} for r in P["regions"]])
        table(reg)

    st.markdown(f"#### Trend · {NAMES[product]}")
    tr = P["trends"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tr["months"], y=tr["surfaced"][product], name="Surfaced", line=dict(color=T.C["slate_sage"], width=2)))
    fig.add_trace(go.Scatter(x=tr["months"], y=tr["takenUp"][product], name="Taken up", line=dict(color=fam_colour, width=2)))
    fig.update_layout(height=260, margin=dict(l=48, r=8, t=10, b=32), plot_bgcolor=D["plot"], paper_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(gridcolor=D["grid"]), yaxis=dict(gridcolor=D["grid"], zeroline=False),
                      font=dict(family="Inter", color=D["text"]), legend=dict(orientation="h"))
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})

with t_cust:
    # ------------------------------------------------------------ Levels 3–5: customer drill-down
    if not shell.can("customer_level"):
        T.banner("Your role sees aggregates only. Customer-level views are limited to Relationship Managers (own book) and Evaluators.", "info")
    else:
        book = [r for r in P["rm_book"] if r["persona"]] if client.role() == "EVALUATOR" else P["rm_book"]
        table(pd.DataFrame([{"Customer": r["name"], "Key": r["key"], "Region": r["region"], "Product": NAMES[r["product"]], "Status": r["status"],
                                    "Likelihood": r["likelihood"], "Eligibility": r["eligibility"], "Impact quality": r["quality"] or "Not estimated",
                                    "Next step": r["next"]} for r in book]))
        with_pack = [r for r in book if r["persona"]]
        pick = st.selectbox("Open customer", [r["key"] for r in with_pack], format_func=lambda k: next(f'{r["name"]} · {k}' for r in with_pack if r["key"] == k))
        row = next(r for r in with_pack if r["key"] == pick)
        cid = next(p["customer_id"] for p in client.personas() if p["persona_key"] == row["persona"])
        doc = client.opportunities(cid, client.role())
        gp = st.segmented_control("Opportunity", list(NAMES), format_func=lambda g: NAMES[g], default=row["product"], key="drill-gp") or row["product"]
        opp = next(o for o in doc["opportunities"] if o["opportunity_id"] == gp)
        T.render(f'<div class="gd-crumbs">Portfolio / {NAMES[gp]} / <b>{T.esc(row["name"])}</b> / Evidence / Impact / Action</div>')

        t360, tev, tim, tact = st.tabs(["Customer 360", "Evidence", "Impact", "Action"])
        with t360:
            st.markdown(f"**{T.esc(doc['display_name'])}** · {T.esc(doc['customer_key'])} · {T.esc(doc['region'])}")
            table(pd.DataFrame([{"Source": f["source"], "As of": f["asOf"], "Kind": f["kind"]} for f in doc["data_freshness"]]))
            table(pd.DataFrame([{"Product held": p["name"], "Since": p["since"], "Status": p["status"]} for p in doc["products_held"]]))
            for o in doc["opportunities"]:
                T.render(f'<div style="margin-top:8px"><b>{T.esc(o["opportunity_name"])}</b> {T.status_badge(o["status"])}</div>' + T.verdicts(o))
        with tev:
            T.render(T.evidence(opp))
            c = opp["confidence"]
            st.caption(f"Confidence {c['overall']:.2f} = completeness {c['completeness']:.2f} · recency {c['recency']:.2f} · stability {c['stability']:.2f} · in-distribution {c['in_distribution']:.2f}")
        with tim:
            T.render(T.impact_block(opp) or '<p class="gd-muted">No impact for this status.</p>')
            im = opp["impact"]
            if im.get("formula"):
                st.caption(f"Formula: {im['formula']} · Baseline: {im.get('baseline')} · Horizon: {im.get('horizon')} · Factors: {', '.join(im.get('factor_refs') or [])}")
        with tact:
            el = T.ELIGIBILITY[opp["eligibility"]["result"]][1]
            brief = (f"{doc['display_name']} · {NAMES[gp]}: status {opp['status'].replace('_', ' ').lower()}, likelihood {opp['likelihood_band'].lower()}, "
                     f"eligibility {el.lower()}, impact quality {(opp['impact'].get('quality') or 'not estimated').lower()}. "
                     f"Suggested next step: {row['next'] if row['product'] == gp else 'review the card with the customer'}. Not a credit decision.")
            T.render(f'<div class="gd-card gd-card--flat"><span class="gd-tag">RM brief · standard summary</span><p style="margin:8px 0 0">{T.esc(brief)}</p></div>')
            if st.button("Add to call list", type="primary", disabled=opp["status"] in ("RULED_OUT",)):
                st.toast("Added to your call list. Logged with a purpose reason.")

with t_gov:
    # ------------------------------------------------------------ governance strip
    g = P["governance"]
    a, b, c, d = st.columns(4)
    a.metric("Abstention rate", f'{g["abstention_rate"]:.1%}')
    b.metric("Sentences verified", f'{g["claims_verified"]:,}')
    c.metric("Claims blocked", f'{st.session_state.get("blocked_total", g["claims_blocked"]):,}')
    d.metric("Audit chain", "Verified" if g["chain"]["status"] == "ok" else "BROKEN", help=f'{g["chain"]["rows"]:,} rows · head {g["chain"]["head"]}')
    if shell.can("governance"):
        with st.expander("Fairness: recommendation and abstention rates by income and age band"):
            for name, rows in (("Income band", g["fairness"]["income"]), ("Age band", g["fairness"]["age"])):
                table(pd.DataFrame([{name: r["band"], "Customers": r["customers"], "Recommend rate": f'{r["recommend"]:.0%}',
                                            "Abstain rate": f'{r["abstain"]:.0%}', "Brier": f'{r["brier"]:.3f}'} for r in rows]))
            st.caption("Age, income and fine-grained postcode are not model features. They are used here only to audit fairness, in aggregate.")

T.footer()
