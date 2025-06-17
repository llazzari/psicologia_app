import logging
import os
from datetime import date
from typing import Iterator

import duckdb
import pytest

from data.database import (
    add_appointment,
    add_patient,
    connect_to_db,
    create_appointments_table,
    create_patients_table,
    edit_appointment_data,
    edit_patient_data,
    get_appointment_by_id,
    get_patient_by_id,
)
from data.models import Appointment, Patient


@pytest.fixture(scope="session")
def logger() -> Iterator[logging.Logger]:
    """Fixture to set up a file logger for the test session."""
    log_file = "test_run.log"
    log = logging.getLogger("TestLogger")
    log.setLevel(logging.INFO)
    log.propagate = False
    if log.hasHandlers():
        log.handlers.clear()
    file_handler = logging.FileHandler(log_file, mode="w")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    log.info("--- Starting new test session from Pelotas, Brazil ---")
    yield log
    log.removeHandler(file_handler)
    logging.shutdown()


@pytest.fixture
def db_connection(logger: logging.Logger) -> Iterator[duckdb.DuckDBPyConnection]:
    """Fixture to provide a clean database connection for each test."""
    db_file = "psychologist_app_test.db"
    logger.info(f"FIXTURE-SETUP: Preparing database file: {db_file}")
    if os.path.exists(db_file):
        os.remove(db_file)
    connection = connect_to_db(db_file)
    create_patients_table(connection)
    create_appointments_table(connection)
    yield connection
    connection.close()
    if os.path.exists(db_file):
        os.remove(db_file)
    logger.info(f"FIXTURE-TEARDOWN: Cleaned up database file: {db_file}")


@pytest.fixture
def patient_child_model() -> Patient:
    """Fixture to provide a sample patient model for tests."""
    return Patient(
        name="Test Patient",
        address="123 Test St, Test City, Test State",
        is_child=True,
        birthdate=date(2010, 1, 1),
        cpf_cnpj="123.456.789-00",
        school="Test School",
        tutor_cpf_cnpj="987.654.321-00",
    )


@pytest.fixture
def patient_adult_model() -> Patient:
    """Fixture to provide a sample adult patient model for tests."""
    return Patient(
        name="Adult Patient",
        address="456 Adult St, Adult City, Adult State",
        is_child=False,
        birthdate=date(1985, 5, 15),
        cpf_cnpj="123.323.232-22",
    )


@pytest.fixture
def appointment_attended(patient_child_model: Patient) -> Appointment:
    """Fixture to provide a sample attended appointment model for tests."""
    return Appointment(
        patient_id=patient_child_model.id,
        appointment_date=date(2023, 10, 1),
        status="attended",
    )


def test_create_patients_table(
    db_connection: duckdb.DuckDBPyConnection, logger: logging.Logger
) -> None:
    """Tests that the 'patients' table is created with the correct columns."""
    logger.info("TEST-RUN: test_create_patients_table")
    result = db_connection.execute("PRAGMA table_info('patients');").fetchall()
    columns = {row[1]: row[2] for row in result}
    expected_columns = {
        "id": "UUID",
        "name": "VARCHAR",
        "address": "VARCHAR",
        "birthdate": "DATE",
        "cpf_cnpj": "VARCHAR",
        "is_child": "BOOLEAN",
        "school": "VARCHAR",
        "tutor_cpf_cnpj": "VARCHAR",
    }
    assert columns == expected_columns, "Table columns do not match expected schema."
    logger.info("SUCCESS: 'patients' table schema is correct.")


def test_add_and_get_patient_with_pydantic(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    patient_child_model: Patient,
    patient_adult_model: Patient,
) -> None:
    """
    Tests that a full patient record can be added using a Pydantic model
    and then retrieved correctly.
    """
    logger.info("TEST-RUN: test_add_and_get_patient_with_pydantic")

    for patient_model in [patient_child_model, patient_adult_model]:
        age: str = "child" if patient_model.is_child else "adult"
        msg: str = f"Testing adding and retrieving {age} patient: "

        logger.info(msg)
        try:
            new_patient_id = add_patient(db_connection, patient_model)
            assert new_patient_id == patient_model.id, (
                "The returned ID should match the model's ID."
            )

            retrieved_patient_model = get_patient_by_id(db_connection, new_patient_id)
            assert retrieved_patient_model is not None, (
                "get_patient_by_id() should return a record."
            )

            assert retrieved_patient_model == patient_model

            logger.info(
                f"SUCCESS: Patient '{patient_model.name}' was added and retrieved successfully."
            )

        except Exception as e:
            logger.error(
                "FAILURE: Test failed with an unexpected exception.", exc_info=True
            )
            pytest.fail(f"Test failed with an unexpected exception: {e}")


def test_edit_patient(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    patient_adult_model: Patient,
) -> None:
    """
    Tests that a patient can be edited successfully.
    """
    logger.info("TEST-RUN: test_edit_patient")

    patient_id = add_patient(db_connection, patient_adult_model)

    updated_patient = patient_adult_model.model_copy(
        update={"address": "789 Updated St, Updated City, Updated State"}
    )
    edit_patient_data(db_connection, updated_patient)

    db_connection.execute(
        """
        UPDATE patients 
        SET address = ? 
        WHERE id = ?;
        """,
        (updated_patient.address, updated_patient.id),
    )

    retrieved_patient = get_patient_by_id(db_connection, patient_id)

    assert retrieved_patient.address == updated_patient.address, (
        "The address should have been updated."
    )

    logger.info("SUCCESS: Patient was edited successfully.")


def test_add_appointment(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    appointment_attended: Appointment,
) -> None:
    """
    Tests that an appointment can be added successfully.
    """
    logger.info("TEST-RUN: test_add_appointment")

    try:
        new_appointment_id = add_appointment(db_connection, appointment_attended)
        assert new_appointment_id == appointment_attended.id, (
            "The returned ID should match the model's ID."
        )

        retrieved_appointment_model = get_appointment_by_id(
            db_connection, new_appointment_id
        )
        assert retrieved_appointment_model is not None, (
            "get_appointment_by_id() should return a record."
        )

        assert retrieved_appointment_model == appointment_attended

        logger.info(
            f"SUCCESS: Appointment with ID '{appointment_attended.id}' was added and retrieved successfully."
        )

    except Exception as e:
        logger.error(
            "FAILURE: Test failed with an unexpected exception.", exc_info=True
        )
        pytest.fail(f"Test failed with an unexpected exception: {e}")


def test_edit_appointment_data(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    appointment_attended: Appointment,
) -> None:
    """
    Tests that an appointment can be edited successfully.
    """
    logger.info("TEST-RUN: test_edit_appointment_data")

    # Add the initial appointment
    add_appointment(db_connection, appointment_attended)

    updated_appointment = appointment_attended.model_copy(
        update={"status": "cancelled", "appointment_date": date(2022, 10, 1)}
    )
    edit_appointment_data(db_connection, updated_appointment)

    retrieved_appointment = get_appointment_by_id(db_connection, updated_appointment.id)

    assert retrieved_appointment.status == updated_appointment.status, (
        "The status should have been updated."
    )

    logger.info("SUCCESS: Appointment was edited successfully.")
