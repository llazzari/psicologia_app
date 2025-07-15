import streamlit as st
from database_manager import get_db_connection

from data import psychologist_settings
from data.models import PsychologistSettings


@st.cache_data(ttl=3600)
def get_by_(email: str) -> PsychologistSettings:
    connection = get_db_connection()
    return psychologist_settings.get_by_email(connection, email)


def save(settings: PsychologistSettings) -> None:
    connection = get_db_connection()
    psychologist_settings.insert(connection, settings)
