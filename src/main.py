# Conteúdo do arquivo: src/main.py

import streamlit as st

# --- Configuração da Página ---
# É uma boa prática definir a configuração na página principal
# O Streamlit aplicará isso a todas as páginas do app
st.set_page_config(
    page_title="Sistema de Gestão | Psicologia", page_icon="🧠", layout="wide"
)

# --- Página Principal ---
st.title("Bem-vinda ao seu Sistema de Gestão")
st.markdown("---")

st.header("Visão Geral")
st.info(
    """
    Este é o seu painel de controle central. No futuro, esta página exibirá um resumo financeiro 
    com os principais indicadores.

    **Para começar, utilize o menu de navegação na barra lateral à esquerda para:**
    - **Gerenciar Pacientes:** Cadastrar, visualizar e editar informações dos pacientes.
    - **Acessar a Agenda:** Visualizar e marcar suas sessões.
    """
)

st.success("Aplicação pronta para uso! Selecione uma página ao lado para começar.")
