import uuid
from datetime import date, datetime, timedelta
from typing import Any

import logfire
import streamlit as st

from data import appointment, patient
from data.models.appointment_models import Appointment
from data.models.patient_models import Patient
from service.database_manager import get_db_connection
from service.patient_manager import get_patient_by_id
from utils.helpers import get_week_days

logfire.configure()


@st.cache_data(ttl=3600)
def get_appointment_from(selected_event: dict[str, Any]) -> Appointment:
    logfire.info(
        f"SERVICE-OP: Fetching appointment from selected event: {selected_event.get('id', 'unknown')}"
    )
    connection = get_db_connection()
    event_id: uuid.UUID = get_id_from_event(selected_event)
    appt = appointment.get_by_id(connection, event_id)
    logfire.info(f"SERVICE-OP: Retrieved appointment {appt.id} for event {event_id}")
    return appt


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
        patient = get_patient_by_id(appt.patient_id)
        patient_name = patient.info.name if patient else "Paciente desconhecido"
        return {
            "id": str(appt.id),
            "title": f"{patient_name} ({appt.notes})" if appt.notes else patient_name,
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
    logfire.info("SERVICE-OP: Fetching calendar events")
    connection = get_db_connection()
    appointments: list[Appointment] = appointment.get_all(connection)
    events = _turn_weekly_appointments_into_calendar_events(appointments)
    logfire.info(
        f"SERVICE-OP: Generated {len(events)} calendar events from {len(appointments)} appointments"
    )
    return events


def copy_appointments_for_next_week() -> None:
    """Copies all appointments for the current week to the next week."""
    logfire.info("SERVICE-OP: Copying appointments for next week")
    connection = get_db_connection()
    next_week_appointments: list[Appointment] = appointment.get_all(
        connection, period=get_week_days(date.today() + timedelta(days=7))
    )
    this_week_appointments: list[Appointment] = appointment.get_all(
        connection, period=get_week_days(date.today())
    )
    if next_week_appointments:
        logfire.info("SERVICE-OP: Next week already has appointments, skipping copy")
        return
    logfire.info(
        f"SERVICE-OP: Copying {len(this_week_appointments)} appointments to next week"
    )
    for appt in this_week_appointments:
        appt.id = uuid.uuid4()
        appt.appointment_date += timedelta(days=7)
        appointment.insert(connection, appt)
    logfire.info("SERVICE-OP: Successfully copied appointments to next week")


def get_patients() -> list[Patient] | None:
    logfire.info("SERVICE-OP: Fetching active patients for schedule")
    connection = get_db_connection()
    patients = patient.get_all(connection, are_active=True)
    logfire.info(f"SERVICE-OP: Retrieved {len(patients)} active patients")
    return patients


def update_appointment(appt: Appointment) -> None:
    logfire.info(
        f"SERVICE-OP: Updating appointment {appt.id} for patient {appt.patient_id}"
    )
    connection = get_db_connection()
    appointment.insert(connection, appt)
    logfire.info(f"SERVICE-OP: Successfully updated appointment {appt.id}")
