import streamlit as st

from modules import navbar
from pages import homepage
from service.database_manager import initialize_database


def main():
    """Main function to run the Streamlit application."""
    st.set_page_config(
        page_title="Sistema de Gerenciamento",
        page_icon=":material/network_intelligence:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # if not st.user.is_logged_in:
    #     if st.button("Login com Google", icon=":material/login:"):
    #         st.login("google")

    # else:
    navbar.render()
    homepage.render()
    initialize_database()

    # mock.insert_patients()
    # mock.insert_appointments()
    # settings_service.insert(PsychologistSettings(user_email=st.user.email))  # type: ignore
    # st.session_state.settings = settings_service.get_by_(st.user.email)  # type: ignore

    # llm.get_document_content()


# TODO - add a company page with expenses and revenues
# TODO - add a return to docs_list and patients_list from doc_editor

if __name__ == "__main__":
    main()
