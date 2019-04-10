import pymongo
from sys import argv

if __name__ == '__main__':
    recipe_id = int(argv[1])
    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    recipes_coll = db['recipes']
    recipe = recipes_coll.find_one({'id':recipe_id})
    print('Full recipe:', recipe)