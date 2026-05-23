import xmlrpc.client
import base64
from datetime import datetime

from .config import vault_get_odoo_user, vault_get_odoo_pass
from .app_utils import debugText
from .odoo_utils import ODOO_BASE_URL, ODOO_DB, json_to_odoo


def json_to_odoo_by_xmlrpc(odoo_user, odoo_pass, module, json, supporting_dropdown_json, upload_filepath):
    """
    Insert expense into Odoo using XML-RPC instead of Selenium.
    """

    # 基本連線
    common = xmlrpc.client.ServerProxy(f"{ODOO_BASE_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, odoo_user, odoo_pass, {})
    models = xmlrpc.client.ServerProxy(f"{ODOO_BASE_URL}/xmlrpc/2/object")

    # 準備 JSON
    summary_json = json["summary"]
    details_json = json["details"]

    description = summary_json["name"]
    category_id = supporting_dropdown_json["categories"][0]["id"]  # 取第一個 category
    employee_id = supporting_dropdown_json["employee"]["id"]
    manager_id = supporting_dropdown_json["manager"]["id"]
    total_amount = summary_json["total_amount"]
    expense_date = summary_json["date"]

    dt = datetime.strptime(expense_date, "%Y-%m-%d")
    expense_date_ui = dt.strftime("%Y-%m-%d")  # XML-RPC 用 ISO 格式

    notes_text = "\n".join(
        f"{d['item']} - {d['price_unit']} x {d['quantity']}"
        for d in details_json
    )

    # 建立 expense record
    expense_id = models.execute_kw(
        ODOO_DB, uid, odoo_pass,
        'hr.expense', 'create',
        [{
            'name': description,
            'product_id': category_id,
            'total_amount': total_amount,
            'employee_id': employee_id,
            'date': expense_date_ui,
            'description': notes_text,
        }]
    )

    # 可選：attach receipt file
    with open(upload_filepath, "rb") as f:
        file_data = f.read()

    models.execute_kw(
        ODOO_DB, uid, odoo_pass,
        'ir.attachment', 'create',
        [{
            'name': f"Receipt_{expense_id}",
            'res_model': 'hr.expense',
            'res_id': expense_id,
            'type': 'binary',
            #'datas': xmlrpc.client.Binary(file_data),
            'datas': base64.b64encode(file_data).decode(),
        }]
    )

    return expense_id




def get_models(ODOO_BASE_URL, ODOO_DB, ODOO_USER, ODOO_PASS):
    print("get_models...1", ODOO_BASE_URL, ODOO_DB, ODOO_USER, ODOO_PASS)
    common = xmlrpc.client.ServerProxy(f"{ODOO_BASE_URL}/xmlrpc/2/common")
    print("get_models...2")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
    print("get_models...3")
    models = xmlrpc.client.ServerProxy(f"{ODOO_BASE_URL}/xmlrpc/2/object")
    print("get_models...4", uid, models)
    return uid, models


def mock_expense_dropdowns():
    return {
        "categories": [
            {"id": 5, "name": "Communication", "code": "COMM"}, 
            {"id": 6, "name": "Expenses", "code": "EXP_GEN"}, 
            {"id": 1, "name": "Meals", "code": "FOOD"}, 
            {"id": 4, "name": "Gifts", "code": "GIFT"}, 
            {"id": 3, "name": "Mileage", "code": "MIL"}, 
            {"id": 2, "name": "Travel & Accommodation", "code": "TRANS & ACC"}], 
        "employee": {"id": 2, "name": "Tester1", "parent_id": (1, "Administrator")}, 
        "manager": {"id": 1, "name": "Administrator"}, 
        "payment_modes": [
            {"value": "own_account", "label": "Employee (to reimburse)"}, 
            {"value": "company_account", "label": "Company"}
        ]
    }


def fetch_expense_dropdowns(ODOO_BASE_URL, ODOO_DB, ODOO_USER, ODOO_PASS):

    uid, models = get_models(ODOO_BASE_URL, ODOO_DB, ODOO_USER, ODOO_PASS)

    categories = models.execute_kw(
        ODOO_DB, uid, ODOO_PASS,
        "product.product", "search_read",
        [[["can_be_expensed", "=", True]]],
        {"fields": ['id', 'name', 'default_code']}
    )

 

    # Current employee linked to this user
    employees = models.execute_kw(
        ODOO_DB, uid, ODOO_PASS,
        "hr.employee", "search_read",
        [[["user_id", "=", uid]]],
        {"fields": ["id", "name", "parent_id"]}
    )

    employee = employees[0] if employees else {}
    manager = {}

    # If employee has a manager (parent_id)
    if employee and employee.get("parent_id"):
        manager_id = employee["parent_id"][0]  # first element is ID
        manager = models.execute_kw(
            ODOO_DB, uid, ODOO_PASS,
            "hr.employee", "read",
            [manager_id],
            {"fields": ["id", "name"]}
        )[0]

    return {
        "categories": categories,
        "employee": employee,
        "manager": manager,
    }



 

def fetch_employee(ODOO_BASE_URL, ODOO_DB, ODOO_USER, ODOO_PASS):
    uid, models = get_models(ODOO_BASE_URL, ODOO_DB, ODOO_USER, ODOO_PASS)
    employees = models.execute_kw(
        ODOO_DB, uid, ODOO_PASS,
        "hr.employee", "search_read",
        [[["user_id", "=", uid]]],
        {"fields": ["id", "name"]}
    )
    print("fetch_employee: ")
    print(employees)
    return employees[0] if employees else {}

def fetch_expense_categories(ODOO_BASE_URL, ODOO_DB, ODOO_USER, ODOO_PASS):
    uid, models = get_models(ODOO_BASE_URL, ODOO_DB, ODOO_USER, ODOO_PASS)
    categories = models.execute_kw(
        ODOO_DB, uid, ODOO_PASS,
        "product.product", "search_read",
        [[]],
        {"fields": ["id", "code"]}
    )
    return categories


def fetch_expense_fields_get(ODOO_BASE_URL, ODOO_DB, ODOO_USER, ODOO_PASS):
    uid, models = get_models(ODOO_BASE_URL, ODOO_DB, ODOO_USER, ODOO_PASS)
    fields = models.execute_kw(
        ODOO_DB, uid, ODOO_PASS,
        "hr.expense", "fields_get",
        [],   # empty list = all fields
        {"attributes": ["string", "type", "relation", "selection"]}
    )
    #print("fetch_expense_fields:")
    #for field_name, meta in fields.items():
    #    print(field_name, "=>", meta)
    return fields
