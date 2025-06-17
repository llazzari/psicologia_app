import logging
import os
from datetime import date
from typing import Iterator

import duckdb
import pytest

from data.appointment import create_appointments_table
from data.database import connect_to_db
from data.models import Patient
from data.monthly_invoice import create_monthly_invoices_table
from data.patient import create_patients_table


@pytest.fixture(scope="session")
def logger() -> Iterator[logging.Logger]:
    """Fixture to set up a file logger for the test session."""
    log_file = "test_run.log"
    log = logging.getLogger("TestLogger")
    log.setLevel(logging.INFO)
    log.propagate = False
    if log.hasHandlers():
        log.handlers.clear()
    file_handler = logging.FileHandler(log_file, mode="w")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    log.info("--- Starting new test session from Pelotas, Brazil ---")
    yield log
    log.removeHandler(file_handler)
    logging.shutdown()


@pytest.fixture
def db_connection(logger: logging.Logger) -> Iterator[duckdb.DuckDBPyConnection]:
    """Fixture to provide a clean database connection for each test."""
    db_file = "psychologist_app_test.db"
    logger.info(f"FIXTURE-SETUP: Preparing database file: {db_file}")
    if os.path.exists(db_file):
        os.remove(db_file)
    connection = connect_to_db(db_file)
    create_patients_table(connection)
    create_appointments_table(connection)
    create_monthly_invoices_table(connection)
    yield connection
    connection.close()
    if os.path.exists(db_file):
        os.remove(db_file)
    logger.info(f"FIXTURE-TEARDOWN: Cleaned up database file: {db_file}")


@pytest.fixture
def patient_child_model() -> Patient:
    """Fixture to provide a sample patient model for tests."""
    return Patient(
        name="Test Patient",
        address="123 Test St, Test City, Test State",
        is_child=True,
        birthdate=date(2010, 1, 1),
        cpf_cnpj="123.456.789-00",
        school="Test School",
        tutor_cpf_cnpj="987.654.321-00",
    )


@pytest.fixture
def patient_adult_model() -> Patient:
    """Fixture to provide a sample adult patient model for tests."""
    return Patient(
        name="Adult Patient",
        address="456 Adult St, Adult City, Adult State",
        is_child=False,
        birthdate=date(1985, 5, 15),
        cpf_cnpj="123.323.232-22",
    )
