from pathlib import Path

from haystack import Document, Pipeline
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.retrievers import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore

from data.models.document_models import DocumentCategory
from utils.helpers import read_file

# Map each document category to its guideline/template file(s)
DOCUMENT_GUIDELINE_MAP = {
    DocumentCategory.DECLARATION: ["CFP_resolucao-6-2019.pdf"],
    DocumentCategory.PSYCHOLOGICAL_CERTIFICATE: ["CFP_resolucao-6-2019.pdf"],
    DocumentCategory.PSYCHOLOGICAL_REPORT: ["CFP_resolucao-6-2019.pdf"],
    DocumentCategory.MULTIDISCIPLINARY_REPORT: ["CFP_resolucao-6-2019.pdf"],
    DocumentCategory.PSYCHOLOGICAL_EVALUATION_REPORT: ["CFP_resolucao-6-2019.pdf"],
    DocumentCategory.PSYCHOLOGICAL_OPINION: ["CFP_resolucao-6-2019.pdf"],
    DocumentCategory.PRONTUARY: ["CFP_resolucao-5-2025.pdf"],
    DocumentCategory.ANAMNESIS: ["anamnesis.md"],
    DocumentCategory.BUDGET: ["budget.md"],
    # Add more mappings as needed
}

# Cache document stores per category
document_stores: dict[DocumentCategory, InMemoryDocumentStore] = {}

# Get the absolute path to the docs directory
DOCS_DIR = Path.cwd() / "docs"


def get_document_store_for_category(
    category: DocumentCategory,
) -> InMemoryDocumentStore:
    if category in document_stores:
        return document_stores[category]

    store = InMemoryDocumentStore()
    files = DOCUMENT_GUIDELINE_MAP.get(category, [])
    docs: list[Document] = []

    for file_name in files:
        file_path = DOCS_DIR / file_name
        if file_path.exists():
            docs.append(Document(content=read_file(file_path)))

    if docs:
        # Embed and index documents
        embedder = SentenceTransformersTextEmbedder(model="intfloat/e5-large-v2")
        pipe = Pipeline()
        pipe.add_component(instance=embedder, name="embedder")

        result = pipe.run({"embedder": {"text": [doc.content for doc in docs]}})
        embeddings: list[list[float]] = result["embedder"]["embedding"]
        embedded_docs: list[Document] = []
        for doc, embedding in zip(docs, embeddings):
            doc.embedding = embedding
            embedded_docs.append(doc)
        store.write_documents(embedded_docs)

    document_stores[category] = store
    return store


def retrieve_context(
    query: str, category: DocumentCategory, top_k: int = 5
) -> list[str]:
    store = get_document_store_for_category(category)
    embedder = SentenceTransformersTextEmbedder(model="intfloat/e5-large-v2")
    retriever = InMemoryEmbeddingRetriever(document_store=store, top_k=top_k)

    pipe = Pipeline()
    pipe.add_component(instance=embedder, name="embedder")
    pipe.add_component(instance=retriever, name="retriever")
    pipe.connect("embedder.embedding", "retriever.query_embedding")

    result = pipe.run({"embedder": {"text": query}})
    docs = result["retriever"]["documents"]

    return [doc.content for doc in docs]


if __name__ == "__main__":
    print(retrieve_context("O que é um prontuário?", DocumentCategory.PRONTUARY))
