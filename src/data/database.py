import logging

import duckdb

log = logging.getLogger("TestLogger")


def connect_to_db(db_path: str) -> duckdb.DuckDBPyConnection:
    """
    Establishes a connection to the DuckDB database.

    This function is our application's dedicated way to interact with
    the database connection, abstracting the direct call to the library.

    Args:
        db_path (str): The file path for the database.

    Returns:
        duckdb.DuckDBPyConnection: A connection object to the database,
                                    or None if an error occurs.
    """
    try:
        log.info(f"APP-LOGIC: Attempting to connect to database at '{db_path}'")
        connection = duckdb.connect(database=db_path, read_only=False)  # type: ignore
        log.info("APP-LOGIC: Database connection successful.")
    except Exception:
        log.error("APP-LOGIC: Failed to connect to database.", exc_info=True)
        # In a real app, we might raise the exception or handle it differently.
        # For now, returning None is a clear failure signal.
        raise Exception("Failed to connect to the database.")

    return connection
