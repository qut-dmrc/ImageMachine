import os
import json
import csv
import re
import numpy as np

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
            if _element == None:
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

root_folder = "datasets"
for _,dirs,_ in os.walk(root_folder):
    os.chdir(os.path.join(os.getcwd(),"datasets"))
    for _dir in dirs:
        print(_dir)
        img_to_hashtags_map = {}
        hashtag_by_hashtag_matrix = {}
        os.chdir(os.path.join(".",_dir))
        with open("metadata.json",'r', encoding="utf8") as f:
            metadata = json.load(f)
        imgToHashtags(metadata) # img to tags
        os.chdir('../')
