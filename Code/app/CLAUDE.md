# Rules for app/ (GreenProof UI)

- Read docs/3 Architecture.md sections 1.7, 2 and 5.5 before UI work.
- Only create or edit files under app/. Never edit greenproof/, api/, fixtures/ or contracts.py.
- All data comes through app/client.py. Pages never import engines directly.
- Colours, spacing and fonts come only from app/theme.py. No hard-coded hex values.
- The ONLY unsafe_allow_html call is st.markdown(theme.css(), unsafe_allow_html=True) once per page. Never put any data value inside HTML. Render data with st.metric, st.write, st.dataframe, st.plotly_chart, st.badge-style widgets.
- No network calls except through client.py. Never log request or response bodies.
- Every status and badge shows an icon AND a text label; never colour alone.
- Mobile-first: single column under 640px, tap targets 44px.
- Every page shows the synthetic-data banner.
- After each change, run: streamlit run app/Home.py and the AppTest smoke tests in app/tests/.
