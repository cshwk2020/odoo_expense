import sys, os, threading
import io
import json
import cv2
import base64
import hashlib
import xmlrpc.client
import numpy as np
from flask import Flask, request, jsonify, Response, render_template
from flask_cors import CORS
from werkzeug.datastructures import FileStorage

from .globals import progress_queue, stop_flag
from .logging_utils import logger 
from .app_utils import debugText, mask_password
from .ocr_utils import preocr_process_image, np_array_to_base64_image, convert_to_gray_image, run_easyocr_bytes, mock_easyocr
from .ai_utils import run_ai_convert_text_to_json, mock_ai_convert_text_to_json
from .odoo_utils import json_to_odoo 
from .odoo_xmlrpc import get_models, fetch_employee, fetch_expense_categories, fetch_expense_dropdowns
from .odoo_utils import ODOO_BASE_URL, ODOO_DB
from .vault_utils import vault_get_odoo_user, vault_get_odoo_pass

#
app = Flask(__name__, template_folder='Template')
CORS(app)  # Enable CORS
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


#
active_jobs = {}


@app.route("/image2json", methods=['POST'])
def image2json():

    try:
        data = request.get_json()

        if not data or 'receipt_image' not in data:
            return jsonify({
                'status': False,
                'msg': 'No receipt image provided',
                'data': {}
                }), 400
        
        expense_dropdowns = data.get("expense_dropdowns")
        module = data.get("module")
        expense_id = data.get('expense_id')

        #
        image_b64 = data.get('receipt_image')
        if image_b64.startswith('data:image'):
            image_b64 = image_b64.split(',')[1]
        image_bytes = base64.b64decode(image_b64)

        logger.info(f"Processing receipt for expense_id: {expense_id}")
        
        # Store job as started
        if expense_id:
            active_jobs[expense_id] = {'status': 'processing', 'cancelled': False}
        
         
        # Process the receipt image
        # Option 1: Use OCR (Tesseract) to extract text
        # Option 2: Use a receipt parsing API
        # Option 3: Mock data for testing
        
        # For demo, extract data from image (implement your logic here)
        expense_dropdowns, gray_image, ocr_text, content_json = extract_receipt_data(image_bytes, expense_dropdowns)
        
        # Check if cancelled
        if expense_id and active_jobs.get(expense_id, {}).get('cancelled'):
            logger.info(f"Job {expense_id} was cancelled")
            return jsonify({
                'msg': 'cancelled',
                'status': False,
                'data':''
                })
        
 
        # Return extracted data
        response_data = {
            'status': True,
            'msg': 'success',
            'data': content_json
            
        }
        
        logger.info(f"Extracted data: {response_data}")
        
        # Update job status
        if expense_id:
            active_jobs[expense_id] = {'status': 'completed', 'cancelled': False}
        
        return jsonify(response_data), 200
        
    except Exception as e:
        error_msg = str(e) 
        logger.error(f"Error processing receipt: {error_msg}")
        response_data = {
                'status': False,
                'msg': error_msg,
                'data': {}
            }
        return jsonify(
            response_data
        ), 500

 

# 
def extract_receipt_data(image_bytes, expense_dropdowns):
 
    #
    #gray_image, texts = mock_easyocr(image_bytes)   
    gray_image, texts = run_easyocr_bytes(image_bytes)   
     
    print("extract_receipt_data: texts == ")
    print(texts)
   
    #
    print("Expense Categories:")
    if expense_dropdowns["categories"]:
        categories = expense_dropdowns["categories"]
        for category in categories:
            print(f"ID: {category['id']}, Name: {category['code']}")

    print("\nEmployee:")
    if expense_dropdowns["employee"]:
        employee = expense_dropdowns["employee"]
        print(f"ID: {employee['id']}, Name: {employee['name']}")
    else:
        print("No employee found.")

    print("\nManager:")
    if expense_dropdowns["manager"]:
        manager = expense_dropdowns["manager"]
        print(f"ID: {manager['id']}, Name: {manager['name']}")
    else:
        print("No manager found.")


    # deepseek
    employee_id = employee['id']
    categories_str = ", ".join([c["name"] for c in categories])
    ocr_text = "\n".join(texts)

    #content_json = mock_ai_convert_text_to_json(ocr_text, expense_dropdowns)
    content_json = run_ai_convert_text_to_json(ocr_text, expense_dropdowns)
    print('content_json:', content_json)

    return expense_dropdowns, gray_image, ocr_text, content_json


