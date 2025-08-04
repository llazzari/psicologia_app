from pathlib import Path

import chromadb
import dotenv
import logfire
from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.prompts import PromptTemplate
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import (
    ResponseMode,
    get_response_synthesizer,  # type: ignore
)
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding  # type: ignore
from llama_index.llms.mistralai import MistralAI  # type: ignore
from llama_index.vector_stores.chroma import ChromaVectorStore  # type: ignore

logfire.configure()

config = dotenv.dotenv_values(".env")
MISTRAL_API_KEY = config.get("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    logfire.error("RETRIEVAL-ERROR: MISTRAL_API_KEY is not set")
    raise ValueError("MISTRAL_API_KEY is not set")

logfire.info("RETRIEVAL-SETUP: Initializing retrieval service with Mistral API")

# Improved embedding model for better semantic understanding
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-large-en-v1.5",  # Larger model for better embeddings
    device="cuda",  # Change to "cuda" if you have GPU
)

# Configure LLM with better parameters
Settings.llm = MistralAI(
    api_key=MISTRAL_API_KEY,
    model="mistral-large-latest",  # Use the latest model for better responses
    temperature=0.1,  # Lower temperature for more precise responses
    max_tokens=2048,
)

# Custom prompt template for better RAG responses
CUSTOM_PROMPT_TEMPLATE = """Você é um assistente especializado em psicologia e documentação psicológica. 
Sua tarefa é responder perguntas com base nos documentos fornecidos.

Contexto dos documentos:
{context_str}

Pergunta: {query_str}

Instruções:
1. Responda apenas com base nas informações fornecidas no contexto
2. Se a informação não estiver no contexto, diga "Não encontrei essa informação nos documentos disponíveis"
3. Seja preciso e conciso
4. Use linguagem clara e profissional
5. Se houver múltiplas fontes, cite-as quando relevante

Resposta:"""


def check_collection_status():
    """Check if the ChromaDB collection has documents"""
    logfire.info("RETRIEVAL-OP: Checking ChromaDB collection status")
    db = chromadb.PersistentClient(path="./chroma_db")
    try:
        collection = db.get_collection("quickstart")
        count = collection.count()
        logfire.info(f"RETRIEVAL-OP: Collection 'quickstart' has {count} documents")
        return count
    except Exception as e:
        logfire.error(f"RETRIEVAL-ERROR: Error accessing collection: {e}")
        return 0


def load_and_index_documents():
    """Load documents from docs/CFP_resolutions folder and index them into ChromaDB"""
    logfire.info("RETRIEVAL-OP: Starting document loading and indexing process")
    docs_path = Path("./docs/CFP_resolutions")

    if not docs_path.exists():
        logfire.error("RETRIEVAL-ERROR: docs/CFP_resolutions folder not found!")
        return False

    logfire.info("RETRIEVAL-OP: Loading documents from docs/CFP_resolutions folder")

    # Load documents using SimpleDirectoryReader
    documents = SimpleDirectoryReader(  # type: ignore
        input_dir=str(docs_path), recursive=True, required_exts=[".md", ".pdf", ".txt"]
    ).load_data()

    logfire.info(f"RETRIEVAL-OP: Loaded {len(documents)} documents")

    if not documents:
        logfire.error(
            "RETRIEVAL-ERROR: No documents found in docs/CFP_resolutions folder!"
        )
        return False

    # Initialize ChromaDB and clear existing collection
    db = chromadb.PersistentClient(path="./chroma_db")

    # Delete existing collection to start fresh
    try:
        db.delete_collection("quickstart")
        print("🗑️  Deleted existing collection")
    except Exception:
        pass

    # Create new collection
    chroma_collection = db.create_collection("quickstart")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Create index with documents
    print("🔧 Creating index with documents...")
    VectorStoreIndex.from_documents(  # type: ignore
        documents,  # type: ignore
        storage_context=storage_context,
        embed_model=Settings.embed_model,
    )

    print("✅ Documents indexed successfully!")
    return True


def create_optimized_query_engine(top_k: int = 5, alpha: float = 0.5):
    """Create an optimized query engine with configurable parameters"""

    db = chromadb.PersistentClient(path="./chroma_db")

    chroma_collection = db.get_or_create_collection("quickstart")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Create index with better configuration
    index = VectorStoreIndex.from_vector_store(  # type: ignore
        vector_store,
        storage_context=storage_context,
        embed_model=Settings.embed_model,
    )

    # Create retriever with optimized parameters
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=top_k,  # Retrieve top K most similar documents
        alpha=alpha,  # Balance between dense and sparse retrieval
    )

    # Create response synthesizer with custom prompt
    response_synthesizer = get_response_synthesizer(
        llm=Settings.llm,
        response_mode=ResponseMode.COMPACT,  # More concise responses
        structured_answer_filtering=True,  # Filter out irrelevant information
        text_qa_template=PromptTemplate(CUSTOM_PROMPT_TEMPLATE),
    )

    # Create optimized query engine
    return RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
    )


def test_query(query: str, top_k: int = 5, alpha: float = 0.5):
    """Test a query with detailed output"""
    print(f"🔍 Query: {query}")
    print(f"⚙️  Config: top_k={top_k}, alpha={alpha}")
    print("=" * 50)

    query_engine = create_optimized_query_engine(top_k=top_k, alpha=alpha)

    # Test retrieval separately first
    print("🔍 Testing retrieval...")
    retriever = query_engine.retriever
    retrieved_nodes = retriever.retrieve(query)
    print(f"📄 Retrieved {len(retrieved_nodes)} nodes")

    if retrieved_nodes:
        print("📚 Retrieved content:")
        for i, node in enumerate(retrieved_nodes, 1):
            print(f"  {i}. Score: {getattr(node, 'score', 'N/A')}")
            print(f"     Text: {node.text[:200]}...")
            print()
    else:
        print("❌ No nodes retrieved!")
        return None

    # Now test the full query
    print("🤖 Testing full query...")
    response = query_engine.query(query)
    print(f"📝 Resposta: {response}")

    # Print retrieved sources for debugging
    if hasattr(response, "source_nodes") and response.source_nodes:
        print(f"📄 Fontes: {len(response.source_nodes)} documentos recuperados")
        print("\n📚 Documentos recuperados:")
        for i, node in enumerate(response.source_nodes, 1):
            score = getattr(node, "score", "N/A")
            print(f"{i}. Score: {score}")
            print(f"   Conteúdo: {node.text[:200]}...")
            print()

    return response


# Test different queries and configurations
if __name__ == "__main__":
    # First, check if we have any documents
    print("🔍 Checking collection status...")
    doc_count = check_collection_status()

    # If collection is empty, load documents
    if doc_count == 0:
        print("\n📚 Collection is empty. Loading documents from docs/ folder...")
        if load_and_index_documents():
            print("✅ Documents loaded and indexed successfully!")
        else:
            print("❌ Failed to load documents!")
            exit(1)
    else:
        print(f"✅ Collection has {doc_count} documents")

    print("\n" + "=" * 80 + "\n")

    # Test queries
    test_queries: list[str] = [
        "Quais são os tipos de documentos psicológicos?",
        "Como fazer um relatório psicológico?",
        "Quais são os elementos de uma avaliação psicológica?",
        "Como documentar uma sessão de terapia?",
    ]

    for query in test_queries:
        test_query(query, top_k=5, alpha=0.5)
        print("\n" + "=" * 80 + "\n")
