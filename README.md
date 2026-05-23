
## Portfolio Project: automate receipt to ODOO expense records

> Introduction: 

- This project automates expense entry into Odoo ERP using OCR and LLM parsing.

> Key pipeline steps:

- upload receipt image  

- extract OCR texts from receipt image, 

- LLM extract expense information from OCR texts into OCR JSON,

- Auto-Create both Odoo Expense Record And Automation Record from OCR JSON,

- staff regularly review automation status of each auto-created odoo expense, and fix it when needed.


> Business Benefit

Manual expense entry is slow, error‑prone, and frustrating for employees.  
This project eliminates repetitive data entry by automatically reading receipts, parsing them into structured data, and inserting them directly into Odoo ERP.  

Result: faster reimbursements, fewer mistakes, and saved time.


> Three Iterations of Expense Automation:

> 1. Selenium UI Automation

- Approach: upload receipt image, and selenium will drive Odoo’s web interface, filling expense forms and uploading receipts automatically.

[![Click to Watch the youtube demo](./odoo_expense_doc/ocr_llm_selenium_odoo.jpg)](https://youtu.be/Xd6Jz8SfZVY)

- Pros:
  - High traceability: users can visually see what the automation is doing.
  - Easy to debug when something goes wrong (selectors, fields).
  - No need to modify Odoo’s backend.

- Cons:
  - Fragile: UI changes break selectors.
  - Slower and resource‑heavy (browser automation).
  - Requires user to wait and watch the automation run.


> 2. Odoo Expense Button Extension

- Approach: Inherit Odoo’s [ Attach Receipt ] button, add logic to call EasyOCR + LLM, then parse text into JSON that matches `hr.expense` fields.

[![Click to Watch the youtube demo](./odoo_expense_doc/inherit_odoo_attach_receipt_btn.jpg)](https://youtu.be/PlU3FX94n9M)

- Pros:
  - Seamless integration with existing Odoo workflow.
  - Users remain in control: they can adjust parsed data before saving.
  - Itegrated with Odoo’s UI, no external steps needed.

- Cons:
  - Requires custom Odoo module development.
  - Slightly higher maintenance when upgrading Odoo versions.
  - Still depends on user interaction (semi‑automated).


> 3. XML‑RPC Direct Insertion

- Approach: upload receipt image, and XML‑RPC API direct calls to insert expense record to odoo in the background.

[![Click to Watch the youtube demo](./odoo_expense_doc/ocr_llm_xmlrpc_odoo.jpg)](https://youtu.be/DMegoO_GpFw)

- Pros:
  - Fast, lightweight, no browser overhead.
  - Scales better for batch automation.

- Cons:
  - No visual traceability: users cannot see each record being filled.
  - Debugging is harder (errors only visible in logs).
  - Risk of silent mistakes if not reviewed.
  - users occasionally review automation records instead of watching every run.



---

> ## github repo

### - python flask: 

after n8n received incoming gmail of dedicated staff email account, 
it will pass to python flask for processing the pipeline all the way 
from email body to auto-creating sale order records in ODOO backend.

[https://github.com/cshwk2020/odoo_sales/tree/main](https://github.com/cshwk2020/odoo_sales/tree/main)

- config.py : all important key configuration such as LLM ApiKey, odoo admin and password, etc.

- ms.py : microservice of python flask to receive webhook from n8n Gmail on_recv trigger. 

- ai_parse_utils.py : LLM parsing email body text into cleaned JSON list, and related mock LLM API functions.

- rag_mmr_utils.py : RAG matching cleaned JSON list with odoo product listing embedding in chroma vector store, and related mock RAG API functions.

- rag_upsert.py : ONCE OFF initial convert odoo product listing into embedding in chroma vector store. 

- odoo_utils.py : odoo related functions such as create sale order, etc.

- vault_utils.py : security hvac utils to get sensitive information such as LLM ApiKey and password from vault instead of hardcode in source code.

- test/* : unit testing by pytest -s

- data/odoo_product_listing.xlsx : odoo product listing for convert into embeddings to chroma

### - ODOO module : automation_sale_monitoring 
    
beside microservice, there is a ODOO module for staff to monitoring the automated sale email processing status, 
and manual edit and fix the sale order form 
when LLM has difficulty handling ambigous sale requests from email body.

[https://github.com/cshwk2020/odoo/tree/19.0/addons/automation_sale_monitoring](https://github.com/cshwk2020/odoo/tree/19.0/addons/automation_sale_monitoring)

- model/sale_monitoring.py : keep track of status for auto-creating sale order record, and FK from sale_monitoring to sale_order record. 

- model/sale_order_inherit.py : add orm navigtion from sale_order to sale_monitoring record.

- views/sale_monitoring_views.xml : list view and form view for sale_monitoring records.


---



