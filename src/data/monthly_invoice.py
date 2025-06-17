import logging
from uuid import UUID

import duckdb
import pandas as pd

from data.models import MonthlyInvoice

log = logging.getLogger("TestLogger")


def create_monthly_invoices_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Creates the 'monthly_invoices' table with the expanded schema."""
    try:
        log.info(
            "APP-LOGIC: Attempting to create 'monthly_invoices' table with new schema."
        )
        sql_command = """
        CREATE TABLE IF NOT EXISTS monthly_invoices (
            id UUID PRIMARY KEY, 
            patient_id UUID NOT NULL,
            invoice_month VARCHAR NOT NULL,
            session_price INTEGER NOT NULL,
            sessions_completed INTEGER NOT NULL,
            payment_status VARCHAR CHECK (payment_status IN ('pending', 'paid', 'overdue', 'waived')) NOT NULL,
            payment_date DATE
        );
        """
        connection.execute(sql_command)
        log.info("APP-LOGIC: 'monthly_invoices' table created or already exists.")
    except Exception:
        log.error(
            "APP-LOGIC: Failed to create 'monthly_invoices' table.", exc_info=True
        )
        raise


def add(connection: duckdb.DuckDBPyConnection, invoice: MonthlyInvoice) -> UUID:
    """
    Adds a new monthly invoice to the 'monthly_invoices' table.
    """
    try:
        log.info(
            f"APP-LOGIC: Attempting to add monthly invoice for patient ID {invoice.patient_id}."
        )
        invoice_df = pd.DataFrame([invoice.model_dump()])
        connection.register("invoice_df", invoice_df)

        sql = """
        INSERT INTO monthly_invoices 
        SELECT id, patient_id, invoice_month, session_price, sessions_completed, payment_status, payment_date FROM invoice_df
        """
        connection.execute(sql)
        log.info(
            f"APP-LOGIC: Successfully inserted monthly invoice with ID {invoice.id}."
        )
        return invoice.id
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to add monthly invoice for patient ID {invoice.patient_id}.",
            exc_info=True,
        )
        raise


def get_by_id(
    connection: duckdb.DuckDBPyConnection, invoice_id: UUID
) -> MonthlyInvoice:
    """
    Retrieves a monthly invoice by ID from the 'monthly_invoices' table.
    Returns a Pydantic model instance.
    """
    try:
        log.info(
            f"APP-LOGIC: Attempting to retrieve monthly invoice with ID {invoice_id}."
        )
        sql = "SELECT * FROM monthly_invoices WHERE id = ?;"
        result = connection.execute(sql, (invoice_id,)).fetchone()  # type: ignore

        if result is None:
            log.warning(f"APP-LOGIC: No invoice found with ID {invoice_id}.")
            raise ValueError(f"No invoice found with ID {invoice_id}.")

        invoice = MonthlyInvoice(
            **{k: v for k, v in zip(MonthlyInvoice.model_fields.keys(), result)}  # type: ignore
        )
        log.info(
            f"APP-LOGIC: Successfully retrieved monthly invoice with ID {invoice.id}."
        )
        return invoice
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to retrieve monthly invoice with ID {invoice_id}.",
            exc_info=True,
        )
        raise


def update(connection: duckdb.DuckDBPyConnection, invoice: MonthlyInvoice) -> None:
    """
    Updates an existing monthly invoice's data in the 'monthly_invoices' table.
    """
    try:
        log.info(
            f"APP-LOGIC: Attempting to update monthly invoice with ID {invoice.id}."
        )
        invoice_df = pd.DataFrame([invoice.model_dump()])
        connection.register("invoice_df", invoice_df)

        sql = """
        UPDATE monthly_invoices 
        SET patient_id = invoice_df.patient_id, 
            invoice_month = invoice_df.invoice_month, 
            session_price = invoice_df.session_price, 
            sessions_completed = invoice_df.sessions_completed, 
            payment_status = invoice_df.payment_status, 
            payment_date = invoice_df.payment_date
        FROM invoice_df
        WHERE monthly_invoices.id = invoice_df.id;
        """
        connection.execute(sql)
        log.info(
            f"APP-LOGIC: Successfully updated monthly invoice with ID {invoice.id}."
        )
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to update monthly invoice with ID {invoice.id}.",
            exc_info=True,
        )
        raise
