import streamlit as st


def render() -> None:
    st.logo(
        "assets/marca_roxa1.png", icon_image="assets/simbolo_roxo1.png", size="large"
    )
    with st.sidebar:
        st.page_link("main.py", label="Página Inicial", icon=":material/home:")

        st.markdown("## Gerenciamento")

        st.page_link(
            "pages/patients_page.py",
            label="Pacientes",
            icon=":material/patient_list:",
        )
        st.page_link(
            "pages/schedule_page.py",
            label="Agendamento Semanal",
            icon=":material/event:",
        )
        st.page_link(
            "pages/monthly_invoices.py",
            label="Controle Financeiro",
            icon=":material/attach_money:",
        )

        st.markdown("## Usuário Logado")

        st.page_link("pages/logout.py", label="Logout", icon=":material/logout:")
        # st.page_link(
        #     "pages/settings_page.py", label="Configurações", icon=":material/settings:"
        # )


# !FIXME when documents are open, the patients page in the sidebar does not clean the URL
