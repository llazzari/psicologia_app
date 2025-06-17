import logging
from datetime import date

import duckdb
import pytest

from data import appointment
from data.models import Appointment, Patient


@pytest.fixture
def appointment_attended(patient_child_model: Patient) -> Appointment:
    """Fixture to provide a sample attended appointment model for tests."""
    return Appointment(
        patient_id=patient_child_model.id,
        appointment_date=date(2023, 10, 1),
        status="attended",
    )


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
        new_appointment_id = appointment.add(db_connection, appointment_attended)
        assert new_appointment_id == appointment_attended.id, (
            "The returned ID should match the model's ID."
        )

        retrieved_appointment_model = appointment.get_by_id(
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
    appointment.add(db_connection, appointment_attended)

    updated_appointment = appointment_attended.model_copy(
        update={"status": "cancelled", "appointment_date": date(2022, 10, 1)}
    )
    appointment.update(db_connection, updated_appointment)

    retrieved_appointment = appointment.get_by_id(db_connection, updated_appointment.id)

    assert retrieved_appointment.status == updated_appointment.status, (
        "The status should have been updated."
    )

    logger.info("SUCCESS: Appointment was edited successfully.")
