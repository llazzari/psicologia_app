import uuid

import streamlit as st

from modules import navbar
from pages import patients_list
from pages.documents_view import display_patient_docs, doc_editor


def main() -> None:
    st.set_page_config(
        layout="wide", page_title="Pacientes", initial_sidebar_state="collapsed"
    )
    navbar.render()

    if "patient_id" in st.query_params:
        if "edit" in st.query_params:
            doc_editor()
            return
        display_patient_docs(uuid.UUID(st.query_params["patient_id"]))
    else:
        patients_list.render()


if __name__ == "__main__":
    main()
