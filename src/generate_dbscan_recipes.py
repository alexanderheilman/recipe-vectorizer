import numpy as np
import pandas as pd
from collections import Counter
from string import *
from sklearn.metrics.pairwise import cosine_similarity
from sys import argv, exit
import pymongo
from modeling_functions import *
from functions import *

if __name__ == '__main__':
    if len(argv) != 2:
        print("Usage: python {} <search_term>".format(argv[0]))
        exit(1)
    search_term = argv[1]

    threshold = 0.8
    min_points = 4

    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    recipes_coll = db['recipes']

    print('Searching for {} recipes...'.format(search_term))
    recipes, ratings = find_recipes_matching_search(recipes_coll, search_term)
    print('{} recipes found.'.format(len(recipes)))

    df = create_dataframe(recipes)
    X = df.values
    cosine_sims = cosine_similarity(X)


    labels = dbscan(cosine_sims, threshold, min_points)
    n_clusters = int(max(labels))
    recipe_names_in_cluster = []
    for i in range(1, n_clusters+1):
        cluster_idxs = [j for j, label in enumerate(labels) if label == i]
        recipe_names_in_cluster.append(get_recipe_names(cluster_idxs, df.index, recipes))

    cluster_keywords = []
    for names in recipe_names_in_cluster:
        cluster_keywords.append(find_keywords(names, limit=4))
    
    recipe_results = generate_recipes_from_dbscan(labels, df, ratings)
    units_by_ing = get_common_units_by_ingredient(recipes)

    for i, r in enumerate(recipe_results):
        print('\nRecipes in cluster (5 of {}) :'.format(len(recipe_names_in_cluster[i])))
        print(recipe_names_in_cluster[i][:5])
        print('\nCluster keywords :')
        print(cluster_keywords[i])
        print('\nSuggested recipe :')
        for j, qty in enumerate(r):
            ing = r.index[j]
            print(convert_qty_to_common_units(ing, qty*10, units_by_ing), ing)
        print('--------------------------------')