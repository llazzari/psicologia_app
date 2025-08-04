import logfire
import streamlit as st

from data import psychologist_settings
from data.models.psychologist_settings_models import PsychologistSettings
from service.database_manager import get_db_connection

logfire.configure()


@st.cache_data(ttl=3600)
def get_by_(email: str) -> PsychologistSettings:
    logfire.info(f"SERVICE-OP: Fetching psychologist settings for email: {email}")
    connection = get_db_connection()
    settings = psychologist_settings.get_by_email(connection, email)
    logfire.info(f"SERVICE-OP: Retrieved settings for email: {email}")
    return settings


def insert(settings: PsychologistSettings) -> None:
    logfire.info(
        f"SERVICE-OP: Inserting psychologist settings for email: {settings.user_email}"
    )
    connection = get_db_connection()
    psychologist_settings.insert(connection, settings)
    logfire.info(
        f"SERVICE-OP: Successfully inserted settings for email: {settings.user_email}"
    )
