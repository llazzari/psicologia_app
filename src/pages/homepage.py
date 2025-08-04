import logfire
import streamlit as st

logfire.configure()


@st.cache_data()
def render() -> None:
    logfire.info("PAGE-RENDER: Rendering homepage")
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
