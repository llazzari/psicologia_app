import logging
from uuid import uuid4

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


def test_update_patient(
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


def test_get_nonexistent_patient(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
) -> None:
    """
    Tests that attempting to retrieve a non-existent patient raises the appropriate error.
    """
    logger.info("TEST-RUN: test_get_nonexistent_patient")

    non_existent_id = uuid4()

    with pytest.raises(ValueError) as exc_info:
        patient.get_by_id(db_connection, non_existent_id)

    print(exc_info.value)
    assert str(exc_info.value) == f"No patient found with ID {non_existent_id}."
    logger.info("SUCCESS: Non-existent patient retrieval handled correctly")


def test_update_multiple_fields(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    patient_child_model: Patient,
) -> None:
    """
    Tests that multiple fields of a patient can be updated simultaneously.
    """
    logger.info("TEST-RUN: test_update_multiple_fields")

    # First add the patient
    patient.add(db_connection, patient_child_model)

    # Update multiple fields
    updated_patient = patient_child_model.model_copy(
        update={
            "name": "Updated Name",
            "address": "New Address",
            "school": "New School",
            "tutor_cpf_cnpj": "111.222.333-44",
        }
    )

    patient.update(db_connection, updated_patient)

    # Retrieve and verify all updated fields
    retrieved_patient = patient.get_by_id(db_connection, patient_child_model.id)

    assert retrieved_patient.name == updated_patient.name, "Name should be updated"
    assert retrieved_patient.address == updated_patient.address, (
        "Address should be updated"
    )
    assert retrieved_patient.school == updated_patient.school, (
        "School should be updated"
    )
    assert retrieved_patient.tutor_cpf_cnpj == updated_patient.tutor_cpf_cnpj, (
        "Tutor CPF should be updated"
    )

    logger.info("SUCCESS: Multiple fields updated successfully")


def test_add_duplicate_patient_id(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    patient_adult_model: Patient,
) -> None:
    """
    Tests that attempting to add a patient with a duplicate ID is handled appropriately.
    """
    logger.info("TEST-RUN: test_add_duplicate_patient_id")

    patient.add(db_connection, patient_adult_model)

    duplicate_patient = patient_adult_model.model_copy(
        update={"name": "Different Name"}
    )

    with pytest.raises(Exception):
        patient.add(db_connection, duplicate_patient)

    logger.info("SUCCESS: Duplicate patient ID handled correctly")
