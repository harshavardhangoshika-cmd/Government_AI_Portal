"""
Unified Citizen AI Help RAG Service
===================================
Coordinates query retrieval and response generation for the Government Portal.
"""

from typing import Dict, Any, Optional
from app.rag.retriever import get_retriever
from app.rag.generator import generate_rag_response


def ask_civic_rag(query: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Main entry point for answering citizen questions using RAG.
    """
    if not query or not query.strip():
        return {
            "answer": "Please ask a question regarding municipal complaints, government welfare schemes, or citizen SLAs.",
            "sources": [],
            "suggested_actions": []
        }

    retriever = get_retriever()
    retrieved_docs = retriever.retrieve(query, top_k=top_k)
    response = generate_rag_response(query, retrieved_docs)

    return response


if __name__ == "__main__":
    test_q = "How do I report broken streetlights on my street and how long will it take?"
    res = ask_civic_rag(test_q)
    print("QUERY:", test_q)
    print("\nANSWER:\n", res["answer"])
    print("\nSOURCES:", res["sources"])
