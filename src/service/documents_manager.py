from uuid import UUID

import logfire

from data import documents
from data.models.document_models import Document, DocumentCategory
from service.database_manager import get_db_connection

logfire.configure()


def get_all_documents_for(patient_id: UUID) -> list[Document]:
    logfire.info(f"SERVICE-OP: Fetching all documents for patient {patient_id}")
    connection = get_db_connection()
    docs = documents.get_all_for_patient_id(connection, patient_id)
    logfire.info(
        f"SERVICE-OP: Retrieved {len(docs)} documents for patient {patient_id}"
    )
    return docs


def _get_all_for_category(
    all_documents: list[Document], category: DocumentCategory
) -> list[Document]:
    filtered_docs = [doc for doc in all_documents if doc.category == category]
    logfire.info(
        f"SERVICE-OP: Filtered {len(filtered_docs)} documents for category {category.value}"
    )
    return filtered_docs


def get_all_for_category(
    patient_id: UUID, category: DocumentCategory
) -> list[Document]:
    logfire.info(
        f"SERVICE-OP: Fetching documents for patient {patient_id}, category {category.value}"
    )
    all_documents = get_all_documents_for(patient_id)
    return _get_all_for_category(all_documents, category)


def insert_document(document: Document) -> None:
    logfire.info(
        f"SERVICE-OP: Inserting document {document.id} for patient {document.patient_id}"
    )
    connection = get_db_connection()
    documents.insert(connection, document)
    logfire.info(f"SERVICE-OP: Successfully inserted document {document.id}")
