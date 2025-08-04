from datetime import datetime
from typing import Any, Optional

import logfire
import streamlit as st
from streamlit_calendar import calendar  # type: ignore

from data.models.appointment_models import Appointment
from data.models.patient_models import Patient
from modules import navbar
from service.patient_manager import get_patient_by_id
from service.schedule import (
    get_appointment_from,
    get_calendar_events,
    get_patients,
    update_appointment,
)

logfire.configure()


@st.dialog("Agende a sessão", width="large")
def schedule_appointment(
    selected_datetime: Optional[datetime] = None,
    selected_event: Optional[dict[str, Any]] = None,
) -> None:
    if selected_event:
        logfire.info(
            f"USER-ACTION: Opening appointment edit modal for event: {selected_event.get('id', 'unknown')}"
        )
    elif selected_datetime:
        logfire.info(
            f"USER-ACTION: Opening appointment creation modal for datetime: {selected_datetime}"
        )

    if not selected_datetime and not selected_event:
        raise ValueError("selected_datetime and selected_event must be provided")

    patients = get_patients()
    if not patients:
        st.warning("Nenhum paciente cadastrado. Cadastre um paciente primeiro.")
        return

    index: int = 0  # type: ignore
    appt = Appointment(patient_id=patients[0].id)

    if selected_event:
        appt: Appointment = get_appointment_from(selected_event)
        patient_: Patient = get_patient_by_id(appt.patient_id)
        index: int = patients.index(patient_)
    elif selected_datetime:
        appt.appointment_date = selected_datetime.date()
        appt.appointment_time = selected_datetime.time()
    else:
        raise ValueError("One of selected_datetime and selected_event must be provided")

    with st.form("appointment_form", border=False):
        selected_patient: Patient = st.selectbox(
            "Selecione um paciente",
            patients,
            format_func=lambda p: p.info.name,
            placeholder="Selecione um paciente",
            index=index,
        )

        appt.patient_id = selected_patient.id

        col_1, col_2, col_3 = st.columns(3, vertical_alignment="center")
        with col_1:
            appt.appointment_date = st.date_input(
                "Data da sessão",
                value=appt.appointment_date,
            )
        with col_2:
            appt.appointment_time = st.time_input(
                "Horário de início", value=appt.appointment_time, step=300
            )
        with col_3:
            appt.duration = st.number_input(
                "Duração (minutos)",
                min_value=15,
                max_value=300,  # 5 hours max
                value=appt.duration,
                step=5,
                format="%d",
                help="Duração da sessão em minutos: 1 sessão típica -> 45 min, 2 sessões -> 90 min, 3 sessões -> 135 min.",
            )

        col_1, _, col_2 = st.columns([1, 2, 2], vertical_alignment="center")
        with col_1:
            appt.is_free_of_charge = st.checkbox(
                "É gratuita?", value=appt.is_free_of_charge
            )
        with col_2:
            translated_status: dict[str, str] = {
                "done": "Realizada",
                "to recover": "A recuperar",
                "cancelled": "Cancelada",
            }
            pills_options: list[str] = (
                ["done", "to recover", "cancelled"] if selected_event else ["done"]
            )
            appt.status = st.pills(
                "Status",
                options=pills_options,
                default="done",
                format_func=lambda x: translated_status[x],
                help="Status da sessão. 'Realizada' contempla sessões que foram ou serão realizadas. 'A recuperar' contempla sessões que podem ser remarcadas. 'Cancelada' contempla sessões canceladas que não serão remarcadas.",
            )  # type: ignore

        appt.notes = st.text_area("Observações", value=appt.notes)

        submitted = st.form_submit_button("Salvar", type="primary")

        if submitted:
            logfire.info(
                f"USER-ACTION: User saved appointment {appt.id} for patient {appt.patient_id}"
            )
            update_appointment(appt)
            st.toast("Alterações salvas.", icon=":material/event_available:")
            st.session_state.event = appt
            st.rerun()


CALENDAR_OPTIONS: dict[str, Any] = {
    "editable": True,
    "selectable": True,
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "timeGridDay,timeGridWeek,dayGridMonth",
    },
    "slotMinTime": "08:00:00",
    "slotMaxTime": "19:30:00",
    "slotDuration": "01:00:00",
    "slotLabelFormat": {
        "hour": "numeric",
        "minute": "2-digit",
        "omitZeroMinute": False,
    },
    "allDaySlot": False,
    "scrollTime": "08:00:00",
    "expandRows": True,
    "locale": "pt-br",
    "timeZone": "America/Sao_Paulo",
    "weekends": False,
    "initialView": "timeGridWeek",
}
CUSTOM_CSS: str = """
    .fc-event-past {
        opacity: 0.8;
    }
    .fc-event-time {
        font-style: italic;
    }
    .fc-event-title {
        font-weight: 700;
    }
    .fc-toolbar-title {
        font-size: 2rem;
    }
"""


def render() -> None:
    logfire.info("PAGE-RENDER: Rendering schedule page")
    st.set_page_config(
        layout="wide",
        page_title="Agendamento Semanal",
        initial_sidebar_state="collapsed",
        page_icon=":material/network_intelligence:",
    )
    st.title("Agendamento Semanal")

    navbar.render()

    # Always get the latest events just before rendering the calendar
    logfire.info("DATA-FETCH: Loading calendar events for schedule page")
    calendar_events: list[dict[str, Any]] = get_calendar_events()
    logfire.info(f"DATA-FETCH: Loaded {len(calendar_events)} calendar events")

    calendar_callback = calendar(
        events=calendar_events,
        options=CALENDAR_OPTIONS,
        custom_css=CUSTOM_CSS,
    )

    selected_event: dict[str, Any] | None = calendar_callback.get("eventClick", {}).get(
        "event", None
    )
    selected_datetime_iso: str | None = calendar_callback.get("dateClick", {}).get(
        "date", None
    )

    if "event" not in st.session_state:
        if selected_event:
            schedule_appointment(selected_event=selected_event)
        elif selected_datetime_iso:
            selected_datetime: datetime = datetime.fromisoformat(selected_datetime_iso)
            schedule_appointment(selected_datetime=selected_datetime)
    else:
        st.session_state.pop("event")


if __name__ == "__main__":
    render()
