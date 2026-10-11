"""Interactive Green Living Profile Quiz component.

Enables interviewers and customers to manually adjust housing, vehicle, and energy inputs
and watch all three verdicts (Propensity, Eligibility, Carbon Impact) recalculate live in <50ms.
"""
from __future__ import annotations

import streamlit as st

import client
import theme as T


def render_profile_quiz(customer_id: str, display_name: str, default_expanded: bool = False) -> None:
    """Render interactive quiz studio to adjust customer inputs and recalculate live."""
    is_custom = f"_custom_pack_{customer_id}" in st.session_state
    label = "📝 Green Living Quiz — Adjust Inputs Live"
    if is_custom:
        label += " (Custom Inputs Active ✅)"

    with st.expander(label, expanded=default_expanded or is_custom):
        st.markdown(
            '<p class="gd-muted" style="margin-bottom:12px;font-size:14px">'
            'Manually adjust this customer\'s living situation, transport, and energy habits. '
            'Clicking <b>Recompute Evidence Pack</b> runs the real feature engineering, calibrated ML models, '
            'eligibility rules, and physics-based carbon engine live in &lt;50ms.'
            '</p>',
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### 🏡 Property & Energy")
            housing = st.radio(
                "Housing Situation",
                ["Homeowner", "Tenant / Renter"],
                index=0,
                key=f"qz-house-{customer_id}",
                help="Renters are legally ineligible for solar and structural heat pump alterations.",
            )
            heating = st.selectbox(
                "Home Heating System",
                ["Gas Central Heating", "Electric / Heat Pump"],
                index=0,
                key=f"qz-heat-{customer_id}",
            )
            gas_kwh = st.slider(
                "Estimated Annual Gas Consumption (kWh)",
                min_value=3000,
                max_value=25000,
                value=12000,
                step=500,
                key=f"qz-gas-{customer_id}",
                help="UK average is approx 11,500 kWh/year.",
            )
            roof = st.selectbox(
                "Roof Suitability for Solar",
                ["Good Sun & Pitch (Suitable)", "Shaded or Flat (Unsuitable)", "Not Inspected (Unknown)"],
                index=0,
                key=f"qz-roof-{customer_id}",
            )
            existing_solar = st.checkbox(
                "Already has solar panels installed",
                value=False,
                key=f"qz-exsolar-{customer_id}",
            )

        with c2:
            st.markdown("##### 🚗 Transport & Banking")
            vehicle = st.selectbox(
                "Primary Vehicle",
                ["Petrol Car", "Diesel Car", "Electric Vehicle (EV)", "Hybrid Car", "No Vehicle"],
                index=0,
                key=f"qz-veh-{customer_id}",
            )
            no_car = vehicle == "No Vehicle"
            mileage = st.slider(
                "Annual Driving Mileage",
                min_value=1000,
                max_value=25000,
                value=10000,
                step=500,
                disabled=no_car,
                key=f"qz-mileage-{customer_id}",
            )
            fuel_spend = st.slider(
                "Estimated Monthly Fuel Spend (£/mo)",
                min_value=0,
                max_value=350,
                value=0 if no_car else 140,
                step=10,
                disabled=no_car,
                key=f"qz-fuel-{customer_id}",
            )
            statement_pref = st.selectbox(
                "Bank Statements & Accessibility",
                ["Paper Statements (12/year)", "Digital Statements Only", "Accessibility Paper Requirement"],
                index=0,
                key=f"qz-stmt-{customer_id}",
                help="Accessibility flag legally prevents promoting paperless switch.",
            )

        b_recompute, b_reset = st.columns([2, 1])
        with b_recompute:
            if st.button("🚀 Recompute Evidence Pack Live", type="primary", use_container_width=True, key=f"qz-btn-run-{customer_id}"):
                # Map inputs to features
                is_homeowner = housing == "Homeowner"
                fuel_map = {
                    "Petrol Car": ("petrol", "PETROL"),
                    "Diesel Car": ("diesel", "DIESEL"),
                    "Electric Vehicle (EV)": ("bev", "BEV"),
                    "Hybrid Car": ("hybrid", "HYBRID"),
                    "No Vehicle": ("none", None),
                }
                f_type, v_f_type = fuel_map[vehicle]
                roof_map = {
                    "Good Sun & Pitch (Suitable)": "suitable",
                    "Shaded or Flat (Unsuitable)": "unsuitable",
                    "Not Inspected (Unknown)": "unknown",
                }

                answers = {
                    "home_owner": is_homeowner,
                    "fuel_type": f_type,
                    "vehicle_fuel_type": v_f_type,
                    "has_ev": vehicle == "Electric Vehicle (EV)",
                    "annual_mileage": None if no_car else float(mileage),
                    "avg_monthly_fuel_gbp": 0.0 if no_car else float(fuel_spend),
                    "gas_kwh": float(gas_kwh) if heating == "Gas Central Heating" else 0.0,
                    "gas_kwh_12m": float(gas_kwh) if heating == "Gas Central Heating" else 0.0,
                    "roof_suitability": roof_map[roof],
                    "existing_solar": existing_solar,
                    "paper_statements_12m": 12 if statement_pref == "Paper Statements (12/year)" else 0,
                    "accessibility_paper_need": statement_pref == "Accessibility Paper Requirement",
                }

                with st.spinner("Running calibrated ML models & carbon engine..."):
                    client.compute_custom_pack(customer_id, display_name, answers)
                    st.toast("Evidence pack recomputed live!", icon="🌱")
                    st.rerun()

        with b_reset:
            if is_custom:
                if st.button("🔄 Reset to Default", use_container_width=True, key=f"qz-btn-rst-{customer_id}"):
                    client.reset_custom_pack(customer_id)
                    st.toast("Reverted to verified baseline profile.", icon="🔄")
                    st.rerun()
