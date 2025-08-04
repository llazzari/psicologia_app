import logging
from datetime import date, time
from uuid import uuid4

import duckdb
import pytest

from data import appointment
from data.models.appointment_models import Appointment
from data.models.patient_models import Patient


@pytest.fixture
def appointment_attended(patient_child_model: Patient) -> Appointment:
    """Fixture to provide a sample attended appointment model for tests."""
    return Appointment(
        patient_id=patient_child_model.id,
        appointment_date=date(2025, 6, 12),
        appointment_time=time(14, 30),
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
        new_appointment_id = appointment.insert(db_connection, appointment_attended)
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


def test_get_nonexistent_appointment(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
) -> None:
    """
    Tests that attempting to retrieve a non-existent appointment raises the appropriate error.
    """
    logger.info("TEST-RUN: test_get_nonexistent_appointment")

    non_existent_id = uuid4()

    with pytest.raises(ValueError) as exc_info:
        appointment.get_by_id(db_connection, non_existent_id)

    assert str(exc_info.value) == f"No appointment found with ID {non_existent_id}."
    logger.info("SUCCESS: Non-existent appointment retrieval handled correctly")


def test_add_duplicate_appointment_id(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    appointment_attended: Appointment,
) -> None:
    """
    Tests that attempting to add an appointment with a duplicate ID is handled appropriately.
    """
    logger.info("TEST-RUN: test_add_duplicate_appointment_id")

    # Add the first appointment
    appointment.insert(db_connection, appointment_attended)

    # Try to add another appointment with the same ID but different data
    duplicate_appointment = appointment_attended.model_copy(
        update={"status": "no-show"}
    )

    with pytest.raises(Exception):
        appointment.insert(db_connection, duplicate_appointment)

    logger.info("SUCCESS: Duplicate appointment ID handled correctly")
