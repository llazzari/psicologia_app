from datetime import datetime

import duckdb
import numpy as np
import streamlit as st

from data import monthly_invoice, patient
from data.models import MonthlyInvoice, Patient
from modules import navbar
from service.database_manager import get_db_connection

st.set_page_config(
    layout="wide",
    page_title="Controle Financeiro",
    initial_sidebar_state="collapsed",
)

navbar.render()


def _get_total(
    sessions_completed: int,
    sessions_to_recover: int,
    session_price: int,
    free_sessions: int,
) -> str:
    total: float = (
        session_price * (sessions_completed + sessions_to_recover - free_sessions) / 100
    )
    return f"R$ {total:,.2f}".replace(",", "-").replace(".", ",").replace("-", ".")


def _update_invoice_metrics(
    connection: duckdb.DuckDBPyConnection,
    month_invoice: MonthlyInvoice,
    patient_: Patient,
) -> None:
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(
        8, vertical_alignment="center"
    )
    with col1:
        st.markdown(f"**{patient_.name}**")
    col2.metric(
        label="Realizadas",
        value=month_invoice.sessions_completed,
        help="Sessões realizadas no mês. Inclui sessões gratuitas.",
    )
    col3.metric(
        label="A recuperar",
        value=month_invoice.sessions_to_recover,
        help="Sessões a recuperar.",
    )
    with col4:
        with st.popover("Datas das sessões"):
            formatted_dates: dict[str, list[str]] = {
                "Datas das sessões": [
                    date.strftime("%d/%m/%Y")
                    for date in month_invoice.appointment_dates
                ]
            }
            st.dataframe(  # type: ignore
                formatted_dates,
                hide_index=True,
                use_container_width=True,
            )
    with col5:
        month_invoice.session_price = int(
            st.number_input(
                label="Preço (R$)",
                value=np.round(float(month_invoice.session_price / 100), 2),
                help="Preço da sessão",
            )
            * 100
        )
    col6.metric(
        label="Total",
        value=_get_total(
            month_invoice.sessions_completed,
            month_invoice.sessions_to_recover,
            month_invoice.session_price,
            month_invoice.free_sessions,
        ),
        help="Valor total das sessões feitas e a recuperar. Não inclui sessões gratuitas.",
    )
    with col7:
        month_invoice.payment_date = st.date_input(
            label="Data de pagamento",
            value=month_invoice.payment_date,
            format="DD/MM/YYYY",
            disabled=True if month_invoice.payment_status == "paid" else False,
        )
    with col8:
        month_invoice.nf_number = st.number_input(
            label="nº recibo",
            value=month_invoice.nf_number,
            step=1,
        )

    monthly_invoice.insert(connection, month_invoice)


st.markdown(
    """
<style>
[data-testid="stMetricValue"] {
    font-size: 20px;
}
</style>
""",
    unsafe_allow_html=True,
)

current_month: int = datetime.today().month
current_year: int = datetime.today().year
months_br: list[str] = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]
st.header("**Controle financeiro**")

col1, col2, _ = st.columns([2, 1, 3])
with col1:
    chosen_month = int(
        st.selectbox(
            "Selecione o mês",
            options=np.arange(1, 13, 1),
            index=current_month - 2,  # gets the index of the previous month
            format_func=lambda x: months_br[x - 1],  # type: ignore
        )
    )
with col2:
    year_options: list[int] = np.arange(current_year - 5, current_year + 5, 1).tolist()
    chosen_year = int(
        st.selectbox(
            "Selecione o ano",
            options=year_options,
            index=year_options.index(current_year),
        )
    )

with st.container(border=True):
    connection = get_db_connection()
    monthly_invoices: list[MonthlyInvoice] = monthly_invoice.get_all_in_period(
        connection, chosen_month, chosen_year
    )
    if not monthly_invoices:
        st.info("Não há dados para esse mês.")
    for month_invoice in monthly_invoices:
        patient_: Patient = patient.get_by_id(connection, month_invoice.patient_id)
        _update_invoice_metrics(connection, month_invoice, patient_)
