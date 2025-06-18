from datetime import datetime

import pandas as pd
import streamlit as st

from utils.helpers import generate_time_slots, get_week_days  # type: ignore

st.set_page_config(layout="wide")
st.title("🗓️ Agendamento Semanal")

if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.today().date()

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("⬅️ Semana Anterior"):
        st.session_state.current_date -= pd.Timedelta(weeks=1)
        st.rerun()
with col3:
    if st.button("Próxima Semana ➡️"):
        st.session_state.current_date += pd.Timedelta(weeks=1)
        st.rerun()

# --- Calendar Grid ---
week_days = get_week_days(st.session_state.current_date)  # type: ignore
morning_time_slots = generate_time_slots(
    start_hour=8, start_minutes=0, end_hour=11, end_minutes=45, interval_minutes=45
)
afternoon_time_slots = generate_time_slots(
    start_hour=13, start_minutes=30, end_hour=19, end_minutes=30, interval_minutes=45
)
time_slots = morning_time_slots + afternoon_time_slots

days_of_week_pt = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
days_of_week = [
    f"{pt_day} ({day.strftime('%d/%m')})"  # type: ignore
    for day, pt_day in zip(week_days, days_of_week_pt)  # type: ignore
]
time_labels = [slot.strftime("%H:%M") for slot in time_slots]
data = {day: [""] * len(time_slots) for day in days_of_week}
df = pd.DataFrame(data, index=time_labels)
df.index.name = "Horário"

st.dataframe(df, use_container_width=True, height=600)  # type: ignore
