import logging

import duckdb

from data.appointment import create_appointments_table
from data.monthly_invoice import create_monthly_invoices_table
from data.patient import create_patients_table

DB_PATH: str = "data/database.db"

log = logging.getLogger("TestLogger")


def connect(db_path: str) -> duckdb.DuckDBPyConnection:
    """
    Establishes a connection to the DuckDB database.

    This function is our application's dedicated way to interact with
    the database connection, abstracting the direct call to the library.

    Args:
        db_path (str): The file path for the database.

    Returns:
        duckdb.DuckDBPyConnection: A connection object to the database.
    """
    try:
        log.info(f"APP-LOGIC: Attempting to connect to database at '{db_path}'")
        connection = duckdb.connect(database=db_path, read_only=False)  # type: ignore
        log.info("APP-LOGIC: Database connection successful.")
    except Exception:
        log.error("APP-LOGIC: Failed to connect to database.", exc_info=True)
        raise Exception("Failed to connect to the database.")

    return connection


def initialize(connection: duckdb.DuckDBPyConnection) -> None:
    """
    Initializes the database by creating necessary tables.

    This function is called to set up the database schema, ensuring that
    all required tables are created before any operations are performed.

    Args:
        connection (duckdb.DuckDBPyConnection): The connection object to the database.
    """
    log.info("APP-LOGIC: Initializing database schema.")

    create_patients_table(connection)
    create_appointments_table(connection)
    create_monthly_invoices_table(connection)

    log.info("APP-LOGIC: Database schema initialized successfully.")
