import os
import json
import csv
import re
import numpy as np
import pandas as pd
from keras.preprocessing.image import load_img
from heatmap import *
import matplotlib.pyplot as plt
from PIL import Image

def keys_exists(element, keys):
    '''
    Check if *keys (nested) exists in `element` (dict).
    '''
    if not isinstance(element, dict):
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')
    keys = keys.split('.')
    _element = element
    for key in keys:
        try:
            if key.isnumeric():
                key = int(key)
            if type(_element) == str:
                return None
            _element = _element[key]
            if _element == None or (not isinstance(_element,dict) and _element.lower() =='nan'):
                return None
        except KeyError:
            return None
    return _element

def addHashtagsToMap(post_hashtags):
    # current_hashtag_length = len(hashtag_by_hashtag_matrix.keys())
    for idx, hashtag1 in enumerate(post_hashtags):
        if hashtag1 not in hashtag_by_hashtag_matrix.keys():
            prev_rows = [0]*(len(hashtag_by_hashtag_matrix.keys())+1)
            hashtag_by_hashtag_matrix[hashtag1] = prev_rows
        hashtag1_idx_in_map = list(hashtag_by_hashtag_matrix.keys()).index(hashtag1)
        hashtag_by_hashtag_matrix[hashtag1][hashtag1_idx_in_map] += 1 # add one on diagonal line
        for hashtag2_idx in range(idx+1, len(post_hashtags)):
            hashtag2 = post_hashtags[hashtag2_idx]
            if hashtag2 not in hashtag_by_hashtag_matrix.keys():
                prev_rows = [0]*(len(hashtag_by_hashtag_matrix.keys())+1)
                hashtag_by_hashtag_matrix[hashtag2] = prev_rows
            hashtag2_idx_in_map = list(hashtag_by_hashtag_matrix.keys()).index(hashtag2)
            # check if hashtag2 index is within the range
            if hashtag2_idx_in_map >= len(hashtag_by_hashtag_matrix[hashtag1]):
                hashtag_by_hashtag_matrix[hashtag1] += [0]*(hashtag2_idx_in_map-len(hashtag_by_hashtag_matrix[hashtag1])+1)
            if hashtag1_idx_in_map >= len(hashtag_by_hashtag_matrix[hashtag2]):
                hashtag_by_hashtag_matrix[hashtag2] += [0]*(hashtag1_idx_in_map-len(hashtag_by_hashtag_matrix[hashtag2])+1)
            hashtag_by_hashtag_matrix[hashtag1][hashtag2_idx_in_map] += 1 #+1 for every link from hashtag1
            hashtag_by_hashtag_matrix[hashtag2][hashtag1_idx_in_map] += 1 #+1 for every link to hashtag1

def imgToHashtags(metadata):
    for datum in metadata:
        node = datum['node']
        caption = keys_exists(node,"edge_media_to_caption.edges.0.node.text") or \
        keys_exists(node,"caption.text") or \
        keys_exists(node,"description") # get caption
        caption = caption.replace('\n',' ') if caption != None else None
        hashtags = re.findall(r"#(\w+)",caption) if caption != None else [] # retrieve hashtags
        hashtags = [str(hashtag).lower() for hashtag in hashtags]

        img_to_hashtags_map[datum['_mediaPath'][0]] = hashtags

def getAncestorClusters(prevClusters, node, img_to_cluster_map, all_clusters):
    if node["name"]=='leaf':
        image = node['centroid'].split('/')[-1]
        image = image.split('\\')[-1]
        img_to_cluster_map[image] = prevClusters 
        return
    if prevClusters!="":
        currentCluster = prevClusters.split(',')[-1]+'-'+str(node['name'])
        clustersString = prevClusters+","+currentCluster
    else:
        currentCluster = node['name']
        clustersString = currentCluster
    all_clusters.append(currentCluster)
    for child in node["children"]:
        getAncestorClusters(clustersString, child, img_to_cluster_map,all_clusters)

def storeGradCam(folder, ori_img_filename, dest_folder):
    rescaling = 224
    # Plotting
    ori_img = load_img(os.path.join(folder, ori_img_filename), target_size=(rescaling,rescaling), interpolation='bicubic')
    # ori_img = Image.open(os.path.join(folder, ori_img_filename))
    heatmap = generateHeatmap(os.path.join(folder, ori_img_filename))
    plt.figure(figsize=(15,15))
    plt.axis("off")
    plt.imshow(ori_img)
    plt.imshow(heatmap.reshape(224,224,3), alpha=0.5) # Overlap with nice colouring
    plt.savefig(os.path.join(dest_folder, ori_img_filename), bbox_inches='tight')
    plt.clf()
    plt.close()

