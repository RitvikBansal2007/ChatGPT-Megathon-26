"""Proof Card: the recommendation that carries its own receipt.

Block order (brand guidelines 10.2): status row, headline, why-now, impact, three verdicts,
Confidence Ladder, evidence, Claim-Check stamp, actions, disclaimer, feedback.
Designed states: RECOMMEND, SOFT_SURFACE, ABSTAIN, REVIEW, RULED_OUT.
"""
from __future__ import annotations

import streamlit as st

import client
import theme as T


def _confidence_html(c: dict) -> str:
    rows = [("Data completeness", c["completeness"]), ("Data recency", c["recency"]),
            ("Model stability", c["stability"]), ("In-distribution", c["in_distribution"]), ("How sure we are", c["overall"])]
    out = ""
    for label, v in rows:
        bold = "font-weight:700;" if label == "How sure we are" else ""
        colour = T.C["ink_soft"] if label == "How sure we are" else T.C["aqua"]
        out += (f'<div style="display:grid;grid-template-columns:150px 1fr 44px;gap:12px;align-items:center;margin:6px 0;{bold}font-size:13px">'
                f'<span>{label}</span><span style="height:8px;border-radius:999px;background:rgba(11,31,24,.12);overflow:hidden">'
                f'<i style="display:block;height:100%;width:{v * 100:.0f}%;background:{colour};border-radius:999px"></i></span>'
                f'<span style="text-align:right;font-feature-settings:\'tnum\' 1">{v:.2f}</span></div>')
    return out


def _ladder(opp: dict, key: str) -> None:
    lad = opp.get("ladder")
    if not lad:
        return
    inp = lad["input"]
    if inp["type"] == "number":
        miles = st.number_input("Yearly mileage (miles a year)", min_value=0, max_value=100_000, step=100, value=None,
                                placeholder=inp.get("placeholder", ""), key=f"{key}-miles",
                                help="Your MOT certificate shows recent mileage.")
        if st.button("Update my estimate", key=f"{key}-miles-go", type="primary" if opp["status"] == "ABSTAIN" else "secondary"):
            if not miles:
                st.error("Enter a yearly mileage between 1 and 100,000 miles.")
            else:
                r = client.ladder_mileage(int(miles))
                T.render(f'<div class="gd-impact" style="background:#fff"><div class="gd-impact__l"><span>Your updated estimate</span><span class="gd-tag">Estimate</span></div>'
                         f'<p class="gd-impact__kpi">{T.num(r["low"])} to {T.num(r["high"])} <small>kg CO₂e a year</small></p>'
                         f'<p class="gd-muted" style="margin:0">{T.esc(r["bills"])}</p>{T.range_bar(r["low"], r["central"], r["high"], T.C["verdant"])}'
                         f'<p class="gd-small gd-muted" style="margin:8px 0 0">Impact quality is now high. Estimate, not a guarantee.</p></div>')
                st.caption("Indicative figure. The carbon engine confirms it once your mileage is saved.")
    elif inp["type"] == "choice":
        choice = st.radio(lad.get("question") or lad["prompt"], inp["options"], index=None, key=f"{key}-choice")
        if choice is not None:
            unsure = choice == inp["options"][-1] or "north" in choice.lower()
            res = opp.get("ladder_result")
            if unsure or not res:
                T.banner('We\'ll keep this as "Need one thing" for now. A recent bill or a quick installer check would let us estimate it.', "warn")
            else:
                T.render(f'<div class="gd-impact" style="background:#fff"><div class="gd-impact__l"><span>Your estimate</span><span class="gd-tag">Estimate</span></div>'
                         f'<p class="gd-impact__kpi">{T.num(res["low"])} to {T.num(res["high"])} <small>kg CO₂e a year</small></p>'
                         f'<p class="gd-muted" style="margin:0">{T.esc(res["bills"])}</p>{T.range_bar(res["low"], res["central"], res["high"], T.C["verdant"])}'
                         f'<p class="gd-small gd-muted" style="margin:8px 0 0">Impact quality is now {T.esc(res["quality"].lower())}.</p></div>')
    else:
        st.file_uploader("Upload a recent bill (PDF or photo)", type=["pdf", "png", "jpg"], key=f"{key}-upload",
                         help="We read the yearly kWh only. The file is encrypted and never sent to the AI.")


