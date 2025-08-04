from typing import Optional
from uuid import UUID

import logfire
import streamlit as st

from data import patient
from data.models.patient_models import Patient
from service.database_manager import get_db_connection

logfire.configure()


def update_patient_on_db(patient_: Patient) -> None:
    logfire.info(
        f"SERVICE-OP: Updating patient {patient_.info.name} (ID: {patient_.id}) in database"
    )
    connection = get_db_connection()
    patient.insert(connection, patient_)
    logfire.info(f"SERVICE-OP: Successfully updated patient {patient_.info.name}")


def get_all_patients(
    are_active: bool = False, status: Optional[str] = None
) -> list[Patient]:
    logfire.info(
        f"SERVICE-OP: Fetching all patients (active: {are_active}, status: {status})"
    )
    connection = get_db_connection()
    patients = patient.get_all(connection, are_active, status)
    logfire.info(f"SERVICE-OP: Retrieved {len(patients)} patients from database")
    return patients


@st.cache_data(ttl=3600)
def get_patient_by_id(patient_id: UUID) -> Patient:
    logfire.info(f"SERVICE-OP: Fetching patient by ID: {patient_id}")
    connection = get_db_connection()
    patient_data = patient.get_by_id(connection, patient_id)
    logfire.info(
        f"SERVICE-OP: Retrieved patient {patient_data.info.name} (ID: {patient_id})"
    )
    return patient_data
