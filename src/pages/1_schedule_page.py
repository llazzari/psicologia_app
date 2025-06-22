from datetime import datetime

import pandas as pd
import streamlit as st

from data import appointment, database
from data.database import DB_PATH
from utils.helpers import get_week_days  # type: ignore

st.set_page_config(layout="wide")
st.title("🗓️ Agendamento Semanal")

if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.today().date()

# !FIXME Align col3 with the right side of the page
col1, col3 = st.columns([1, 1])
with col1:
    if st.button("⬅️ Semana Anterior"):
        st.session_state.current_date -= pd.Timedelta(weeks=1)
        st.rerun()
with col3:
    if st.button("Próxima Semana ➡️"):
        st.session_state.current_date += pd.Timedelta(weeks=1)
        st.rerun()

week_days = get_week_days(st.session_state.current_date)  # type: ignore

with database.connect(DB_PATH) as connection:
    appointments: pd.DataFrame = appointment.list_all_for_week(connection, week_days)  # type: ignore


updated_df = st.data_editor(appointments, use_container_width=True)  # type: ignore
