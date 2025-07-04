import streamlit as st


def render() -> None:
    st.logo(
        "assets/marca_roxa1.png", icon_image="assets/simbolo_roxo1.png", size="large"
    )
    with st.sidebar:
        st.markdown("## Usuário Logado")
        st.page_link("pages/logout.py", label="Logout", icon=":material/logout:")

        st.markdown("## Navegação")
        st.page_link("main.py", label="Página Inicial", icon=":material/home:")
        st.page_link(
            "pages/2_patients_page.py",
            label="Pacientes",
            icon=":material/patient_list:",
        )
        st.page_link(
            "pages/1_schedule_page.py",
            label="Agendamento Semanal",
            icon=":material/event:",
        )
        st.page_link(
            "pages/3_monthly_invoices.py",
            label="Controle Financeiro",
            icon=":material/attach_money:",
        )
