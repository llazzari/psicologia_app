import datetime
import logging
from uuid import UUID

import duckdb
import pandas as pd

from data.models import Appointment
from utils.helpers import generate_time_slots

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
            appointment_hour TIME NOT NULL,
            status VARCHAR CHECK (status IN ('attended', 'cancelled', 'no-show')) NOT NULL,
            weekday VARCHAR DEFAULT NULL
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
        SELECT id, patient_id, appointment_date, appointment_hour, status, weekday FROM appointment_df
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


def update(connection: duckdb.DuckDBPyConnection, appointment: Appointment) -> None:
    """
    Updates an existing appointment's data in the 'appointments' table.
    """
    log.info(f"APP-LOGIC: Attempting to update appointment with ID {appointment.id}.")

    appointment_df = pd.DataFrame([appointment.model_dump()])

    connection.register("appointment_df", appointment_df)

    sql = """
    UPDATE appointments 
    SET patient_id = appointment_df.patient_id, 
        appointment_date = appointment_df.appointment_date,
        appointment_hour = appointment_df.appointment_hour,
        status = appointment_df.status,
        weekday = appointment_df.weekday
    FROM appointment_df
    WHERE appointments.id = appointment_df.id;
    """

    connection.execute(sql)
    # Ensure weekday is set
    if not appointment.weekday:
        appointment = appointment.model_copy(update={"weekday": None})

    log.info(f"APP-LOGIC: Successfully updated appointment with ID {appointment.id}.")


def list_all_for_week(
    connection: duckdb.DuckDBPyConnection, week: list[datetime.date]
) -> pd.DataFrame:
    """
    Lists all appointments for the given week in a format ready for the schedule page.
    Returns a DataFrame with:
    - Time slots as index
    - Days of the week as columns (e.g. 'Segunda (20/06)')
    - Patient names in the cells
    """
    try:
        log.info("APP-LOGIC: Attempting to list appointments with patient names.")
        sql = """
        SELECT 
            a.weekday as day_column,
            a.appointment_hour,
            p.name as patient_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.appointment_date BETWEEN ? AND ?
        """
        cursor = connection.execute(sql, (min(week), max(week)))
        df: pd.DataFrame = cursor.df()

        days = [
            f"{['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta'][d.weekday()]} ({d.day:02d}/{d.month:02d})"
            for d in week
        ]

        morning_time_slots = generate_time_slots(
            start_hour=8,
            start_minutes=0,
            end_hour=11,
            end_minutes=45,
            interval_minutes=45,
        )
        afternoon_time_slots = generate_time_slots(
            start_hour=13,
            start_minutes=30,
            end_hour=19,
            end_minutes=30,
            interval_minutes=45,
        )
        time_slots = morning_time_slots + afternoon_time_slots

        if df.empty:
            log.warning("No appointments found.")
            # Create an empty DataFrame with the correct structure

            df = pd.DataFrame(columns=days)
        else:
            # Pivot the DataFrame so that each weekday is a column
            df = df.pivot(
                index="appointment_hour", columns="day_column", values="patient_name"
            ).reindex(index=time_slots, columns=days, fill_value="")
        df.index.name = "Horário"
        df.index = pd.to_datetime(df.index.astype(str)).strftime("%H:%M")  # type: ignore
        df.fillna("", inplace=True)  # type: ignore
        log.info("Successfully retrieved appointments schedule for the week.")
        return df
    except Exception:
        log.error(
            "Failed to retrieve appointments.",
            exc_info=True,
        )
        raise
