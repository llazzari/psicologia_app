import logging
from uuid import UUID

import duckdb
import pandas as pd

from data.models import Patient

log = logging.getLogger("TestLogger")


def connect_to_db(db_path: str) -> duckdb.DuckDBPyConnection:
    """
    Establishes a connection to the DuckDB database.

    This function is our application's dedicated way to interact with
    the database connection, abstracting the direct call to the library.

    Args:
        db_path (str): The file path for the database.

    Returns:
        duckdb.DuckDBPyConnection: A connection object to the database,
                                    or None if an error occurs.
    """
    try:
        log.info(f"APP-LOGIC: Attempting to connect to database at '{db_path}'")
        connection = duckdb.connect(database=db_path, read_only=False)
        log.info("APP-LOGIC: Database connection successful.")
    except Exception:
        log.error("APP-LOGIC: Failed to connect to database.", exc_info=True)
        # In a real app, we might raise the exception or handle it differently.
        # For now, returning None is a clear failure signal.
        raise Exception("Failed to connect to the database.")

    return connection


def create_patients_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Creates the 'patients' table with the expanded schema."""
    try:
        log.info("APP-LOGIC: Attempting to create 'patients' table with new schema.")
        sql_command = """
        CREATE TABLE IF NOT EXISTS patients (
            id UUID PRIMARY KEY, 
            name VARCHAR NOT NULL, 
            address VARCHAR,
            birthdate DATE, 
            is_child BOOLEAN NOT NULL,
            cpf_cnpj VARCHAR, 
            school VARCHAR, 
            tutor_cpf_cnpj VARCHAR,
        );
        """
        connection.execute(sql_command)
        log.info("APP-LOGIC: 'patients' table created or already exists.")
    except Exception:
        log.error("APP-LOGIC: Failed to create 'patients' table.", exc_info=True)
        raise


def add_patient(connection: duckdb.DuckDBPyConnection, patient: Patient) -> UUID:
    """
    Adds a new patient to the 'patients' table using a Pydantic model.
    """
    try:
        log.info(f"APP-LOGIC: Attempting to add patient '{patient.name}'.")
        patient_dict = patient.model_dump()
        patient_df = pd.DataFrame([patient_dict])
        print(patient_df.columns)

        connection.register("patient_df", patient_df)

        sql = """
        INSERT INTO patients 
        SELECT id, name, address, birthdate, is_child, cpf_cnpj, school, tutor_cpf_cnpj FROM patient_df
        """
        connection.execute(sql)
        log.info(f"APP-LOGIC: Successfully inserted patient with ID {patient.id}.")
        return patient.id
    except Exception:
        log.error(f"APP-LOGIC: Failed to add patient '{patient.name}'.", exc_info=True)
        raise


def get_patient_by_id(
    connection: duckdb.DuckDBPyConnection, patient_id: UUID
) -> Patient:
    """
    Retrieves a patient by ID from the 'patients' table.
    Returns a Pydantic model instance.
    """
    try:
        log.info(f"APP-LOGIC: Attempting to retrieve patient with ID {patient_id}.")
        sql = "SELECT * FROM patients WHERE id = ?;"
        result = connection.execute(sql, (patient_id,)).fetchone()

        if result is None:
            log.warning(f"APP-LOGIC: No patient found with ID {patient_id}.")
            return None

        patient = Patient(**{k: v for k, v in zip(Patient.model_fields.keys(), result)})
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


def edit_patient_data(connection: duckdb.DuckDBPyConnection, patient: Patient) -> None:
    """
    Updates an existing patient's data in the 'patients' table.
    """
    try:
        log.info(f"APP-LOGIC: Attempting to update patient '{patient.name}'.")
        patient_dict = patient.model_dump()
        patient_df = pd.DataFrame([patient_dict])

        connection.register("patient_df", patient_df)

        sql = """
        UPDATE patients 
        SET name = patient_df.name, 
            address = patient_df.address, 
            birthdate = patient_df.birthdate, 
            is_child = patient_df.is_child, 
            cpf_cnpj = patient_df.cpf_cnpj, 
            school = patient_df.school, 
            tutor_cpf_cnpj = patient_df.tutor_cpf_cnpj
        FROM patient_df
        WHERE patients.id = patient_df.id;
        """
        connection.execute(sql)
        log.info(f"APP-LOGIC: Successfully updated patient with ID {patient.id}.")
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to update patient '{patient.name}'.", exc_info=True
        )
        raise
