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
            appointment_date DATE NOT NULL, 
            status VARCHAR CHECK (status IN ('attended', 'cancelled', 'no-show')) NOT NULL
        );
        """
        connection.execute(sql_command)
        log.info("APP-LOGIC: 'appointments' table created or already exists.")
    except Exception:
        log.error("APP-LOGIC: Failed to create 'appointments' table.", exc_info=True)
        raise


def add(connection: duckdb.DuckDBPyConnection, appointment: Appointment) -> UUID:
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
        INSERT INTO appointments 
        SELECT id, patient_id, appointment_date, status FROM appointment_df
        """
        connection.execute(sql)
        log.info(
            f"APP-LOGIC: Successfully inserted appointment with ID {appointment.id}."
        )
        return appointment.id
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
    Retrieves a appointment by ID from the 'appointments' table.
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


def update(connection: duckdb.DuckDBPyConnection, appointment: Appointment) -> None:
    """
    Updates an existing appointment's data in the 'appointments' table.
    """
    try:
        log.info(
            f"APP-LOGIC: Attempting to update appointment with ID {appointment.id}."
        )
        appointment_df = pd.DataFrame([appointment.model_dump()])
        connection.register("appointment_df", appointment_df)

        sql = """
        UPDATE appointments 
        SET patient_id = appointment_df.patient_id, 
            appointment_date = appointment_df.appointment_date, 
            status = appointment_df.status
        FROM appointment_df
        WHERE appointments.id = appointment_df.id;
        """
        connection.execute(sql)
        log.info(
            f"APP-LOGIC: Successfully updated appointment with ID {appointment.id}."
        )
    except Exception:
        log.error(
            f"APP-LOGIC: Failed to update appointment with ID {appointment.id}.",
            exc_info=True,
        )
        raise
