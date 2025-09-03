# from llm_utils import query_llm

# def extract_structured_fields(ocr_text: str) -> dict:
#     prompt = f"""
# You are an expert in reading medical documents for insurance claims.

# Extract the following fields from the document:
# - Patient Name
# - Age
# - Diagnosis
# - Date of Admission
# - Date of Discharge
# - Hospital Name
# - Insurance Company Name
# - Policy ID
# - Claimed Amount

# Here is the document text:
# \"\"\"{ocr_text}\"\"\"

# Provide the extracted values in this JSON format:
# {{
#   "name": "",
#   "age": "",
#   "diagnosis": "",
#   "date_of_admission": "",
#   "date_of_discharge": "",
#   "hospital_name": "",
#   "insurance_company": "",
#   "policy_id": "",
#   "claimed_amount": ""
# }}
# """

#     response = query_llm(prompt)
#     try:
#         return eval(response) if isinstance(response, str) else response
#     except Exception as e:
#         return {"error": f"Failed to parse response: {e}", "raw_response": response}


import json
from llm_utils import query_llm  # unchanged import

def extract_structured_fields(ocr_text: str) -> dict:
    prompt = f"""
You are an expert in reading medical documents for insurance claims.

Extract the following fields from the document:
- Patient Name
- Age
- Diagnosis
- Date of Admission
- Date of Discharge
- Hospital Name
- Insurance Company Name
- Policy ID
- Claimed Amount

Here is the document text:
\"\"\"{ocr_text}\"\"\"


Return ONLY valid JSON in this exact format (no extra text):
{{
  "name": "",
  "age": "",
  "diagnosis": "",
  "date_of_admission": "",
  "date_of_discharge": "",
  "hospital_name": "",
  "insurance_company": "",
  "policy_id": "",
  "claimed_amount": ""
}}
""".strip()

    response = query_llm(prompt)
    try:
        return json.loads(response)
    except Exception as e:
        return {"error": f"Failed to parse JSON: {e}", "raw_response": response}
