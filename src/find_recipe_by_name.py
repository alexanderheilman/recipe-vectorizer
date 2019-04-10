import pymongo
from sys import argv

if __name__ == '__main__':
    name = argv[1]
    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    recipes_coll = db['recipes']
    recipe = recipes_coll.find_one({'name':name})
    print('Full recipe:', recipe)