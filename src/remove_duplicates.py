import pymongo

mc = pymongo.MongoClient()
db = mc['allrecipes']
recipes_coll = db['recipes']
results_coll = db['search_results']

while True:
    cursor = recipes_coll.find()
    repeats = set()
    for recipe in cursor:
        if len(list(recipes_coll.find({'id':recipe['id']}))) > 1:
            repeats.add(recipe['id'])
    print('{} repeats found in "recipes" collection.'.format(len(repeats)))
    if len(repeats) == 0:
        break
    for recipe_id in repeats:
        recipes_coll.delete_one({'id':recipe_id})

len_prev = 0
while True:
    cursor = results_coll.find()
    repeats = set()
    len_current = 0
    for result in cursor:
        if len(list(results_coll.find({'id':result['id']}))) > 1:
            repeats.add(result['id'])
        len_current += 1
    print('{} repeats found in "search_results" collection.'.format(len(repeats)))
    if len(repeats) == 0:
        break
    # Remove 'unviewed' repeats before removing 'viewed' repeats
    # (only remove 'viewed' if we aren't making progress removing
    # 'unviewed' entries.)
    if len_prev == len_current:
        for result_id in repeats:
            del_result = results_coll.delete_one({'id':result_id, 'viewed':-1})
            if del_result.deleted_count == 0:
                results_coll.delete_one({'id':result_id, 'viewed':1})
    else:
        for result_id in repeats:
            results_coll.delete_one({'id':result_id, 'viewed':0})
    
    len_prev = len_current