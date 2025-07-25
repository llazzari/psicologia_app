import streamlit as st

from data import psychologist_settings
from data.models.psychologist_settings_models import PsychologistSettings
from service.database_manager import get_db_connection


@st.cache_data(ttl=3600)
def get_by_(email: str) -> PsychologistSettings:
    connection = get_db_connection()
    return psychologist_settings.get_by_email(connection, email)


def insert(settings: PsychologistSettings) -> None:
    connection = get_db_connection()
    psychologist_settings.insert(connection, settings)
