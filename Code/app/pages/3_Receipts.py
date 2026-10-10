"""Receipts page (placeholder)."""

import streamlit as st

import theme
from components.chrome import banner, current_role

st.set_page_config(page_title="GreenProof – Receipts", layout="wide")
st.markdown(theme.css(), unsafe_allow_html=True)  # the only unsafe_allow_html call

banner()
st.title("Receipts")
st.caption(f"Viewing as: {current_role()}")
st.info("Baselines, calibration and evaluation results will appear here.", icon=":material/construction:")
