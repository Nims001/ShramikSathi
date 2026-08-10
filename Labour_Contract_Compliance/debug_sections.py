"""
Quick diagnostic: fetch specific sections by number directly (not via
similarity search) to inspect what's actually there.
"""

from src.ingestion.embed_and_index import get_vectorstore

vectorstore = get_vectorstore()

for section_num in ["28", "29", "68", "69", "70", "71", "72", "73", "74"]:
    results = vectorstore.get(where={"section": section_num})
    if results["documents"]:
        for doc, meta in zip(results["documents"], results["metadatas"]):
            print(f"--- Section {section_num} (part {meta.get('section_part')}) ---")
            print(doc[:200])
            print()
    else:
        print(f"--- Section {section_num}: not found ---\n")