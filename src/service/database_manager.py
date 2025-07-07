import logging

import duckdb
import streamlit as st

from data import database

log = logging.getLogger("TestLogger")


@st.cache_resource()
def get_db_connection() -> duckdb.DuckDBPyConnection:
    return database.connect(database.DB_PATH)


def initialize_database() -> None:
    log.info("APP-LOGIC: Initializing database schema.")
    connection = get_db_connection()
    database.initialize(connection)
    log.info("APP-LOGIC: Database schema initialized successfully.")
