import logging
from typing import Any, Optional
from uuid import UUID

import duckdb
import pandas as pd

from data.models import Patient

log = logging.getLogger("TestLogger")


def create_patients_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Creates the 'patients' table with the expanded schema."""
    try:
        log.info("APP-LOGIC: Attempting to create 'patients' table with new schema.")
        sql_command = """
        CREATE TABLE IF NOT EXISTS patients (
            id UUID PRIMARY KEY, 
            name VARCHAR NOT NULL, 
            address VARCHAR,
            contact VARCHAR,
            birthdate DATE, 
            is_child BOOLEAN,
            cpf_cnpj VARCHAR, 
            school VARCHAR, 
            tutor_cpf_cnpj VARCHAR,
            status VARCHAR CHECK (status IN ('active', 'inactive', 'in testing', 'lead')) DEFAULT 'active' NOT NULL,
            contract VARCHAR,
        );
        """
        connection.execute(sql_command)
        log.info("APP-LOGIC: 'patients' table created or already exists.")
    except Exception:
        log.error("APP-LOGIC: Failed to create 'patients' table.", exc_info=True)
        raise


def insert(connection: duckdb.DuckDBPyConnection, patient: Patient) -> None:
    """
    Adds a new patient to the 'patients' table using a Pydantic model.
    """
    try:
        log.info(f"APP-LOGIC: Attempting to add patient '{patient.name}'.")
        patient_dict = patient.model_dump()
        patient_df = pd.DataFrame([patient_dict])

        connection.register("patient_df", patient_df)

        sql = """
        INSERT OR REPLACE INTO patients 
        SELECT 
            id, 
            name, 
            address, 
            contact, 
            birthdate, 
            is_child, 
            cpf_cnpj, 
            school, 
            tutor_cpf_cnpj, 
            status,
            contract
        FROM patient_df
        """
        connection.execute(sql)
        log.info(f"APP-LOGIC: Successfully inserted patient with ID {patient.id}.")

    except Exception:
        log.error(f"APP-LOGIC: Failed to add patient '{patient.name}'.", exc_info=True)
        raise


def get_by_id(connection: duckdb.DuckDBPyConnection, patient_id: UUID) -> Patient:
    """
    Retrieves a patient by ID from the 'patients' table.
    Returns a Pydantic model instance.
    """
    try:
        log.info(f"APP-LOGIC: Attempting to retrieve patient with ID {patient_id}.")
        sql = "SELECT * FROM patients WHERE id = ?;"
        result = connection.execute(sql, (patient_id,)).fetchone()  # type: ignore

        if result is None:
            log.warning(f"APP-LOGIC: No patient found with ID {patient_id}.")
            raise ValueError(f"No patient found with ID {patient_id}.")

        patient = Patient(**{k: v for k, v in zip(Patient.model_fields.keys(), result)})  # type: ignore
        log.info(
            f"APP-LOGIC: Successfully retrieved patient '{patient.name}' with ID {patient.id}."
        )
        return patient
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to retrieve patient with ID {patient_id}.",
            exc_info=True,
        )
        raise


def _make_patient_from_(row: tuple[Any, ...]) -> Patient:
    return Patient(**{k: v for k, v in zip(Patient.model_fields.keys(), row)})


def get_all(
    connection: duckdb.DuckDBPyConnection,
    are_active: bool = False,
    status: Optional[str] = None,
) -> list[Patient]:
    """
    Retrieves all patients from the 'patients' table.
    Returns a list of Pydantic model instances.
    """
    try:
        log.info("APP-LOGIC: Attempting to retrieve all patients.")
        sql = "SELECT * FROM patients ORDER BY name, status DESC;"
        if status:
            sql = f"SELECT * FROM patients WHERE status = '{status}' ORDER BY name, status DESC;"
        if are_active:
            sql = "SELECT * FROM patients WHERE status != 'inactive' ORDER BY name, status DESC;"
        results = connection.execute(sql).fetchall()  # type: ignore

        if not results:
            log.warning("APP-LOGIC: No patients found in the database.")
            return []

        patients: list[Patient] = [_make_patient_from_(row) for row in results]
        log.info(f"APP-LOGIC: Successfully retrieved {len(patients)} patients.")
        return patients
    except Exception:
        log.error("APP-LOGIC: Failed to retrieve all patients.", exc_info=True)
        raise
