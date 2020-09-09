import json
import os
from fs.zipfs import ZipFS
from predict import predict_path, predict_image
from clump import clump
from PIL import Image
from pathlib import Path

def main():
    createMetadata = True
    source_file = "downloads.zip"
    source_meta = "../data/jane.txy.json"
    metadata = []
    if not createMetadata:
        input_file = os.path.join(os.getcwd(), source_meta)
        with open(input_file, 'r', encoding="utf8") as f:
            metadata = json.load(f)
    metadata_out, vgg16_predictions, vgg19_predictions = createMetadataAndModelFilters(source_file, createMetadata, metadata)
    clusterData = {}
    tree_vgg16 = clump(vgg16_predictions, metadata_out)
    tree_vgg19 = clump(vgg19_predictions, metadata_out)
    clusterData['tree_vgg16'] = tree_vgg16
    clusterData['tree_vgg19'] = tree_vgg19        
    writeJSONToFile("clusters.json", clusterData, 'w')

def createMetadataAndModelFilters(source_file, create_metadata, metadata):
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

if __name__ == "__main__":
    main()
