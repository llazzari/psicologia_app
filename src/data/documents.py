import logging
from typing import Any
from uuid import UUID

import duckdb

from data.db_utils import insert_model
from data.models.document_models import (
    Document,
    DocumentCategory,
    ProntuaryContent,
    PsychologicalOpinionContent,
    PsychologicalReportContent,
)

log = logging.getLogger("TestLogger")

CONTENT_MODEL_MAP = {
    DocumentCategory.PRONTUARY: ProntuaryContent,
    DocumentCategory.PSYCHOLOGICAL_REPORT: PsychologicalReportContent,
    DocumentCategory.PSYCHOLOGICAL_OPINION: PsychologicalOpinionContent,
    # ...add other mappings as needed...
}


def document_field_map(document: Document) -> dict[str, Any]:
    return {
        "id": str(document.id),
        "patient_id": str(document.patient_id),
        "category": document.category.value,
        "file_name": document.file_name,
        "content": document.content.model_dump_json(),
    }


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
                file_name VARCHAR,
                content TEXT
            )
            """
        )
        log.info("Table 'documents' created successfully.")
    except Exception:
        log.error("Failed to create the 'documents' table.", exc_info=True)
        raise


def insert(connection: duckdb.DuckDBPyConnection, document: Document) -> None:
    try:
        insert_model(
            connection,
            "documents",
            document_field_map(document),
        )
        log.info(f"Inserted document with ID {document.id}")
    except Exception:
        log.error(f"Failed to insert document with ID {document.id}", exc_info=True)
        raise


def remove(connection: duckdb.DuckDBPyConnection, document_id: UUID) -> None:
    try:
        log.info(f"Removing document with ID: {document_id}")
        connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        log.info(f"Removed document with ID: {document_id}")
    except Exception:
        log.error(f"Failed to remove document with ID: {document_id}", exc_info=True)
        raise


def _fetch_document_row(
    connection: duckdb.DuckDBPyConnection, document_id: UUID
) -> tuple[Any, ...] | None:
    sql = "SELECT * FROM documents WHERE id = ?"
    return connection.execute(sql, (str(document_id),)).fetchone()  # type: ignore


def get_by_id(connection: duckdb.DuckDBPyConnection, document_id: UUID) -> Document:
    try:
        log.info(f"Retrieving document with ID: {document_id}")
        row = _fetch_document_row(connection, document_id)
        log.info(f"Retrieved document with ID: {document_id}")
        if row is None:
            raise ValueError(f"No document found with ID {document_id}")
        # Unpack fields
        id, patient_id, category, file_name, content_json = row  # type: ignore
        category_enum = DocumentCategory(category)
        content_model = CONTENT_MODEL_MAP.get(category_enum, ProntuaryContent)
        content = content_model.model_validate_json(content_json)  # type: ignore
        return Document(
            id=id,  # type: ignore
            patient_id=patient_id,  # type: ignore
            category=category_enum,
            file_name=file_name,  # type: ignore
            content=content,
        )
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
            "SELECT * FROM documents WHERE patient_id = ?", (str(patient_id),)
        ).fetchall()
        log.info("Retrieved all documents for the patient.")
        documents_list: list[Document] = []
        for result in results:
            id, patient_id, category, file_name, content_json = result
            category_enum = DocumentCategory(category)
            content_model = CONTENT_MODEL_MAP.get(category_enum, ProntuaryContent)
            content = content_model.model_validate_json(content_json)
            documents_list.append(
                Document(
                    id=id,
                    patient_id=patient_id,
                    category=category_enum,
                    file_name=file_name,
                    content=content,
                )
            )
        return documents_list
    except Exception:
        log.error("Failed to retrieve the patient's documents.", exc_info=True)
        raise
