from pymongo import MongoClient
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
import time

cluster = None
mongo_client = None


def check(status):
    global cluster, mongo_client
    try:
        cluster = Cluster(['localhost'], port=9042)
        session = cluster.connect()
        session.row_factory = dict_factory
        status['cassandra'] = True
    except:
        status['cassandra'] = False

    try:
        mongo_client = MongoClient(serverSelectionTimeoutMS=1000)
        mongo_client.server_info()
        status['mongodb'] = True
    except:
        status['mongodb'] = False
    time.sleep(2)
    check(status)


def get_cassandra_session():
    return cluster


def get_mongodb_client():
    return mongo_client
