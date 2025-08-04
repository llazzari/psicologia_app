import duckdb
import logfire
import streamlit as st

from data import database

logfire.configure()


@st.cache_resource()
def get_db_connection() -> duckdb.DuckDBPyConnection:
    return database.connect(database.DB_PATH)


def initialize_database() -> None:
    logfire.info("APP-LOGIC: Initializing database schema.")
    connection = get_db_connection()
    database.initialize(connection)
    logfire.info("APP-LOGIC: Database schema initialized successfully.")
