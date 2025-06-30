import uuid
from datetime import date, datetime, time
from typing import Any, Optional

import streamlit as st
from streamlit_calendar import calendar  # type: ignore

from data import appointment, database, patient
from data.models import Appointment, Patient
from service.schedule import get_appointment_from, get_calendar_events

st.set_page_config(layout="wide")
st.title("🗓️ Agendamento Semanal")


@st.dialog("Agende a sessão", width="large")
def schedule_appointment(
    selected_datetime: Optional[datetime] = None,
    selected_event: Optional[dict[str, Any]] = None,
) -> None:
    if not selected_datetime and not selected_event:
        raise ValueError("selected_datetime and selected_event must be provided")

    with database.connect(database.MOCK_DB_PATH) as connection:
        patients: list[Patient] = patient.get_all(connection)
        print(patients)
        if not patients:
            st.warning("Nenhum paciente cadastrado. Cadastre um paciente primeiro.")
            return

        date_value: date = datetime.now().date()
        time_value: time = datetime.now().time()
        duration_value: int = 45
        is_free_of_charge_value: bool = False
        notes_value: str = ""
        appt_id: uuid.UUID = uuid.uuid4()
        index: int = 0

        if selected_event:
            appt: Appointment = get_appointment_from(connection, selected_event)
            pat: Patient = patient.get_by_id(connection, appt.patient_id)
            index: int = patients.index(pat)
            date_value: date = appt.appointment_date
            time_value: time = appt.appointment_time
            duration_value: int = appt.duration
            is_free_of_charge_value: bool = appt.is_free_of_charge
            notes_value: str = appt.notes
            appt_id: uuid.UUID = appt.id
        elif selected_datetime:
            date_value: date = selected_datetime.date()
            time_value: time = selected_datetime.time()

        selected_patient = st.selectbox(
            "Selecione um paciente",
            patients,
            format_func=lambda p: p.name,
            placeholder="Selecione um paciente",
            index=index,
        )

        col_1, col_2, col_3 = st.columns(3, vertical_alignment="center")
        with col_1:
            appointment_date = st.date_input(
                "Data da sessão",
                value=date_value,
            )
        with col_2:
            appointment_time = st.time_input(
                "Horário de início", value=time_value, step=300
            )
        with col_3:
            duration = st.number_input(
                "Duração (minutos)",
                min_value=15,
                max_value=300,  # 5 hours max
                value=duration_value,
                step=5,
                format="%d",
                help="Duração da sessão em minutos: 1 sessão típica -> 45 min, 2 sessões -> 90 min, 3 sessões -> 135 min.",
            )

        is_free_of_charge = st.checkbox("É gratuita?", value=is_free_of_charge_value)

        notes = st.text_area("Observações", value=notes_value)

        appt = Appointment(
            id=appt_id,
            patient_id=selected_patient.id,
            patient_name=selected_patient.name,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            duration=duration,
            is_free_of_charge=is_free_of_charge,
            notes=notes,
        )

        col1, col2, col3 = st.columns([2, 2, 1])
        if selected_event:
            with col1:
                if st.button(
                    "Cancelar", help="Cancela a sessão e a remove do calendário."
                ):
                    appointment.remove(connection, appt.id)
                    st.warning("Agendamento cancelado.")
                    st.rerun()
            with col2:
                if st.button(
                    "Remarcar",
                    help="Remove a sessão do calendário mas permite a remarcação posteriormente.",
                ):
                    appt.status = "to recover"
                    appointment.insert(connection, appt)
                    st.warning("Agendamento remarcado.")
                    st.rerun()
        with col3:
            with st.columns([1, 3])[1]:
                if st.button("Agendar", type="primary"):
                    appointment.insert(connection, appt)
                    st.success("Consulta agendada!")
                    st.rerun()


calendar_options: dict[str, Any] = {
    "editable": True,
    "selectable": True,
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "timeGridDay,timeGridWeek",
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
custom_css: str = """
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

# Always get the latest events just before rendering the calendar
calendar_events: list[dict[str, Any]] = get_calendar_events()

calendar_callback = calendar(
    events=calendar_events,
    options=calendar_options,
    custom_css=custom_css,
)

selected_event: dict[str, Any] | None = calendar_callback.get("eventClick", {}).get(
    "event", None
)
selected_datetime_iso: str | None = calendar_callback.get("dateClick", {}).get(
    "date", None
)


if selected_event:
    schedule_appointment(selected_event=selected_event)
elif selected_datetime_iso:
    selected_datetime: datetime = datetime.fromisoformat(selected_datetime_iso)
    schedule_appointment(selected_datetime=selected_datetime)
