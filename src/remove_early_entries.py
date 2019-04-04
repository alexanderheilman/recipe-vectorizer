"""
Script for removing early recipe entries for which the raw ingredients list was not saved.
Also flags these recipes in as 'not viewed' in the results collection so they can be 
scraped again.
"""

import pymongo

mc = pymongo.MongoClient()
db = mc['allrecipes']
recipes_coll = db['recipes']
results_coll = db['search_results']

recipe_ids = set()
cursor = recipes_coll.find({'ingredients_raw':{'$exists':False}})

for recipe in cursor:
    recipe_ids.add(recipe['id'])
    recipes_coll.delete_one({'id':recipe['id']})

for recipe_id in recipe_ids:
    results_coll.update_one({'id':recipe_id},
                            {"$set":{'viewed': 0}}, upsert=False)
