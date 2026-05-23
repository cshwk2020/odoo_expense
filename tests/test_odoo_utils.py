import pytest
from odoo_expense.vault_utils import vault_get_odoo_user, vault_get_odoo_pass
from odoo_expense.odoo_utils import ODOO_BASE_URL, ODOO_DB
from odoo_expense.odoo_xmlrpc import fetch_expense_dropdowns
from odoo_expense.config import MOCK_FILE_LLM_JSON

from odoo_expense.odoo_utils import json_to_odoo

TEST_FILE_PATH = "/Users/cshwk1995/Desktop/img/receipts/IMG_2150.jpg"

@pytest.mark.skip(reason="temporarily disabled")
def test_json_to_odoo():

    module = "Expense"
    odoo_user = vault_get_odoo_user()
    odoo_pass = vault_get_odoo_pass()
    expense_dropdowns = fetch_expense_dropdowns(ODOO_BASE_URL, ODOO_DB, odoo_user, odoo_pass)
    content_json = MOCK_FILE_LLM_JSON
    filepath = TEST_FILE_PATH

    odoo_result = json_to_odoo(odoo_user, odoo_pass, module, content_json, expense_dropdowns, filepath)
   