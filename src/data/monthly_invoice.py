import datetime
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
            invoice_month INTEGER NOT NULL,
            invoice_year INTEGER NOT NULL,
            session_price INTEGER NOT NULL,
            sessions_completed INTEGER NOT NULL,
            sessions_to_recover INTEGER NOT NULL,
            payment_status VARCHAR CHECK (payment_status IN ('pending', 'paid', 'overdue', 'waived')) NOT NULL,
            nf_number INTEGER,
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


def insert(connection: duckdb.DuckDBPyConnection, invoice: MonthlyInvoice) -> UUID:
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
        INSERT OR REPLACE INTO monthly_invoices 
        SELECT 
            id, 
            patient_id, 
            invoice_month, 
            invoice_year, 
            session_price, 
            sessions_completed, 
            sessions_to_recover, 
            payment_status, 
            nf_number, 
            payment_date
        FROM invoice_df
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


def get_all_in_period(
    connection: duckdb.DuckDBPyConnection, month: int, year: int
) -> list[MonthlyInvoice]:
    """
    Retrieves all monthly invoices for a given month from the 'monthly_invoices' table.
    Returns a list of Pydantic model instances.
    """
    try:
        log.info(
            f"APP-LOGIC: Attempting to retrieve all invoices for month {month} and year {year}."
        )
        month_begin: datetime.date = datetime.date(year, month, 1)
        month_end: datetime.date = month_begin + datetime.timedelta(days=31)
        sql = """
            SELECT
                patient_id,
                -- Conta condicionalmente as sessões com status 'done'
                COUNT(CASE WHEN status = 'done' THEN 1 END) AS sessions_completed,
                -- Conta condicionalmente as sessões com status 'to recover'
                COUNT(CASE WHEN status = 'to recover' THEN 1 END) AS sessions_to_recover,
                 -- CONTA SEPARADAMENTE AS SESSÕES GRATUITAS
                COUNT(CASE WHEN is_free_of_charge = true THEN 1 END) AS free_sessions_count,
                -- Agrega todas as datas de agendamento feitos em uma lista
                COALESCE(
                    list(appointment_date ORDER BY appointment_date ASC) FILTER (WHERE status = 'done'),
                    []
                ) AS completed_appointment_dates
            FROM
                appointments
            WHERE
                -- Filtra os agendamentos para um mês e ano específicos (ex: Junho de 2025)
                appointment_date BETWEEN ? AND ?
            GROUP BY
                patient_id;
        """
        results = connection.execute(sql, (month_begin, month_end)).fetchall()  # type: ignore

        if not results:
            log.warning(
                f"APP-LOGIC: No invoices found for month {month} and year {year}."
            )
            return []

        invoices: list[MonthlyInvoice] = []

        for row in results:
            patient_id = row[0]
            sessions_completed = row[1]
            sessions_to_recover = row[2]
            free_sessions = row[3]
            appointment_dates = [date for date in row[4] if date is not None]

            if not appointment_dates:
                log.warning(
                    f"APP-LOGIC: No appointments found for patient ID {patient_id} in month {month} and year {year}."
                )
                continue

            new_invoice = MonthlyInvoice(
                patient_id=patient_id,
                invoice_month=month,
                invoice_year=year,
                appointment_dates=appointment_dates,
                sessions_completed=sessions_completed,
                sessions_to_recover=sessions_to_recover,
                free_sessions=free_sessions,
            )

            insert(connection, new_invoice)

            invoices.append(new_invoice)

        log.info(
            f"APP-LOGIC: Successfully retrieved {len(invoices)} invoices for month {month} and year {year}."
        )
        return invoices
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to retrieve invoices for month {month} and year {year}.",
            exc_info=True,
        )
        raise
