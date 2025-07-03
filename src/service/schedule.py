import uuid
from datetime import date, datetime, timedelta
from typing import Any

import duckdb

from data import appointment, database
from data.database import DB_PATH
from data.models import Appointment
from utils.helpers import get_week_days


def get_appointment_from(
    connection: duckdb.DuckDBPyConnection, selected_event: dict[str, Any]
) -> Appointment:
    event_id: uuid.UUID = get_id_from_event(selected_event)
    return appointment.get_by_id(connection, event_id)


def get_id_from_event(selected_event: dict[str, Any]) -> uuid.UUID:
    event_id: str | None = selected_event.get("id", None)
    if not event_id:
        raise ValueError("Event ID not found")
    return uuid.UUID(event_id)


def _turn_weekly_appointments_into_calendar_events(
    appointments: list[Appointment],
) -> list[dict[str, Any]]:
    """
    Converts a list of Appointment objects into a format suitable for the calendar.
    """

    def _turn_appointment_into_event(appt: Appointment) -> dict[str, Any]:
        """
        Converts a single Appointment object into a calendar event dictionary.
        """
        return {
            "id": str(appt.id),
            "title": f"{appt.patient_name} ({appt.notes})"
            if appt.notes
            else appt.patient_name,
            "start": datetime.combine(
                appt.appointment_date, appt.appointment_time
            ).isoformat(),
            "end": (
                datetime.combine(appt.appointment_date, appt.appointment_time)
                + timedelta(minutes=appt.duration)
            ).isoformat(),
            "allDay": False,
        }

    return [_turn_appointment_into_event(appt) for appt in appointments]


def get_calendar_events() -> list[dict[str, Any]]:
    """Returns a list of calendar events for a given period."""
    with database.connect(DB_PATH) as connection:
        appointments: list[Appointment] = appointment.get_all(connection)
        return _turn_weekly_appointments_into_calendar_events(appointments)


def copy_appointments_for_next_week() -> None:
    """Copies all appointments for the current week to the next week."""
    with database.connect(DB_PATH) as connection:
        next_week_appointments: list[Appointment] = appointment.get_all(
            connection, period=get_week_days(date.today() + timedelta(days=7))
        )
        this_week_appointments: list[Appointment] = appointment.get_all(
            connection, period=get_week_days(date.today())
        )
        if next_week_appointments:
            return
        for appt in this_week_appointments:
            appt.id = uuid.uuid4()
            appt.appointment_date += timedelta(days=7)
            appointment.insert(connection, appt)
