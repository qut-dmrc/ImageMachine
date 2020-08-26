from PIL import Image
from PIL.ExifTags import TAGS
import os, sys
import datetime as dt
import json
import pandas as pd

for dirname, subdirs, images in os.walk("downloads\hashtag\instagood"):
    metadata = []
    for inImg in images:
        ## convert image types
        f, e = os.path.splitext(inImg)
        outImg = f + ".jpg"
        if inImg != outImg:
            try:
                os.rename(os.path.join(dirname,inImg),os.path.join(dirname,outImg))
            except OSError:
                print("cannot convert", inImg)
        filemeta = {}
        node = {}
        # img = Image.open(os.path.join(dirname,outfile))
        filepath = os.path.join(dirname,outImg)
        node['created_at_timestamp'] = os.path.getctime(filepath)
        node['modified_at_timestamp'] = os.path.getmtime(filepath)
        # node['byte_size'] = os.path.getsize(filepath)
        filemeta['node'] = node
        filemeta['_mediaPath'] = os.path.join(dirname, os.path.basename(inImg))
        metadata.append(filemeta)
    data = json.dumps(metadata)
    f = open(r'output.json','w')
    f.write(data)

# read from json file and add new info
with open(os.path.join(os.getcwd(), "output.json"), 'r', encoding='utf8') as read_file:
    data = json.load(read_file)
    for item in data:
        path = os.path.join(os.getcwd(),item['_mediaPath'])
        img = Image.open(path)
        width = img.size[0]
        height = img.size[1]
        item['node']['dimensions'] = {'width': width, 'height': height}
data = json.dumps(data)
f = open(r'output.json','w')
f.write(data)


# timestamp = data[0]['shortcode_media']['taken_at_timestamp']
# print(dt.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'))
    

        