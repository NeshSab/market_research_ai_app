"""
RAG-based knowledge base search tool for market intelligence retrieval.

This module provides semantic search capabilities over the internal knowledge
base using retrieval-augmented generation (RAG) techniques. It serves as the
primary source for established market analysis frameworks, sector insights,
and expert commentary.

The tool leverages FAISS vector search to find relevant documents and
provides structured output for integration with LLM-based analysis workflows.

Key features:
- Semantic search over curated knowledge base
- Market analysis framework retrieval
- Sector-specific insight discovery
- Expert commentary and pattern analysis
- Primary source prioritization for research
"""

import logging
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from ..services.retrievers import retrieve_semantic


class RAGSearchInput(BaseModel):
    query: str = Field(..., description="Search query for the internal knowledge base")


@tool(args_schema=RAGSearchInput)
def search_knowledge_base(query: str) -> str:
    """
    **PRIMARY SOURCE**: Search internal knowledge base for expert analysis frameworks.

    Use this FIRST for:
    • Established market analysis methodologies and frameworks
    • Sector-specific insights and investment approaches
    • Historical market patterns and analytical models
    • Expert commentary on market dynamics and trends

    This should be your go-to source before external searches.
    """
    try:
        docs = retrieve_semantic("var/faiss_index", query, k=3)

        if not docs:
            return "No relevant information found in internal knowledge base."

        formatted_results = []
        sources = []

        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "kb")
            source = source.replace("knowledge_base/playbooks/", "")
            chunk = doc.metadata.get("chunk", "")
            chunk_info = f" (chunk {chunk})" if chunk else ""

            formatted_results.append(
                f"*{i}. {source}{chunk_info}*\n{doc.page_content[:600]}..."
            )
            sources.append(f"{source}{chunk_info}")

        result = "\n\n".join(formatted_results)
        result += f"\n\n*Knowledge Base Sources: {', '.join(sources)}*"

        return result

    except Exception as e:
        logging.error(f"Error searching knowledge base: {e}")
        return f"Error searching knowledge base: {str(e)}"
