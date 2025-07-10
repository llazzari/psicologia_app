import logging
from uuid import UUID

import duckdb

from data.models import Document

log = logging.getLogger("TestLogger")


def create_documents_table(db_connection: duckdb.DuckDBPyConnection) -> None:
    """
    Create the 'documents' table in the database.
    """
    try:
        log.info("Creating the 'documents' table in the database.")
        db_connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY,
                patient_id UUID,
                category VARCHAR,
                file_name VARCHAR
            )
            """
        )
        log.info("Table 'documents' created successfully.")
    except Exception:
        log.error("Failed to create the 'documents' table.", exc_info=True)
        raise


def insert(connection: duckdb.DuckDBPyConnection, document: Document) -> None:
    try:
        log.info(f"Inserting document: {document}")
        connection.execute(
            "INSERT INTO OR REPLACE documents VALUES (?, ?, ?, ?)",
            document.model_dump().values(),
        )
        log.info("Inserted document.")
    except Exception:
        log.error("Failed to insert document.", exc_info=True)
        raise


def remove(connection: duckdb.DuckDBPyConnection, document_id: UUID) -> None:
    try:
        log.info(f"Removing document with ID: {document_id}")
        connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        log.info(f"Removed document with ID: {document_id}")
    except Exception:
        log.error(f"Failed to remove document with ID: {document_id}", exc_info=True)
        raise


def get_by_id(connection: duckdb.DuckDBPyConnection, document_id: UUID) -> Document:
    try:
        log.info(f"Retrieving document with ID: {document_id}")
        result = connection.execute(  # type: ignore
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
        log.info(f"Retrieved document with ID: {document_id}")
        return Document(**{k: v for k, v in zip(Document.model_fields.keys(), result)})  # type: ignore
    except Exception:
        log.error(f"Failed to retrieve document with ID: {document_id}", exc_info=True)
        raise


def get_all_for_patient_id(
    connection: duckdb.DuckDBPyConnection, patient_id: UUID
) -> list[Document]:
    try:
        log.info(
            "Retrieving all documents for patient with ID: " + str(patient_id) + "."
        )
        results = connection.execute(
            "SELECT * FROM documents WHERE patient_id = ?", (patient_id,)
        ).fetchall()  # type: ignore
        log.info("Retrieved all documents for the patient.")
        return [
            Document(**{k: v for k, v in zip(Document.model_fields.keys(), result)})
            for result in results
        ]  # type: ignore
    except Exception:
        log.error("Failed to retrieve the patient's documents.", exc_info=True)
        raise
