import os
import io
import cv2
import numpy as np
from PIL import Image, ImageOps
import base64
import threading
import easyocr
from werkzeug.datastructures import FileStorage

from .globals import progress_queue, stop_flag
from .app_utils import debugText  # helper for logging
from .logging_utils import logger 
from .config import MODE_REAL, MOCK_FILE_PATH, MOCK_FILE_OCR_TEXTS

import logging

logger = logging.getLogger(__name__)




def real_easyocr_bytes(image_bytes):

    reader = easyocr.Reader(['ch_tra', 'en'])
    gray_image = convert_to_gray_image(image_bytes)
    results = reader.readtext(gray_image)

    texts = [text for (_, text, _) in results]
    for (_, text, prob) in results:
        print(f"OCR detected: {text} (confidence {prob:.2f})")
        if stop_flag.is_set():
            return
        
    return gray_image, texts


def mock_easyocr_bytes(image_bytes):
    
    mock_file_obj = filepath_to_fileobj(MOCK_FILE_PATH)
    gray_image = convert_to_gray_image(mock_file_obj)
    return gray_image, MOCK_FILE_OCR_TEXTS


def run_easyocr_bytes(image_bytes):

    if MODE_REAL:
        return real_easyocr_bytes(image_bytes)
    else:
        return mock_easyocr_bytes(image_bytes)


def run_easyocr_file(filepath):
 
    with open(filepath, "rb") as f:
        data = f.read()

    return run_easyocr_bytes(io.BytesIO(data))
    


def convert_to_gray_image(file_obj):
    """
    Convert a FileStorage or BytesIO object into a preprocessed grayscale numpy array.
    """
    # FileStorage 情況
    if hasattr(file_obj, "stream"):
        data = file_obj.read()
        file_obj.stream.seek(0)
    else:
        # BytesIO 或其他 file-like object
        data = file_obj.read()
        file_obj.seek(0)

    # 用 PIL 開
    image = Image.open(io.BytesIO(data))
    image = ImageOps.exif_transpose(image)

    # 轉 numpy array
    image_np = np.array(image)

    # 灰階轉換
    if len(image_np.shape) == 3 and image_np.shape[2] == 3:
        gray_image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    elif len(image_np.shape) == 3 and image_np.shape[2] == 4:
        gray_image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2GRAY)
    else:
        gray_image_np = image_np

    # Threshold, denoise, resize
    _, gray_image_np = cv2.threshold(gray_image_np, 150, 255, cv2.THRESH_BINARY)
    gray_image_np = cv2.medianBlur(gray_image_np, 1)

    h, w = gray_image_np.shape
    if w < 800:
        scale = 800 / w
        gray_image_np = cv2.resize(gray_image_np, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC)

    logger.info(f"Image preprocessed: {gray_image_np.shape}, dtype={gray_image_np.dtype}")
    return gray_image_np


def ndarray_to_filepath(abs_path, image_np):
    cv2.imwrite(abs_path, image_np)
    return abs_path

def fileobj_to_filepath(abs_path, file_obj):

    #abs_path = os.path.abspath(os.path.join(upload_folder, file_obj.filename))
    file_obj.save(abs_path)
    return abs_path


def filepath_to_fileobj(file_path):

    with open(file_path, "rb") as f:
        data = f.read()
        stream = io.BytesIO(data)   # keep in-memory buffer
        return FileStorage(
            stream=stream,
            filename=os.path.basename(file_path),
            content_type="image/jpeg"
        )

     
def file_to_base64(file):

    if file:
        # Read file bytes
        image_bytes = file.read()
        # Encode to base64 string
        receipt_image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    else:
        receipt_image_b64 = None

    return receipt_image_b64
    

def base64_to_filebytes(base64_str):

    file_bytes = base64.b64decode(base64_str)
    return file_bytes


def mock_easyocr(image_bytes):
    # 1 items
    #return ['佳寶', 'Anif3o foto tPifiHRKET', '食品', '性寶妄畝u執市堪;', '土瓜灣新鋪({8153 )', '客戶服務熱線:2418-5888', '收銀機:K153-001', '收銀員:13292', '發票編號:{153260411-0141$', '11/04/2026', '17:5;:00', 'Pli', '商品名稱', '單價', '數量', '金額', '1017418-芬達橙味汽水330m]', '4.00', '/.Ot0', ' 0o', '小計$:', '4.00', '整單折扣:', '20%', '-0.30', '應收總計$', '3.20', '實收總計 $', '4.00', '現金 $', '4.60', '找換 $', '0 .30', '購買件數', '1:00', '多謝慧顧請冉光臨']
    
    # 2 items

    gray_image = preocr_process_bytes(image_bytes)
    texts = ['惠康 wellcome', '紅磡中心!電話:27643119', '4', '40. 00', '四洲蘿荀牛瞞麵五包裝', '17.50', '火船牌三合一白咖啡10PC', '總金鵠', '57. 50', '促鈾僵胄總金!', '-0. 00', '僵忘券低屈總金輝', '-0. 00', '宦除廳付金頡', '57. 50', '抹萩', '0. 00', '現金', '100. 00', '披贖', '42. 50', '25042026/18 :54/0807/002/3985/00002406', '2504260004980023985', '串即日起至2026年5月21日於門市或惠康網', '店買滿$50,', '即可掃0R Code參加初夏派禮大', '抽獎, 齊抽八+萬份獎品,其中包括豊富焚', 'Join', '品及優患/現金券|受條款及細則約束.', 'the Wellcome Early Summer', 'Lucky', 'Draw!', 'Spend', '$50', 'at', 'physical', 'stores', 'or', 'online shop', 'and', 'scan', 'the', 'QR', 'code', 'below', 't0', 'join', 'the lucky draw', 'fron today', 't0', '21', 'May!', '800k', 'prizes,', 'including']
    return gray_image, texts


 

def np_array_to_base64_image(np_array):
    # Encode NumPy array to JPEG in memory
    success, buffer = cv2.imencode(".jpg", np_array)
    if not success:
        return None
    return base64.b64encode(buffer).decode("utf-8")


def deskew(gray_image):
    # Invert colors for text detection
    gray_inv = cv2.bitwise_not(gray_image)
    coords = np.column_stack(np.where(gray_inv > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    # Correct angle
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    (h, w) = gray_image.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(gray_image, M, (w, h),
                             flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)
    return rotated


def dewarp_wave(gray_image):
    # Ensure grayscale
    if len(gray_image.shape) != 2:
        raise ValueError("Expected grayscale image")

    h, w = gray_image.shape

    # Example: create source and destination points for warp
    # (Here we just simulate a correction — in practice you’d detect curves)
    src_pts = np.float32([[0,0], [w-1,0], [0,h-1], [w-1,h-1]])
    dst_pts = np.float32([[0,0], [w-1,0], [int(0.05*w),h-1], [w-1-int(0.05*w),h-1]])

    # Compute perspective transform
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(gray_image, M, (w,h),
                                 flags=cv2.INTER_CUBIC,
                                 borderMode=cv2.BORDER_REPLICATE)

    return warped



def preocr_process_image(file_path):
    img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)

    # Instead of calculating angle and rotating,
    # just keep the image as-is
    rotated = img  

    dirpath, filename = os.path.split(file_path)
    new_filename = "preocr_" + filename
    preocr_filepath = os.path.join(dirpath, new_filename)

    cv2.imwrite(preocr_filepath, rotated)
    return preocr_filepath
 

  