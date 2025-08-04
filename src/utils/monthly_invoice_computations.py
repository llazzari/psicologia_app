import streamlit as st

from data.models.patient_models import PatientStatus


@st.cache_data(ttl=3600)
def format_currency(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "-").replace(".", ",").replace("-", ".")


@st.cache_data(ttl=3600)
def get_total(
    sessions_completed: int,
    sessions_to_recover: int,
    session_price: int,
    free_sessions: int,
    patient_status: PatientStatus,
) -> int:
    if patient_status == PatientStatus.IN_TESTING:
        return 280000  # TODO - GET IT FROM SETTINGS
    else:
        base_total = session_price * (
            sessions_completed + sessions_to_recover - free_sessions
        )
        return base_total


@st.cache_data(ttl=3600)
def get_formatted_price(session_price: int) -> str:
    return format_currency(session_price / 100)


@st.cache_data(ttl=3600)
def get_total_sessions(sessions_completed: int, sessions_to_recover: int) -> int:
    return sessions_completed + sessions_to_recover
