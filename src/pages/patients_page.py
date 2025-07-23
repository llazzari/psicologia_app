import uuid

import streamlit as st

from modules import navbar
from pages import patients_list
from pages.documents_view import display_patient_docs, doc_editor
from service.patient_manager import get_patient_by_id


def main() -> None:
    st.set_page_config(
        layout="wide",
        page_title="Pacientes",
        initial_sidebar_state="collapsed",
        page_icon=":material/network_intelligence:",
    )
    navbar.render()

    if "edit" in st.query_params:
        doc_editor()
    elif "patient_id" in st.query_params:
        st.session_state["patient"] = get_patient_by_id(
            uuid.UUID(st.query_params["patient_id"])
        )
        display_patient_docs(uuid.UUID(st.query_params["patient_id"]))

    else:
        patients_list.render()


if __name__ == "__main__":
    main()
