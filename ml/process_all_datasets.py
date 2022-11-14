import os
import json
import csv
import re
import numpy as np
import pandas as pd
from keras.preprocessing.image import load_img
import scipy.spatial.distance as dist

# from heatmap import *
# import matplotlib.pyplot as plt
# from PIL import Image

def write_to_file(data_dict, col_names, a1_cell, output_fn):
    rows = []
    rows.append([a1_cell]+col_names)
    for (key,value) in data_dict.items():
        if type(value) == dict:
            value = list(value.values())
        row = [key]+value
        rows.append(row)
    # print(rows)
    with open(output_fn,'w', encoding='utf-8', errors='ignore', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

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
    # current_hashtag_length = len(hashtags_hashtags_matrix.keys())
    for idx, hashtag1 in enumerate(post_hashtags):
        if hashtag1 not in hashtags_hashtags_matrix.keys():
            prev_rows = [0]*(len(hashtags_hashtags_matrix.keys())+1)
            hashtags_hashtags_matrix[hashtag1] = prev_rows
        hashtag1_idx_in_map = list(hashtags_hashtags_matrix.keys()).index(hashtag1)
        hashtags_hashtags_matrix[hashtag1][hashtag1_idx_in_map] += 1 # add one on diagonal line
        for hashtag2_idx in range(idx+1, len(post_hashtags)):
            hashtag2 = post_hashtags[hashtag2_idx]
            if hashtag2 not in hashtags_hashtags_matrix.keys():
                prev_rows = [0]*(len(hashtags_hashtags_matrix.keys())+1)
                hashtags_hashtags_matrix[hashtag2] = prev_rows
            hashtag2_idx_in_map = list(hashtags_hashtags_matrix.keys()).index(hashtag2)
            # check if hashtag2 index is within the range
            if hashtag2_idx_in_map >= len(hashtags_hashtags_matrix[hashtag1]):
                hashtags_hashtags_matrix[hashtag1] += [0]*(hashtag2_idx_in_map-len(hashtags_hashtags_matrix[hashtag1])+1)
            if hashtag1_idx_in_map >= len(hashtags_hashtags_matrix[hashtag2]):
                hashtags_hashtags_matrix[hashtag2] += [0]*(hashtag1_idx_in_map-len(hashtags_hashtags_matrix[hashtag2])+1)
            hashtags_hashtags_matrix[hashtag1][hashtag2_idx_in_map] += 1 #+1 for every link from hashtag1
            hashtags_hashtags_matrix[hashtag2][hashtag1_idx_in_map] += 1 #+1 for every link to hashtag1

def imgToMetadata(metadata):
    for datum in metadata:
        node = datum['node']
        img_path = datum['_mediaPath'][0].split('/')[-1].split('.')[0]+'.jpg'
        # img to hashtags map 1:m
        hashtags = getMetaHashtags(node)
        img_to_hashtags_map[img_path] = hashtags
        # img to user map 1:1
        user = getMetaUser(node)
        img_to_user_map[img_path] = user
        # user to hashtags 1(user):m(images):m(hashtags)
        if user not in list(user_to_hashtags_map.keys()):
            user_to_hashtags_map[user] = []
        user_to_hashtags_map[user]+=hashtags

def getMetaHashtags(node):
    caption = keys_exists(node,"edge_media_to_caption.edges.0.node.text") or \
    keys_exists(node,"caption.text") or \
    keys_exists(node,"description") # get caption
    caption = caption.replace('\n',' ') if caption != None else None
    hashtags = re.findall(r"#(\w+)",caption) if caption != None else [] # retrieve hashtags
    hashtags = [str(hashtag).lower() for hashtag in hashtags]
    return hashtags

def getMetaUser(node):
    return keys_exists(node,"user.username")

def getAncestorClusters(prevClusters, node, img_to_cluster_map, all_clusters):
    if node["name"]=='leaf':
        image = node['centroid'].split('/')[-1]
        image = image.split('\\')[-1].split('.')[0]+".jpg"
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

def generateClusterNodelist(cluster):
    # img_to_cluster_map, cluster_set
    all_clusters = []
    getAncestorClusters("", cluster, img_to_cluster_map,all_clusters) 
    clusterSet = list(set(all_clusters))
    clusterSet.sort()
    # hashtags_cluster matrix
    for img in img_to_hashtags_map.keys(): # loop through every image, img_to_user_map.keys() is fine too
        if img not in img_to_cluster_map:
            continue
        # clusters info
        img_clusters = img_to_cluster_map[img].split(',')
        
        #hashtags_cluster
        hashtags = img_to_hashtags_map[img]
        for hashtag in hashtags:
            if hashtag not in hashtags_clusters_nodelist:
                hashtags_clusters_nodelist[hashtag] = dict(zip(clusterSet,[0]*len(clusterSet))) # use dict instead of variable to avoid referening the same object
            for cluster in img_clusters:
                hashtags_clusters_nodelist[hashtag][cluster] += 1
        # users_clusters
        user = img_to_user_map[img]
        if user not in list(users_clusters_nodelist.keys()):
            users_clusters_nodelist[user] = dict(zip(clusterSet, [0]*len(clusterSet)))
        for cluster in img_clusters:
            users_clusters_nodelist[user][cluster]+=1

    # writing hashtags_clusters_nodelist
    write_to_file(hashtags_clusters_nodelist,list(clusterSet),"ID","hashtagClusterNodelist.csv")
    # writing users_clusters_nodelist
    write_to_file(users_clusters_nodelist,list(clusterSet),"ID","userClusterNodelist.csv")

def generateHashtagToHashtag():
    hashtags_hashtags_matrix = {}
    #add hashtag to hashtag-by-hashtag matrix
    for hashtags in list(img_to_hashtags_map.values()):
        addHashtagsToMap(hashtags)
    row_length = [len(row) for row in list(hashtags_hashtags_matrix.values())]
    max_row_length = np.max(row_length)
    # hashtags_hashtags_matrix_values= [row + [0]*(max_row_length-len(row)) for row in list(hashtags_hashtags_matrix.values())]
    rows = []
    rows.append(['']+list(hashtags_hashtags_matrix.keys()))
    for idx, hashtag in enumerate(list(hashtags_hashtags_matrix.keys())):
        matrix_cells = hashtags_hashtags_matrix[hashtag]
        row = [hashtag] + matrix_cells + [0]*(max_row_length-len(matrix_cells))
        rows.append(row)
    with open("hashtag_by_hashtag_matrix.csv",'w', encoding='utf-8', errors='ignore', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def generateUserMatrix():
    # user matrix
    hashtagSet = [hashtag for hashtags in user_to_hashtags_map.values() for hashtag in hashtags]
    # users_to_hashtags_matrix as an input for users_to_users_matrix
    users_hashtags_matrix = {}
    for (user,hashtags) in user_to_hashtags_map.items():
        if user not in list(users_hashtags_matrix.keys()):
            users_hashtags_matrix[user] = dict(zip(hashtagSet,[0]*len(hashtagSet)))
        for hashtag in hashtags:
            users_hashtags_matrix[user][hashtag] += 1
    # users_to_users_matrix (pairwise comparison)           
    users_users_matrix = {}
    for (user, hashtags) in users_hashtags_matrix.items():
        users_users_matrix[user] = [0]*len(list(users_hashtags_matrix.keys()))
        for idx,x in enumerate(users_hashtags_matrix.keys()):
            users_users_matrix[user][idx] = dist.euclidean(list(users_hashtags_matrix[user].values()),list(users_hashtags_matrix[x].values()))
    # write_to_file
    write_to_file(users_users_matrix, list(users_users_matrix.keys()), "", "users_users_pairwise.csv")
# root = os.getcwd()
# for _dir in os.listdir(root):
#     if os.path.isfile(os.path.join(root,_dir)):
#         continue
#     print("Processing", os.path.join(root,_dir))
#     os.chdir(os.path.join(root,_dir))
#     generateClusterNodelist()
#     generateHashtagToHashtag()
    # generateHeatmapImages("input_data/images"\

def clusterStatsCore(cluster):
    img_to_cluster_map = {}
    all_clusters = []
    getAncestorClusters("", cluster, img_to_cluster_map,all_clusters) 
    cluster_to_img_map = {}
    for (img,cluster) in img_to_cluster_map.items():
        img_clusters = img_to_cluster_map[img].split(',')
        for cluster in img_clusters:
            if cluster not in list(cluster_to_img_map.keys()):
                cluster_to_img_map[cluster] = []
            cluster_to_img_map[cluster].append(img)
    cluster_tags_in_img_map = {}
    cluster_tags_in_caption_map = {}
    core_categories = {
        'cottagecore': 'cottagecore',
        "nostalgiacore":'altcore',
        "childhoodcore":'altcore',
        "cybercore":'altcore',
        "webcore":'altcore',
        "dreamcore":'altcore',
        "liminalcore":'altcore',
        "90score":'altcore',
        "memorycore":'altcore',
        "forgottencore":'altcore',
        "abandonedcore":'altcore',
        "strangecore":'altcore',
        "oddcore":'altcore',
        "weirdcore":'altcore',
        "voidcore":'altcore',
        "y2kcore":'altcore',
        "goblincore":'nichecore',
        "forestcore":'nichecore',
        "naturecore":'nichecore',
        "farmcore":'nichecore',
        "grandmacore":'nichecore',
        "witchcore":'nichecore',
        "honeycore":'nichecore',
        "warmcore":'nichecore',
        "frogcore":'nichecore',
        "cozycore":'nichecore',
        "darkcottagecore":'nichecore',
        "gardencore":'nichecore',
        "flowercore":'nichecore',
        "faecore":'nichecore'
    }
    cluster_tags_stat = []
    cluster_tags_stat.append(["ID","#_posts","#_cottagecore_collect","#_altcores_collect","#_nichecores_collect","#_cottagecore_caption","#_altcores_caption","#_nichecores_caption"])
    for (cluster, imgs) in cluster_to_img_map.items():
        # print('cluster', cluster)
        # print([img.split('_')[0] for img in imgs])
        tags_collection_counter = {}
        tags_caption_counter = {}
        for img in imgs:
            category = 'nichecore' if img.split('_')[0] not in list(core_categories.keys()) else core_categories[img.split('_')[0]]
            if category not in list(tags_collection_counter.keys()):
                tags_collection_counter[category]=0
            tags_collection_counter[category]+=1
            for hashtag in list(set(img_to_hashtags_map[img])):
                if hashtag not in list(core_categories.keys()):
                    continue
                tags_caption_category = core_categories[hashtag]+"_caption"
                if tags_caption_category not in list(tags_caption_counter.keys()):
                    tags_caption_counter[tags_caption_category]=0
                tags_caption_counter[tags_caption_category]+=1
        cluster_tags_stat.append([cluster]+[len(imgs)]+
                                    [tags_collection_counter['cottagecore'] if 'cottagecore' in list(tags_collection_counter.keys()) else 0]+
                                    [tags_collection_counter['altcore'] if 'altcore' in list(tags_collection_counter.keys()) else 0]+
                                    [tags_collection_counter['nichecore'] if 'nichecore' in list(tags_collection_counter.keys()) else 0]+
                                    [tags_caption_counter['cottagecore_caption'] if 'cottagecore_caption' in list(tags_caption_counter.keys()) else 0]+
                                    [tags_caption_counter['altcore_caption'] if 'altcore_caption' in list(tags_caption_counter.keys()) else 0]+
                                    [tags_caption_counter['nichecore_caption'] if 'nichecore_caption' in list(tags_caption_counter.keys()) else 0]
                                    )
    with open("cluster_tags_stat.csv",'w', encoding='utf-8', errors='ignore', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(cluster_tags_stat)

root_folder = "dataset"
for _,dirs,_ in os.walk(root_folder):
    os.chdir(os.path.join(os.getcwd(),"dataset"))
    for _dir in dirs:
        print(_dir)
        os.chdir(os.path.join(".",_dir))
        # mappings
        img_to_cluster_map = {}
        img_to_hashtags_map = {}   
        img_to_user_map = {}
        user_to_hashtags_map = {}
        # nodelists
        users_clusters_nodelist = {}
        hashtags_clusters_nodelist = {}
        # read input files
        with open("clusters.json",'r', encoding="utf8") as f:
            cluster = json.load(f)
        with open("metadata.json",'r', encoding="utf8") as f:
            metadata = json.load(f)
    
        imgToMetadata(metadata) # get metadata, e.g. users and hashtags
        generateClusterNodelist(cluster)
        generateUserMatrix()
        # generateHashtagToHashtag()
        clusterStatsCore(cluster)
        os.chdir('../')
