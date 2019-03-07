from mongoengine import connect

from xenian.bot import MONGODB_CONFIGURATION

connect(db=MONGODB_CONFIGURATION['db_name'], host=MONGODB_CONFIGURATION['host'], port=MONGODB_CONFIGURATION['port'])

from .telegram import *
from .tg_chat import *
from .tg_user import *
from .tg_message import *
from .button import *
from .gif import *
from .anime_file import *
