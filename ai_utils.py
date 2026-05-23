import requests, json
from .globals import progress_queue, stop_flag
from .app_utils import debugText
from .vault_utils import vault_get_deepseek_key
from .config import MODE_REAL, MOCK_FILE_LLM_JSON


# deepseek
API_MODEL_VER = "deepseek-v4-flash"
API_KEY = vault_get_deepseek_key()
url = "https://api.deepseek.com/chat/completions"


def run_ai_convert_text_to_json(ocr_text, expense_dropdowns):

    if MODE_REAL:
        return real_ai_convert_text_to_json(ocr_text, expense_dropdowns)
    else:
        return mock_ai_convert_text_to_json(ocr_text, expense_dropdowns)


def mock_ai_convert_text_to_json(ocr_text, expense_dropdowns):

    print(f"mock_ai_convert_text_to_json...{ocr_text}")  
    print(f"mock_ai_convert_text_to_json...{expense_dropdowns}")  

    return MOCK_FILE_LLM_JSON


def real_ai_convert_text_to_json(ocr_text, expense_dropdowns):
    
    if expense_dropdowns["categories"]:
        categories = expense_dropdowns["categories"]
    else:
        categories = [] 

    print("\nEmployee:")
    if expense_dropdowns["employee"]:
        employee = expense_dropdowns["employee"]
        print(f"ID: {employee['id']}, Name: {employee['name']}")
    else:
        employee = {}
        print("No employee found.")

    print("\nManager:")
    if expense_dropdowns["manager"]:
        manager = expense_dropdowns["manager"]
        print(f"ID: {manager['id']}, Name: {manager['name']}")
    else:
        manager = {}
        print("No manager found.")


    # deepseek
    employee_name = employee['name']
    manager_name = manager['name']
    categories_str = ", ".join([c["code"] for c in categories])


    payload = {
        "model": API_MODEL_VER,
        "messages": [
            {
                "role": "system",
                "content": f"""
                You are a parser that converts messy OCR receipt text into JSON for Odoo ERP.
                Rules:
                - Output one JSON object with keys: summary, details.
                - summary must include these exact keys: total_amount, employee, manager, paid_by, name, date, category, confidence_level
                - Do not use synonyms like "total" or "amount", for example, always use "total_amount".
                - category must be inferred overall all items in the receipt (choose ONE from this list: {categories_str}).
                  Always try to classify most appropriate overall receipt category,
                  If a single category appear matching all items in same receipt, use that single category cover all items.
                  If multiple categories appear for vaious items in the same receipt, fallback to the generic EXP_GEN product.
                - details must list each line item with price_unit, quantity, and item text.
                - paid_by: either own_account OR company_account". 
                        Look for keywords like “Cash”, “Visa”, “MasterCard”, “Change”, etc. -> assume employee paid.
                        Look for “Company Card”, “Corporate Account”, “Paid by Company” -> assume company account.
                        If your OCR pipeline can’t detect payment mode reliably, you can default to "own_account" (since most receipts are employee‑paid) and allow manual override.
                - confidence_level: 0.00 - 1.00, based on applying all rules mentioned above, to ambiguity level of OCR output provided. 
                - status must be one of: "incomplete", "complete", "error".
                        "complete" if all required summary fields are present (total_amount, employee, paid_by, name, date, category) AND details list has at least one valid item.
                        "incomplete" if some required fields are missing or ambiguous (e.g. missing date, missing category, empty details).
                        "error" if the OCR text cannot be parsed into valid JSON at all, or if the receipt is unreadable.
                - if status is NOT complete, need explain reasons in remark field.


                - Return only valid JSON { ... } not list  [ ... ].
                """
            },
            {
                "role": "user",
                "content": f"""Here is the OCR output:
    {ocr_text}\n\nEmployee Name: {employee_name}

    Return JSON as a list of expense records, each matching Odoo hr.expense fields:

    expense_json example format:
    {{
    "summary": {{
        "total_amount": 84,
        "employee":  {employee_name},
        "manager":  {manager_name},
        "paid_by": "own_account | company_account",
        "name": "Receipt from Wellcome",
        "date": "2026-04-25",
        "category": "XXXXXX",
        "confidence_level": 0.00-1.00,
        "status": incomplete | complete | error,
        "remark": "OK",
    }},
    "details": [
        {{"price_unit": 57.5, "quantity": 1, "item": "四洲蘿荀牛瞞麵五包裝 - 40.0\n火船牌三合一白咖啡10PC - 17.5"}},
        {{"price_unit": 26.5, "quantity": 1, "item": "other item might or might not be food"}}
    ]
    }}

            """
  
            }
          
        ],
        "response_format": { "type": "json_object" },
        "reasoning_effort": "low",
        "stream": False
    }


    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    """
    response = requests.post(url, headers=headers, json=payload)

    debugText('response: ')
    debugText(json.dumps(response.json(), indent=2, ensure_ascii=False))

    raw = response.json()
    content_str = raw["choices"][0]["message"]["content"]
    try:
        content_json = json.loads(content_str)
        return content_json
    except json.JSONDecodeError:
        debugText("DeepSeek returned invalid JSON string in 'content':")
        debugText(content_str)
        raise
    """

    print("payload: ")
    print(payload)

    response = requests.post(url, headers=headers, json=payload)

    raw = response.json()
    content_str = raw["choices"][0]["message"]["content"]

    try:
        content_json = json.loads(content_str)   # Python dict

        # Convert back to proper JSON string with double quotes
        json_str = json.dumps(content_json, ensure_ascii=False, indent=2)
        print("Parsed JSON:")
        print(json_str)
        #
        return content_json
        
    except json.JSONDecodeError:
        print("DeepSeek returned invalid JSON string in 'content':")
        print(content_str)
        raise



