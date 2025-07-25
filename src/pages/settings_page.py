import streamlit as st

from data.models.psychologist_settings_models import PsychologistSettings
from modules import navbar
from service import settings_service


def _price_as_float(price_in_cents: int) -> float:
    """Format a price in cents to a float."""
    return price_in_cents / 100


def _price_in_cents(price: float) -> int:
    """Format a price to cents."""
    return int(price * 100)


def render():
    st.set_page_config(
        page_icon=":material/network_intelligence:",
        layout="wide",
        page_title="Configurações",
        initial_sidebar_state="collapsed",
    )
    st.title("Minhas configurações")

    navbar.render()

    email = st.user.get("email", None)

    if not email:
        raise ValueError("User email not found.")

    current_settings: PsychologistSettings = settings_service.get_by_(email)  # type: ignore

    with st.form("settings_form"):
        st.markdown("Atualize suas informações profissionais.")

        name = st.text_input(
            "Seu Nome Completo", value=current_settings.psychologist_name
        )
        cols = st.columns(4)
        with cols[0]:
            crp = st.text_input("Seu CRP", value=current_settings.crp)
        with cols[1]:
            price = st.number_input(
                "Preço Padrão da Sessão (R$)",
                value=_price_as_float(current_settings.default_session_price),
                step=0.01,
            )
        with cols[2]:
            evaluation_price = st.number_input(
                "Preço Padrão da Avaliação (R$)",
                value=_price_as_float(current_settings.default_evaluation_price),
                step=0.01,
            )
        with cols[3]:
            session_duration = st.number_input(
                "Duração Padrão da Sessão (min)",
                value=current_settings.default_session_duration,
                step=1,
            )

        submitted = st.form_submit_button("Salvar configurações")

        if submitted:
            updated_settings = PsychologistSettings(
                user_email=email,  # type: ignore
                psychologist_name=name,
                crp=crp,
                default_session_price=_price_in_cents(price),
                default_evaluation_price=_price_in_cents(evaluation_price),
                default_session_duration=session_duration,
            )
            settings_service.insert(updated_settings)
            st.session_state.settings = updated_settings
            st.toast("Configurações salvas com sucesso!")


if __name__ == "__main__":
    render()
