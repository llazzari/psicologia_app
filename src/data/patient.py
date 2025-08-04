from typing import Any, Optional
from uuid import UUID

import duckdb
import logfire

from data.db_utils import insert_model
from data.models.patient_models import (
    Child,
    Patient,
    PatientGender,
    PatientInfo,
    PatientStatus,
)

logfire.configure()


def create_patients_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Creates the 'patients' table with the expanded schema to match the Patient model."""
    try:
        logfire.info(
            "APP-LOGIC: Attempting to create 'patients' table with new schema."
        )
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
        logfire.info("APP-LOGIC: 'patients' table created or already exists.")
    except Exception:
        logfire.error("APP-LOGIC: Failed to create 'patients' table.", exc_info=True)
        raise


def patient_field_map(model: Patient) -> dict[str, Any]:
    return {
        "id": model.id,
        "name": model.info.name,
        "address": model.info.address,
        "contact": model.info.contact,
        "birthdate": model.info.birthdate,
        "gender": model.info.gender,
        "cpf_cnpj": model.info.cpf_cnpj,
        "status": model.status,
        "diagnosis": model.diagnosis,
        "contract": model.contract,
        "school": model.child.school if model.child else None,
        "grade": model.child.grade if model.child else None,
        "class_time": model.child.class_time if model.child else None,
        "tutor_name": model.child.tutor_name if model.child else None,
        "tutor_cpf_cnpj": model.child.tutor_cpf_cnpj if model.child else None,
    }


def insert(connection: duckdb.DuckDBPyConnection, patient: Patient) -> None:
    try:
        insert_model(
            connection,
            "patients",
            patient_field_map(patient),
        )
        logfire.info(f"Inserted patient with ID {patient.id}")
    except Exception:
        logfire.error(f"Failed to insert patient with ID {patient.id}", exc_info=True)
        raise


def _fetch_patient_row(
    connection: duckdb.DuckDBPyConnection, patient_id: UUID
) -> tuple[Any, ...] | None:
    sql = "SELECT * FROM patients WHERE id = ?;"
    return connection.execute(sql, (patient_id,)).fetchone()  # type: ignore


def get_by_id(connection: duckdb.DuckDBPyConnection, patient_id: UUID) -> Patient:
    """
    Retrieves a patient by ID from the 'patients' table.
    Returns a Pydantic model instance, reconstructing nested fields.
    """
    try:
        logfire.info(f"APP-LOGIC: Attempting to retrieve patient with ID {patient_id}.")
        row = _fetch_patient_row(connection, patient_id)
        if row is None:
            logfire.warning(f"APP-LOGIC: No patient found with ID {patient_id}.")
            raise ValueError(f"No patient found with ID {patient_id}.")
        columns = [
            desc[1]
            for desc in connection.execute("PRAGMA table_info('patients')").fetchall()
        ]
        row_dict: dict[str, Any] = dict(zip(columns, row))  # type: ignore
        # Reconstruct nested models
        info = PatientInfo(
            name=row_dict["name"],
            address=row_dict["address"],
            contact=row_dict["contact"],
            birthdate=row_dict["birthdate"],
            gender=PatientGender(row_dict["gender"]) if row_dict["gender"] else None,
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
        logfire.info(
            f"APP-LOGIC: Successfully retrieved patient '{patient.info.name}' with ID {patient.id}."
        )
        return patient
    except Exception:
        logfire.error(
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
        logfire.info("APP-LOGIC: Attempting to retrieve all patients.")
        sql = "SELECT * FROM patients ORDER BY name, status DESC;"
        if status:
            sql = f"SELECT * FROM patients WHERE status = '{status}' ORDER BY name, status DESC;"
        if are_active:
            sql = "SELECT * FROM patients WHERE status != 'inactive' ORDER BY name, status DESC;"
        results = connection.execute(sql).fetchall()  # type: ignore
        if not results:
            logfire.warning("APP-LOGIC: No patients found in the database.")
            return []
        patients: list[Patient] = [_make_patient_from_(row) for row in results]
        logfire.info(f"APP-LOGIC: Successfully retrieved {len(patients)} patients.")
        return patients
    except Exception:
        logfire.error("APP-LOGIC: Failed to retrieve all patients.", exc_info=True)
        raise