def generateThumbnails(folder, apath, dest_folder):
    img = Image.open(os.path.join(folder,apath))
    img.thumbnail((50,50))
    img.save(os.path.join(dest_folder, apath))
    img.close()

def generateHeatmapImages(source_file):
    source_file = os.listdir(os.path.join(os.getcwd(),source_file))[0]
    source_file = os.path.join("input_data/images",source_file)
    explainer_folder = source_file+"_explainer"
    thumbnail_folder = source_file+"_thumbnail"
    if not os.path.isdir(thumbnail_folder):
            os.mkdir(thumbnail_folder)
    if not os.path.isdir(explainer_folder):
        os.mkdir(explainer_folder)
    for path, subdirs, files in os.walk(source_file):
        for name in files:
            storeGradCam(path, name, explainer_folder)
            generateThumbnails(path,name,thumbnail_folder)

def generateClusterMap():
    with open("clusters.json",'r', encoding="utf8") as f:
        cluster = json.load(f)
    with open("metadata.json",'r', encoding="utf8") as f:
        metadata = json.load(f)

    img_to_cluster_map = {}
    img_to_hashtags_map = {}
    all_clusters = []
    adjacency_matrix = {}

    imgToHashtags(metadata, img_to_hashtags_map) # img to tags
    getAncestorClusters("", cluster, img_to_cluster_map,all_clusters) # img to clusters
    ## Create an empty cluster dict for each hashtag
    clusterSet = list(set(all_clusters))
    clusterSet.sort()
    clusterDictInit = dict(zip(clusterSet,[0]*len(clusterSet)))
    # adjacency matrix
    for (img,hashtags) in img_to_hashtags_map.items():
        if img not in img_to_cluster_map:
            continue
        img_clusters = img_to_cluster_map[img].split(',')
        for hashtag in hashtags:
            if hashtag not in adjacency_matrix:
                adjacency_matrix[hashtag] = dict(zip(clusterSet,[0]*len(clusterSet))) # use dict instead of variable to avoid referening the same object
            for cluster in img_clusters:
                adjacency_matrix[hashtag][cluster] = 1

    ## convert adjacency map to csv
    rows = []
    rows.append(["ID"]+list(clusterDictInit.keys()))
    for hashtag,clusters in adjacency_matrix.items():
        row = [hashtag]+list(clusters.values())
        rows.append(row)

    with open("nodelist.csv",'w', encoding='utf-8', errors='ignore', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def generateHashtagToHashtag():
    hashtag_by_hashtag_matrix = {}
    #add hashtag to hashtag-by-hashtag matrix
    for hashtags in list(img_to_hashtags_map.values()):
        addHashtagsToMap(hashtags)
    row_length = [len(row) for row in list(hashtag_by_hashtag_matrix.values())]
    max_row_length = np.max(row_length)
    # hashtag_by_hashtag_matrix_values= [row + [0]*(max_row_length-len(row)) for row in list(hashtag_by_hashtag_matrix.values())]
    rows = []
    rows.append(['']+list(hashtag_by_hashtag_matrix.keys()))
    for idx, hashtag in enumerate(list(hashtag_by_hashtag_matrix.keys())):
        matrix_cells = hashtag_by_hashtag_matrix[hashtag]
        row = [hashtag] + matrix_cells + [0]*(max_row_length-len(matrix_cells))
        rows.append(row)
    with open("hashtag_by_hashtag_matrix.csv",'w', encoding='utf-8', errors='ignore', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

root = os.getcwd()
for _dir in os.listdir(root):
    if os.path.isfile(os.path.join(root,_dir)):
        continue
    print("Processing", os.path.join(root,_dir))
    os.chdir(os.path.join(root,_dir))
    generateClusterMap()
    generateHashtagToHashtag()
    # generateHeatmapImages("input_data/images")

# root_folder = "datasets"
# for _,dirs,_ in os.walk(root_folder):
#     os.chdir(os.path.join(os.getcwd(),"datasets"))
#     for _dir in dirs:
#         print(_dir)
#         img_to_hashtags_map = {}
#         hashtag_by_hashtag_matrix = {}
#         os.chdir(os.path.join(".",_dir))
#         with open("metadata.json",'r', encoding="utf8") as f:
#             metadata = json.load(f)
#         imgToHashtags(metadata) # img to tags
#         os.chdir('../')
