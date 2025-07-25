from datetime import date
from typing import Optional

import streamlit as st

from data.models.patient_models import (
    PATIENT_STATUS_PT,
    PATIENT_STATUS_PT_SINGULAR,
    Child,
    ClassTime,
    Patient,
    PatientGender,
    PatientInfo,
    PatientStatus,
)
from service.patient_manager import get_all_patients, update_patient_on_db


@st.dialog("Adicionar/editar dados do paciente", width="large")
def _patient_modal(patient_: Optional[Patient] = None) -> None:
    if patient_ is None:
        patient_ = Patient(info=PatientInfo(name=""))  # uses default values
        is_child = (
            st.pills(
                "Escolha a faixa etária",
                options=["Criança", "Adulto"],
                default="Criança",
            )
            == "Criança"
        )
        if is_child:
            patient_.child = Child()

    with st.form("patient_form", border=False):
        col_name, col_birthdate, col_gender = st.columns([3, 1, 1])
        with col_name:
            patient_.info.name = st.text_input(
                "Nome completo", value=patient_.info.name
            )
        with col_birthdate:
            patient_.info.birthdate = st.date_input(
                "Data de nascimento",
                value=patient_.info.birthdate,
                format="DD/MM/YYYY",
                min_value=date(1940, 1, 1),
                max_value=date.today(),
            )
        with col_gender:
            patient_.info.gender = st.pills(
                "Gênero",
                options=list(PatientGender),
                format_func=lambda x: "M" if x == PatientGender.MALE else "F",
                default=patient_.info.gender
                if patient_.info.gender
                else PatientGender.MALE,
            )

        patient_.info.address = st.text_input("Endereço", value=patient_.info.address)

        col1, col2, col3 = st.columns(3)
        with col1:
            patient_.info.contact = st.text_input(
                "Celular",
                value=patient_.info.contact,
                help="Somente números. Ex: 53999999999",
            )
        with col2:
            patient_.info.cpf_cnpj = st.text_input(
                "CPF/CNPJ",
                value=patient_.info.cpf_cnpj,
                help="Somente números. Ex: 12345678910",
            )
        with col3:
            patient_.status = st.selectbox(
                "Status",
                options=PatientStatus,
                index=list(PatientStatus).index(
                    patient_.status
                ),  # transforms Enum to list and selects the index
                format_func=lambda x: PATIENT_STATUS_PT_SINGULAR[x].capitalize(),
            )

        if patient_.child:
            st.divider()
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                patient_.child.school = st.text_input(
                    "Escola", value=patient_.child.school
                )
            with col2:
                patient_.child.class_time = st.pills(
                    "Turno",
                    options=list(ClassTime),
                    format_func=lambda x: "Manhã"
                    if x == ClassTime.MORNING
                    else "Tarde",
                    default=patient_.child.class_time
                    if patient_.child.class_time
                    else ClassTime.MORNING,
                )  # type: ignore
            with col3:
                patient_.child.grade = st.text_input(
                    "Série", value=patient_.child.grade
                )

            col_tutor1, col_tutor2 = st.columns([3, 2])
            with col_tutor1:
                patient_.child.tutor_name = st.text_input(
                    "Nome do Tutor", value=patient_.child.tutor_name
                )
            with col_tutor2:
                patient_.child.tutor_cpf_cnpj = st.text_input(
                    "CPF/CNPJ do Tutor",
                    value=patient_.child.tutor_cpf_cnpj,
                    help="Somente números. Ex: 12345678910",
                )
            st.divider()

        col1, col2 = st.columns([3, 2])
        with col1:
            patient_.diagnosis = st.text_input("Diagnóstico", value=patient_.diagnosis)
        with col2:
            patient_.contract = st.text_input(
                "CNPJ convênio",
                value=patient_.contract,
                help="Somente números. Ex: 12345678910",
            )

        submitted = st.form_submit_button("Salvar alterações")
        if submitted:
            update_patient_on_db(patient_)
            st.session_state["all_patients"] = get_all_patients()
            st.rerun()


def _display_patient_info(patient_: Patient):
    """
    Displays the information for a single patient in a consistent format.
    """
    with st.container(border=True):
        col1, col2, col3, col4, col5 = st.columns(
            [2, 1, 1, 1, 1], vertical_alignment="center"
        )
        with col1:
            st.markdown(f"**{patient_.info.name.strip()}**")
            if patient_.child:
                st.caption("Criança/Adolescente")
        col2.metric(
            label="Nascimento",
            value=patient_.info.birthdate.strftime("%d/%m/%Y")
            if patient_.info.birthdate
            else "N/A",
        )
        col3.metric(
            label="Idade", value=patient_.info.age if patient_.info.age else "N/A"
        )
        with col4:
            if st.button(
                "Ver documentos",
                key=f"view_{patient_.id}",
                icon=":material/docs:",
            ):
                st.query_params.update({"patient_id": f"{patient_.id}"})
                st.session_state["patient"] = patient_
                st.rerun()

        with col5:
            if st.button(
                "Editar",
                key=f"edit_{patient_.id}",
                icon=":material/person_edit:",
                help="Editar dados do paciente",
            ):
                _patient_modal(patient_)


def _display_patients():
    expanded_status: dict[PatientStatus, bool] = {
        PatientStatus.ACTIVE: True,
        PatientStatus.IN_TESTING: True,
        PatientStatus.LEAD: False,
        PatientStatus.INACTIVE: False,
    }

    all_patients = st.session_state["all_patients"]

    def group_patients_by_status(status: str) -> list[Patient]:
        return [patient for patient in all_patients if patient.status == status]

    for status in PatientStatus:
        patients: list[Patient] = group_patients_by_status(status)
        with st.expander(
            f"**Pacientes {PATIENT_STATUS_PT[status]}** ({len(patients)})",
            expanded=expanded_status[status],
        ):
            if not patients:
                st.info("Nenhum paciente encontrado com este status.")
            else:
                for patient_ in patients:
                    _display_patient_info(patient_)


def render() -> None:
    st.title("Gerenciamento de Pacientes")
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

    st.divider()

    if "all_patients" not in st.session_state:
        st.session_state["all_patients"] = get_all_patients()

    if st.button("Adicionar paciente", icon=":material/person_add:"):
        _patient_modal()

    _display_patients()
