# def build_prompt(ocr_text, policy_text):
#     return f"""
# You are a health insurance claim evaluator.

# OCR Extracted Medical Report:
# \"\"\"{ocr_text}\"\"\"

# Relevant Policy Terms:
# \"\"\"{policy_text}\"\"\"

# Based on the above, decide:
# 1. Can this claim be approved? (Yes/No)
# 2. Reason for the decision.

# Respond in JSON format with:
# {{
#   "status": "Approved" or "Rejected",
#   "reasoning": "..."
# }}
# """


import os
from typing import List, Dict
from policy_search import find_or_fetch_policy_pdf, _insurer_key
from policy_ingest import read_pdf_text, clean_text, chunk_text
from embeddings_faiss import ensure_index, search

def retrieve_policy_clauses(insurer: str, queries: List[str], k_per_query=4) -> List[str]:
    """
    1) Ensure policy PDF is cached locally.
    2) Read & chunk policy text.
    3) Build or load FAISS index for this insurer.
    4) Run semantic search for each query and collect top passages.
    """
    pdf_path = find_or_fetch_policy_pdf(insurer, keywords=["coverage", "exclusions", "hospitalization", "cashless"])
    if not pdf_path:
        return []

    text = clean_text(read_pdf_text(pdf_path))
    passages = chunk_text(text)
    if not passages:
        return []

    insurer_key = _insurer_key(insurer)
    index, texts = ensure_index(insurer_key, passages)

    seen, out = set(), []
    for q in queries:
        for score, passage in search(index, texts, q, k=k_per_query):
            # De-dup near-identical passages
            key = passage[:200]
            if key not in seen:
                seen.add(key)
                out.append(passage)
    # Keep a reasonable cap to avoid prompt bloat
    return out[:12]

def build_prompt(ocr_text: str, structured: Dict, policy_clauses: List[str]) -> str:
    insurer = structured.get("insurance_company", "") or "Unknown"
    claimed = structured.get("claimed_amount", "")
    diagnosis = structured.get("diagnosis", "")

    clauses_joined = "\n\n---\n".join(policy_clauses) if policy_clauses else "No clauses retrieved."

    return f"""
You are a senior health insurance claim adjudicator. Use ONLY the provided claim data and policy excerpts.

TASKS:
1) Determine if the diagnosis/treatment are covered.
2) Identify covered vs non-medical or excluded items.
3) If covered, compute an approved amount (if possible) in brief.
4) If information is insufficient, return "query" with what is missing.
5) Cite the relevant policy excerpts in your reasoning.

CLAIM (OCR EXTRACT):
\"\"\"{ocr_text[:8000]}\"\"\"  # truncated to keep prompt size reasonable

STRUCTURED FIELDS:
{structured}

POLICY EXCERPTS:
\"\"\"
{clauses_joined}
\"\"\"


Return ONLY valid JSON with this schema:
{{
  "status": "approved" | "rejected" | "partial" | "query",
  "approved_amount": null | number,
  "covered_items": string[],
  "excluded_items": string[],
  "reasoning": "short, cite clause snippets where relevant (e.g., 'Excl 2: ...')"
}}
""".strip()
