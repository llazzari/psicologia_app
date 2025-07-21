import logging
from typing import Any, Optional
from uuid import UUID

import duckdb
import pandas as pd

from data.models import Child, Patient, PatientGender, PatientInfo, PatientStatus

log = logging.getLogger("TestLogger")


def create_patients_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Creates the 'patients' table with the expanded schema to match the Patient model."""
    try:
        log.info("APP-LOGIC: Attempting to create 'patients' table with new schema.")
        sql_command = """
        CREATE TABLE IF NOT EXISTS patients (
            id UUID PRIMARY KEY,
            name VARCHAR NOT NULL,
            address VARCHAR,
            contact VARCHAR,
            birthdate DATE,
            gender VARCHAR CHECK (gender IN ('male', 'female')),
            cpf_cnpj VARCHAR,
            status VARCHAR CHECK (status IN ('active', 'inactive', 'in testing', 'lead')) DEFAULT 'active' NOT NULL,
            diagnosis VARCHAR,
            contract VARCHAR,
            school VARCHAR,
            grade VARCHAR,
            class_time VARCHAR,
            tutor_name VARCHAR,
            tutor_cpf_cnpj VARCHAR
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
    Flattens nested fields for storage.
    """
    try:
        log.info(f"APP-LOGIC: Attempting to add patient '{patient.info.name}'.")
        # Flatten patient model for DB
        patient_dict = {
            "id": patient.id,
            "name": patient.info.name,
            "address": patient.info.address,
            "contact": patient.info.contact,
            "birthdate": patient.info.birthdate,
            "gender": patient.info.gender,
            "cpf_cnpj": patient.info.cpf_cnpj,
            "status": patient.status,
            "diagnosis": patient.diagnosis,
            "contract": patient.contract,
            "school": patient.child.school if patient.child else None,
            "grade": patient.child.grade if patient.child else None,
            "class_time": patient.child.class_time if patient.child else None,
            "tutor_name": patient.child.tutor_name if patient.child else None,
            "tutor_cpf_cnpj": patient.child.tutor_cpf_cnpj if patient.child else None,
        }
        patient_df: pd.DataFrame = pd.DataFrame([patient_dict])  # type: ignore
        connection.register("patient_df", patient_df)  # type: ignore
        sql = """
        INSERT OR REPLACE INTO patients 
        SELECT 
            id, name, address, contact, birthdate, gender, cpf_cnpj, status, diagnosis, contract, school, grade, class_time, tutor_name, tutor_cpf_cnpj
        FROM patient_df
        """
        connection.execute(sql)
        log.info(f"APP-LOGIC: Successfully inserted patient with ID {patient.id}.")
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to add patient '{getattr(patient.info, 'name', 'unknown')}'.",
            exc_info=True,
        )
        raise


def get_by_id(connection: duckdb.DuckDBPyConnection, patient_id: UUID) -> Patient:
    """
    Retrieves a patient by ID from the 'patients' table.
    Returns a Pydantic model instance, reconstructing nested fields.
    """
    try:
        log.info(f"APP-LOGIC: Attempting to retrieve patient with ID {patient_id}.")
        sql = "SELECT * FROM patients WHERE id = ?;"
        result = connection.execute(sql, (patient_id,)).fetchone()  # type: ignore
        if result is None:
            log.warning(f"APP-LOGIC: No patient found with ID {patient_id}.")
            raise ValueError(f"No patient found with ID {patient_id}.")

        columns = [
            desc[1]
            for desc in connection.execute("PRAGMA table_info('patients')").fetchall()
        ]

        row_dict: dict[str, Any] = dict(zip(columns, result))  # type: ignore
        # Reconstruct nested models
        info = PatientInfo(
            name=row_dict["name"],
            address=row_dict["address"],
            contact=row_dict["contact"],
            birthdate=row_dict["birthdate"],
            gender=PatientGender(row_dict["gender"]),
            cpf_cnpj=row_dict["cpf_cnpj"],
        )
        child = None
        if any(
            row_dict.get(f) is not None
            for f in ["school", "grade", "class_time", "tutor_name", "tutor_cpf_cnpj"]
        ):
            child = Child(
                school=row_dict["school"],
                grade=row_dict["grade"],
                class_time=row_dict["class_time"],
                tutor_name=row_dict["tutor_name"],
                tutor_cpf_cnpj=row_dict["tutor_cpf_cnpj"],
            )
        patient = Patient(
            id=row_dict["id"],
            info=info,
            status=PatientStatus(row_dict["status"]),
            diagnosis=row_dict["diagnosis"],
            contract=row_dict["contract"],
            child=child,
        )
        log.info(
            f"APP-LOGIC: Successfully retrieved patient '{patient.info.name}' with ID {patient.id}."
        )
        return patient
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to retrieve patient with ID {patient_id}.",
            exc_info=True,
        )
        raise


def _make_patient_from_(row: tuple[Any, ...]) -> Patient:
    # Get columns for mapping
    columns = [
        "id",
        "name",
        "address",
        "contact",
        "birthdate",
        "gender",
        "cpf_cnpj",
        "status",
        "diagnosis",
        "contract",
        "school",
        "grade",
        "class_time",
        "tutor_name",
        "tutor_cpf_cnpj",
    ]
    row_dict: dict[str, Any] = dict(zip(columns, row))  # type: ignore
    info = PatientInfo(
        name=row_dict["name"],
        address=row_dict["address"],
        contact=row_dict["contact"],
        birthdate=row_dict["birthdate"],
        gender=row_dict["gender"],
        cpf_cnpj=row_dict["cpf_cnpj"],
    )
    child = None
    if any(
        row_dict.get(f) is not None
        for f in ["school", "grade", "class_time", "tutor_name", "tutor_cpf_cnpj"]
    ):
        child = Child(
            school=row_dict["school"],
            grade=row_dict["grade"],
            class_time=row_dict["class_time"],
            tutor_name=row_dict["tutor_name"],
            tutor_cpf_cnpj=row_dict["tutor_cpf_cnpj"],
        )
    return Patient(
        id=row_dict["id"],
        info=info,
        status=PatientStatus(row_dict["status"]),
        diagnosis=row_dict["diagnosis"],
        contract=row_dict["contract"],
        child=child,
    )


def get_all(
    connection: duckdb.DuckDBPyConnection,
    are_active: bool = False,
    status: Optional[str] = None,
) -> list[Patient]:
    """
    Retrieves all patients from the 'patients' table.
    Returns a list of Pydantic model instances, reconstructing nested fields.
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
