import os, time
from datetime import datetime
import uuid
import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

from .globals import progress_queue, stop_flag
from .app_utils import debugText

#
DUPLICATE_RECEIPT_ERR_TEXT = "an expense with the same receipt already exists."
#
SELENIUM_GOOGLE_CHROME_BINARY = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SELENIUM_GOOGLE_CHROME_DRIVER = "/usr/local/bin/chromedriver"
# 
ODOO_BASE_URL = "http://localhost:8069"
ODOO_LOGON_URL = f"{ODOO_BASE_URL}/web/login?redirect=/odoo/discuss"
ODOO_DB = "odoo"
#
ODOO_MODULES = {
    "Expense": f"{ODOO_BASE_URL}/odoo/expenses",
    "Invoice": f"{ODOO_BASE_URL}/web#action=invoice_module",
    "Purchase": f"{ODOO_BASE_URL}/web#action=purchase_module"
}

def simple_textfield_sevalue(driver, input_ref, input_value):
    # Use that id to locate the input
    input_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, input_ref))
    )
    input_element.clear()
    input_element.send_keys(input_value)

def date_mmddyyyy_setvalue(driver, input_ref, input_value):
    #
    date_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, input_ref))
    )
    date_input.click()
    # 
    date_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, input_ref))
    )
    date_input.send_keys(input_value)
    date_input.send_keys(Keys.TAB)  


def simple_dropdown_setvalue(driver, input_ref, input_value):
    #
    input_element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, input_ref))
    )
    input_element.clear()
    input_element.send_keys(input_value)
    time.sleep(0.5)
    input_element.send_keys(Keys.ENTER)

def complex_dropdown_setvalue(driver, input_ref, input_value):
    #
    input_element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, input_ref))
    )
    #
    input_element.click()
    input_element.send_keys(Keys.BACKSPACE)
    time.sleep(0.5)  # let Odoo update
    #
    input_element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, input_ref))
    )
    input_element.send_keys(input_value)
    time.sleep(0.5)
    input_element.send_keys(Keys.ENTER)


"""
def attach_receipt(driver, ABS_FILE_PATH_TO_UPLOAD):
   
    import subprocess
    
    # Step 1: Click the Attach Receipt button
    all_elements_with_attach = driver.find_elements(By.XPATH, "//*[contains(text(), 'Attach Receipt')]")
    print(f"Found {len(all_elements_with_attach)} elements with 'Attach Receipt' text")
    attach_element = all_elements_with_attach[0]

    if attach_element.tag_name == 'button':
        attach_button = attach_element
    else:
        attach_button = attach_element.find_element(By.XPATH, "./ancestor::button")

    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", attach_button)
    time.sleep(0.5)
    attach_button.click()
    print("Clicked Attach Receipt")
    
    # Wait for dialog
    time.sleep(2)
    
    # Step 2: Use AppleScript to handle the file dialog
    applescript = f'''
    tell application "System Events"
        tell process "Chrome"
            -- Wait for file dialog
            delay 1
            -- Press Cmd+Shift+G to open Go to folder
            keystroke "g" using {{command down, shift down}}
            delay 0.5
            -- Type the file path
            keystroke "{ABS_FILE_PATH_TO_UPLOAD}"
            delay 0.5
            -- Press Enter
            keystroke return
            delay 0.5
            -- Press Enter again to confirm
            keystroke return
        end tell
    end tell
    '''
    
    subprocess.run(['osascript', '-e', applescript])
    print(f"File selected: {os.path.basename(ABS_FILE_PATH_TO_UPLOAD)}")
    
    time.sleep(4)
    return True
"""

