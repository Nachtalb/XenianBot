# See http://peak.telecommunity.com/DevCenter/setuptools#namespace-packages
try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)

from pymongo import MongoClient

from xenian_bot.settings import MONGODB_CONFIGURATION

job_queue = None

mongodb_client = MongoClient(host=MONGODB_CONFIGURATION['host'], port=MONGODB_CONFIGURATION['port'])
mongodb_database = mongodb_client[MONGODB_CONFIGURATION['db_name']]
