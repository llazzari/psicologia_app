from uuid import UUID

import numpy as np
import streamlit as st

from data.models import (
    DOCUMENT_CATEGORY_PT,
    Document,
    DocumentCategory,
    DocumentContent,
    Patient,
)
from service import llm
from service.documents_manager import get_all_documents_for, insert_document
from service.patient_manager import get_patient_by_id


async def doc_editor() -> None:
    doc = st.session_state["doc"]

    st.title("Editar documento")

    cols = st.columns([3, 1])
    with cols[0]:
        doc.file_name = st.text_input("Nome do documento", value=doc.file_name)
    with cols[1]:
        doc.category = st.selectbox(
            "Categoria",
            options=DocumentCategory,
            format_func=lambda category: DOCUMENT_CATEGORY_PT[category].capitalize(),
            index=list(DocumentCategory).index(doc.category),
        )

    st.divider()

    col_obs, col_ai = st.columns([2, 4])
    with col_obs:
        with st.form(key=f"form_{doc.id}_obs", border=False):
            user_input = st.text_area(
                "Observações",
                height=200,
                value=st.session_state[f"obs_{doc.id}"]
                if f"obs_{doc.id}" in st.session_state
                else "",
                key=f"obs_{doc.id}",
            )
            btn_generate = st.form_submit_button(
                "Gerar documento",
                icon=":material/text_fields_alt:",
            )
            if btn_generate:
                if user_input:
                    ai_content: DocumentContent = await llm.generate_content(
                        doc, user_input
                    )
                    st.session_state[f"ai_{doc.id}"] = ai_content.content
                    # Optionally append to document content
                    st.session_state[f"content_{doc.id}"] += "\n\n" + ai_content.content

    with col_ai:
        st.markdown("Prontuário gerado por IA")
        if st.session_state[f"ai_{doc.id}"]:
            st.markdown(st.session_state[f"ai_{doc.id}"])

    with st.form(key=f"form_{doc.id}_content", clear_on_submit=False):
        doc.content.content = st.text_area(
            "Prontuário completo",
            key=f"content_{doc.id}",
            height=400,
            value=st.session_state[f"content_{doc.id}"]
            if f"content_{doc.id}" in st.session_state
            else doc.content.content,
        )
        btn_save = st.form_submit_button(
            "Salvar",
            icon=":material/save:",
        )
        if btn_save:
            insert_document(doc)
            st.toast("Documento salvo com sucesso!", icon=":material/check:")


def display_docs_header(patient_: Patient) -> None:
    st.title(f"Documentos de {patient_.name.strip()}")
    cols = st.columns(4)
    with cols[0]:
        if st.button("Voltar para a lista de pacientes", icon=":material/arrow_back:"):
            st.query_params.pop("patient_id")
            st.session_state.pop("patient")
            st.rerun()
    with cols[1]:
        if st.button("Adicionar documento", icon=":material/docs:"):
            st.query_params["edit"] = "true"
            st.session_state["doc"] = Document(patient_id=patient_.id)
            st.rerun()

    st.divider()


def display_patient_docs(patient_id: UUID) -> None:
    st.session_state["patient"] = get_patient_by_id(patient_id)
    patient_ = st.session_state["patient"]

    display_docs_header(patient_)

    all_patient_docs: list[Document] = get_all_documents_for(patient_.id)

    if not all_patient_docs:
        st.info("Nenhum documento encontrado para este paciente.")
        return

    categories: list[DocumentCategory] = list(
        np.unique([doc.category for doc in all_patient_docs])
    )
    for doc_category in categories:
        with st.expander(f"**{DOCUMENT_CATEGORY_PT[doc_category].capitalize()}**"):
            docs: list[Document] = [
                doc for doc in all_patient_docs if doc.category == doc_category
            ]
            if not docs:
                st.info("Nenhum documento deste tipo encontrado.")
            for doc in docs:
                if st.button(f"{doc.file_name}", type="tertiary"):
                    st.query_params["edit"] = "true"
                    st.session_state["doc"] = doc
                    st.rerun()
