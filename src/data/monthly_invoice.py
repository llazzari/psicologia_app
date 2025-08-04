import datetime
import json
from typing import Any
from uuid import UUID

import duckdb
import logfire

from data.db_utils import insert_model
from data.models.invoice_models import AppointmentData, MonthlyInvoice
from utils.helpers import get_last_day_of_month

logfire.configure()


def create_monthly_invoices_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Creates the 'monthly_invoices' table with the expanded schema."""
    try:
        logfire.info(
            "APP-LOGIC: Attempting to create 'monthly_invoices' table with new schema."
        )
        sql_command = """
        CREATE TABLE IF NOT EXISTS monthly_invoices (
            id UUID PRIMARY KEY, 
            patient_id UUID NOT NULL,
            invoice_month INTEGER NOT NULL,
            invoice_year INTEGER NOT NULL,
            appointment_data JSON NOT NULL,
            session_price INTEGER NOT NULL,
            partaking INTEGER NOT NULL DEFAULT 0,
            payment_status VARCHAR CHECK (payment_status IN ('pending', 'paid', 'overdue', 'waived')) NOT NULL,
            nf_number INTEGER,
            payment_date DATE,
            total INTEGER NOT NULL
        );
        """
        connection.execute(sql_command)

        logfire.info("APP-LOGIC: 'monthly_invoices' table created or already exists.")
    except Exception:
        logfire.error(
            "APP-LOGIC: Failed to create 'monthly_invoices' table.", exc_info=True
        )
        raise


def insert(connection: duckdb.DuckDBPyConnection, invoice: MonthlyInvoice) -> UUID:
    try:
        field_map = invoice.model_dump()
        # Remove appointment_data and add it as JSON
        appointment_data = field_map.pop("appointment_data")
        field_map["appointment_data"] = json.dumps(appointment_data, default=str)

        insert_model(
            connection,
            "monthly_invoices",
            field_map,
        )
        logfire.info(
            f"APP-LOGIC: Successfully inserted monthly invoice with ID {invoice.id}."
        )
        return invoice.id
    except Exception:
        logfire.error(
            f"APP-LOGIC: Failed to add monthly invoice for patient ID {invoice.patient_id}.",
            exc_info=True,
        )
        raise


def update(connection: duckdb.DuckDBPyConnection, invoice: MonthlyInvoice) -> None:
    """Updates an existing monthly invoice in the database."""
    try:
        field_map = invoice.model_dump()

        # Handle appointment_data as JSON
        appointment_data = field_map.pop("appointment_data")
        field_map["appointment_data"] = json.dumps(appointment_data, default=str)

        # Build the SET clause for UPDATE
        set_clause = ", ".join([f"{k} = ?" for k in field_map.keys() if k != "id"])
        values = [v for k, v in field_map.items() if k != "id"]
        values.append(invoice.id)  # Add id for WHERE clause

        sql = f"""
            UPDATE monthly_invoices 
            SET {set_clause}
            WHERE id = ?;
        """
        connection.execute(sql, values)

        logfire.info(
            f"APP-LOGIC: Successfully updated monthly invoice with ID {invoice.id}."
        )
    except Exception:
        logfire.error(
            f"APP-LOGIC: Failed to update monthly invoice with ID {invoice.id}.",
            exc_info=True,
        )
        raise


def _fetch_invoice_row(
    connection: duckdb.DuckDBPyConnection, invoice_id: UUID
) -> tuple[Any, ...] | None:
    sql = "SELECT * FROM monthly_invoices WHERE id = ?;"
    return connection.execute(sql, (invoice_id,)).fetchone()  # type: ignore


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
        row = _fetch_invoice_row(connection, invoice_id)
        if row is None:
            log.warning(f"APP-LOGIC: No invoice found with ID {invoice_id}.")
            raise ValueError(f"No invoice found with ID {invoice_id}.")

        # Parse the row data
        field_names = [desc[0] for desc in connection.description]  # type: ignore
        row_dict = dict(zip(field_names, row))

        # Parse appointment_data from JSON
        if row_dict.get("appointment_data"):
            appointment_data_dict = json.loads(row_dict["appointment_data"])
            appointment_data = AppointmentData(**appointment_data_dict)
            row_dict["appointment_data"] = appointment_data

        invoice = MonthlyInvoice(**row_dict)
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


def get_existing_invoices_in_period(
    connection: duckdb.DuckDBPyConnection, month: int, year: int
) -> list[MonthlyInvoice]:
    """
    Retrieves existing monthly invoices for a given month from the 'monthly_invoices' table.
    Returns a list of Pydantic model instances.
    """
    try:
        log.info(
            f"APP-LOGIC: Attempting to retrieve existing invoices for month {month} and year {year}."
        )
        sql = """
            SELECT * FROM monthly_invoices 
            WHERE invoice_month = ? AND invoice_year = ?
            ORDER BY patient_id;
        """
        results = connection.execute(sql, (month, year)).fetchall()  # type: ignore

        if not results:
            log.warning(
                f"APP-LOGIC: No existing invoices found for month {month} and year {year}."
            )
            return []

        invoices: list[MonthlyInvoice] = []

        for row in results:
            # Parse the row data
            field_names = [desc[0] for desc in connection.description]  # type: ignore
            row_dict = dict(zip(field_names, row))

            # Parse appointment_data from JSON
            if row_dict.get("appointment_data"):
                appointment_data_dict = json.loads(row_dict["appointment_data"])
                appointment_data = AppointmentData(**appointment_data_dict)
                row_dict["appointment_data"] = appointment_data

            print(row_dict)
            invoice = MonthlyInvoice(**row_dict)
            invoices.append(invoice)

        log.info(
            f"APP-LOGIC: Successfully retrieved {len(invoices)} existing invoices for month {month} and year {year}."
        )
        return invoices
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to retrieve existing invoices for month {month} and year {year}.",
            exc_info=True,
        )
        raise


def get_all_in_period(
    connection: duckdb.DuckDBPyConnection, month: int, year: int
) -> list[MonthlyInvoice]:
    """
    Retrieves all monthly invoices for a given month. First checks for existing invoices
    in the database, and only generates new ones from appointments if none exist or if
    appointment data has changed.
    Returns a list of Pydantic model instances.
    """
    try:
        log.info(
            f"APP-LOGIC: Attempting to retrieve all invoices for month {month} and year {year}."
        )

        # First, try to get existing invoices from the database
        existing_invoices = get_existing_invoices_in_period(connection, month, year)

        if existing_invoices:
            log.info(
                f"APP-LOGIC: Found {len(existing_invoices)} existing invoices for month {month} and year {year}."
            )

            # Check if appointment data has changed for any invoice
            current_appointment_data = _get_current_appointment_data(
                connection, month, year
            )
            needs_update = False

            for invoice in existing_invoices:
                current_data = current_appointment_data.get(invoice.patient_id)
                if current_data:
                    # The hash comparison is removed, so we just check if the data is different
                    if current_data != invoice.appointment_data:
                        needs_update = True
                        break

            if not needs_update:
                log.info("APP-LOGIC: Existing invoices are up-to-date.")
                return existing_invoices
            else:
                log.info(
                    "APP-LOGIC: Appointment data has changed, regenerating invoices."
                )

        # Generate new invoices from appointments
        log.info(
            f"APP-LOGIC: Generating new invoices from appointments for month {month} and year {year}."
        )

        current_appointment_data = _get_current_appointment_data(
            connection, month, year
        )

        if not current_appointment_data:
            log.warning(
                f"APP-LOGIC: No appointments found for month {month} and year {year}."
            )
            return []

        invoices: list[MonthlyInvoice] = []

        for patient_id, appointment_data in current_appointment_data.items():
            if not appointment_data.appointment_dates:
                log.warning(
                    f"APP-LOGIC: No appointments found for patient ID {patient_id} in month {month} and year {year}."
                )
                continue

            new_invoice = MonthlyInvoice(
                patient_id=patient_id,
                invoice_month=month,
                invoice_year=year,
                appointment_data=appointment_data,
                partaking=0,  # Default value for partaking
            )

            insert(connection, new_invoice)
            invoices.append(new_invoice)

        log.info(
            f"APP-LOGIC: Successfully generated {len(invoices)} new invoices for month {month} and year {year}."
        )
        return invoices
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to retrieve invoices for month {month} and year {year}.",
            exc_info=True,
        )
        raise


def _get_current_appointment_data(
    connection: duckdb.DuckDBPyConnection, month: int, year: int
) -> dict[UUID, AppointmentData]:
    """Get current appointment data for all patients in a given month/year."""
    month_begin: datetime.date = datetime.date(year, month, 1)
    month_end: datetime.date = get_last_day_of_month(year, month)

    sql = """
        SELECT
            patient_id,
            CAST(
                COALESCE(
                    SUM(CASE WHEN status = 'done' AND is_free_of_charge = false THEN duration / 45.0 ELSE 0 END), 
                0)
            AS INTEGER) AS sessions_completed,
            COUNT(CASE WHEN status = 'to recover' THEN 1 END) AS sessions_to_recover,
            COUNT(CASE WHEN is_free_of_charge = true THEN 1 END) AS free_sessions_count,
            COALESCE(
                list(appointment_date ORDER BY appointment_date ASC) FILTER (WHERE status = 'done'),
                []
            ) AS completed_appointment_dates
        FROM
            appointments
        WHERE
            appointment_date BETWEEN ? AND ?
        GROUP BY
            patient_id;
    """

    results = connection.execute(sql, (month_begin, month_end)).fetchall()  # type: ignore

    appointment_data: dict[UUID, AppointmentData] = {}

    for row in results:
        patient_id = row[0]
        sessions_completed = row[1]
        sessions_to_recover = row[2]
        free_sessions = row[3] if row[3] is not None else 0
        appointment_dates = [date for date in row[4] if date is not None]

        appointment_data[patient_id] = AppointmentData(
            sessions_completed=sessions_completed,
            sessions_to_recover=sessions_to_recover,
            free_sessions=free_sessions,
            appointment_dates=appointment_dates,
        )

    return appointment_data
