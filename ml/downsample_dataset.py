import json
import os
from PIL import Image

## modify
datasize = 200 
fname = "productivity"
##

metadata_path = "input_data/metadata/{}.json"
image_folder_path = "input_data/images/{}/"
with open(metadata_path.format(fname), 'r', encoding="utf8") as f:
    metadata = json.load(f)

with open(metadata_path.format(fname+"_"+str(datasize)), 'w') as f:
    f.write(json.dumps(metadata[0:datasize]))

# create new image folder
if not os.path.exists(image_folder_path.format(fname+"_200")):
    os.mkdir(image_folder_path.format(fname+"_200"))

metadata = metadata[0:datasize]
for datum in metadata:
    img_url = ""
    if 'image_versions2' in datum:
        img_url = datum['image_versions2']['candidates'][0]['url']
    else:
        img_url = datum['carousel_media'][0]['image_versions2']['candidates'][0]['url']
    img_url = img_url.split('?')[0].split('/')[-1].split('.')[0]+".jpg"
    img = Image.open(os.path.join(image_folder_path.format(fname),img_url))
    img.save(os.path.join(image_folder_path.format(fname+"_200"),img_url))