import os, threading
import io
import json
from flask import Flask, request, Response, render_template
from werkzeug.datastructures import FileStorage
from .globals import progress_queue, stop_flag
from .app_utils import debugText, mask_password
from .ocr_utils import preocr_process_image, run_easyocr_file, mock_easyocr
from .ai_utils import run_ai_convert_text_to_json, mock_ai_convert_text_to_json
from .odoo_utils import json_to_odoo 
from .odoo_xmlrpc import fetch_employee, fetch_expense_categories, fetch_expense_dropdowns
from .odoo_utils import ODOO_BASE_URL, ODOO_DB
from .vault_utils import vault_get_odoo_user, vault_get_odoo_pass
from .config import MODE_REAL

app = Flask(__name__, template_folder='Template')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

 
def run_job(filepath, module, odoo_user, odoo_pass):
 
    gray_image_np, texts = run_easyocr_file(filepath)
    
    debugText("run_easyocr: texts == ")
    debugText(texts)

    if stop_flag.is_set(): return

    #
    expense_dropdowns = fetch_expense_dropdowns(ODOO_BASE_URL, ODOO_DB, odoo_user, odoo_pass)
    print("expense_dropdowns: ", expense_dropdowns)
    
    print("Expense Categories:")
    if expense_dropdowns["categories"]:
        categories = expense_dropdowns["categories"]
        for category in categories:
            print(f"ID: {category['id']}, Name: {category['name']}")

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
    
    
    debugText("content_json: ")
    debugText(content_json)
    if stop_flag.is_set(): return


    # odoo
    print('odoo_user: ', odoo_user)
    print('odoo_pass: ', odoo_pass)
    print('module: ', module)
    print('content_json: ', content_json)
    print('expense_dropdowns: ', expense_dropdowns)
    print('filepath: ', filepath)
    odoo_result = json_to_odoo(odoo_user, odoo_pass, module, content_json, expense_dropdowns, filepath)
   


@app.route('/')
def index():
    # return render_template('menu_upload.html')
    return render_template(
        "menu_upload.html",
        odooUser=vault_get_odoo_user(),
        odooPass=vault_get_odoo_pass()
    )


@app.route("/automation", methods=['POST'])
def automation_upload():
    module = request.form.get("module")
    odoo_user = request.form["odooUser"]
    odoo_pass = request.form["odooPass"]

    file = request.files['receipt']
    
    #
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    abs_filepath = os.path.abspath(filepath)
    debugText(f'abs_filepath: {abs_filepath}')

    debugText(f"module: {module}")
    debugText(f"odoo_user: {odoo_user}")
    debugText(f"odoo_pass: {mask_password(odoo_pass)}")
    debugText(f"filepath: {filepath}")

    
    stop_flag.clear()
    threading.Thread(target=run_job, args=(abs_filepath, module, odoo_user, odoo_pass)).start()
    
    return "Upload received"


@app.route("/automation/reset", methods=["POST"])
def automation_reset():
    global stop_flag
    global progress_queue

    # stop bg run_job
    stop_flag.set()
    # Empty the queue
    while not progress_queue.empty():
        try:
            progress_queue.get_nowait()
        except queue.Empty:
            break
    return "Reset done"


@app.route("/automation/stream", methods=["GET"])
def automation_stream():
    global stop_flag
    global progress_queue

    def generate():
        while True:
            if stop_flag.is_set():
                # yield f"data: stop_flag::is_set...automation_stream terminated\n\n"
                break
            msg = progress_queue.get()
            
            # Ensure msg is a string
            if isinstance(msg, dict):
                msg_str = json.dumps(msg, ensure_ascii=False)
            else:
                msg_str = str(msg)
                if "finished" in msg_str.lower():
                    break

            yield f"data: {msg}\n\n"

    return Response(generate(), mimetype="text/event-stream")




if __name__ == "__main__":
    app.run(debug=True)
