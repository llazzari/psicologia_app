import streamlit as st

from data import database, patient
from data.models import Patient


def update_patient_on_db() -> None:
    with database.connect(database.DB_PATH) as connection:
        patient.insert(connection, st.session_state.patient)


def get_all_patients() -> list[Patient]:
    with database.connect(database.DB_PATH) as connection:
        return patient.get_all(connection)


def get_patients_by_status(all_patients: list[Patient], status: str) -> list[Patient]:
    return [p for p in all_patients if p.status == status]
