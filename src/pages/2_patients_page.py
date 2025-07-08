from datetime import date
from typing import Optional

import streamlit as st

from data.models import Patient
from modules import navbar
from service.patient_manager import get_all_patients, update_patient_on_db


@st.dialog("Adicionar/editar dados do paciente", width="small")
def _patient_modal(patient_: Optional[Patient] = None) -> None:
    if patient_ is None:
        patient_ = Patient(name="")  # uses default values

    patient_.name = st.text_input("Nome", value=patient_.name)
    patient_.address = st.text_input("Endereço", value=patient_.address)

    col1, _, col2 = st.columns([2, 1, 2], vertical_alignment="center")
    with col1:
        patient_.birthdate = st.date_input(
            "Data de nascimento",
            value=patient_.birthdate,
            format="DD/MM/YYYY",
            min_value=date(1940, 1, 1),
            max_value=date.today(),
        )
    with col2:
        patient_.is_child = st.checkbox("Criança/Adolescente", value=patient_.is_child)

    col1, col2, col3 = st.columns(3)
    with col1:
        patient_.contact = st.text_input(
            "Celular",
            value=patient_.contact,
            help="Somente números. Ex: 53999999999",
            max_chars=11,
        )
    with col2:
        patient_.cpf_cnpj = st.text_input(
            "CPF/CNPJ",
            value=patient_.cpf_cnpj,
            help="Somente números. Ex: 12345678910",
            max_chars=11,
        )
    with col3:
        translated_status: dict[str, str] = {
            "active": "Ativo",
            "in testing": "Em avaliação",
            "lead": "Prospecto",
            "inactive": "Inativo",
        }
        patient_.status = st.selectbox(
            "Status",
            options=["active", "in testing", "lead", "inactive"],
            index=["active", "in testing", "lead", "inactive"].index(patient_.status),
            format_func=lambda x: translated_status[x],
        )

    if patient_.is_child:
        col1, col2 = st.columns([3, 2])
        with col1:
            patient_.school = st.text_input("Escola", value=patient_.school)
        with col2:
            patient_.tutor_cpf_cnpj = st.text_input(
                "CPF/CNPJ do Tutor",
                value=patient_.tutor_cpf_cnpj,
                help="Somente números. Ex: 12345678910",
                max_chars=11,
            )

    if st.button("Salvar alterações"):
        update_patient_on_db(patient_)
        st.rerun()


def _get_age(birthdate: date | None) -> str:
    """
    Calculates the age of a patient based on their birthdate.
    Returns a string representation of the age.
    """
    if not birthdate:
        return "N/A"
    today = date.today()
    age = (
        today.year
        - birthdate.year
        - ((today.month, today.day) < (birthdate.month, birthdate.day))
    )
    age_str: str = f"{age} anos" if age > 1 else f"{age} ano"
    months = (today.month - birthdate.month) % 12
    months_str: str = f"{months} meses" if months > 1 else f"{months} mês"
    if months == 0:
        return age_str
    return f"{age_str} e {months_str}"


def _display_patient_info(patient_: Patient):
    """
    Displays the information for a single patient in a consistent format.
    """
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.markdown(f"**{patient_.name.strip()}**")
            if patient_.is_child:
                st.caption("Criança/Adolescente")
        with col2:
            st.metric(
                label="Nascimento",
                value=patient_.birthdate.strftime("%d/%m/%Y")
                if patient_.birthdate
                else "N/A",
            )
        with col3:
            st.metric(label="Idade", value=_get_age(patient_.birthdate))
        with col4:
            if st.button("Editar", key=f"edit_{patient_.id}"):
                _patient_modal(patient_)


def render() -> None:
    st.set_page_config(
        layout="wide", page_title="Pacientes", initial_sidebar_state="collapsed"
    )
    navbar.render()

    st.title("👥 Gerenciamento de Pacientes")
    st.markdown(
        "Visualize e gerencie todos os pacientes cadastrados, organizados por status."
    )

    st.markdown(
        """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 14px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    all_patients: list[Patient] = get_all_patients()

    active_patients: list[Patient] = [p for p in all_patients if p.status == "active"]
    testing_patients: list[Patient] = [
        p for p in all_patients if p.status == "in testing"
    ]
    inactive_patients: list[Patient] = [
        p for p in all_patients if p.status == "inactive"
    ]
    leads: list[Patient] = [p for p in all_patients if p.status == "lead"]

    st.divider()

    if st.button("Adicionar paciente", icon=":material/person_add:"):
        _patient_modal()

    # --- Active Patients List (Expanded by default) ---
    with st.expander(f"**Pacientes Ativos** ({len(active_patients)})", expanded=True):
        if not active_patients:
            st.info("Nenhum paciente ativo no momento.")
        else:
            for patient_ in active_patients:
                _display_patient_info(patient_)

    # --- Patients in Testing List (Expanded by default) ---
    with st.expander(
        f"**Pacientes em Avaliação** ({len(testing_patients)})", expanded=True
    ):
        if not testing_patients:
            st.info("Nenhum paciente em processo de avaliação.")
        else:
            for patient_ in testing_patients:
                _display_patient_info(patient_)

    # --- Prospective Patients List (Collapsed by default) ---
    with st.expander(f"**Prospectos** ({len(leads)})", expanded=False):
        if not leads:
            st.info("Nenhum prospecto.")
        else:
            for patient_ in leads:
                _display_patient_info(patient_)

    # --- Inactive Patients List (Collapsed by default) ---
    with st.expander(
        f"**Pacientes Inativos** ({len(inactive_patients)})", expanded=False
    ):
        if not inactive_patients:
            st.info("Nenhum paciente inativo.")
        else:
            for patient_ in inactive_patients:
                _display_patient_info(patient_)


if __name__ == "__main__":
    render()
