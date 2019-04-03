import pymongo

if __name__ == '__main__':
    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    recipes_coll = db['recipes']
    results_coll = db['search_results']
    print("Entries in 'recipes' collection        :", len(list(recipes_coll.find())))
    print("Entries in 'search_results' collection :", len(list(results_coll.find())))