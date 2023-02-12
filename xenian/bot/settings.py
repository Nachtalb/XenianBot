import json
import logging
import os
from pathlib import Path
from shutil import copy
import sys

from dotenv import load_dotenv


load_dotenv()

CONFIG_PATH = Path(os.environ.get("CONFIG_PATH", "/config"))
CONFIG_PATH.mkdir(exist_ok=True)

config_file = CONFIG_PATH / "config.json"
if not config_file.exists():
    default_config = Path(__file__).with_name("config/config.json")
    copy(default_config, config_file)
    print(f"{'*' * 50}\nFill out the config and restart: \"{config_file}\"\n{'*' * 50}")
    sys.exit()

config = json.loads(config_file.read_text())


BASE_DIR = Path(__file__) / "commands/templates"

TELEGRAM_API_TOKEN = config["bot_token"]

ANIME_SERVICES = config["anime_services"]

ADMINS = config["admins"]

SUPPORTER = config["supporters"]

TEMPLATE_DIR = config["template_dir"].format(BASE_DIR=str(BASE_DIR))

# More information about polling and webhooks can be found here:
# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks
MODE = config["mode"]

UPLOADER = config["uploader"]

match config["log_level"]:
    case "info":
        LOG_LEVEL = logging.INFO
    case "debug":
        LOG_LEVEL = logging.DEBUG
    case "warning" | _:
        LOG_LEVEL = logging.WARNING

# These Instagram credentials are used for the centralized Instagram account which automatically follows private
# accounts and downloads images / videos
INSTAGRAM_CREDENTIALS = {
    "username": "INSTAGRAM_USERNAME",
    "password": "INSTAGRAM_PASSWORD",
}

MONGODB_CONFIGURATION = {
    "host": "HOST_OF_YOUR_DB",  # default: localhost
    "port": "PORT_OF_YOUR_DB_AS_INT",  # default: 27017
    "db_name": "DATABASE_NAME",
}
