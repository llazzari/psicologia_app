import uuid
from datetime import datetime, timedelta
from typing import Any

import duckdb

from data import appointment, database
from data.database import MOCK_DB_PATH
from data.models import Appointment


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
    with database.connect(MOCK_DB_PATH) as connection:
        appointments: list[Appointment] = appointment.get_all(connection)
        return _turn_weekly_appointments_into_calendar_events(appointments)
