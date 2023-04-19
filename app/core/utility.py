import os
from app.core import database
from ..stdio import *
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from app.core.config import DIR_PATH


def save_image_file(img, file_path, file_name):
    if not img:
        return None
    if not os.path.exists(file_path):
        os.makedirs(file_path)
        print("The new directory is created!")

    if img.format == "PNG":
        print("convert ing to RBG")
        img = img.convert("RGB")
    img = img.resize((400, 400))

    try:
        _path_save_file = f"{file_path}/{file_name}.jpg"
        img.save(_path_save_file, "PNG")
        return _path_save_file
    except Exception as e:
        print_error(e)
        return None
