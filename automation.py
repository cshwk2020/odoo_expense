import os, threading, queue, json, base64, hashlib
from flask import Flask, request, Response, render_template
import easyocr

from .globals import stop_flag, progress_queue
from .config import vault_get_odoo_user, vault_get_odoo_pass
from .app_utils import debugText
from .ocr_utils import run_easyocr_file
from .ai_utils import run_ai_convert_text_to_json
from .odoo_xmlrpc import fetch_expense_dropdowns, get_models
from .odoo_utils import ODOO_BASE_URL, ODOO_DB

app = Flask(__name__, template_folder='Template')
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def run_job(filepath, module, odoo_user, odoo_pass):
    try:
        progress_queue.put(f"filepath: {filepath}")

        # Step 1: OCR
        gray_image, texts = run_easyocr_file(filepath)
        ocr_text = "\n".join(texts)
        progress_queue.put(f"OCR texts: {texts}")

        if stop_flag.is_set():
            progress_queue.put("stopped")
            return

        # Step 2: Dropdowns
        expense_dropdowns = fetch_expense_dropdowns(ODOO_BASE_URL, ODOO_DB, odoo_user, odoo_pass)
        progress_queue.put(f"expense_dropdowns: {expense_dropdowns}")

        if stop_flag.is_set():
            progress_queue.put("stopped")
            return

        # Step 3: AI convert OCR → JSON
        content_json = run_ai_convert_text_to_json(ocr_text, expense_dropdowns)
        progress_queue.put(f"content_json: {content_json}")

        if stop_flag.is_set():
            progress_queue.put("stopped")
            return

        # Step 4: Prepare expense + monitor values
        with open(filepath, "rb") as f:
            image_bytes = f.read()
        receipt_image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # 灰階圖轉 base64
        try:
            import cv2
            _, buf = cv2.imencode(".png", gray_image)
            gray_image_b64 = base64.b64encode(buf).decode("utf-8")
        except Exception:
            gray_image_b64 = None

        summary = content_json.get("summary", {})
        expense_vals = {
            "automation_monitor": True,
            "name": summary.get("name"),
            "total_amount": summary.get("total_amount"),
            "date": summary.get("date"),
            "payment_mode": summary.get("paid_by"),
            "description": summary.get("remark"),
        }
        expense_vals = {k: v for k, v in expense_vals.items() if v is not None}

        # normalize module value to lowercase
        module_value = str(module).lower() if module else "expense"

        monitor_vals = {
            "module": module_value,
            "raw_image": receipt_image_b64,
            "preocr_image": gray_image_b64,
            "ocr_text": ocr_text,
            "ocr_json": content_json,
            "status": summary.get("status"),
            "confidence": summary.get("confidence_level"),
            "message": summary.get("remark"),
            "image_hash": hashlib.sha256(image_bytes).hexdigest(),
        }
        monitor_vals = {k: v for k, v in monitor_vals.items() if v is not None}

        # Step 5: Call Odoo XML-RPC custom method
        uid, models = get_models(ODOO_BASE_URL, ODOO_DB, odoo_user, odoo_pass)
        expense_id, monitor_id = models.execute_kw(
            ODOO_DB, uid, odoo_pass,
            "hr.expense", "create_with_monitor",
            [expense_vals, monitor_vals]
        )

        progress_queue.put(f"Expense created with ID {expense_id}, Monitor ID {monitor_id}")
        progress_queue.put("Automation finished")

    except Exception as e:
        progress_queue.put(f"ERROR: {str(e)}")


@app.route('/')
def index():
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
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    abs_filepath = os.path.abspath(filepath)

    debugText(f'abs_filepath: {abs_filepath}')
    debugText(f"module: {module}")
    debugText(f"odoo_user: {odoo_user}")
    debugText(f"odoo_pass: {odoo_pass}")
    debugText(f"filepath: {filepath}")

    stop_flag.clear()
    threading.Thread(target=run_job, args=(abs_filepath, module, odoo_user, odoo_pass)).start()

    return "Upload received"


@app.route("/automation/stream")
def automation_stream():
    def generate():
        while True:
            if stop_flag.is_set():
                break
            msg = progress_queue.get()
            msg_str = json.dumps(msg, ensure_ascii=False) if isinstance(msg, dict) else str(msg)
            yield f"data: {msg_str}\n\n"
            if "finished" in msg_str.lower():
                break
    return Response(generate(), mimetype="text/event-stream")


@app.route("/automation/reset", methods=["POST"])
def automation_reset():
    stop_flag.set()
    while not progress_queue.empty():
        try:
            progress_queue.get_nowait()
        except queue.Empty:
            break
    return "Reset done"


if __name__ == "__main__":
    app.run(debug=True)
