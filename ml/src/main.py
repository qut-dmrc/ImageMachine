import json
import os
from fs.zipfs import ZipFS
from PIL import Image
from pathlib import Path
from io import BytesIO
import requests
import pandas as pd
import numpy as np
import time
import concurrent.futures
from predict import predict_path, predict_image
from clump import clump

def main():
    INPUT_FOLDER_IMG = "input_data/images/downloads/memes/"
    INPUT_FOLDER_METADATA = "input_data/metadata"
    OUTPUT_FOLDER = "output_data"
    ## user input
    createMetadata = True
    source_file = "downloads.zip"
    # source_meta = "jane.txy.json"
    source_meta = "2020-02_image_urls_by_day.csv"
    url_fieldname = "media_url"
    # source_file_abs = os.path.join(INPUT_FOLDER_IMG, source_file)

    # download images
    source_meta_abs = os.path.join(INPUT_FOLDER_METADATA, source_meta)
    downloadImageFromURLinCSV(source_meta_abs, url_fieldname, INPUT_FOLDER_IMG)

    metadata = []
    if not createMetadata:
        input_file = os.path.join(os.getcwd(), os.path.join(INPUT_FOLDER_METADATA, source_meta))
        with open(input_file, 'r', encoding="utf8") as f:
            metadata = json.load(f)
    
    # # start_time = time.time()
    # # data_size = [100, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]
    # # execution_time = []
    # # for i in range(len(data_size)):
    #     # start_time = time.time()
    # metadata_out, vgg16_predictions, vgg19_predictions = readFromCSVURL(100, source_meta, createMetadata, metadata)
    # # metadata_out, vgg16_predictions, vgg19_predictions = readFromZip(source_file_abs, createMetadata, metadata) # read from zip
    # tree_vgg16 = clump(vgg16_predictions, metadata_out)
    # tree_vgg19 = clump(vgg19_predictions, metadata_out)
    # clusterData = {}
    # clusterData['tree_vgg16'] = tree_vgg16
    # clusterData['tree_vgg19'] = tree_vgg19        
    # writeJSONToFile(".././graph/static/clusters.json", clusterData, 'w')
    # # writeJSONToFile(".././graph/static/clusters_{}.json".format(data_size[i]), clusterData, 'w')
    # #     execution_time.append(time.time() - start_time)
    # #     print("Size: {} Seconds: {}".format(data_size[i], execution_time[i]))

# def readFromCSVURL(data_size, src_metadata, create_metadata, metadata):
#     vgg16_predictions = []
#     vgg19_predictions = []
#     df = pd.read_csv(src_metadata)['media_url']
#     images = np.array(df)
#     dir_path = "downloads/"
#     for i in range(len(images)):
#         # add to metadata
#         filemeta = {}
#         node = {}
#         # img = Image.open(os.path.join(dirname,outfile))
#         # node['byte_size'] = os.path.getsize(filepath)
#         filemeta['node'] = node
#         filemeta['_mediaPath'] = [images[i]]
#         metadata.append(filemeta)
#         response = requests.get(images[i])
#         if not response.content:
#             continue
#         output = predict_image(Image.open(BytesIO(response.content)))
#         vgg16_predictions.append(output[0])
#         vgg19_predictions.append(output[1])
#         if i == data_size:
#             break;           

#     if create_metadata:
#         writeJSONToFile('metadata_{}.json'.format(data_size), metadata, 'w')
#     return metadata, vgg16_predictions, vgg19_predictions

def readFromZip(source_file, create_metadata, metadata):
    vgg16_predictions = []
    vgg19_predictions = []
    # walk through zip file
    with ZipFS(os.path.join(os.getcwd(),source_file)) as archive:
       ## metadata provided  
        if len(metadata) > 0:
            # follow the sequence in metadatas
            for node in metadata:
                apath = node['_mediaPath'][0].replace('\\','/')
                with archive.open(apath,'rb') as file:
                    output = predict_image(Image.open(file))
                    vgg16_predictions.append(output[0])
                    vgg19_predictions.append(output[1])
        ## no metadata
        else:
            for apath in archive.walk.files():
                # print(apath, type(apath))
                ## create metadata
                if create_metadata:
                    _mediaPath = apath[1:].replace('/','\\')
                    # add to metadata
                    filemeta = {}
                    node = {}
                    # img = Image.open(os.path.join(dirname,outfile))
                    # node['byte_size'] = os.path.getsize(filepath)
                    filemeta['node'] = node
                    filemeta['_mediaPath'] = [_mediaPath]
                    metadata.append(filemeta)

                with archive.open(apath,'rb') as file:
                    ## Model Filters
                    output = predict_image(Image.open(file))
                    vgg16_predictions.append(output[0])
                    vgg19_predictions.append(output[1])
                
    if create_metadata:
        writeJSONToFile('metadata.json', metadata, 'w')
    return metadata, vgg16_predictions, vgg19_predictions


def writeJSONToFile(filename, data, mode):
    data = json.dumps(data)
    f = open(filename, mode)
    f.write(data)

def load_url(url, img_folder):
    response = requests.get(url)
    filename = url.split('/')[-1]
    if response:
        img = Image.open(BytesIO(response.content))
        img.save(img_folder+filename)

def downloadImageFromURLinCSV(src_metadata, fieldname, img_folder):
    df = pd.read_csv(src_metadata)[fieldname]
    images = np.array(df)[7223:1000001]
    #images = np.array(df)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for url in images:
            executor.submit(load_url, url, img_folder)
    

if __name__ == "__main__":
    main()
