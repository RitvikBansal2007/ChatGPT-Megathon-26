"""Scenario Lab and the red-team Claim-Check button.

The Lab only edits inputs; it never writes to a verdict. The API recomputes all
three verdicts on the mutated customer and returns before, after, diff, cause,
invariance and elapsed time.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

import client
import theme as T

FIXED_CLAIM = "Switching will save you 4,000 kg a year and you're pre-approved."


def scenario_lab(customer_id: str) -> None:
    with st.container(key="gd-panel-lab"):
        st.caption("Change one input and watch all three verdicts recompute. The Lab edits inputs only, never verdicts.")
        cat = client.mutation_catalogue()
        labels = {m["id"]: m["label"] for m in cat}
        picked = st.pills("Mutation", list(labels), format_func=lambda i: labels[i],
                          selection_mode="multi", default=[], key=f"lab-{customer_id}")
        ids = picked or []
        if not ids:
            st.caption("Pick a mutation, for example Set vehicle to EV.")
            return
        st.caption(next(m["hint"] for m in cat if m["id"] == ids[0]) if len(ids) == 1 else f"{len(ids)} mutations applied together.")
        res = client.scenario(customer_id, ids)
        if "error" in res:
            T.banner(res["error"], "warn")
            return

        changed = [p for p in res["before"] if res["before"][p]["status"] != res["after"][p]["status"]]
        if not changed:
            T.banner("No status changed. Other fields may have moved: see the diff below.", "info")
        names = {"GP01": "EV Finance", "GP02": "Green Home", "GP03": "Solar Finance", "GP04": "Paperless"}
        for p in changed:
            cause = next((d["cause"] for d in res["diff"] if d["product"] == p), "")
            T.render(f'<div style="margin:8px 0"><b>{names[p]}</b><div class="gd-row" style="margin:4px 0">{T.status_badge(res["before"][p]["status"])}'
                     f'<span aria-hidden="true">→</span>{T.status_badge(res["after"][p]["status"])}</div>'
                     f'<code style="font-size:12px">{T.esc(cause)}</code></div>')
        ok = res.get("invariance_ok")
        T.render(f'<div class="gd-row" style="margin:8px 0"><span class="gd-tag" style="color:{"var(--success-tx)" if ok else "var(--error-tx)"}">'
                 f'Invariance {"OK" if ok else "FAILED"}</span><span class="gd-tag">{res.get("elapsed_ms", 0):.1f} ms</span></div>')
        if res["diff"]:
            df = pd.DataFrame(res["diff"]).rename(columns={"product": "Product", "field": "Field", "from": "From", "to": "To", "cause": "Cause"})
            st.dataframe(df, hide_index=True, width="stretch")


def redteam(customer_id: str = "CUST-0001", opportunity_id: str = "GP01") -> None:
    with st.container(key="gd-panel-redteam"):
        st.caption("Inject a fake claim. The verifier checks it against the Evidence Pack before any customer could see it.")
        st.session_state.setdefault("blocked_total", client.portfolio(client.role())["governance"]["claims_blocked"])
        text = st.text_area("Sentence to check", FIXED_CLAIM, key="rt-text", height=80)
        if st.button("Inject fake claim", type="primary", key="rt-go"):
            res = client.claimcheck(customer_id, opportunity_id, text)
            sent = res["sentences"][0]
            if res["verdict"] == "BLOCKED":
                st.session_state["blocked_total"] += 1
                out, i = "", 0
                for v in sorted([v for v in sent["violations"] if v.get("start") is not None], key=lambda v: v["start"]):
                    out += T.esc(text[i:v["start"]]) + f'<mark class="gd-viol">{T.esc(text[v["start"]:v["end"]])}<sup>{T.esc(v["rule"])}</sup></mark>'
                    i = v["end"]
                out += T.esc(text[i:])
                T.render(f'<p style="opacity:.75;text-decoration:line-through;text-decoration-color:var(--error)">{out}</p>')
                T.render('<div class="gd-row">' + "".join(f'<span class="gd-tag" style="color:var(--error-tx)">{T.esc(v["rule"])}: {T.esc(v["span"])}</span>' for v in sent["violations"]) + "</div>")
                T.banner(f'Blocked. Safe template shown instead: "{res.get("fallback_text")}"', "ok")
            else:
                T.banner("Passed: every number and phrase is backed by the Evidence Pack.", "ok")
        st.metric("Claims blocked", f'{st.session_state["blocked_total"]:,}')
