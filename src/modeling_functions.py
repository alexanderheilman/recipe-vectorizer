import numpy as np
import networkx as nx
import pandas as pd
from collections import Counter
from string import *
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from matplotlib import cm

#########################################
#   Recipe searching and data structuring
#########################################

def create_dataframe(recipes, cutoff=None):
    if cutoff == None:
        cutoff = int(len(recipes)**(1/3))
#    print('Ingredient cutoff : {} occurrences'.format(cutoff))
    recipe_ids = _get_recipe_ids(recipes)
    common_ingredients = _get_common_ingredients(recipes, cutoff=cutoff)
    df = pd.DataFrame(columns=common_ingredients, index=recipe_ids).fillna(0)
    unknown_servings = []
    for recipe in recipes:
        idx = recipe['id']
        servings = recipe['directions']['servings']
        if not servings:
            unknown_servings.append(recipe)
            #print('Servings missing')
            continue
        for ing, qty in recipe['ingredients'].items(): 
            norm_qty = qty['normalized_qty']
            if ing in df.columns:
                df.loc[idx, ing] = norm_qty / servings
    # Determine approx servings for recipes where it is not specified
    for recipe in unknown_servings:
        servings = _approximate_servings(recipe, df)
        recipe['directions']['approx_servings'] = servings
    # Apply approx servings to recipes and insert data into dataframe
    for recipe in unknown_servings:
        servings = recipe['directions']['approx_servings']
        for ing, qty in recipe['ingredients'].items(): 
            norm_qty = qty['normalized_qty']
            if ing in df.columns:
                df.loc[idx, ing] = norm_qty / servings
    return df

def _get_recipe_ids(recipes):
    recipe_ids = []
    for recipe in recipes:
        recipe_ids.append(recipe['id'])
    return recipe_ids

def _approximate_servings(recipe, df):
    recipe_qtys = []
    df_means = []
    for ing, qty in recipe['ingredients'].items():
        if ing in df.columns:
            recipe_qtys.append(qty['normalized_qty'])
            ing_vals = df[df[ing] != 0][ing]
            df_means.append(np.mean(ing_vals))
    qtys_array = np.array(recipe_qtys)
    df_means_array = np.array(df_means)
    count = 1
    while True:
        err = np.mean(abs(qtys_array/count - df_means_array)) * count
        next_err = np.mean(abs(qtys_array/(count+1) - df_means_array)) * (count+1)
        if next_err > err:
            return count
        count += 1
        err = next_err
        
def _get_common_ingredients(recipes, cutoff=2):
    ingredients = Counter()
    for recipe in recipes:
        for ing in recipe['ingredients'].keys():
            ingredients[ing] += 1
    #print('Number of unique ingredients :', len(ingredients))
    common_ingredients = []
    for item, count in ingredients.most_common():
        if count >= cutoff:
            common_ingredients.append(item)
    #print('Number of common ingredients :', len(common_ingredients))
    return common_ingredients

def find_recipes_matching_search(collection, search_term):
    matching_recipes = []
    ratings = []
    for recipe in collection.find():
        flag = False
        for word in search_term.split():
            if len(recipe['name'].lower().split(word.lower())) > 1:
                flag = True
            if recipe['category']['lvl_2']:
                if len(recipe['category']['lvl_2'].lower().split(word.lower())) > 1:
                    flag = True
            if recipe['category']['lvl_3']:
                if len(recipe['category']['lvl_3'].lower().split(word.lower())) > 1:
                    flag = True
        if flag:
            matching_recipes.append(recipe)
            ratings.append(recipe['rating_info'])
    return matching_recipes, ratings


#########################################
#   Graph functions
#########################################

def create_graph(similarity_matrix, threshold, weight=100):
    G = nx.Graph()
    for i, row in enumerate(similarity_matrix):
        for j in range(i+1, len(similarity_matrix)):
            if similarity_matrix[i,j] > threshold:
                G.add_edge(i, j, weight=weight*similarity_matrix[i,j])
    return G

def remove_isolates(G, min_size=3):
    for subG in nx.connected_component_subgraphs(G.copy()):
        if len(subG) < min_size:
            for node in subG.nodes:
                G.remove_node(node)

def split_graph(G):
    initial_communities = nx.number_connected_components(G)
    while initial_communities == nx.number_connected_components(G):
        betweenness = nx.edge_betweenness_centrality(G)
        edge_array = np.array([key for key, val in betweenness.items()])
        between_array = np.array([val for key, val in betweenness.items()])
        most_important_edge = edge_array[np.argmax(between_array)]
        G.remove_edge(most_important_edge[0], most_important_edge[1])

