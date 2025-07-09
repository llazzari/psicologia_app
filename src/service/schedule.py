import uuid
from datetime import date, datetime, timedelta
from typing import Any

import streamlit as st

from data import appointment, patient
from data.models import Appointment, Patient
from service.database_manager import get_db_connection
from utils.helpers import get_week_days


@st.cache_data(ttl=3600)
def get_appointment_from(selected_event: dict[str, Any]) -> Appointment:
    connection = get_db_connection()
    event_id: uuid.UUID = get_id_from_event(selected_event)
    return appointment.get_by_id(connection, event_id)


def get_id_from_event(selected_event: dict[str, Any]) -> uuid.UUID:
    event_id: str | None = selected_event.get("id", None)
    if not event_id:
        raise ValueError("Event ID not found")
    return uuid.UUID(event_id)


@st.cache_data(hash_funcs={Appointment: lambda a: a.id}, ttl=3600)
def _turn_weekly_appointments_into_calendar_events(
    appointments: list[Appointment],
) -> list[dict[str, Any]]:
    """
    Converts a list of Appointment objects into a format suitable for the calendar.
    """

    @st.cache_data(hash_funcs={Appointment: lambda a: a.id}, ttl=3600)
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
    connection = get_db_connection()
    appointments: list[Appointment] = appointment.get_all(connection)
    return _turn_weekly_appointments_into_calendar_events(appointments)


def copy_appointments_for_next_week() -> None:
    """Copies all appointments for the current week to the next week."""
    connection = get_db_connection()
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


def get_patients() -> list[Patient] | None:
    connection = get_db_connection()
    return patient.get_all(connection, are_active=True)


def update_appointment(appt: Appointment) -> None:
    connection = get_db_connection()
    appointment.insert(connection, appt)
