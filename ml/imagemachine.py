import json
import os
from fs.zipfs import ZipFS
from predict import predict_path, predict_image
from clump import clump
from PIL import Image

def main():
    hasMetadata = False
    if not hasMetadata:
        metadata = []
        metadataFilename = "metadata_created.json"
    else:
        metadataFilename = "metadata_created.json"
        input_file = os.path.join(os.getcwd(), metadataFilename)
        with open(input_file, 'r', encoding="utf8") as f:
            metadata = json.load(f)
    vgg16_predictions = []
    vgg19_predictions = []
    # walk through zip file, TODO: metadata provided
    with ZipFS(os.path.join(os.getcwd(),"downloads.zip")) as archive:
        for apath in archive.walk.files():
            if not hasMetadata:
                ## create metadata
                _mediaPath = apath[1:].replace('/','\\\\')
                # add to metadata
                filemeta = {}
                node = {}
                # img = Image.open(os.path.join(dirname,outfile))
                # node['byte_size'] = os.path.getsize(filepath)
                filemeta['node'] = node
                filemeta['_mediaPath'] = [_mediaPath]
                metadata.append(filemeta)
                writeJSONToFile(metadataFilename, metadata, 'w')
    #         with archive.open(apath,'rb') as file:
    #             ## Clustering
    #             output = predict_image(Image.open(file))
    #             vgg16_predictions.append(output[0])
    #             vgg19_predictions.append(output[1])
    # clusterData = {}
    # tree_vgg16 = clump(vgg16_predictions, metadata)
    # tree_vgg19 = clump(vgg19_predictions, metadata)
    # clusterData['tree_vgg16'] = tree_vgg16
    # clusterData['tree_vgg19'] = tree_vgg19        
    # writeJSONToFile("clusters.json", clusterData, 'w')


def writeJSONToFile(filename, data, mode):
    data = json.dumps(data)
    f = open(filename, mode)
    f.write(data)

if __name__ == "__main__":
    main()
