import streamlit as st

from data.models import PsychologistSettings
from service import settings_service


def render():
    st.title("⚙️ Minhas Configurações")

    email = st.user.get("email", None)

    if not email:
        raise ValueError("User email not found in session state.")

    current_settings: PsychologistSettings = settings_service.get_by_(email)  # type: ignore

    with st.form("settings_form"):
        st.markdown("Atualize suas informações profissionais.")

        name = st.text_input(
            "Seu Nome Completo", value=current_settings.psychologist_name
        )
        crp = st.text_input("Seu CRP", value=current_settings.crp)
        price = st.number_input(
            "Preço Padrão da Sessão (R$)",
            value=current_settings.default_session_price,
            format="%.2f",
        )

        submitted = st.form_submit_button("Salvar Configurações")

        if submitted:
            updated_settings = PsychologistSettings(
                user_email=email,  # type: ignore
                psychologist_name=name,
                crp=crp,
                default_session_price=price,
            )
            settings_service.save(updated_settings)
            st.toast("Configurações salvas com sucesso!")
