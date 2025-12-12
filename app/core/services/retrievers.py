"""
Document retrieval and semantic search services.

This module provides advanced document retrieval capabilities using FAISS
vector stores and semantic search. It implements various retrieval strategies
including simple similarity search and RAG fusion for enhanced document
discovery.

Key capabilities:
- FAISS vector store loading and management
- Semantic similarity search with configurable result counts
- RAG fusion retrieval combining multiple query variants
- Document deduplication and stable ID generation
- LangChain integration for retrieval chains

The service supports both simple retrieval and advanced techniques like
query expansion for improved search results in knowledge base applications.
"""

from __future__ import annotations
import hashlib
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from ..prompts.tools.query_variants import system_prompt, user_prompt


def get_embeddings() -> OpenAIEmbeddings:
    """
    Create OpenAI embeddings instance for vector operations.

    Returns
    -------
    OpenAIEmbeddings
        Configured OpenAI embeddings client
    """
    return OpenAIEmbeddings()


def load_vectorstore(index_path: str) -> FAISS:
    """
    Load FAISS vector store from disk.

    Parameters
    ----------
    index_path : str
        Path to the FAISS index directory

    Returns
    -------
    FAISS
        Loaded FAISS vector store instance
    """
    return FAISS.load_local(
        index_path,
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


def get_semantic_retriever(index_path: str, k: int = 4) -> VectorStoreRetriever:
    """
    Create semantic similarity retriever from vector store.

    Parameters
    ----------
    index_path : str
        Path to the FAISS index directory
    k : int, default 4
        Number of similar documents to retrieve

    Returns
    -------
    VectorStoreRetriever
        Configured retriever for semantic search
    """
    vs = load_vectorstore(index_path)
    return vs.as_retriever(search_type="similarity", search_kwargs={"k": k})


def retrieve_semantic(index_path: str, query: str, k: int = 4) -> list[Document]:
    """
     Retrieve semantically similar documents for a query.

    Parameters
    ----------
    index_path : str
        Path to the FAISS index directory
    query : str
        Search query for document retrieval
    """
    retriever = get_semantic_retriever(index_path, k=k)
    return retriever.invoke(query)


def create_semantic_chain(index_path: str, k: int = 4) -> 'RunnableLambda':
    """
    Create a retrieval chain using modern LangChain patterns.
    Returns a chain that can be composed with other chains.
    """
    retriever = get_semantic_retriever(index_path, k=k)

    def retrieve_docs(inputs: dict) -> list[Document]:
        query = inputs.get("query", inputs) if isinstance(inputs, dict) else inputs
        return retriever.invoke(str(query))

    return RunnableLambda(retrieve_docs)


def generate_query_variants(
    query: str, n_variants: int = 4, model: str = "gpt-4o-mini"
) -> list[str]:
    """
    Produce a handful of semantically diverse rewrites to improve recall.
    Uses modern LangChain prompt template and chain.
    """

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_prompt()), ("user", user_prompt(query, n_variants))]
    )

    llm = ChatOpenAI(model=model, temperature=0.0)
    chain = prompt_template | llm | StrOutputParser()

    response = chain.invoke({"query": query, "n_variants": n_variants})
    variants = [line.strip(" -•\t") for line in response.splitlines() if line.strip()]
    unique: list[str] = []
    seen = set()
    for q in [query] + variants:
        if q not in seen:
            unique.append(q)
            seen.add(q)
    return unique


def _stable_doc_id(doc: Document) -> str:
    """
    Stable id for de-duplication. Prefer (source + start_index) else content hash.
    """
    source = str(doc.metadata.get("source", ""))
    start = str(doc.metadata.get("start_index", ""))
    if source:
        return f"{source}:{start}"
    h = hashlib.sha256(doc.page_content[:256].encode("utf-8")).hexdigest()
    return f"hash:{h}"


def _rrf_merge(
    results_by_query: list[list[Document]], k: int = 5, k_per_list: int = 5
) -> list[Document]:
    """
    Reciprocal Rank Fusion. score = sum(1 / (K0 + rank)), K0=60.
    """
    K0 = 60
    scores: dict[str, float] = {}
    best_doc: dict[str, Document] = {}

    for docs in results_by_query:
        for rank, doc in enumerate(docs[:k_per_list], start=1):
            did = _stable_doc_id(doc)
            scores[did] = scores.get(did, 0.0) + 1.0 / (K0 + rank)
            if did not in best_doc:
                best_doc[did] = doc

    ranked_ids = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
    return [best_doc[d] for d in ranked_ids[:k]]


def retrieve_rag_fusion(
    index_path: str,
    query: str,
    k: int = 5,
    k_per_query: int = 4,
    n_variants: int = 4,
    model_for_variants: str = "gpt-4o-mini",
) -> list[Document]:
    """
    Better recall than simple semantic search using modern LangChain chains.

    1) Generate query variants with LLM chain
    2) Retrieve top-k_per_query for each variant
    3) Fuse with RRF and return top-k
    """
    vs = load_vectorstore(index_path)
    retr = vs.as_retriever(search_kwargs={"k": k_per_query})

    variants = generate_query_variants(
        query, n_variants=n_variants, model=model_for_variants
    )
    results_by_query: list[list[Document]] = [retr.invoke(v) for v in variants]

    return _rrf_merge(results_by_query, k=k, k_per_list=k_per_query)


def create_rag_fusion_chain(
    index_path: str,
    k: int = 5,
    k_per_query: int = 4,
    n_variants: int = 4,
    model_for_variants: str = "gpt-4o-mini",
):
    """
    Create a RAG fusion chain that can be composed with other chains.
    Returns a chain that takes a query and returns fused documents.
    """
    vs = load_vectorstore(index_path)
    retriever = vs.as_retriever(search_kwargs={"k": k_per_query})

    def rag_fusion_retrieve(inputs: dict) -> list[Document]:
        query = inputs.get("query", inputs) if isinstance(inputs, dict) else inputs
        query_str = str(query)
        variants = generate_query_variants(
            query_str, n_variants=n_variants, model=model_for_variants
        )
        results_by_query = [retriever.invoke(variant) for variant in variants]
        return _rrf_merge(results_by_query, k=k, k_per_list=k_per_query)

    return RunnableLambda(rag_fusion_retrieve)
