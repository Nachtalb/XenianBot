from pymongo import MongoClient

from xenian.bot.settings import MONGODB_CONFIGURATION

job_queue = None

mongodb_client = MongoClient(**MONGODB_CONFIGURATION["server"])
mongodb_database = mongodb_client[MONGODB_CONFIGURATION["db_name"]]
