# from fastapi import FastAPI, UploadFile, File
# from fastapi.middleware.cors import CORSMiddleware
# from typing import List

# from ocr_utils import extract_text_from_file
# from llm_utils import query_llm
# from rag_utils import build_prompt
# from field_extractor import extract_structured_fields

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.post("/process-claim/")
# async def process_claim(files: List[UploadFile] = File(...)):
#     combined_text = ""
    
#     for file in files:
#         contents = await file.read()
#         file_text = extract_text_from_file(contents, file.filename)
#         combined_text += f"\n\n--- Document: {file.filename} ---\n{file_text}"

#     structured_data = extract_structured_fields(combined_text)
    
#     policy_text = "According to the policy, hospitalization must exceed 24 hours and pre-approval is needed for surgeries."
#     prompt = build_prompt(combined_text, policy_text)
#     decision = query_llm(prompt)

#     return {
#         "ocr_text": combined_text,
#         "structured_data": structured_data,
#         "decision": decision
#     }


from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from ocr_utils import extract_text_from_file
from llm_utils import query_llm
from rag_utils import build_prompt, retrieve_policy_clauses
from field_extractor import extract_structured_fields

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process-claim/")
async def process_claim(files: List[UploadFile] = File(...)):
    combined_text = ""

    for file in files:
        contents = await file.read()
        file_text = extract_text_from_file(contents, file.filename)
        combined_text += f"\n\n--- Document: {file.filename} ---\n{file_text}"

    # Step 1: LLM-assisted field extraction
    structured_data = extract_structured_fields(combined_text)

    insurer = ""
    if isinstance(structured_data, dict):
        insurer = structured_data.get("insurance_company") or ""

    # Step 2: RAG - retrieve relevant policy clauses using FAISS
    # Build search queries from structured fields + heuristics
    q = []
    if isinstance(structured_data, dict):
        if structured_data.get("diagnosis"): q.append(structured_data["diagnosis"])
        if structured_data.get("claimed_amount"): q.append(f"charges {structured_data['claimed_amount']}")
        q += ["coverage", "exclusions", "hospitalization", "pre-authorization", "bed charges", "non-medical items"]

    policy_clauses = retrieve_policy_clauses(insurer, q) if insurer else []

    # Step 3: Build decision prompt and query LLM
    prompt = build_prompt(combined_text, structured_data if isinstance(structured_data, dict) else {}, policy_clauses)
    decision = query_llm(prompt)

    return {
        "ocr_text": combined_text,
        "structured_data": structured_data,
        "policy_clauses_used": policy_clauses[:6],  # show a handful on UI
        "decision": decision
    }
    if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


