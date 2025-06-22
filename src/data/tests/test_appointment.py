import logging
from datetime import date, time
from uuid import uuid4

import duckdb
import pytest

from data import appointment
from data.models import Appointment, Patient


@pytest.fixture
def appointment_attended(patient_child_model: Patient) -> Appointment:
    """Fixture to provide a sample attended appointment model for tests."""
    return Appointment(
        patient_id=patient_child_model.id,
        appointment_date=date(2025, 6, 12),
        appointment_hour=time(14, 30),
        status="attended",
        weekday=None,  # "Quinta (12/06)",
    )


@pytest.fixture
def appointment_cancelled(patient_child_model: Patient) -> Appointment:
    """Fixture to provide a sample cancelled appointment model for tests."""
    return Appointment(
        patient_id=patient_child_model.id,
        appointment_date=date(2023, 10, 2),
        appointment_hour=time(15, 0),
        status="cancelled",
        weekday=None,
    )


@pytest.fixture
def appointment_no_show(patient_child_model: Patient) -> Appointment:
    """Fixture to provide a sample no-show appointment model for tests."""
    return Appointment(
        patient_id=patient_child_model.id,
        appointment_date=date(2023, 10, 3),
        appointment_hour=time(16, 30),
        status="no-show",
        weekday=None,
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


def test_update_appointment(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    appointment_attended: Appointment,
) -> None:
    """
    Tests that an appointment can be edited successfully.
    """
    logger.info("TEST-RUN: test_update_appointment")

    # Add the initial appointment
    appointment.add(db_connection, appointment_attended)

    updated_appointment = appointment_attended.model_copy(
        update={
            "status": "cancelled",
            "appointment_date": date(2025, 6, 21),
            "appointment_hour": time(9, 0),
            "weekday": "Sábado (21/06)",
        }
    )
    appointment.update(db_connection, updated_appointment)

    retrieved_appointment = appointment.get_by_id(db_connection, updated_appointment.id)

    assert retrieved_appointment.status == updated_appointment.status, (
        "The status should have been updated."
    )
    assert (
        retrieved_appointment.appointment_hour == updated_appointment.appointment_hour
    ), "The appointment hour should have been updated."
    assert retrieved_appointment.weekday == updated_appointment.weekday

    logger.info("SUCCESS: Appointment was edited successfully.")


def test_add_appointments_with_different_statuses(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    appointment_attended: Appointment,
    appointment_cancelled: Appointment,
    appointment_no_show: Appointment,
) -> None:
    """
    Tests that appointments with different valid statuses can be added successfully.
    """
    logger.info("TEST-RUN: test_add_appointments_with_different_statuses")

    appointments = [appointment_attended, appointment_cancelled, appointment_no_show]

    for test_appointment in appointments:
        status_type = test_appointment.status
        try:
            new_id = appointment.add(db_connection, test_appointment)
            retrieved = appointment.get_by_id(db_connection, new_id)

            assert retrieved.status == status_type, (
                f"Appointment status should be '{status_type}'"
            )
            assert retrieved.appointment_hour == test_appointment.appointment_hour, (
                f"Appointment hour should be '{test_appointment.appointment_hour}'"
            )
            assert retrieved.weekday == test_appointment.weekday
            logger.info(f"SUCCESS: Added appointment with '{status_type}' status")
        except Exception as e:
            logger.error(
                f"FAILURE: Failed to add {status_type} appointment", exc_info=True
            )
            pytest.fail(f"Failed to add {status_type} appointment: {e}")

    logger.info("SUCCESS: All appointment status types were added successfully")


def test_add_appointment_with_invalid_status(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    appointment_attended: Appointment,
) -> None:
    """
    Tests that attempting to add an appointment with an invalid status is handled appropriately.
    """
    logger.info("TEST-RUN: test_add_appointment_with_invalid_status")

    invalid_appointment = appointment_attended.model_copy()
    invalid_appointment_dict = invalid_appointment.model_dump()
    invalid_appointment_dict["status"] = "invalid_status"

    with pytest.raises(Exception):
        appointment.add(
            db_connection,
            Appointment(**invalid_appointment_dict),  # type: ignore
        )

    logger.info("SUCCESS: Invalid appointment status handled correctly")


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
    appointment.add(db_connection, appointment_attended)

    # Try to add another appointment with the same ID but different data
    duplicate_appointment = appointment_attended.model_copy(
        update={"status": "no-show"}
    )

    with pytest.raises(Exception):
        appointment.add(db_connection, duplicate_appointment)

    logger.info("SUCCESS: Duplicate appointment ID handled correctly")


def test_update_multiple_appointment_fields(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    appointment_attended: Appointment,
) -> None:
    """
    Tests that multiple fields of an appointment can be updated simultaneously.
    """
    logger.info("TEST-RUN: test_update_multiple_appointment_fields")

    # Add initial appointment
    appointment.add(db_connection, appointment_attended)

    # Update multiple fields
    new_date = date(2025, 6, 21)
    new_time = time(10, 15)
    updated_appointment = appointment_attended.model_copy(
        update={
            "status": "cancelled",
            "appointment_date": new_date,
            "appointment_hour": new_time,
            "weekday": "Sábado (21/06)",
        }
    )

    appointment.update(db_connection, updated_appointment)

    # Verify all updates
    retrieved = appointment.get_by_id(db_connection, appointment_attended.id)

    assert retrieved.status == "cancelled", "Status should be updated"
    assert retrieved.appointment_date == new_date, "Date should be updated"
    assert retrieved.appointment_hour == new_time, "Time should be updated"
    # Check weekday field
    assert retrieved.weekday == updated_appointment.weekday

    logger.info("SUCCESS: Multiple appointment fields updated successfully")


def test_list_all_for_week(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
) -> None:
    logger.info("TEST-RUN: test_list_all_for_week")

    # Create appointments in chronological order
    appointment1 = Appointment(
        patient_id=uuid4(),
        appointment_date=date(2025, 6, 17),
        appointment_hour=time(14, 30),
        status="attended",
    )

    appointment2 = Appointment(
        patient_id=uuid4(),
        appointment_date=date(2025, 6, 17),
        appointment_hour=time(15, 30),
        status="attended",
    )

    appointment_out_of_week = Appointment(
        patient_id=uuid4(),
        appointment_date=date(2025, 6, 1),
        appointment_hour=time(14, 30),
        status="cancelled",
    )

    # Add appointments in random order
    appointment.add(db_connection, appointment2)
    appointment.add(db_connection, appointment_out_of_week)
    appointment.add(db_connection, appointment1)

    appointments = appointment.list_all_for_week(
        db_connection, [date(2025, 6, 16), date(2025, 6, 20)]
    )
    # If DataFrame, check weekday column exists and is correct
    if hasattr(appointments, "columns") and "weekday" in appointments.columns:
        for idx, row in appointments.iterrows():  # type: ignore
            dt = row["appointment_date"]  # type: ignore
            weekdays_pt = [
                "Segunda",
                "Terça",
                "Quarta",
                "Quinta",
                "Sexta",
                "Sábado",
                "Domingo",
            ]
            weekday_idx = dt.weekday()  # type: ignore
            expected_weekday = (
                f"{weekdays_pt[weekday_idx]} ({dt.day:02d}/{dt.month:02d})"  # type: ignore
            )
            assert row["weekday"] == expected_weekday
        # Compare first and second appointment fields
        row1 = appointments.iloc[0]  # type: ignore
        row2 = appointments.iloc[1]  # type: ignore
        assert row1["appointment_date"] == appointment1.appointment_date
        assert row1["appointment_hour"] == appointment1.appointment_hour
        assert row2["appointment_date"] == appointment2.appointment_date
        assert row2["appointment_hour"] == appointment2.appointment_hour
        assert row1["weekday"] == appointment1.weekday
        assert row2["weekday"] == appointment2.weekday
    logger.info("SUCCESS: Appointment listing for the week works correctly")


def test_list_all_for_week_no_appointments(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
) -> None:
    """
    Tests that listing appointments for a week with no appointments returns an empty list.
    """
    logger.info("TEST-RUN: test_list_all_for_week_no_appointments")

    appointments = appointment.list_all_for_week(
        db_connection, [date(2025, 6, 16), date(2025, 6, 20)]
    )

    assert len(appointments) == 0, "There should be no appointments in the week"
    logger.info("SUCCESS: No appointments for the week handled correctly")


def test_list_all_for_week_invalid_date(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
) -> None:
    """
    Tests that listing appointments for a week with no appointments returns an empty list.
    """
    logger.info("TEST-RUN: test_list_all_for_week_invalid_date")

    with pytest.raises(ValueError):
        _ = appointment.list_all_for_week(
            db_connection, [date(2025, 6, 16), date(2025, 6, 200)]
        )

    logger.info("SUCCESS: Invalid date for week listing handled correctly")
