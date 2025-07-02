import streamlit as st


def render() -> None:
    with st.sidebar:
        st.page_link("main.py", label="Página Inicial")
        st.page_link("pages/2_patients_page.py", label="Pacientes")
        st.page_link("pages/1_schedule_page.py", label="Agendamento Semanal")
        st.page_link("pages/3_monthly_invoices.py", label="Controle Financeiro")
