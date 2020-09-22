import json
import concurrent.futures
import requests
from PIL import Image
from io import BytesIO

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
