from typing import Optional

from data import patient
from data.models import Patient
from service.database_manager import get_db_connection


def update_patient_on_db(patient_: Patient) -> None:
    connection = get_db_connection()
    patient.insert(connection, patient_)


def get_all_patients(
    are_active: bool = False, status: Optional[str] = None
) -> list[Patient]:
    connection = get_db_connection()
    return patient.get_all(connection, are_active, status)
