"""Retrieval for the "Analyse with AI" step.

Runs one vectorstore search per relevant topic (topic_mapper.py) and per
free-text clause, then deduplicates overlapping sections so the prompt doesn't
repeat the same Labour Act section multiple times.
"""

from typing import Dict, List

from langchain_core.documents import Document

from .config import RETRIEVAL_K
from .schemas import Employer
from .topic_mapper import TOPIC_QUERIES, determine_relevant_topics
from .vectorstore import get_vectorstore


def retrieve_for_topics(topics: List[str], vectorstore=None, k: int = RETRIEVAL_K) -> Dict[str, List[Document]]:
    """One retrieval query per topic. Returns topic -> list of Documents."""
    if vectorstore is None:
        vectorstore = get_vectorstore()
    results = {}
    for topic in topics:
        query = TOPIC_QUERIES[topic]
        results[topic] = vectorstore.similarity_search(query, k=k)
    return results


def retrieve_for_free_text_clauses(clauses: List[str], vectorstore=None, k: int = RETRIEVAL_K) -> Dict[str, List[Document]]:
    """One retrieval query per free-text clause the user typed in manually."""
    if vectorstore is None:
        vectorstore = get_vectorstore()
    results = {}
    for clause in clauses:
        results[clause] = vectorstore.similarity_search(clause, k=k)
    return results


def deduplicate_sections(topic_results: Dict[str, List[Document]]) -> List[Document]:
    """Deduplicates retrieved sections by (section, section_part)."""
    seen = set()
    deduped = []
    for docs in topic_results.values():
        for doc in docs:
            key = (doc.metadata.get("section"), doc.metadata.get("section_part"))
            if key not in seen:
                seen.add(key)
                deduped.append(doc)
    return deduped


def build_retrieval_context(employer: Employer, vectorstore=None) -> dict:
    """Full retrieval step for one employer's data."""
    topics = determine_relevant_topics(employer)
    topic_results = retrieve_for_topics(topics, vectorstore)

    clause_results = {}
    if employer.other_clauses:
        clause_results = retrieve_for_free_text_clauses(employer.other_clauses, vectorstore)

    all_results = {**topic_results, **clause_results}
    deduped_sections = deduplicate_sections(all_results)

    return {
        "topics": topics,
        "topic_results": topic_results,
        "clause_results": clause_results,
        "deduped_sections": deduped_sections,
    }
