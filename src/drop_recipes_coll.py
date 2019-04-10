import pymongo

mc = pymongo.MongoClient()
db = mc['allrecipes']
recipes_coll = db['recipes']

response = input('Are you sure? (Y/n)')
if response == 'Y':
    recipes_coll.drop()