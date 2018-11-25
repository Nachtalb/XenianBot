from pymongo import MongoClient
from xenian.bot.settings import MONGODB_CONFIGURATION

job_queue = None

mongodb_client = MongoClient(host=MONGODB_CONFIGURATION['host'], port=MONGODB_CONFIGURATION['port'])
mongodb_database = mongodb_client[MONGODB_CONFIGURATION['db_name']]