def split_subgraph(subG, G, return_history=False):
    """
    Only makes splits within subG, a subgraph of G, but also removes edges in G
    """
    initial_communities = nx.number_connected_components(subG)
    history = []
    while initial_communities == nx.number_connected_components(subG):
        betweenness = nx.edge_betweenness_centrality(subG)
        edge_array = np.array([key for key, val in betweenness.items()])
        between_array = np.array([val for key, val in betweenness.items()])
        most_important_edge = edge_array[np.argmax(between_array)]
        subG.remove_edge(most_important_edge[0], most_important_edge[1])
        G.remove_edge(most_important_edge[0], most_important_edge[1])
        if return_history:
            history.append(G.copy())
    if return_history:
        return history

#########################################
#   Plotting functions
#########################################

def plot_weighted_graph(G, ax, k=0.5, fixed_axes=None):
    eigen_centralities = nx.eigenvector_centrality(G)
    eigen_array = np.array([val for key, val in eigen_centralities.items()])
    node_colors = [cm.jet(eig/np.max(eigen_array)) for eig in eigen_array]

    betweenness = nx.edge_betweenness_centrality(G)
    between_array = np.array([val for key, val in betweenness.items()])
    edge_colors = [cm.jet(bet/np.max(between_array)) for bet in between_array]

    spring = nx.spring_layout(G, k=k, weight='weight', seed=427)
    nx.draw_networkx_nodes(G,
                           pos=spring,
                           node_size=150 * eigen_array/np.max(eigen_array) + 10,
                           node_color=node_colors,
                           ax=ax,
                           alpha=0.5,
                           with_labels=False)
    nx.draw_networkx_edges(G,
                           pos=spring,
                           edge_color=edge_colors,
                           width=8 * between_array/np.max(between_array) + 0.1,
                           alpha=0.5)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    if fixed_axes:
        ax.set_xlim(left=fixed_axes[0], right=fixed_axes[1])
        ax.set_ylim(bottom=fixed_axes[2], top=fixed_axes[3])


#########################################
#   Analysis
#########################################

def get_recipe_names(node_set, recipe_ids, recipe_list):
    recipe_names = []
    for node in node_set:
        r_id = recipe_ids[node]
        for recipe in recipe_list:
            if recipe['id'] == r_id:
                recipe_names.append(recipe['name'])
                break
    return recipe_names

stopwords = ['the','and','i','ii','iii','iv','of','with','for','a']

def find_keywords(recipe_names, stopwords=stopwords, limit=10):
    all_words = Counter()
    for name in recipe_names:
        for word in name.split():
            w = ''.join([letter for letter in word.lower() if letter in ascii_lowercase])
            if w and w not in stopwords:
                all_words[w] += 1
    return all_words.most_common()[:limit]

def get_ingredient_frequencies(df):
    frequencies = Counter()
    for col in df.columns:
        frequencies[col] = np.mean(df[col] != 0)
    return frequencies

def generate_recipes_from_graph(G, df, ratings, n_ingredients=20):
    recipes = []
    ratings_array = np.ones(len(df))
    for i, rating in enumerate(ratings):
        try:
            score = rating['rating'] * np.log(rating['reviews'])
            if score > 0:
                ratings_array[i] = score
        except:
            continue
    subgraphs = list(nx.connected_component_subgraphs(G))
    for subG in subgraphs:
        eigen_centralities = nx.eigenvector_centrality(subG)
        eigen_array = np.array([val for key, val in eigen_centralities.items()])
        
        # Mask = 'Is recipe in cluster?'
        components = set(subG.nodes)
        mask = [(i in components) for i in range(len(df.index))]
        sub_df = df.loc[mask,:]
        sub_ratings = ratings_array[mask]

        weights = eigen_array * sub_ratings
        # Get N most commonly listed ingredients for each cluster
        ing_freqs = get_ingredient_frequencies(sub_df)
        ing_list = [key for key, val in ing_freqs.most_common()[:n_ingredients]]
        
        # Weight ingredient proportions by eigenvector centrality of recipes
        weighted_proportions = sub_df.loc[:,ing_list] * weights.reshape(-1,1)/np.sum(weights)
        recipes.append(np.sum(weighted_proportions, axis=0))
    return recipes