from pymongo import MongoClient
from bson.json_util import dumps
client = MongoClient()
db = client['movie']
collection = db['country']
# collection.update_many({'name': 'hamed'}, {'$set': {'id': 112}})
# items = {'name':'hamed', 'id': 13, 'family': 'safari'}
# collection.insert_one(items)
# print(dumps(collection.find()))
# print(json.loads(dumps(collection.find())))
for i in collection.find():
    print(dumps(i))
