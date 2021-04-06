from pathlib import Path
import concurrent.futures
import os
import json
from PIL import Image
from io import BytesIO

def main():
    all_clusters = [str(i) for i in Path('./input_data/images/clusters/').rglob('*.{}'.format('json'))]
    # convert xlsx to csv
    for c in all_clusters:
        dest_folder = c.split('.')[0]
        if not os.path.isdir(dest_folder): 
            os.mkdir(dest_folder) # create folder
        with open(c, 'r', encoding="utf8") as f:
            images_json = json.load(f)
            images = [i['_mediaPath'][0] for i in images_json]
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for image_path in images:
                    executor.submit(load_image, image_path, dest_folder)

def load_image(image_path, img_folder):
    img = Image.open(os.path.join('input_data/images',image_path))
    img.save(os.path.join(img_folder,image_path.split('\\')[-1]))

main()