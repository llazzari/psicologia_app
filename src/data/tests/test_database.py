import logging

import duckdb


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
