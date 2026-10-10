"""Cockpit page (placeholder)."""

import streamlit as st

import theme
from components.chrome import banner, current_role

st.set_page_config(page_title="GreenProof – Cockpit", layout="wide")
st.markdown(theme.css(), unsafe_allow_html=True)  # the only unsafe_allow_html call

banner()
st.title("Cockpit")
st.caption(f"Viewing as: {current_role()}")
st.info("Portfolio tiles, funnel and drill-down will appear here.", icon=":material/construction:")