def render(doc: dict, opp: dict, key: str = "card") -> None:
    status = opp["status"]
    with st.container(key=f"gd-proof-{key}"):
        T.render(f'<div class="gd-accent" style="background:{T.accent_for(status)}"></div>{T.card_header(opp)}')

        if status == "RULED_OUT":
            T.render(T.why_not(opp) + T.verdicts(opp))
            st.caption("No action on this card. Products your data rules out are never recommended.")
        else:
            T.render(T.impact_block(opp))
            if status == "REVIEW" and opp.get("review"):
                rv = opp["review"]
                T.render(f'<p style="margin:4px 0">{T.esc(rv["message"])}</p>')
                ans = st.radio(rv["question"], rv["options"], index=None, key=f"{key}-review")
                c1, c2 = st.columns(2)
                if c1.button("Confirm", key=f"{key}-review-go", type="primary", disabled=ans is None):
                    st.toast("Thanks. We'll re-run this card with your answer.")
                if c2.button("Skip for now", key=f"{key}-review-skip"):
                    st.toast("Skipped. The impact estimate stays hidden for now.")
            T.render(T.verdicts(opp))
            if opp.get("ladder"):
                if status == "ABSTAIN":
                    T.render(f'<div class="gd-ladder">{T.icon("gauge", 18)}<span>{T.esc(opp["ladder"]["prompt"])}</span></div>')
                    _ladder(opp, key)
                else:
                    with st.expander(opp["ladder"]["prompt"]):
                        _ladder(opp, key)

            T.render(T.claim_stamp(opp))
            im = opp["impact"]
            with st.expander("See the receipt"):
                labels = ["Why you're seeing this"] + (["How we worked this out"] if im["status"] == "ESTIMATED" else []) + ["How sure we are", "What backs each sentence"]
                parts = dict(zip(labels, st.tabs(labels)))
                with parts["Why you're seeing this"]:
                    T.render(T.evidence(opp))
                if "How we worked this out" in parts:
                    with parts["How we worked this out"]:
                        rows = [("Formula", im.get("formula")), ("Baseline", im.get("baseline")), ("Time horizon", im.get("horizon")),
                                ("Factor source", ", ".join(im.get("factor_refs") or []))]
                        T.render("".join(f'<p style="margin:4px 0"><span class="gd-muted">{k}:</span> <b>{T.esc(v)}</b></p>' for k, v in rows if v))
                        st.caption("Estimate, not a guarantee. Calculated by the carbon engine, never by the AI.")
                with parts["How sure we are"]:
                    T.render(_confidence_html(opp["confidence"]))
                    st.caption("Likelihood is not creditworthiness, and it is not a credit decision.")
                with parts["What backs each sentence"]:
                    for sent in opp["explanation"]["sentences"]:
                        tags = " ".join(f'<span class="gd-tag gd-tag--code">{T.esc(f)}</span>' for f in sent["fields"])
                        T.render(f'<div style="padding:8px 0;border-top:1px solid var(--divider)">✓ {T.esc(sent["text"])}<div style="margin-top:4px">{tags}</div></div>')

            na = opp["next_action"]
            if status in ("RECOMMEND",) and na.get("label"):
                if st.button(na["label"], key=f"{key}-primary", type="primary", width="stretch"):
                    st.toast("Opening the next step. Nothing is submitted without your confirmation.")
                if na.get("secondary") and st.button(na["secondary"], key=f"{key}-secondary", width="stretch"):
                    st.toast("Suitability check started: 3 to 5 questions.")
            elif status == "SOFT_SURFACE":
                st.button("Learn more", key=f"{key}-learn", width="stretch")
        T.render('<p class="gd-disc" style="margin:8px 0 4px">Not a credit decision · Likelihood is not creditworthiness</p>')
        c_help, c_fb = st.columns(2)
        if c_help.button("Talk to a person", key=f"{key}-human", type="tertiary", icon=":material/chat:"):
            st.toast("A person will call you back. Pick a time on the Help page.")
        if status != "RULED_OUT":
            with c_fb.popover("Not quite right?", width="stretch"):
                st.caption("This changes when we show the card, never its numbers.")
                for label, k in (("Not relevant", "nr"), ("This is wrong", "wr"), ("Remind me later", "rm")):
                    if st.button(label, key=f"{key}-fb-{k}", width="stretch"):
                        st.toast("Thanks. We've noted that.")
