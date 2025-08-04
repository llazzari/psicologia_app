from uuid import UUID

import logfire
import numpy as np
import streamlit as st

from data.models.document_models import (
    Document,
    DocumentCategory,
)
from data.models.patient_models import Patient
from service.documents_manager import get_all_documents_for
from service.patient_manager import get_patient_by_id

logfire.configure()


def doc_editor() -> None:
    doc: Document = st.session_state["doc"]
    logfire.info(
        f"PAGE-RENDER: Opening document editor for document {doc.id} (patient: {doc.patient_id})"
    )

    st.title("Editar documento")

    cols = st.columns([3, 1])
    with cols[0]:
        doc.file_name = st.text_input("Nome do documento", value=doc.file_name)
    with cols[1]:
        doc.category = st.selectbox(
            "Categoria",
            options=DocumentCategory,
            index=list(DocumentCategory).index(doc.category),
        )

    st.divider()

    col_obs, col_ai = st.columns([2, 4])
    with col_obs:
        with st.form(key=f"form_{doc.id}_obs", border=False):
            user_input = st.text_area(
                "Observações",
                height=200,
                value=st.session_state.get(f"obs_{doc.id}", ""),
                key=f"obs_{doc.id}",
            )
            btn_generate = st.form_submit_button(
                "Gerar documento",
                icon=":material/text_fields_alt:",
            )
            if btn_generate:
                pass
                # if user_input:
                # ai_content = generate(user_input, doc.category)
                # ai_content = llm.generate_content(doc, user_input)
                # st.session_state[f"ai_{doc.id}"] = ai_content
    with col_ai:
        st.markdown("Documento gerado por IA")
        if st.session_state.get(f"ai_{doc.id}"):
            st.markdown(st.session_state[f"ai_{doc.id}"])

    # Render the form for editing the content fields
    with st.form(key=f"form_{doc.id}_content", clear_on_submit=False):
        st.text_area(
            f"{doc.category.capitalize()} completo",
            key=f"content_{doc.id}",
            height=400,
            value=st.session_state.get(f"content_{doc.id}", ""),
            help="O conteúdo do documento completo a ser salvo.",
        )
        btn_save = st.form_submit_button(
            "Salvar",
            icon=":material/save:",
        )
        if btn_save:
            logfire.info(f"USER-ACTION: User saved document {doc.id}")
            # doc.content = st.session_state.get(f"content_{doc.id}", doc.content)
            # insert_document(doc)
            st.toast("Documento salvo com sucesso!", icon=":material/check:")


def display_docs_header(patient_: Patient) -> None:
    st.title(f"Documentos de {patient_.info.name.strip()}")
    cols = st.columns(4)
    with cols[0]:
        if st.button("Voltar para a lista de pacientes", icon=":material/arrow_back:"):
            logfire.info(
                f"USER-ACTION: User navigated back from patient {patient_.info.name} documents"
            )
            st.query_params.pop("patient_id")
            st.session_state.pop("patient")
            st.rerun()
    with cols[1]:
        if st.button("Adicionar documento", icon=":material/docs:"):
            logfire.info(
                f"USER-ACTION: User clicked to add document for patient {patient_.info.name}"
            )
            st.query_params["edit"] = "true"
            st.session_state["doc"] = Document(patient_id=patient_.id)
            st.rerun()

    st.divider()


def display_patient_docs(patient_id: UUID) -> None:
    logfire.info(f"PAGE-RENDER: Displaying documents for patient {patient_id}")
    st.session_state["patient"] = get_patient_by_id(patient_id)
    patient_ = st.session_state["patient"]

    display_docs_header(patient_)

    all_patient_docs: list[Document] = get_all_documents_for(patient_.id)
    logfire.info(
        f"DATA-FETCH: Retrieved {len(all_patient_docs)} documents for patient {patient_.info.name}"
    )

    if not all_patient_docs:
        st.info("Nenhum documento encontrado para este paciente.")
        return

    categories: list[DocumentCategory] = list(
        np.unique([doc.category for doc in all_patient_docs])
    )
    for doc_category in categories:
        with st.expander(f"**{doc_category.value.capitalize()}**"):
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
