import pymongo

mc = pymongo.MongoClient()
db = mc['allrecipes']
results_coll = db['search_results']

response = input('Are you sure? (Y/n)')
if response == 'Y':
    results_coll.update_many({'viewed':1}, {"$set":{'viewed': 0}}, upsert=False)