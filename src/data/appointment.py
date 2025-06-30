import logging
from uuid import UUID

import duckdb
import pandas as pd

from data.models import Appointment

log = logging.getLogger("TestLogger")


def create_appointments_table(connection: duckdb.DuckDBPyConnection) -> None:
    """Creates the 'appointments' table with the required schema."""
    try:
        log.info("APP-LOGIC: Attempting to create 'appointments' table.")
        sql_command = """
        CREATE TABLE IF NOT EXISTS appointments (
            id UUID PRIMARY KEY, 
            patient_id UUID NOT NULL,
            patient_name VARCHAR NOT NULL, 
            appointment_date DATE NOT NULL,
            appointment_time TIME NOT NULL,
            duration INTEGER DEFAULT 45 NOT NULL, -- in minutes
            is_free_of_charge BOOLEAN DEFAULT FALSE NOT NULL,
            notes VARCHAR DEFAULT '' NOT NULL,
            status VARCHAR CHECK (status IN ('done', 'to recover')) DEFAULT 'done' NOT NULL
        );
        """
        connection.execute(sql_command)
        log.info("APP-LOGIC: 'appointments' table created or already exists.")
    except Exception:
        log.error("APP-LOGIC: Failed to create 'appointments' table.", exc_info=True)
        raise


def insert(connection: duckdb.DuckDBPyConnection, appointment: Appointment) -> None:
    """
    Adds a new appointment to the 'appointments' table.
    The appointment should be a dictionary with keys matching the table schema.
    """
    try:
        log.info(
            f"APP-LOGIC: Attempting to add appointment for patient ID {appointment.patient_id}."
        )
        appointment_df = pd.DataFrame([appointment.model_dump()])
        connection.register("appointment_df", appointment_df)

        sql = """
        INSERT OR REPLACE INTO appointments 
        SELECT 
            id, 
            patient_id, 
            patient_name,
            appointment_date,
            appointment_time, 
            duration,
            is_free_of_charge,
            notes,
            status 
        FROM appointment_df
        """
        connection.execute(sql)
        log.info(
            f"APP-LOGIC: Successfully inserted appointment with ID {appointment.id}."
        )
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to add appointment for patient ID {appointment.patient_id}.",
            exc_info=True,
        )
        raise


def get_by_id(
    connection: duckdb.DuckDBPyConnection, appointment_id: UUID
) -> Appointment:
    """
    Retrieves an appointment by ID from the 'appointments' table.
    Returns a Pydantic model instance.
    """
    try:
        log.info(
            f"APP-LOGIC: Attempting to retrieve appointment with ID {appointment_id}."
        )
        sql = "SELECT * FROM appointments WHERE id = ?;"
        result = connection.execute(sql, (appointment_id,)).fetchone()  # type: ignore

        if result is None:
            log.warning(f"APP-LOGIC: No appointment found with ID {appointment_id}.")
            raise ValueError(f"No appointment found with ID {appointment_id}.")

        appointment = Appointment(
            **{k: v for k, v in zip(Appointment.model_fields.keys(), result)}  # type: ignore
        )
        log.info(
            f"APP-LOGIC: Successfully retrieved appointment with ID {appointment.id}."
        )
        return appointment
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to retrieve patient with ID {appointment_id}.",
            exc_info=True,
        )
        raise


def get_all(connection: duckdb.DuckDBPyConnection) -> list[Appointment]:
    """
    Lists all appointments for the given week.
    """
    try:
        log.info("APP-LOGIC: Attempting to list appointments with patient names.")
        sql = """SELECT * FROM appointments WHERE status == 'done'"""
        cursor = connection.execute(sql)

        return [
            Appointment(
                **{k: v for k, v in zip(Appointment.model_fields.keys(), result)}  # type: ignore
            )
            for result in cursor.fetchall()
        ]
    except Exception:
        log.error(
            "Failed to retrieve appointments.",
            exc_info=True,
        )
        raise


def remove(connection: duckdb.DuckDBPyConnection, appointment_id: UUID) -> None:
    """
    Removes an appointment by ID from the 'appointments' table.
    """
    try:
        log.info(
            f"APP-LOGIC: Attempting to remove appointment with ID {appointment_id}."
        )
        sql = "DELETE FROM appointments WHERE id = ?;"
        connection.execute(sql, (appointment_id,))
        log.info(
            f"APP-LOGIC: Successfully removed appointment with ID {appointment_id}."
        )
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to remove appointment with ID {appointment_id}.",
            exc_info=True,
        )
        raise
