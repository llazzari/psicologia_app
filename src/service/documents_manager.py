from uuid import UUID

from data import documents
from data.models import Document, DocumentCategory
from service.database_manager import get_db_connection


def get_all_documents_for(patient_id: UUID) -> list[Document]:
    connection = get_db_connection()
    return documents.get_all_for_patient_id(connection, patient_id)


def _get_all_for_category(
    all_documents: list[Document], category: DocumentCategory
) -> list[Document]:
    return [doc for doc in all_documents if doc.category == category]


def get_all_for_category(
    patient_id: UUID, category: DocumentCategory
) -> list[Document]:
    all_documents = get_all_documents_for(patient_id)
    return _get_all_for_category(all_documents, category)


def insert_document(document: Document) -> None:
    connection = get_db_connection()
    documents.insert(connection, document)
