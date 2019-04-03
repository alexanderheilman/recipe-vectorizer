import pymongo
from datetime import *

if __name__ == '__main__':
    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    recipes_coll = db['recipes']
    cursor = recipes_coll.find().sort([('_id',-1)]).limit(1)
    recipe = next(cursor)
    print('Last recipe name:', recipe['name'])
    timestamp = recipe['_id'].generation_time
    time_str = timestamp.strftime('%Y-%m-%d at %H:%M:%S')
    now = datetime.now(timezone.utc)
    diff = now-timestamp
    print('Recipe collected on {0} ({1} ago)'.format(time_str, str(diff)))
