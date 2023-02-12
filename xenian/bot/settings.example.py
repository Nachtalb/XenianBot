import logging
import os

BASE_DIR = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../"))

TELEGRAM_API_TOKEN = ""

ANIME_SERVICES = [
    {
        "name": "danbooru",
        "type": "danbooru",
        "url": "https://danbooru.donmai.us",
        "api": None,
        "username": None,
        "password": None,
    },
    {
        "name": "safebooru",
        "type": "danbooru",
        "url": "https://safebooru.donmai.us",
        "api": None,
        "username": None,
        "password": None,
    },
    {
        "name": "konachan",
        "type": "moebooru",
        "url": None,
        "hashed_string": None,
        "username": None,
        "password": None,
    },
]


ADMINS = [
    "@SOME_TELEGRAM_USERS",
]  # Users which can do admin tasks like /restart
SUPPORTER = [
    "@SOME_TELEGRAM_USERS",
]  # Users which to contact fo support

TEMPLATE_DIR = os.path.join(BASE_DIR, "xenian/bot/commands/templates")

# More information about polling and webhooks can be found here:
# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks
MODE = {
    "active": "webhook",  # webook or polling, if webhook further configuration is required
    "webhook": {
        "listen": "127.0.0.1",  # what to listen to, normally localhost
        "port": 5000,  # What port to listen to, if you have multiple bots running they mustn't be the same
        "url_path": TELEGRAM_API_TOKEN,  # Use your API Token so no one can send fake requests
        "url": "https://your_domain.tld/%s" % TELEGRAM_API_TOKEN,  # Your Public domain, with your token as path so
        # telegram knows where to send the request to
    },
}

UPLOADER = {
    "uploader": "xenian.bot.uploaders.ssh.SSHUploader",  # What uploader to use
    "url": "YOUR_DOMAIN_FILES_DIR",
    "configuration": {
        "host": "YOUR_HOST_IP",
        "user": "YOUR_USERNAME",
        "password": "YOUR_PASSWORD",  # If the server does only accepts ssh key login this must be the ssh password
        "upload_dir": "HOST_UPLOAD_DIRECTORY",
        "key_filename": "PATH_TO_PUBLIC_SSH_KEY",  # This is not mandatory but some server configurations require it
    },
}

LOG_LEVEL = logging.INFO

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
