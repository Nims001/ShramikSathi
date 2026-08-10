"""RAG-based "Analyse with AI" pipeline.

Ported from the reference pipeline in `Labour_Contract_Compliance/` (retrieval
over a Chroma vectorstore of The Labour Act, 2017, plus a Gemini completion
that only cites retrieved sections). Deterministic findings stay the source of
truth; these AI findings are supplementary and are always visually labelled as
AI-generated in the UI.
"""
