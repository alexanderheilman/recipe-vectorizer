from functions import *
from sys import argv, exit
import pymongo

if __name__ == '__main__':
    if len(argv) != 3:
        print("Usage: python {} <max_count> <reverse?>".format(argv[0]))
        exit(1)
    max_count = int(argv[1])
    reverse = bool(int(argv[2]))
    # Connect to MongoClient and get collection handles
    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    results_coll = db['search_results']
    
    direction = -1 if reverse else 1
    recipes = list(results_coll.find({'viewed':0}).sort([('_id',direction)]).limit(max_count))
    for recipe in recipes:    
        print(recipe['name'])