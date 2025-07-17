from datetime import datetime
from typing import Literal

import numpy as np
import streamlit as st

from data.models import (
    MONTHLY_INVOICE_STATUS_PT,
    PATIENT_STATUS_PT_SINGULAR,
    MonthlyInvoice,
    MonthlyInvoiceStatus,
    Patient,
    PatientStatus,
)
from modules import navbar
from service.monthly_invoice_manager import get_monthly_invoices, update_invoice_on_db
from service.patient_manager import get_patient_by_id
from utils.monthly_invoice_computations import (
    get_formatted_price,
    get_total,
    get_total_sessions,
)


@st.dialog("Editar fatura", width="large")
def _invoice_modal(patient_: Patient, month_invoice: MonthlyInvoice) -> None:
    with st.form("invoice_form", border=False):
        st.markdown(f"**{patient_.name}**")
        
        cols = st.columns(4)
        
        with cols[0]:
            if patient_.status == PatientStatus.IN_TESTING:
                month_invoice.total = int(
                    st.number_input(
                        "Preço da avaliação (R$)",
                        min_value=0.0,
                        step=0.01,
                        value=float(np.round(get_total(
                            month_invoice.sessions_completed,
                            month_invoice.sessions_to_recover,
                            month_invoice.session_price,
                            month_invoice.free_sessions,
                            patient_.status,
                        ) / 100, 2)),
                    )
                    * 100
                )
            else:
                month_invoice.session_price = int(
                    st.number_input(
                        "Preço da sessão (R$)",
                        min_value=0.0,
                        step=0.01,
                        value=float(np.round(month_invoice.session_price / 100, 2)),
                    )
                    * 100
                )
        with cols[1]:
            month_invoice.sessions_completed = st.number_input(
                "Sessões realizadas",
                min_value=0,
                value=month_invoice.sessions_completed,
            )
        with cols[2]:
            month_invoice.sessions_to_recover = st.number_input(
                "Sessões a recuperar",
                min_value=0,
                value=month_invoice.sessions_to_recover,
            )
        with cols[3]:
            month_invoice.free_sessions = st.number_input(
                "Sessões gratuitas", min_value=0, value=month_invoice.free_sessions
            )
        colss = st.columns(3)
        with colss[0]:
            month_invoice.payment_date = st.date_input(
                "Data de pagamento",
                value=month_invoice.payment_date,
                format="DD/MM/YYYY",
            )
        with colss[1]:
            month_invoice.payment_status = st.selectbox(
                "Status da fatura",
                MonthlyInvoiceStatus,
                index=list(MonthlyInvoiceStatus).index(month_invoice.payment_status),
                format_func=lambda status: MONTHLY_INVOICE_STATUS_PT[
                    status
                ].capitalize(),
            )
        with colss[2]:
            month_invoice.nf_number = st.number_input(
                "Número da NF",
                min_value=0,
                value=month_invoice.nf_number,
                step=1,
            )
        submitted = st.form_submit_button("Salvar", icon=":material/save:")
        if submitted:
            update_invoice_on_db(month_invoice)
            st.rerun()


def _display_invoice_metrics(
    month_invoice: MonthlyInvoice,
    patient_: Patient,
) -> None:
    month_invoice.total = get_total(
        month_invoice.sessions_completed,
        month_invoice.sessions_to_recover,
        month_invoice.session_price,
        month_invoice.free_sessions,
        patient_.status,
    )

    col_name, col_sessions, col_prices, col_status, col_info, col_edit = (
        st.columns([2, 1, 2, 1, 2, 1], vertical_alignment="center")
    )
    with col_name:
        st.markdown(f"**{patient_.name}**")
    col_sessions.metric(
        label="Total de sessões",
        value=get_total_sessions(
            month_invoice.sessions_completed, month_invoice.sessions_to_recover
        ),
        help="Inclui sessões realizadas e a recuperar.",
    )

    with col_prices:
        if patient_.status == PatientStatus.IN_TESTING:
            col_prices.metric(
                label="Preço da avaliação (R$)",
                value=get_formatted_price(month_invoice.total),
                help="Preço da avaliação.",
            )
        else:
            col_price, col_total = st.columns(2)
            col_price.metric(
                label="Preço (R$)",
                value=get_formatted_price(month_invoice.session_price),
                help="Preço da sessão.",
            )
            col_total.metric(
                label="Total",
                value=get_formatted_price(month_invoice.total),
                help="Valor total das sessões feitas e a recuperar. Não inclui sessões gratuitas.",
            )

    with col_status:
        BADGE_COLORS: dict[
            PatientStatus, Literal["violet", "gray", "blue", "orange"]
        ] = {
            PatientStatus.ACTIVE: "violet",
            PatientStatus.INACTIVE: "gray",
            PatientStatus.IN_TESTING: "blue",
            PatientStatus.LEAD: "orange",
        }
        st.badge(
            PATIENT_STATUS_PT_SINGULAR[patient_.status], color=BADGE_COLORS[patient_.status]
        )

    with col_info:
        with st.popover("Outras informações", icon=":material/read_more:"):
            st.markdown(f"**Sessões realizadas**: {month_invoice.sessions_completed}")
            st.markdown(f"**Sessões a recuperar**: {month_invoice.sessions_to_recover}")
            if month_invoice.free_sessions > 0:
                st.markdown(f"**Sessões gratuitas**: {month_invoice.free_sessions}")

            st.markdown(
                f"**Datas das sessões**: {', '.join([date.strftime('%d/%m/%Y') for date in month_invoice.appointment_dates])}"
            )

            if patient_.is_child:
                st.markdown(f"**CPF/CNPJ do tutor**: {patient_.tutor_cpf_cnpj}")
            else:
                st.markdown(f"**CPF**: {patient_.cpf_cnpj}")

            if patient_.contract:
                st.markdown(f"**CNPJ do convênio**: {patient_.contract}")

            if month_invoice.payment_date:
                st.markdown(
                    f"**Data de pagamento**: {month_invoice.payment_date.strftime('%d/%m/%Y')}"
                )
                st.markdown(f"**nº recibo**: {month_invoice.nf_number}")
    with col_edit:
        if st.button("", key=f"edit_{patient_.id}", icon=":material/edit:"):
            _invoice_modal(patient_, month_invoice)


def render() -> None:
    st.set_page_config(
        layout="wide",
        page_title="Controle Financeiro",
        initial_sidebar_state="collapsed",
    )

    navbar.render()
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
        year_options: list[int] = np.arange(
            current_year - 5, current_year + 5, 1
        ).tolist()
        chosen_year = int(
            st.selectbox(
                "Selecione o ano",
                options=year_options,
                index=year_options.index(current_year),
            )
        )

    with st.container(border=True):
        monthly_invoices: list[MonthlyInvoice] = get_monthly_invoices(
            chosen_month, chosen_year
        )
        if not monthly_invoices:
            st.info("Não há dados para esse mês.")
        for month_invoice in monthly_invoices:
            patient_: Patient = get_patient_by_id(month_invoice.patient_id)
            _display_invoice_metrics(month_invoice, patient_)


if __name__ == "__main__":
    render()
