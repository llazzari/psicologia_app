import logging
import os

import duckdb
import pytest

from data import database


def test_connect_success(logger: logging.Logger) -> None:
    """Test successful database connection."""
    db_file = "test_connect.db"
    logger.info("TEST-RUN: test_connect_success")

    try:
        connection: duckdb.DuckDBPyConnection = database.connect(db_file)
        assert connection is not None, "Connection should not be None"
        assert isinstance(connection, duckdb.DuckDBPyConnection), (
            "Connection should be a DuckDBPyConnection"
        )
        logger.info("SUCCESS: Database connection established successfully")
    finally:
        if "connection" in locals():
            connection.close()
        if os.path.exists(db_file):
            os.remove(db_file)


def test_connect_invalid_path(logger: logging.Logger) -> None:
    """Test database connection with invalid path."""
    invalid_path = "/nonexistent/directory/db.db"
    logger.info("TEST-RUN: test_connect_invalid_path")

    with pytest.raises(Exception) as exc_info:
        database.connect(invalid_path)

    assert str(exc_info.value) == "Failed to connect to the database."
    logger.info("SUCCESS: Invalid path handled correctly")


def test_initialize_creates_all_tables(logger: logging.Logger) -> None:
    """Test that initialize creates all required tables."""
    db_file = "test_initialize.db"
    logger.info("TEST-RUN: test_initialize_creates_all_tables")

    try:
        connection = database.connect(db_file)
        database.initialize(connection)

        # Check if all tables exist
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()
        table_names = {row[0] for row in tables}

        expected_tables = {"patients", "appointments", "monthly_invoices"}
        assert expected_tables.issubset(table_names), (
            f"Not all required tables were created. Missing: {expected_tables - table_names}"
        )

        logger.info("SUCCESS: All required tables were created successfully")
    finally:
        if "connection" in locals():
            connection.close()
        if os.path.exists(db_file):
            os.remove(db_file)


def test_create_patients_table(
    db_connection: duckdb.DuckDBPyConnection, logger: logging.Logger
) -> None:
    """Tests that the 'patients' table is created with the correct columns."""
    logger.info("TEST-RUN: test_create_patients_table")
    result = db_connection.execute("PRAGMA table_info('patients');").fetchall()
    columns = {row[1]: row[2] for row in result}
    expected_columns = {
        "id": "UUID",
        "name": "VARCHAR",
        "address": "VARCHAR",
        "birthdate": "DATE",
        "cpf_cnpj": "VARCHAR",
        "is_child": "BOOLEAN",
        "school": "VARCHAR",
        "tutor_cpf_cnpj": "VARCHAR",
    }
    assert columns == expected_columns, "Table columns do not match expected schema."
    logger.info("SUCCESS: 'patients' table schema is correct.")


def test_initialize_is_idempotent(logger: logging.Logger) -> None:
    """Test that calling initialize multiple times doesn't cause errors."""
    db_file = "test_idempotent.db"
    logger.info("TEST-RUN: test_initialize_is_idempotent")

    try:
        connection = database.connect(db_file)

        # Initialize multiple times
        for _ in range(3):
            database.initialize(connection)

        # Verify tables are still correct
        result = connection.execute("PRAGMA table_info('patients');").fetchall()
        columns = {row[1]: row[2] for row in result}
        expected_columns = {
            "id": "UUID",
            "name": "VARCHAR",
            "address": "VARCHAR",
            "birthdate": "DATE",
            "cpf_cnpj": "VARCHAR",
            "is_child": "BOOLEAN",
            "school": "VARCHAR",
            "tutor_cpf_cnpj": "VARCHAR",
        }
        assert columns == expected_columns, (
            "Table schema changed after multiple initializations"
        )

        logger.info("SUCCESS: Multiple initializations handled correctly")
    finally:
        if "connection" in locals():
            connection.close()
        if os.path.exists(db_file):
            os.remove(db_file)
