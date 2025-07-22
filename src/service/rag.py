import json
from functools import lru_cache
from typing import Literal, Optional

import streamlit as st
from haystack import Document, Pipeline, component
from haystack.components.builders.prompt_builder import PromptBuilder
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)
from haystack.components.generators import HuggingFaceAPIGenerator
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.retrievers import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore

from data.models import CONTENT_MODEL_MAP, DocumentCategory, DocumentContent
from utils.helpers import extract_text_from_pdf


def load_document(path: str) -> Document:
    return Document(content=extract_text_from_pdf(path))


def split_document(
    document: Document,
    split_by: Literal[
        "function", "page", "passage", "period", "word", "line", "sentence"
    ] = "word",
    split_length: int = 500,
    split_overlap: int = 50,
) -> list[Document]:
    splitter = DocumentSplitter(
        split_by=split_by, split_length=split_length, split_overlap=split_overlap
    )
    split_pipe = Pipeline()
    split_pipe.add_component(instance=splitter, name="splitter")
    result = split_pipe.run({"splitter": {"documents": [document]}})
    return result["splitter"]["documents"]


def embed_documents(
    documents: list[Document], model: str = "intfloat/e5-large-v2"
) -> list[Document]:
    embedder = SentenceTransformersDocumentEmbedder(model=model)
    embed_pipe = Pipeline()
    embed_pipe.add_component(instance=embedder, name="embedder")
    result = embed_pipe.run({"embedder": {"documents": documents}})
    return result["embedder"]["documents"]


def write_documents_to_store(
    documents: list[Document], store: Optional[InMemoryDocumentStore] = None
) -> InMemoryDocumentStore:
    if store is None:
        store = InMemoryDocumentStore()
    store.write_documents(documents)
    return store


def build_rag_pipeline(document_store: InMemoryDocumentStore) -> Pipeline:
    query_embedder = SentenceTransformersTextEmbedder(model="intfloat/e5-large-v2")
    retriever = InMemoryEmbeddingRetriever(document_store=document_store, top_k=5)
    huggingface_generator = HuggingFaceAPIGenerator(
        token=st.secrets.api_keys["huggingface_api_key"],
        api_params={"model": "mistralai/Mistral-7B-Instruct-v0.1"},
        api_type="serverless_inference_api",
    )
    prompt_template = [
        {
            "role": "system",
            "content": (
                "Você é um assistente que gera um documento da categoria {{categoria_documento}} conforme as normas aplicáveis. "
                "Receba trechos do documento e os dados do paciente, e gere um JSON estritamente válido "
                "para o modelo Pydantic {{pydantic_model}}."
            ),
        },
        {
            "role": "user",
            "content": (
                "Trechos normativos:\n{% for doc in documents %}{{doc.content}}\n{% endfor %}\n"
                "Dados do paciente: {{question}}"
            ),
        },
    ]
    prompt_builder = PromptBuilder(template=json.dumps(prompt_template))
    rag_pipe = Pipeline()
    rag_pipe.add_component(instance=query_embedder, name="query_embedder")
    rag_pipe.add_component(instance=retriever, name="retriever")
    rag_pipe.add_component(instance=prompt_builder, name="prompt_builder")
    rag_pipe.add_component(instance=huggingface_generator, name="generator")
    rag_pipe.connect("query_embedder.embedding", "retriever.query_embedding")
    rag_pipe.connect("retriever.documents", "prompt_builder.documents")
    rag_pipe.connect("prompt_builder.messages", "generator.messages")
    return rag_pipe


def validate_output(
    pydantic_model: type[DocumentContent], text: str
) -> dict[str, str | None]:
    try:
        obj = json.loads(text)
        pydantic_model.model_validate(obj)
        return {"valid": text, "invalid": None, "error": None}
    except Exception as e:
        return {"valid": None, "invalid": text, "error": str(e)}


# Haystack component class for output validation
@component
class OutputValidator:
    def __init__(self, pydantic_model: type[DocumentContent]):
        self.pydantic_model = pydantic_model

    @component.output_types(valid=str, invalid=str, error=str)
    def run(self, replies: list[str]) -> dict[str, str | None]:
        text = replies[0]
        return validate_output(self.pydantic_model, text)


@lru_cache(maxsize=1)
def store_documents() -> InMemoryDocumentStore:
    document_store = InMemoryDocumentStore()
    doc = load_document(
        "/mnt/c/Users/lucas/projects/psicologia_app/docs/CFP_resolucao-6-2019.pdf"
    )
    split_docs = split_document(doc)
    embedded_docs = embed_documents(split_docs)
    document_store = write_documents_to_store(embedded_docs, document_store)
    return document_store


def build_rag_pipeline_with_validator(
    document_store: InMemoryDocumentStore, document_category: DocumentCategory
) -> Pipeline:
    rag_pipe = build_rag_pipeline(document_store)
    validator = OutputValidator(CONTENT_MODEL_MAP[document_category])
    rag_pipe.add_component(instance=validator, name="validator")
    rag_pipe.connect("generator.replies", "validator.replies")
    return rag_pipe


def generate(query: str, document_category: DocumentCategory) -> str:
    document_store = store_documents()
    rag_pipe = build_rag_pipeline_with_validator(document_store, document_category)
    pipeline_input = {
        "query_embedder": {"text": query},
        "prompt_builder": {
            "question": query,
            "categoria_documento": document_category.value,
            "pydantic_model": CONTENT_MODEL_MAP[document_category],
        },
    }
    result = rag_pipe.run(pipeline_input)
    valid = result["validator"]["valid"]
    error = result["validator"]["error"]
    return valid if valid else f"Erro: {error}"


# Exemplo de uso
if __name__ == "__main__":
    resp = generate(
        "Paciente Fulano de Tal, 30 anos, demanda: avaliação vocacional.",
        DocumentCategory.PRONTUARY,
    )
    print(resp)
