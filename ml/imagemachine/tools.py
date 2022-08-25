import json
import csv
import concurrent.futures
import requests
from PIL import Image
from io import BytesIO
import re

def writeJSONToFile(filename, data, mode):
    data = json.dumps(data)
    f = open(filename, mode)
    f.write(data)
    f.close()

def writeCSVToFile(filename, data, mode):
    f = open(filename, mode, encoding='utf-8', newline='')
    csv_file = csv.writer(f)
    csv_file.writerows(data)
    f.close()

def flatten_data(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            for a in x:
                flatten(a, name + '_')
        else:
            if name[:-1] in out.keys():
                if type(out[name[:-1]]) is not list:
                    out[name[:-1]] = [out[name[:-1]]]
                out[name[:-1]].append(str(x))
            else:
                out[name[:-1]] = x

    flatten(y)
    return out

def JSONtoCSV(metadata):
    map = {}
    titles = list(flatten_data(metadata[0]).keys()) # get the col titles
    for idx, datum in enumerate(metadata):
        flattened = flatten_data(datum)
        keys = list(flattened.keys())
        for key in keys:
            if key not in map.keys():
                prev_rows = ['']*len(metadata) # create an empty list for a new key that wasn't included in previous row 
                map[key] = prev_rows
            map[key][idx] = flattened[key]

    title = list(map.keys())
    values = list(map.values())
    rows = []
    rows.append(title)
    for i in range(len(metadata)):
        rows.append([value[i] for value in values])
    return rows
 
'''
Images is a nunpy array of urls of which the images are stored
'''
def downloadImageFromURL(images, dest_folder):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for url in images:
            executor.submit(load_url, url, dest_folder)

def load_url(url, img_folder):
    response = requests.get(url)
    filename = url.split('/')[-1]
    if response:
        img = Image.open(BytesIO(response.content))
        img.save(img_folder+filename)

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

def parseFilePath(filePath):
    return re.sub(r"\\+",'/',filePath)
