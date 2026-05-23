import pytest
from test_odoo_xmlrpc import test_fetch_expense_dropdowns
from odoo_expense.ai_utils import run_ai_convert_text_to_json, real_ai_convert_text_to_json
from odoo_expense.config import MOCK_FILE_OCR_TEXTS

@pytest.mark.skip(reason="temporarily disabled")
def test_real_ai_convert_text_to_json ():

    expense_dropdowns = test_fetch_expense_dropdowns()
    ocr_text = "\n".join(MOCK_FILE_OCR_TEXTS)
    result = real_ai_convert_text_to_json(ocr_text, expense_dropdowns)

    print("result: ", result)

