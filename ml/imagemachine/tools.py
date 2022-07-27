import json
import concurrent.futures
import requests
from PIL import Image
from io import BytesIO
import re

def writeJSONToFile(filename, data, mode):
    data = json.dumps(data)
    f = open(filename, mode)
    f.write(data)

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
