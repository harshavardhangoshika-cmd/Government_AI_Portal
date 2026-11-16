"""
Civic & Public Welfare Knowledge Base Retriever
===============================================
Hybrid semantic vector retrieval engine for municipal bylaws,
citizen SLAs, grievance redressal rules, and government welfare schemes.
"""

import os
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_PATH = os.path.join(BASE_DIR, "knowledge_base.json")


class CivicKnowledgeRetriever:
    def __init__(self, kb_path=KB_PATH):
        self.kb_path = kb_path
        self.documents = []
        self.doc_vectors = None
        self.vectorizer = None
        self._load_and_index()

    def _load_and_index(self):
        """Loads knowledge base documents and builds the vector index."""
        if not os.path.exists(self.kb_path):
            raise FileNotFoundError(f"Knowledge base file not found at: {self.kb_path}")

        with open(self.kb_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.documents = data.get("documents", [])

        # Create rich indexing corpus for each document
        corpus = []
        for doc in self.documents:
            kw_str = " ".join(doc.get("keywords", []))
            combined_text = (
                f"{doc.get('topic', '')} "
                f"{doc.get('category', '')} "
                f"{doc.get('authority', '')} "
                f"{doc.get('act_or_scheme', '')} "
                f"{kw_str} "
                f"{doc.get('content', '')} "
                f"{doc.get('escalation', '')}"
            )
            corpus.append(combined_text)

        # Build sublinear TF-IDF vectorizer (unigrams + bigrams + trigrams)
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            sublinear_tf=True,
            stop_words="english"
        )
        self.doc_vectors = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 3, threshold: float = 0.08):
        """
        Retrieves top relevant knowledge documents for a citizen query.

        Parameters:
        - query: Citizen natural language question or description
        - top_k: Maximum number of relevant passages to retrieve
        - threshold: Minimum semantic cosine similarity cutoff

        Returns:
        List of dicts: [ { document, score, match_type }, ... ]
        """
        if not query or not query.strip():
            return []

        q_clean = query.strip()
        q_vec = self.vectorizer.transform([q_clean])
        cosine_scores = cosine_similarity(q_vec, self.doc_vectors)[0]

        # Keyword boost for exact civic matches
        q_lower = q_clean.lower()
        final_scores = np.copy(cosine_scores)

        for idx, doc in enumerate(self.documents):
            # Keyword matching bonus
            for kw in doc.get("keywords", []):
                if kw in q_lower:
                    final_scores[idx] += 0.15

            # Category / authority direct bonus
            if doc.get("category", "").lower() in q_lower:
                final_scores[idx] += 0.20
            if doc.get("authority", "").lower() in q_lower:
                final_scores[idx] += 0.20

        # Sort indices by descending score
        ranked_indices = np.argsort(final_scores)[::-1]

        results = []
        for rank_idx in ranked_indices:
            score = float(final_scores[rank_idx])
            if score < threshold and len(results) > 0:
                break

            doc = self.documents[rank_idx]
            results.append({
                "document": doc,
                "relevance_score": round(score, 3),
                "id": doc.get("id"),
                "topic": doc.get("topic"),
                "category": doc.get("category"),
                "authority": doc.get("authority"),
                "sla_hours": doc.get("sla_hours"),
                "act_or_scheme": doc.get("act_or_scheme"),
                "content": doc.get("content"),
                "escalation": doc.get("escalation"),
                "action_suggested": doc.get("action_suggested")
            })

            if len(results) >= top_k:
                break

        return results


# Global singleton instance
_RETRIEVER = None

def get_retriever():
    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = CivicKnowledgeRetriever()
    return _RETRIEVER


if __name__ == "__main__":
    retriever = get_retriever()
    test_queries = [
        "How do I report a pothole on the road and what is the SLA?",
        "What should I do if raw sewage is leaking from an open manhole?",
        "Can I get subsidy for installing rooftop solar?",
        "Who is responsible if electricity wires are sparking on my street?"
    ]
    for q in test_queries:
        print(f"\nQUERY: {q}")
        matches = retriever.retrieve(q, top_k=2)
        for m in matches:
            print(f" -> [{m['id']}] {m['topic']} (Score: {m['relevance_score']}, SLA: {m['sla_hours']}h)")
