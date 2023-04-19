import json
from logging import exception
import os
from ..stdio import *

# from dotenv import load_dotenv

# load_dotenv("./.env")

# ?--------------------INI Variable------------------------------#
"""Load configuration from .ini file."""
import configparser

# Read local file `config.ini`.
CONFIG_FILE_PATH = "./config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE_PATH)
APP_TITLE = config.get("APP", "APP_TITLE")
DIR_PATH = os.getcwd()
# Auth configs.
API_SECRET_KEY = config.get("APP", "API_SECRET_KEY")
API_ALGORITHM = config.get("APP", "API_ALGORITHM")
API_ACCESS_TOKEN_EXPIRE_MINUTES = int(config.get("APP", "API_ACCESS_TOKEN_EXPIRE_MINUTES"))
LINE_TOKEN = config.get("APP", "LINE_TOKEN")


def set(section, key, value):
    global LINE_TOKEN
    try:
        config.set(section, key, value)
        print(f"Save config.ini : path = {CONFIG_FILE_PATH}")
        with open(CONFIG_FILE_PATH, "w") as configfile:
            config.write(configfile)
        if key == "LINE_TOKEN":
            LINE_TOKEN = config.get("APP", "LINE_TOKEN")
    except Exception as e:
        print_error(e)
