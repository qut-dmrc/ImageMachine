import json
import os
from fs.zipfs import ZipFS
from PIL import Image
from pprint import pformat
import pandas as pd
import numpy as np
import concurrent.futures
import zipfile


from predict import *
from clump import *
from tools import *

class ImageMachine:
    # class attributes 
    src_img_parent = os.path.join("input_data","images")
    src_meta_parent = os.path.join("input_data","metadata")
    dest_meta_parent = "output_data"
    dest_vis_parent = "../graph/static/"

    def download_images(self, src_meta, fieldname, dest_folder=None, size=None):
        """
        Download images from urls specified in a column of a csv file

        Args:
            source_meta (String): filename of type csv in which contains the urls of the images  
            fieldname (String): name of the column of urls
            media_folder (String, optional): the name of media folder in which the images will be stored. Defaults to same name as the source_meta
            size (int, optional): Number of urls to download from. Actual downloaded images might be less if images are removed. Defaults to None.
        """
        if not dest_folder: 
            dest_folder = src_meta.split('.')[0]
        meta_filepath = os.path.join(self.src_meta_parent, src_meta)
        
        # get urls
        df = pd.read_csv(meta_filepath)[fieldname]
        image_urls = np.array(df)[:size]
        media_folder_fullpath = os.path.join(self.src_img_parent, dest_folder, '')
        if not os.path.isdir(media_folder_fullpath): 
            os.mkdir(media_folder_fullpath) # create folder
        downloadImageFromURL(image_urls, media_folder_fullpath)

    def process_images(self, src_img, zip_folder="", src_meta=None, fieldname=None, datasize=None):
        """
        Process images stored in src_img, creating or converting src_meta into json format
        for image processing

        Args:
            src_img (String): Folder in which the images are stored 
            src_meta (String, optional): json or csv metadata file, with all converted into json metadata eventually
            fieldname (String, optional): fieldname of the urls to donwload the images from 
            datasize (int, optional): Limit of images to process. Defaults to None.
        """
        metadata = []
        ## reading metadata
        if src_meta:
            src_meta_abs = os.path.join(self.src_meta_parent, src_meta)
            if src_meta.split('.')[-1] == 'csv':
                print('CSV !')
                metadata = self.CSVtoJSON(src_meta_abs, src_img, fieldname)
        
            if src_meta.split('.')[-1] == 'json':
                print('JSON !')
                with open(src_meta_abs, 'r', encoding="utf8") as f:
                    metadata = json.load(f)
        # print(len(metadata))
        if zip_folder != "":
            metadata_out, vgg16_predictions, vgg19_predictions = self.readFromZip(os.path.join(self.src_img_parent, zip_folder), metadata) # read from zip
        else:
            metadata_out, vgg16_predictions, vgg19_predictions = self.readFromFolder(os.path.join(self.src_img_parent, src_img), metadata) # read from file folder
        # print(len(metadata_out))
        # print(len(vgg16_predictions))
        tree_vgg16 = clump(vgg16_predictions, metadata_out)
        tree_vgg19 = clump(vgg19_predictions, metadata_out)
        clusterData = {}
        clusterData['tree_vgg16'] = tree_vgg16
        clusterData['tree_vgg19'] = tree_vgg19
        writeJSONToFile("../graph/static/clusters.json", clusterData, 'w')
        # writeJSONToFile(".././graph/static/clusters_{}.json".format(data_size[i]), clusterData, 'w')
        # #     execution_time.append(time.time() - start_time)
        # #     print("Size: {} Seconds: {}".format(data_size[i], execution_time[i]))a

    def time_process_images(self):
        # # start_time = time.time()
        # # data_size = [100, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]
        # # execution_time = []
        # # for i in range(len(data_size)):
        #     # start_time = time.time()
        pass

    def CSVtoJSON(self, src_meta_abs, src_media, fieldname):
        df = pd.read_csv(src_meta_abs)
        header = df.columns.values
        metadata = []
        for i in range(df.shape[0]): # number of rows  shape:(row, column)
            row = df.iloc[i].to_dict()
            image_name = df.iloc[i][fieldname].split('/')[-1]
            image_path = os.path.join(src_media, image_name)
            self.appendToMetadata(image_path, metadata, row)
        writeJSONToFile(os.path.join(self.src_meta_parent,'metadata.json'), metadata, 'w')
        return metadata

    def readFromFolder(self, source_file, metadata):
        print("Normal folder")
        vgg16_predictions = []
        vgg19_predictions = []
        ## metadata provided  
        if metadata and len(metadata) > 0:
            # follow the sequence in metadatas
            print('Reading from metadata')
            new_metadata = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for node in metadata:
                    apath = node['_mediaPath'][0].replace('\\','/')
                    apath = apath.split('/')[-1] # filename only
                    if os.path.exists(os.path.join(source_file,apath)):
                        new_metadata.append(node)
                        executor.submit(self.predictImage, source_file, apath, vgg16_predictions, vgg19_predictions)
                metadata = new_metadata

        ## no metadata
        else:
            print('Creating metadata')
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for path, subdirs, files in os.walk(source_file):
                    for name in files:
                        folder = os.path.split(path)[-1]
                        apath = os.path.join(folder, name)
                        self.appendToMetadata(apath, metadata)
                        executor.submit(self.predictImage, path, name, vgg16_predictions, vgg19_predictions)
        writeJSONToFile(os.path.join(self.src_meta_parent,'metadata.json'), metadata, 'w')
        return metadata, vgg16_predictions, vgg19_predictions

    def readFromZip(self, source_file, metadata):
        print("Zip")
        vgg16_predictions = []
        vgg19_predictions = []
        # walk through zip file
        archive = ZipFS(os.path.join(os.getcwd(),source_file))
        ## metadata provided  
        if metadata and len(metadata) > 0:
            # follow the sequence in metadatas
            print('Reading from metadata')
            new_metadata = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for node in metadata:
                    apath = node['_mediaPath'][0].replace('\\','/')
                    if archive.exists(apath):
                        new_metadata.append(node)
                        executor.submit(self.predictImageInZip, archive, apath, vgg16_predictions, vgg19_predictions)
                metadata = new_metadata
        ## no metadata
        else:
            print('Creating metadata')
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for apath in archive.walk.files():
                    # apath: /folder/filename
                    apath = apath[1:]
                    # print(apath, type(apath)) #
                    ## create metadata
                    self.appendToMetadata(apath, metadata)
                    executor.submit(self.predictImageInZip, archive, apath, vgg16_predictions, vgg19_predictions)

        writeJSONToFile(os.path.join(self.src_meta_parent,'metadata.json'), metadata, 'w')
        return metadata, vgg16_predictions, vgg19_predictions

    @staticmethod
    def predictImageInZip(_zipfolder, apath, vgg16_predictions, vgg19_predictions):
        with _zipfolder.open(apath,'rb') as image:
            ## Model Filters
            output = predict_image(Image.open(image))
            vgg16_predictions.append(output[0])
            vgg19_predictions.append(output[1])

    @staticmethod
    def predictImage(_folder, apath, vgg16_predictions, vgg19_predictions):
        output = predict_image(Image.open(os.path.join(_folder,apath)))
        vgg16_predictions.append(output[0])
        vgg19_predictions.append(output[1])

    @staticmethod
    def appendToMetadata(apath, metadata, node_meta=None):
        _mediaPath = apath.replace('/','\\')
        # add to metadata
        filemeta = {}
        if not node_meta:
            node_meta = {}
        # img = Image.open(os.path.join(dirname,outfile))
        # node['byte_size'] = os.path.getsize(filepath)
        filemeta['node'] = node_meta
        filemeta['_mediaPath'] = [_mediaPath]
        metadata.append(filemeta)  
