import pandas as pd
import json
import re
import csv

with open("clusters.json",'r', encoding="utf8") as f:
    cluster = json.load(f)
with open("metadata.json",'r', encoding="utf8") as f:
    metadata = json.load(f)

img_to_cluster_map = {}
img_to_hashtags_map = {}
all_clusters = []
adjacency_matrix = {}

def getAncestorClusters(prevClusters, node):
    if node["name"]=='leaf':
        # image = node['centroid'].split('/')[-1]
        image = node['centroid'].split('\\')[-1]
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
        getAncestorClusters(clustersString,child)

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
            _element = _element[key]
            if _element == None:
                return None
        except KeyError:
            return None
    return _element


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

imgToHashtags(metadata) # img to tags
getAncestorClusters("", cluster) # img to clusters
## Create an empty cluster dict for each hashtag
clusterSet = list(set(all_clusters))
clusterSet.sort()
clusterDictInit = dict(zip(clusterSet,[0]*len(clusterSet)))
# adjacency matrix
for (img,hashtags) in img_to_hashtags_map.items():
    img_clusters = img_to_cluster_map[img].split(',')
    for hashtag in hashtags:
        if hashtag not in adjacency_matrix:
            adjacency_matrix[hashtag] = dict(zip(clusterSet,[0]*len(clusterSet))) # use dict instead of variable to avoid referening the same object
        for cluster in img_clusters:
            adjacency_matrix[hashtag][cluster] = 1

## convert adjacency map to csv
rows = []
rows.append(["Hashtag"]+list(clusterDictInit.keys()))
for hashtag,clusters in adjacency_matrix.items():
    row = [hashtag]+list(clusters.values())
    rows.append(row)

with open("adjacencymap_separate.csv",'w', encoding='utf-8', errors='ignore', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(rows)




