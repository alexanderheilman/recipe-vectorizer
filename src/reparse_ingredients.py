import numpy as np
from functions import *
import string
from string import *
import pymongo

if __name__ == '__main__':
    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    recipes_coll = db['recipes']
    cursor = recipes_coll.find()
    for recipe in cursor:
        raw_ings = recipe['ingredients_raw']
        parsed_ings = parse_ingredients(raw_ings)
        recipes_coll.update_one({'id':recipe['id']},
                            {"$set":{'ingredients': parsed_ings}}, upsert=False)
    print('Last entry')
    print('------------------------')
    print('Initial ingredient list:\n', raw_ings)
    print('------------------------')
    print('Parsed ingredient list:\n', parsed_ings)