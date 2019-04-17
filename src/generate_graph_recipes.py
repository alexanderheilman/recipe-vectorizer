import numpy as np
import networkx as nx
import pandas as pd
from collections import Counter
from string import *
from sklearn.metrics.pairwise import cosine_similarity
from sys import argv, exit
import pymongo
from modeling_functions import *
from functions import *

if __name__ == '__main__':
    if len(argv) != 3:
        print("Usage: python {} <search_term> <num_recipes>".format(argv[0]))
        exit(1)
    search_term = argv[1]
    n_recipes = int(argv[2])

    min_cluster_size = 10

    mc = pymongo.MongoClient()
    db = mc['allrecipes']
    recipes_coll = db['recipes']

    print('Searching for {} recipes...'.format(search_term))
    recipes, ratings = find_recipes_matching_search(recipes_coll, search_term)
    print('{} recipes found.'.format(len(recipes)))

    df = create_dataframe(recipes)
    X = df.values
    cosine_sims = cosine_similarity(X)

    G = create_graph(cosine_sims, threshold=0.75)
    remove_isolates(G, min_cluster_size)

    n_subgraphs = nx.number_connected_components(G)
    print('{} clusters identified.'.format(n_subgraphs))
    while n_subgraphs < n_recipes:
        largest_subgraph = max(nx.connected_component_subgraphs(G), key=len)
        split_subgraph(largest_subgraph, G)
        remove_isolates(G, min_cluster_size)
        new_n = nx.number_connected_components(G)
        if n_subgraphs < new_n:
            print('{} clusters identified.'.format(new_n))
        n_subgraphs = new_n
        if len(G) <= min_cluster_size:
            break

    recipe_names_in_cluster = []
    for component in nx.connected_components(G):
        recipe_names_in_cluster.append(get_recipe_names(component, df.index, recipes))

    cluster_keywords = []
    for names in recipe_names_in_cluster:
        cluster_keywords.append(find_keywords(names, limit=4))
    
    recipe_results = generate_recipes_from_graph(G, df, ratings)
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