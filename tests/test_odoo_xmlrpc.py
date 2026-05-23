import pytest
from odoo_expense.vault_utils import vault_get_odoo_user, vault_get_odoo_pass
from odoo_expense.odoo_utils import ODOO_BASE_URL, ODOO_DB
from odoo_expense.odoo_xmlrpc import fetch_expense_dropdowns


# @pytest.mark.skip(reason="temporarily disabled")
def test_fetch_expense_dropdowns():

    odoo_user = vault_get_odoo_user()
    odoo_pass = vault_get_odoo_pass()
    print("odoo_user: ", odoo_user)
    print("odoo_pass: ", odoo_pass)
    expense_dropdowns = fetch_expense_dropdowns(ODOO_BASE_URL, ODOO_DB, odoo_user, odoo_pass)
    print("expense_dropdowns: ", expense_dropdowns)
    return expense_dropdowns








