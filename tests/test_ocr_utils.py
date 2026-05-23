import os
import io
import cv2
import pytest
from odoo_expense.ocr_utils import preocr_process_image, filepath_to_fileobj, fileobj_to_filepath
from odoo_expense.ocr_utils import convert_to_gray_image, ndarray_to_filepath, run_easyocr_file 
from odoo_expense.app import UPLOAD_FOLDER
from odoo_expense.config import MODE_REAL, MOCK_FILE_PATH, MOCK_FILE_OCR_TEXTS


TEST_FILE_PATH = "/Users/cshwk1995/Desktop/img/receipts/IMG_2150.jpg"


@pytest.mark.skip(reason="temporarily disabled")
def test_run_easyocr_file():
    
    file_path = TEST_FILE_PATH
    filename = os.path.basename(file_path)
    new_file_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, filename))

    gray_image_np, texts = run_easyocr_file(file_path)
    print('texts: ', texts)
    ndarray_to_filepath(new_file_path, gray_image_np)


@pytest.mark.skip(reason="temporarily disabled")
def test_convert_to_gray_image():

    file_path = TEST_FILE_PATH
    file_obj = filepath_to_fileobj(file_path)
    filename = file_obj.filename

    gray_image_obj = convert_to_gray_image(file_obj)
    grayimage_fullpath = os.path.abspath(os.path.join(UPLOAD_FOLDER, 'gray_' + filename))
    cv2.imwrite(grayimage_fullpath, gray_image_obj)


@pytest.mark.skip(reason="temporarily disabled")
def test_fileobj_to_filepath():

    file_path = TEST_FILE_PATH
    file_obj = filepath_to_fileobj(file_path)
     
    new_file_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, "test_copy.jpg"))
    fileobj_to_filepath(new_file_path, file_obj)
    print('test_fileobj_to_filepath: ', file_obj)


@pytest.mark.skip(reason="temporarily disabled")
def test_filepath_to_fileobj():

    file_path = TEST_FILE_PATH
    file_obj = filepath_to_fileobj(file_path)

    print(file_obj.filename)  
    print(file_obj.content_type)  


@pytest.mark.skip(reason="temporarily disabled")
def test_preocr_process_image():

    filepath = TEST_FILE_PATH
    result = preocr_process_image(filepath)
    print("result: ", result)
