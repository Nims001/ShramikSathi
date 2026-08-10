"""
Runs retrieval for each relevant topic (from topic_mapper.py) against
the Chroma vectorstore, and assembles everything the compliance step
needs: the retrieved Labour Act sections per topic, plus the user's
free-text 'other_clauses' (which don't map to a single topic and get
flagged for their own dedicated check).
"""

from typing import List, Dict
from langchain_core.documents import Document

from src.config import RETRIEVAL_K
from src.ingestion.embed_and_index import get_vectorstore
from src.intake.schema import Employer
from src.intake.topic_mapper import determine_relevant_topics, TOPIC_QUERIES


def retrieve_for_topics(topics: List[str], vectorstore=None, k: int = RETRIEVAL_K) -> Dict[str, List[Document]]:
    """
    Runs one retrieval query per topic. Returns a dict mapping
    topic -> list of retrieved Documents (each with .page_content and
    .metadata containing section/chapter/pages).
    """
    if vectorstore is None:
        vectorstore = get_vectorstore()

    results = {}
    for topic in topics:
        query = TOPIC_QUERIES[topic]
        results[topic] = vectorstore.similarity_search(query, k=k)

    return results


def retrieve_for_free_text_clauses(clauses: List[str], vectorstore=None, k: int = RETRIEVAL_K) -> Dict[str, List[Document]]:
    """
    Runs one retrieval query per free-text clause the user typed in
    manually (e.g. "i should work 90 hours per week"). Each clause gets
    its own retrieval, since a free-text clause could be about anything
    and isn't tied to a predefined topic.
    """
    if vectorstore is None:
        vectorstore = get_vectorstore()

    results = {}
    for clause in clauses:
        results[clause] = vectorstore.similarity_search(clause, k=k)

    return results


def deduplicate_sections(topic_results: Dict[str, List[Document]]) -> List[Document]:
    """
    Many topics will retrieve overlapping sections (e.g. 'overtime' and
    'working_hours' both likely pull Section 28). Deduplicate by
    section+part so the final context sent to Gemini isn't repeating
    the same section multiple times.
    """
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
    """
    Full retrieval step for one employer's data: determines relevant
    topics, retrieves sections for each, retrieves for free-text
    clauses, and deduplicates everything into one final section list.
    """
    if vectorstore is None:
        vectorstore = get_vectorstore()

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


if __name__ == "__main__":
    import json
    from src.intake.schema import AnalyseRequest

    with open("tests/sample_data/user.json", encoding="utf-8") as f:
        data = json.load(f)

    parsed = AnalyseRequest(**data)
    employer = parsed.employers[0].employer

    context = build_retrieval_context(employer)

    print(f"Topics: {context['topics']}\n")

    for topic, docs in context["topic_results"].items():
        print(f"--- {topic} ---")
        for d in docs:
            print(f"  Section {d.metadata['section']} (part {d.metadata['section_part']}): {d.page_content[:80]}...")
        print()

    if context["clause_results"]:
        print("--- free-text clauses ---")
        for clause, docs in context["clause_results"].items():
            print(f"Clause: \"{clause}\"")
            for d in docs:
                print(f"  Section {d.metadata['section']} (part {d.metadata['section_part']}): {d.page_content[:80]}...")
            print()

    print(f"\nTotal deduplicated sections to send to Gemini: {len(context['deduped_sections'])}")