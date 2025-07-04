import streamlit as st

from data import database, patient
from modules import navbar


@st.cache_data()
def homepage() -> None:
    st.title("Bem-vindo(a) ao Sistema de Gerenciamento")

    st.markdown("""
    Este é o seu painel de controle para gerenciar agendamentos, pacientes e finanças.
            
    Utilize o menu na barra lateral esquerda para navegar entre as diferentes seções do aplicativo.

    **Funcionalidades disponíveis:**
    - **Página Inicial:** Esta página de boas-vindas.
    - **Pacientes:** Cadastre ou edite pacientes.
    - **Agendamento Semanal:** Visualize e gerencie os agendamentos em uma grade semanal interativa.
    - **Controle Financeiro:** Visualize e gerencie as finanças relacionadas aos pacientes.
                
    Comece selecionando uma opção no menu ao lado.
    """)


def initialize_database() -> None:
    with database.connect(database.DB_PATH) as connection:
        database.initialize(connection)
        st.session_state.all_patients = patient.get_all(connection)


def main():
    """Main function to run the Streamlit application."""

    st.set_page_config(
        page_title="Sistema de Gerenciamento",
        page_icon=":material/network_intelligence:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if not st.user.is_logged_in:
        if st.button("Login com Google", icon=":material/login:"):
            st.login("google")
    else:
        navbar.render()
        homepage()
        initialize_database()


if __name__ == "__main__":
    main()
