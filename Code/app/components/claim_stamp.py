"""Claim-Check stamp: 'N of N sentences verified'.

Shows a verified stamp strip; an expander lists each sentence with source
fields. Text is always html.escape()'d before rendering.
"""

import html
import streamlit as st


def render(explanation: dict) -> None:
    """Render the Claim-Check stamp for one opportunity's explanation."""
    if not explanation:
        return

    verified = explanation.get("verified", 0)
    total = explanation.get("total", 0)
    blocked = explanation.get("blocked", 0)
    source = explanation.get("source", "llm")
    sentences = explanation.get("sentences", [])

    is_template = source == "template"
    stamp_label = f"✓ {verified} of {total} sentences verified"
    if blocked:
        stamp_label += f" · {blocked} blocked"

    st.markdown(
        f'<div class="gd-stamp">'
        f'<span aria-hidden="true">🛡</span>'
        f'<div>'
        f'<strong>{html.escape(stamp_label)}</strong>'
        + (f'<span class="gd-tag" style="margin-left:8px;">Standard summary</span>' if is_template else "")
        + f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if sentences:
        with st.expander("See what backs each statement", expanded=False):
            for i, sent in enumerate(sentences, 1):
                text = html.escape(sent.get("text", ""))
                fields = sent.get("fields", [])
                fields_str = ", ".join(f"`{f}`" for f in fields)
                st.markdown(f"**{i}.** {text}")
                if fields_str:
                    st.caption(f"Source fields: {fields_str}")
                if i < len(sentences):
                    st.divider()
