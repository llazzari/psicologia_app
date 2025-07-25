import datetime
from typing import Any, Optional
from uuid import UUID

import duckdb
import logfire

from data.db_utils import insert_model
from data.models.appointment_models import Appointment

logfire.configure()


def create_appointments_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Creates the 'appointments' table with the required schema."""
    try:
        logfire.info("APP-LOGIC: Attempting to create 'appointments' table.")
        sql_command = """
        CREATE TABLE IF NOT EXISTS appointments (
            id UUID PRIMARY KEY, 
            patient_id UUID NOT NULL,
            appointment_date DATE NOT NULL,
            appointment_time TIME NOT NULL,
            duration INTEGER DEFAULT 45 NOT NULL, -- in minutes
            is_free_of_charge BOOLEAN DEFAULT FALSE NOT NULL,
            notes VARCHAR DEFAULT '' NOT NULL,
            status VARCHAR CHECK (status IN ('done', 'to recover', 'cancelled')) DEFAULT 'done' NOT NULL
        );
        """
        connection.execute(sql_command)
        logfire.info("APP-LOGIC: 'appointments' table created or already exists.")
    except Exception:
        logfire.error(
            "APP-LOGIC: Failed to create 'appointments' table.", exc_info=True
        )
        raise


def insert(connection: duckdb.DuckDBPyConnection, appointment: Appointment) -> None:
    try:
        insert_model(
            connection,
            "appointments",
            appointment.model_dump(),
        )
        logfire.info(f"Inserted appointment with ID {appointment.id}")
    except Exception:
        logfire.error(
            f"Failed to insert appointment with ID {appointment.id}", exc_info=True
        )
        raise


def _fetch_appointment_row(
    connection: duckdb.DuckDBPyConnection, appointment_id: UUID
) -> tuple[Any, ...] | None:
    sql = "SELECT * FROM appointments WHERE id = ?;"
    return connection.execute(sql, (appointment_id,)).fetchone()  # type: ignore


def get_by_id(
    connection: duckdb.DuckDBPyConnection, appointment_id: UUID
) -> Appointment:
    """
    Retrieves an appointment by ID from the 'appointments' table.
    Returns a Pydantic model instance.
    """
    try:
        logfire.info(
            f"APP-LOGIC: Attempting to retrieve appointment with ID {appointment_id}."
        )
        row = _fetch_appointment_row(connection, appointment_id)
        if row is None:
            logfire.warning(
                f"APP-LOGIC: No appointment found with ID {appointment_id}."
            )
            raise ValueError(f"No appointment found with ID {appointment_id}.")

        appointment = Appointment(
            **{k: v for k, v in zip(Appointment.model_fields.keys(), row)}
        )
        logfire.info(
            f"APP-LOGIC: Successfully retrieved appointment with ID {appointment.id}."
        )
        return appointment
    except Exception:
        logfire.error(
            f"APP-LOGIC: Failed to retrieve patient with ID {appointment_id}.",
            exc_info=True,
        )
        raise


def get_all(
    connection: duckdb.DuckDBPyConnection,
    period: Optional[list[datetime.date]] = None,  # type: ignore
) -> list[Appointment]:
    """
    Lists all appointments for a given period.
    """
    try:
        logfire.info("APP-LOGIC: Attempting to list appointments with patient names.")
        sql = """
        SELECT * FROM appointments 
        WHERE status == 'done' AND 
        appointment_date BETWEEN ? AND ?
        """

        if not period:
            today: datetime.date = datetime.date.today()
            period: list[datetime.date] = [
                datetime.date(today.year, 1, 1),
                today + datetime.timedelta(days=30),
            ]
        cursor = connection.execute(sql, (period[0], period[1]))

        return [
            Appointment(
                **{k: v for k, v in zip(Appointment.model_fields.keys(), result)}  # type: ignore
            )
            for result in cursor.fetchall()
        ]
    except Exception:
        logfire.error(
            "Failed to retrieve appointments.",
            exc_info=True,
        )
        raise


def remove(connection: duckdb.DuckDBPyConnection, appointment_id: UUID) -> None:
    """
    Removes an appointment by ID from the 'appointments' table.
    """
    try:
        logfire.info(
            f"APP-LOGIC: Attempting to remove appointment with ID {appointment_id}."
        )
        sql = "DELETE FROM appointments WHERE id = ?;"
        connection.execute(sql, (appointment_id,))
        logfire.info(
            f"APP-LOGIC: Successfully removed appointment with ID {appointment_id}."
        )
    except Exception:
        logfire.error(
            f"APP-LOGIC: Failed to remove appointment with ID {appointment_id}.",
            exc_info=True,
        )
        raise
