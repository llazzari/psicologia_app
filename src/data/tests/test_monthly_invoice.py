import logging

import duckdb
import pytest

from data import monthly_invoice
from data.models import MonthlyInvoice, Patient

# Import common fixtures


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
