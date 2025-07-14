from typing import Optional
from uuid import UUID

import streamlit as st

from data.models import DOCUMENT_CATEGORY_PT, Document, DocumentCategory
from service.documents_manager import get_all_for_category, insert_document
from service.patient_manager import get_patient_by_id


def doc_editor(doc: Optional[Document] = None) -> None:
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
