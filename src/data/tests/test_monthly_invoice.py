import logging
from datetime import date
from uuid import uuid4

import duckdb
import pytest

from data import monthly_invoice
from data.models import MonthlyInvoice, Patient


@pytest.fixture
def monthly_invoice_model(patient_child_model: Patient) -> MonthlyInvoice:
    """Fixture to provide a sample monthly invoice model for tests."""
    return MonthlyInvoice(
        patient_id=patient_child_model.id,
        invoice_month="Jan",
        session_price=23000,
        sessions_completed=4,
        payment_status="pending",
    )


@pytest.fixture
def paid_invoice_model(patient_child_model: Patient) -> MonthlyInvoice:
    """Fixture to provide a sample paid monthly invoice model for tests."""
    return MonthlyInvoice(
        patient_id=patient_child_model.id,
        invoice_month="Feb",
        session_price=23000,
        sessions_completed=3,
        payment_status="paid",
        payment_date=date(2025, 2, 28),
    )


def test_add_monthly_invoice(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    monthly_invoice_model: MonthlyInvoice,
) -> None:
    """
    Tests that a monthly invoice can be added successfully.
    """
    logger.info("TEST-RUN: test_monthly_invoice")

    try:
        new_invoice_id = monthly_invoice.add(db_connection, monthly_invoice_model)
        assert new_invoice_id == monthly_invoice_model.id, (
            "The returned ID should match the model's ID."
        )

        retrieved_inovice_model = monthly_invoice.get_by_id(
            db_connection, new_invoice_id
        )
        assert retrieved_inovice_model is not None, (
            "get_monthly_invoice_by_id() should return a record."
        )

        assert retrieved_inovice_model == monthly_invoice_model

        logger.info(
            f"SUCCESS: Monthly invoice with ID '{monthly_invoice_model.id}' was added and retrieved successfully."
        )

    except Exception as e:
        logger.error(
            "FAILURE: Test failed with an unexpected exception.", exc_info=True
        )
        pytest.fail(f"Test failed with an unexpected exception: {e}")


def test_edit_monthly_invoice(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    monthly_invoice_model: MonthlyInvoice,
) -> None:
    """
    Tests that a monthly invoice can be edited successfully.
    """
    logger.info("TEST-RUN: test_edit_monthly_invoice")

    monthly_invoice.add(db_connection, monthly_invoice_model)

    updated_invoice = monthly_invoice_model.model_copy(
        update={
            "session_price": 25000,
            "payment_status": "paid",
        }
    )
    monthly_invoice.update(db_connection, updated_invoice)

    retrieved_invoice = monthly_invoice.get_by_id(db_connection, updated_invoice.id)

    assert retrieved_invoice.session_price == updated_invoice.session_price, (
        "The session price should have been updated."
    )
    assert retrieved_invoice.payment_status == updated_invoice.payment_status, (
        "The payment status should have been updated."
    )

    logger.info("SUCCESS: Monthly invoice was edited successfully.")


def test_get_nonexistent_invoice(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
) -> None:
    """
    Tests that attempting to retrieve a non-existent invoice raises the appropriate error.
    """
    logger.info("TEST-RUN: test_get_nonexistent_invoice")

    non_existent_id = uuid4()

    with pytest.raises(ValueError) as exc_info:
        monthly_invoice.get_by_id(db_connection, non_existent_id)

    assert str(exc_info.value) == f"No invoice found with ID {non_existent_id}."
    logger.info("SUCCESS: Non-existent invoice retrieval handled correctly")


def test_add_invoice_with_invalid_status(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    monthly_invoice_model: MonthlyInvoice,
) -> None:
    """
    Tests that attempting to add an invoice with an invalid payment status is handled appropriately.
    """
    logger.info("TEST-RUN: test_add_invoice_with_invalid_status")

    invalid_invoice = monthly_invoice_model.model_copy()
    # Attempting to set an invalid status (not in 'pending', 'paid', 'overdue', 'waived')
    invalid_invoice_dict = invalid_invoice.model_dump()
    invalid_invoice_dict["payment_status"] = "invalid_status"

    with pytest.raises(Exception):
        monthly_invoice.add(
            db_connection,
            MonthlyInvoice(**invalid_invoice_dict),  # type: ignore
        )

    logger.info("SUCCESS: Invalid payment status handled correctly")


def test_update_invoice_payment_status_and_date(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    monthly_invoice_model: MonthlyInvoice,
) -> None:
    """
    Tests updating an invoice from pending to paid, including setting the payment date.
    """
    logger.info("TEST-RUN: test_update_invoice_payment_status_and_date")

    # Add initial pending invoice
    monthly_invoice.add(db_connection, monthly_invoice_model)

    # Update to paid status with payment date
    payment_date = date(2025, 6, 15)
    updated_invoice = monthly_invoice_model.model_copy(
        update={
            "payment_status": "paid",
            "payment_date": payment_date,
        }
    )
    monthly_invoice.update(db_connection, updated_invoice)

    # Verify the update
    retrieved_invoice = monthly_invoice.get_by_id(db_connection, updated_invoice.id)
    assert retrieved_invoice.payment_status == "paid", (
        "Status should be updated to paid"
    )
    assert retrieved_invoice.payment_date == payment_date, "Payment date should be set"

    logger.info("SUCCESS: Invoice payment status and date updated successfully")


def test_add_duplicate_invoice_id(
    db_connection: duckdb.DuckDBPyConnection,
    logger: logging.Logger,
    monthly_invoice_model: MonthlyInvoice,
) -> None:
    """
    Tests that attempting to add an invoice with a duplicate ID is handled appropriately.
    """
    logger.info("TEST-RUN: test_add_duplicate_invoice_id")

    # Add the first invoice
    monthly_invoice.add(db_connection, monthly_invoice_model)

    # Try to add another invoice with the same ID but different data
    duplicate_invoice = monthly_invoice_model.model_copy(
        update={"sessions_completed": 5}
    )

    with pytest.raises(Exception):
        monthly_invoice.add(db_connection, duplicate_invoice)

    logger.info("SUCCESS: Duplicate invoice ID handled correctly")
