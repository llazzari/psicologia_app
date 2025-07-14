import uuid
from datetime import date
from typing import Optional
from uuid import UUID

import streamlit as st

from data.models import (
    DOCUMENT_CATEGORY_PT,
    PATIENT_STATUS_PT,
    Document,
    DocumentCategory,
    Patient,
    PatientStatus,
)
from modules import navbar
from service.documents_manager import get_all_for_category, insert_document
from service.patient_manager import (
    get_all_patients,
    get_patient_by_id,
    update_patient_on_db,
)


@st.dialog("Adicionar/editar dados do paciente", width="small")
def _patient_modal(patient_: Optional[Patient] = None) -> None:
    if patient_ is None:
        patient_ = Patient(name="")  # uses default values

    with st.form("patient_form", border=False):
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
            patient_.is_child = st.checkbox(
                "Criança/Adolescente", value=patient_.is_child
            )

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
                options=PatientStatus,
                index=list(PatientStatus).index(
                    patient_.status
                ),  # transforms Enum to list and selects the index
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

        patient_.contract = st.text_input(
            "CNPJ convênio",
            value=patient_.contract,
            help="Somente números. Ex: 12345678910",
            max_chars=11,
        )

        submitted = st.form_submit_button("Salvar alterações")
        if submitted:
            update_patient_on_db(patient_)
            st.session_state["all_patients"] = get_all_patients()
            st.rerun()


@st.cache_data
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
        col1, col2, col3, col4, col5 = st.columns(
            [2, 1, 1, 1, 1], vertical_alignment="center"
        )
        with col1:
            st.markdown(f"**{patient_.name.strip()}**")
            if patient_.is_child:
                st.caption("Criança/Adolescente")
        col2.metric(
            label="Nascimento",
            value=patient_.birthdate.strftime("%d/%m/%Y")
            if patient_.birthdate
            else "N/A",
        )
        col3.metric(label="Idade", value=_get_age(patient_.birthdate))
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


def display_patients_list() -> None:
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


def _doc_editor(doc: Optional[Document] = None) -> None:
    patient_ = st.session_state["patient"]
    if not doc:
        doc = Document(patient_id=patient_.id)

    st.title("Editar documento")
    if st.button("Voltar a lista de documentos", icon=":material/arrow_back:"):
        st.query_params.pop("edit")
        st.rerun()

    cols = st.columns([3, 1])
    with cols[0]:
        doc.file_name = st.text_input("Nome do documento")
    with cols[1]:
        doc.category = st.selectbox(
            "Categoria",
            options=DocumentCategory,
            format_func=lambda category: DOCUMENT_CATEGORY_PT[category].capitalize(),
            index=list(DocumentCategory).index(doc.category),
        )

    st.divider()

    col_input, col_btn, col_output = st.columns([3, 1, 3], vertical_alignment="center")
    with col_input:
        st.text_area(
            "Observações",
            key=f"observations_{patient_.id}",
            height=200,
        )
    with col_btn:
        if st.button(
            "Gerar documento",
            key=f"AI_{patient_.id}",
            icon=":material/text_fields_alt:",
        ):
            pass
    with col_output:
        ai_content = st.text_area("Documento gerado por IA", height=200)

    doc.content += "\n\n" + ai_content  # for prontuaries, have to check the rest

    doc.content = st.text_area(
        "Resultado",
        key=f"content_{patient_.id}",
        height=400,
        value=doc.content,
    )

    if st.button("Salvar", icon=":material/save:"):
        insert_document(doc)
        st.query_params.pop("edit")
        st.rerun()


def display_docs_header(patient_name: str) -> None:
    st.title(f"Documentos de {patient_name.strip()}")
    cols = st.columns(4)
    with cols[0]:
        if st.button("Voltar para a lista de pacientes", icon=":material/arrow_back:"):
            st.query_params.pop("patient_id")
            st.session_state.pop("patient")
            st.rerun()
    with cols[1]:
        if st.button("Adicionar documento", icon=":material/attach_file:"):
            st.query_params["edit"] = "true"
            st.rerun()

    st.divider()


def display_patient_docs(patient_id: UUID) -> None:
    st.session_state["patient"] = get_patient_by_id(patient_id)
    patient_ = st.session_state["patient"]

    display_docs_header(patient_name=patient_.name)

    for doc_category in DocumentCategory:
        with st.expander(f"**{DOCUMENT_CATEGORY_PT[doc_category].capitalize()}**"):
            docs: list[Document] = get_all_for_category(
                patient_id=patient_.id, category=doc_category
            )
            if not docs:
                st.info("Nenhum documento deste tipo encontrado.")
            for doc in docs:
                st.markdown(f"- {doc.file_name}")


def main() -> None:
    st.set_page_config(
        layout="wide", page_title="Pacientes", initial_sidebar_state="collapsed"
    )
    navbar.render()

    if "patient_id" in st.query_params:
        if "edit" in st.query_params:
            _doc_editor()
            return
        display_patient_docs(uuid.UUID(st.query_params["patient_id"]))
    else:
        display_patients_list()


if __name__ == "__main__":
    main()