@app.route('/')
def index():
    # return render_template('menu_upload.html')
    return render_template(
        "menu_upload.html",
        odooUser=vault_get_odoo_user(),
        odooPass=vault_get_odoo_pass()
    )


@app.route("/automation", methods=['POST'])
def image2jodoo():
 
    try:
        module = request.form.get("module")
        odoo_user = request.form["odooUser"]
        odoo_pass = request.form["odooPass"]

        file = request.files['receipt']
        if file:
            # Read file bytes
            image_bytes = file.read()
            # Encode to base64 string
            receipt_image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        else:
            receipt_image_b64 = None
        
         
        ###################

        #
        expense_dropdowns = fetch_expense_dropdowns(ODOO_BASE_URL, ODOO_DB, odoo_user, odoo_pass)
        print("Expense Categories:")
        if expense_dropdowns["categories"]:
            categories = expense_dropdowns["categories"]
            for category in categories:
                print(f"ID: {category['id']}, Name: {category['code']}")

        print("\nEmployee:")
        if expense_dropdowns["employee"]:
            employee = expense_dropdowns["employee"]
            print(f"ID: {employee['id']}, Name: {employee['name']}")
        else:
            print("No employee found.")

        print("\nManager:")
        if expense_dropdowns["manager"]:
            manager = expense_dropdowns["manager"]
            print(f"ID: {manager['id']}, Name: {manager['name']}")
        else:
            print("No manager found.")

        #
        expense_dropdowns, gray_image_bytes, ocr_text, content_json = extract_receipt_data(image_bytes, expense_dropdowns)
        #
        gray_image_b64 = np_array_to_base64_image(gray_image_bytes)
        #
        print("-----------------------------")
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        print('filepath: ')
        print(filepath)
        dirpath, filename = os.path.split(filepath)
        preocr_filename = "preocr_" + filename
        preocr_filepath = os.path.join(dirpath, preocr_filename)
        print('preocr_filepath: ')
        print(preocr_filepath)
        cv2.imwrite(preocr_filepath, gray_image_bytes)


        print('gray_image_b64: ')
        print(len(gray_image_b64))

 
        #
        _summary_json = content_json.get("summary", {})
        _details_json = content_json.get("details", {})
        #
        _name = _summary_json.get("name", "Expense")
        _total_amount = _summary_json.get("total_amount", 0.0)
        _employee = _summary_json.get("employee")
        _category = _summary_json.get("category")
        _message = _summary_json.get("message")
        _remark = _summary_json.get("remark") 
        _confidence_level = _summary_json.get("confidence_level", 0.0)
        _status = _summary_json.get("status")
        _date = _summary_json.get("date")
        _payment_mode = _summary_json.get("paid_by", "own_account")
        _notes = "\n".join(
                f"{d['item']} - {d['price_unit']} x {d['quantity']}"
                for d in _details_json
        )


    

        # missing raw_image
        expense_vals = {
            "automation_monitor": True,
            "name": _name,
            "total_amount": _total_amount,
            "date": _date,
            "payment_mode": _payment_mode,
            "description": _notes,
        }
        expense_vals = {k: v for k, v in expense_vals.items() if v is not None}

        #
        monitor_vals = {
            "module": "expense",
            "raw_image": receipt_image_b64,
            "preocr_image": gray_image_b64,
            "ocr_text": ocr_text,
            "ocr_json": content_json,
            "status": _status,
            "confidence": _confidence_level,
            "message": _message,
            "remark": _remark,
            "image_hash": hashlib.sha256(image_bytes).hexdigest(),
        }
        monitor_vals = {k: v for k, v in monitor_vals.items() if v is not None}
         
        # Call Odoo XML-RPC custom method
        uid, models = get_models(ODOO_BASE_URL, ODOO_DB, odoo_user, odoo_pass)
        (expense_id, monitor_id) = models.execute_kw(
            ODOO_DB, uid, odoo_pass,
            "hr.expense", "create_with_monitor",
            [expense_vals, monitor_vals]
        )

        return jsonify({
            'status': True,
            'msg': 'Expense and monitoring created',
            'data': {
                'expense_id': expense_id,
                'monitor_id': monitor_id,
                'content_json': content_json
            }
        })



    except Exception as e:
        error_msg = str(e) 
        logger.error(f"Error processing receipt: {error_msg}")
        response_data = {
                'status': False,
                'msg': error_msg,
                'data': {}
            }
        return jsonify(
            response_data
        ), 500








if __name__ == "__main__":
    app.run(debug=True)
