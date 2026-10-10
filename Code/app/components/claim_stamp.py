"""Claim-Check stamp aligned to real contracts.py Explanation shape.

Explanation fields (frozen by Akshit):
  explanation["sentences"]         list of Sentence
  explanation["source"]            "llm" | "template"
  explanation["claimcheck_status"] "PASS" | "FALLBACK"

Sentence fields:
  sentence["text"]
  sentence["fields"]   list[str]
  sentence["check"]    "PASS" | "BLOCKED" | "TEMPLATE"
"""

import html
import streamlit as st


def render(explanation: dict | None) -> None:
    if not explanation:
        return

    sentences      = explanation.get("sentences", [])
    source         = explanation.get("source", "template")
    cc_status      = explanation.get("claimcheck_status", "PASS")

    passed  = sum(1 for s in sentences if s.get("check") == "PASS")
    blocked = sum(1 for s in sentences if s.get("check") == "BLOCKED")
    total   = len(sentences)
    is_template = source == "template"

    stamp_label = f"✓ {passed} of {total} statements verified"
    if blocked:
        stamp_label += f" · {blocked} blocked"

    status_color = "#0F7A55" if cc_status == "PASS" else "#B4232A"

    st.markdown(
        f'<div style="background:#DDF8EA;border:1px solid #19C37D;border-radius:10px;'
        f'padding:10px 14px;display:flex;align-items:center;gap:10px;margin:12px 0;">'
        f'<span style="font-size:18px;">🛡</span>'
        f'<div>'
        f'<strong style="color:{status_color};font-size:13px;">{html.escape(stamp_label)}</strong>'
        + (f'<span style="margin-left:8px;font-size:10px;font-family:monospace;'
           f'background:#E3EFE9;padding:2px 6px;border-radius:4px;">Standard summary</span>'
           if is_template else "")
        + f"</div></div>",
        unsafe_allow_html=True,
    )

    if sentences:
        with st.expander("See what backs each statement", expanded=False):
            for i, sent in enumerate(sentences, 1):
                check = sent.get("check", "PASS")
                icon  = "✓" if check == "PASS" else ("⚠" if check == "TEMPLATE" else "✗")
                color = "#0F7A55" if check == "PASS" else ("#F5B53D" if check == "TEMPLATE" else "#B4232A")
                st.markdown(
                    f'<span style="color:{color};font-weight:700;">{icon}</span> '
                    f'{html.escape(sent.get("text",""))}',
                    unsafe_allow_html=True,
                )
                fields = sent.get("fields", [])
                if fields:
                    st.caption("Source fields: " + ", ".join(f"`{f}`" for f in fields))
                if i < len(sentences):
                    st.divider()
