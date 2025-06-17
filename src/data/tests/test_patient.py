import logging

import duckdb
import pytest

from data import patient
from data.models import Patient


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
            new_patient_id = patient.add(db_connection, patient_model)
            assert new_patient_id == patient_model.id, (
                "The returned ID should match the model's ID."
            )

            retrieved_patient_model = patient.get_by_id(db_connection, new_patient_id)
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

    patient_id = patient.add(db_connection, patient_adult_model)

    updated_patient = patient_adult_model.model_copy(
        update={"address": "789 Updated St, Updated City, Updated State"}
    )
    patient.update(db_connection, updated_patient)

    db_connection.execute(
        """
        UPDATE patients 
        SET address = ? 
        WHERE id = ?;
        """,
        (updated_patient.address, updated_patient.id),
    )

    retrieved_patient = patient.get_by_id(db_connection, patient_id)

    assert retrieved_patient.address == updated_patient.address, (
        "The address should have been updated."
    )

    logger.info("SUCCESS: Patient was edited successfully.")