def attach_receipt(driver, ABS_FILE_PATH_TO_UPLOAD):
    
    # Step 1: Click the Attach Receipt button
    all_elements_with_attach = driver.find_elements(By.XPATH, "//*[contains(text(), 'Attach Receipt')]")
    print(f"Found {len(all_elements_with_attach)} elements with 'Attach Receipt' text")
    attach_element = all_elements_with_attach[0]

    if attach_element.tag_name == 'button':
        attach_button = attach_element
    else:
        attach_button = attach_element.find_element(By.XPATH, "./ancestor::button")

    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", attach_button)
    time.sleep(0.5)
    attach_button.click()
    print("Clicked Attach Receipt")
    
    time.sleep(1)
    
   
    # Press Escape to clear any stuck state
    #pyautogui.press('esc')
    #time.sleep(0.5)
    
    
    chrome_rect = driver.get_window_rect()
    dialog_x = chrome_rect['x'] + 300
    dialog_y = chrome_rect['y'] + 200
    pyautogui.click(dialog_x, dialog_y)
    time.sleep(0.5)
  

     

    
    # Now the AppleScript sequence
    pyautogui.hotkey('command', 'shift', 'g')
    time.sleep(0.5)


    screen_width, screen_height = pyautogui.size()
    pyautogui.click(screen_width // 2, screen_height // 2 - 60)
    time.sleep(0.3)

    
    pyautogui.write(ABS_FILE_PATH_TO_UPLOAD)
    time.sleep(0.5)
    
   
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('enter')
   

    print(f"File selected: {os.path.basename(ABS_FILE_PATH_TO_UPLOAD)}")
    time.sleep(0.5)
    return True



"""
def attach_receipt(driver, ABS_FILE_PATH_TO_UPLOAD):
    
    # Step 1: Click the Attach Receipt button
    all_elements_with_attach = driver.find_elements(By.XPATH, "//*[contains(text(), 'Attach Receipt')]")
    print(f"Found {len(all_elements_with_attach)} elements with 'Attach Receipt' text")
    attach_element = all_elements_with_attach[0]

    if attach_element.tag_name == 'button':
        attach_button = attach_element
    else:
        attach_button = attach_element.find_element(By.XPATH, "./ancestor::button")

    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", attach_button)
    time.sleep(0.5)
    attach_button.click()
    print("Clicked Attach Receipt")
    
    time.sleep(2)
    
    # Press Escape to clear any stuck state
    pyautogui.press('esc')
    time.sleep(0.5)
    
    # Click on the dialog to ensure focus (click center of screen)
    screen_width, screen_height = pyautogui.size()
    pyautogui.click(screen_width // 2, screen_height // 2 - 50)
    time.sleep(0.5)
    
    # Now the AppleScript sequence
    pyautogui.hotkey('command', 'shift', 'g')
    time.sleep(0.8)
    
    pyautogui.write(ABS_FILE_PATH_TO_UPLOAD)
    time.sleep(0.5)
    
    pyautogui.press('enter')
    time.sleep(0.5)
    
    pyautogui.press('enter')
    
    print(f"File selected: {os.path.basename(ABS_FILE_PATH_TO_UPLOAD)}")
    time.sleep(4)
    return True

"""



def checkReceiptDuplicated(driver):
    elements = driver.find_elements(By.NAME, "warning_duplicate_receipt_expense")
    if elements:
        warning_text = elements[0].text.strip().lower()
        if DUPLICATE_RECEIPT_ERR_TEXT in warning_text:
            print("Duplicate receipt detected...")
            return True
        else:
            print("Warning element found but text did not match.")
    else:
        print("NO Duplicate receipt detected...")
    
    return False
            





def json_to_odoo(odoo_user, odoo_pass, module, json, supporting_dropdown_json, upload_filepath): 
    global DUPLICATE_RECEIPT_ERR_TEXT
    global SELENIUM_GOOGLE_CHROME_BINARY, SELENIUM_GOOGLE_CHROME_DRIVER
    global ODOO_BASE_URL, ODOO_LOGON_URL, ODOO_DB
    debugText(f'json_to_odoo...odoo_user...{odoo_user}')
    debugText(f'json_to_odoo...odoo_pass...{odoo_pass}')
    debugText(f'json_to_odoo...module...{module}')
    debugText(f'json_to_odoo...json...{json}')
    debugText(f'json_to_odoo...supporting_dropdown_json...{supporting_dropdown_json}')
    debugText(f'json_to_odoo...upload_filepath...{upload_filepath}')

    options = Options()
    options.binary_location = SELENIUM_GOOGLE_CHROME_BINARY

    service = Service(SELENIUM_GOOGLE_CHROME_DRIVER)
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()

    debugText('debug...11')

    driver.get(ODOO_LOGON_URL)

    form_inputs = driver.find_elements(By.CSS_SELECTOR, 'form[action="/web/login"] input')
    debugText("Form inputs found:")
    for inp in form_inputs:
        debugText(f"  - {inp.get_attribute('name')} = {inp.get_attribute('value')} (type: {inp.get_attribute('type')})")

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.NAME, "login"))
    ).send_keys(odoo_user)
    debugText(f'debug...7...{driver.current_url}')
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.NAME, "password"))
    ).send_keys(odoo_pass)
    debugText(f'debug...8...{driver.current_url}')
    WebDriverWait(driver, 10).until(
        lambda d: d.find_element(By.XPATH, "//button[@type='submit']").is_enabled()
    )

    csrf_token = driver.find_element(By.NAME, 'csrf_token').get_attribute('value')
    debugText(f'debug...9...CSRF Token: {csrf_token}')
    db_name = driver.find_element(By.NAME, 'db').get_attribute('value') if driver.find_elements(By.NAME, 'db') else 'default'
    form = driver.find_element(By.CSS_SELECTOR, 'form[action="/web/login"]')
    debugText(f'debug...10...{driver.current_url}')
    form.submit()  # This is the key - it preserves all hidden fields

    debugText(f'debug...11...{driver.current_url}')

    WebDriverWait(driver, 10).until(
        lambda d: d.get_cookie('session_id') is not None
    )

    debugText(f'debug...12...{driver.current_url}')
  
    ############################################################
    next_url = ODOO_MODULES[module]
    debugText(f"next_url: {next_url}")
    driver.get(next_url)
    #
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'New')]"))
    ).click()
    #
    categories = supporting_dropdown_json["categories"]
    employee = supporting_dropdown_json["employee"]
    manager = supporting_dropdown_json["manager"]
    summary_json = json["summary"]
    details_json = json["details"]
    description = summary_json["name"]
    category = summary_json["category"]
    total_amount = summary_json["total_amount"]
    employee_name = employee["name"]
    manager_name = manager["name"]
    #
    expense_date = summary_json["date"]
    dt = datetime.strptime(expense_date, "%Y-%m-%d")
    expense_date_ui = dt.strftime("%m/%d/%Y")
    print("expense_date_ui==", expense_date_ui)
    #
    notes_text = "\n".join(
        f"{d['item']} - {d['price_unit']} x {d['quantity']}"
        for d in details_json
    )
    print("notes_text: ", notes_text)
    #
      
    
  
    #  
    simple_textfield_sevalue(driver, "name_0", description)
    #
    simple_dropdown_setvalue(driver, "product_id_0", category)
   

   
    #
    simple_textfield_sevalue(driver, "total_amount_currency_0", total_amount)
    #
    complex_dropdown_setvalue(driver, "employee_id_0", employee_name)

    # avoid default auto input taxes
    delete_icons = driver.find_elements(By.XPATH, "//div[@name='tax_ids']//i[contains(@class,'oi-close')]")
    for icon in delete_icons:
        driver.execute_script("arguments[0].click();", icon)

    #
    date_mmddyyyy_setvalue(driver, "date_0", expense_date_ui)
    
    # auto input on employee field changed
    # complex_dropdown_setvalue(driver, "manager_id_0", manager_name)
 
    notes_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "description_0"))
    )
    notes_input.clear()
    notes_input.send_keys(notes_text)

    
    # Wait until the hidden field is present in the DOM
    #automation_field = WebDriverWait(driver, 10).until(
    #    EC.presence_of_element_located((By.NAME, "automation_monitor"))
    #)
    #driver.execute_script("arguments[0].value = 'True';", automation_field)



    #
    time.sleep(1.0)
    attach_receipt(driver, upload_filepath)


    time.sleep(1)
 



    # capture screenshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())
    filename = f"odoo_screenshots/expense_{timestamp}_{unique_id}.png"
    ##driver.save_screenshot(filename)




    #
    """
    elements = driver.find_elements(By.NAME, "warning_duplicate_receipt_expense")
    if elements:
        warning_text = elements[0].text.strip().lower()
        if DUPLICATE_RECEIPT_ERR_TEXT in warning_text:
            print("Duplicate receipt detected...")
        else:
            print("Warning element found but text did not match.")
    else:
        print("NO Duplicate receipt detected...")
    """
    
    #print(checkReceiptDuplicated(driver))

  
    submit_btn = driver.find_element(By.XPATH, "//button[@name='action_submit']")
    submit_btn.click()

 



    print("after submit clicked...")

    # Wait for redirect back to list view
    WebDriverWait(driver, 10).until(EC.url_contains("/expenses"))

    print("after submit clicked...")

    driver.get("http://localhost:8069/odoo/expenses")

    # driver.quit()
    debugText('debug...20')
  
    
    return "YES"

 