import streamlit as st

from data import patient
from data.models import Patient
from service.database_manager import get_db_connection


def update_patient_on_db() -> None:
    connection = get_db_connection()
    patient.insert(connection, st.session_state.patient)


def get_all_patients() -> list[Patient]:
    connection = get_db_connection()
    return patient.get_all(connection)
