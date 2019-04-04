"""
Merge search results so that 'viewed' indicator reflects actions of both EC2 instances.
"""
import pymongo
import json

mc = pymongo.MongoClient()
db = mc['allrecipes']
results_coll = db['search_results']

with open('../data/instance-1/search_results.json') as f:
    for line in f:
        result = json.loads(line)
        if result['viewed'] != 0:
            results_coll.update_one({'id':result['id']},
                                    {"$set":{'viewed': result['viewed']}}, upsert=False)

with open('../data/instance-2/search_results.json') as f:
    for line in f:
        result = json.loads(line)
        if result['viewed'] != 0:
            results_coll.update_one({'id':result['id']},
                                    {"$set":{'viewed': result['viewed']}}, upsert=False)