import streamlit as st

from data import database
from modules import navbar


def main():
    """Main function to run the Streamlit application."""

    st.set_page_config(
        page_title="Sistema de Gerenciamento",
        page_icon=":clipboard:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    navbar.render()

    st.title("Bem-vindo(a) ao Sistema de Gerenciamento")

    st.markdown("""
    Este é o seu painel de controle para gerenciar agendamentos, pacientes e finanças.
            
    Utilize o menu na barra lateral esquerda para navegar entre as diferentes seções do aplicativo.

    **Funcionalidades disponíveis:**
    - **Página Inicial:** Esta página de boas-vindas.
    - **Agendamento Semanal:** Visualize e gerencie os agendamentos em uma grade semanal interativa.

    Comece selecionando uma opção no menu ao lado.
    """)

    with database.connect(database.DB_PATH) as connection:
        database.initialize(connection)


if __name__ == "__main__":
    main()
