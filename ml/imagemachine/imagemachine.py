import json
import os
from fs.zipfs import ZipFS
from PIL import Image
from pprint import pformat
import pandas as pd
import numpy as np
import concurrent.futures
import zipfile
import time
import requests
from io import BytesIO
import logging
import datetime
import sys

from .predict import *
from .clump import *
from .tools import *

class ImageMachine:
    # class attributes
    sys.setrecursionlimit(2**20)
    logging.basicConfig(filename='tracking.log', level=logging.DEBUG)
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
        Returns:
            [string]: Folder name that stores all the images
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
        logging.info('{}:Downloading images to {}'.format(datetime.datetime.now(), media_folder_fullpath))
        downloadImageFromURL(image_urls, media_folder_fullpath)
        return dest_folder

    def process_images(self, src_img=None, zip_folder="", src_meta=None, fieldname=None, datasize=None):
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
            metadata = self.get_metadata(src_meta, fieldname, src_img, datasize)
        if src_img:
            if zip_folder != "":
                metadata_out, vgg16_predictions, vgg19_predictions = self.readFromZip(os.path.join(self.src_img_parent, zip_folder), metadata, datasize) # read from zip
            else:
                metadata_out, vgg16_predictions, vgg19_predictions = self.readFromFolder(os.path.join(self.src_img_parent, src_img), metadata, datasize) # read from file folder
        else:
            # get images online
            metadata_out, vgg16_predictions, vgg19_predictions = self.readFromOnline(metadata, datasize)
        self.clustering(vgg16_predictions, vgg19_predictions, metadata_out, datasize)

    def time_process_images(self, sizeArray, src_img=None, zip_folder="", src_meta=None, fieldname=None):        
        execution_time = []
        for size in sizeArray:           
            start_time = time.time()
            logging.info('{}:Processing images in batches, Size: {}'.format(datetime.datetime.now(),size))
            self.process_images(src_img, zip_folder, src_meta, fieldname, size)
            exec_time = time.time()-start_time
            logging.info('{}:Total Execution Time: {}'.format(datetime.datetime.now(),exec_time))
            execution_time.append(exec_time)
        return execution_time

    def get_metadata(self, src_meta, fieldname=None, src_img=None, datasize=None):
        src_meta_abs = os.path.join(self.src_meta_parent, src_meta)
        if src_meta.split('.')[-1] == 'csv':
            logging.info('{}:Reading CSV metadata'.format(datetime.datetime.now()))
            metadata = self.CSVtoJSON(src_meta_abs, fieldname, src_img, datasize)
    
        if src_meta.split('.')[-1] == 'json':
            logging.info('{}:Reading JSON metadata'.format(datetime.datetime.now()))
            with open(src_meta_abs, 'r', encoding="utf8") as f:
                metadata = json.load(f)
        return metadata

    def CSVtoJSON(self, src_meta_abs, fieldname, src_media=None, datasize=None):
        logging.info('{}:Converting CSV to JSON'.format(datetime.datetime.now()))
        df = pd.read_csv(src_meta_abs, dtype='str')
        header = df.columns.values
        if datasize:
            length = min(df.shape[0], datasize)
        else:
            length = df.shape[0]
        metadata = []
        for i in range(length): # number of rows shape:(row, column)
            row = df.iloc[i].to_dict()
            url = None
            if src_media:
                image_name = df.iloc[i][fieldname].split('/')[-1]
                image_path = os.path.join(src_media, image_name)
                url = df.iloc[i][fieldname]
            else:
                image_path = df.iloc[i][fieldname]
            self.appendToMetadata(image_path, metadata, row, url)
        
        # writeJSONToFile(os.path.join(self.src_meta_parent,'metadata.json'), metadata, 'w')
        return metadata

    def readFromOnline(self, metadata, datasize=None):
        logging.info('{}:Requesting images through urls...'.format(datetime.datetime.now()))
        vgg16_predictions = []
        vgg19_predictions = []
        
        newmeta_filename = "metadata_{}.json".format(datasize)
        vgg16_filename = "vgg16_{}.npy".format(datasize)
        vgg19_filename = "vgg19_{}.npy".format(datasize)
        # follow the sequence in metadatas
        new_metadata = []
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for node in metadata:
                url = node['_mediaPath'][0].replace('\\','/')
                response = requests.get(url)
                filename = url.split('/')[-1]
                if response:
                    img = Image.open(BytesIO(response.content))
                    executor.submit(self.predictImageOnline, img, new_metadata, node, vgg16_predictions, vgg19_predictions)
                    if datasize:
                        datasize -= 1
                        if datasize == 0:
                            break
            metadata = new_metadata
        exec_time = time.time()-start_time
        logging.info('{}:Finished processing images. Excecution time: {}'.format(datetime.datetime.now(), exec_time))
        writeJSONToFile(os.path.join(self.src_meta_parent,newmeta_filename), metadata, 'w')
        np.save(os.path.join(self.src_meta_parent,vgg16_filename), vgg16_predictions)
        np.save(os.path.join(self.src_meta_parent,vgg19_filename), vgg19_predictions)
        return metadata, vgg16_predictions, vgg19_predictions

    def readFromFolder(self, source_file, metadata, datasize=None):
        logging.info('{}:Reading images from folder...'.format(datetime.datetime.now()))
        vgg16_predictions = []
        vgg19_predictions = []
        
        newmeta_filename = "metadata_{}.json".format(datasize)
        vgg16_filename = "vgg16_{}.npy".format(datasize)
        vgg19_filename = "vgg19_{}.npy".format(datasize)
        start_time = time.time()
        ## metadata provided  
        if metadata and len(metadata) > 0:
            # follow the sequence in metadatas
            logging.info('{}:Looping through metadata...'.format(datetime.datetime.now()))
            new_metadata = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for node in metadata:
                    apath = node['_mediaPath'][0].replace('\\','/')
                    apath = apath.split('/')[-1] # filename only
                    if os.path.exists(os.path.join(source_file,apath)):
                        # new_metadata.append(node)
                        # executor.submit(self.predictImage, source_file, apath, vgg16_predictions, vgg19_predictions)
                        executor.submit(self.predictImage, source_file, apath, new_metadata, node, vgg16_predictions, vgg19_predictions, True)
                        if datasize:
                            datasize -= 1
                            if datasize == 0:
                                break
                metadata = new_metadata
            # # correct version, non concurrent
            # for node in metadata:
            #     apath = node['_mediaPath'][0].replace('\\','/')
            #     apath = apath.split('/')[-1] # filename only
            #     if os.path.exists(os.path.join(source_file,apath)):
            #         new_metadata.append(node)
            #         output = predict_image(Image.open(os.path.join(source_file,apath)))
            #         vgg16_predictions.append(output[0])
            #         vgg19_predictions.append(output[1])
            #         if datasize:
            #             datasize -= 1
            #             if datasize == 0:
            #                 break
            # metadata = new_metadata
        ## no metadata
        else:
            logging.info('{}:No metadata provided, creating new metadata...'.format(datetime.datetime.now()))
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for path, subdirs, files in os.walk(source_file):
                    for name in files:
                        folder = os.path.split(path)[-1]
                        node = os.path.join(folder, name)
                        # self.appendToMetadata(node, metadata)
                        # executor.submit(self.predictImage, path, name, vgg16_predictions, vgg19_predictions)
                        executor.submit(self.predictImage, path, name, metadata, node, vgg16_predictions, vgg19_predictions, False)
                        if datasize:
                            datasize -= 1
                            if datasize == 0:
                                break
        exec_time = time.time() - start_time
        logging.info('{}:Finished processing images. Excecution time: {}'.format(datetime.datetime.now(), exec_time))
        writeJSONToFile(os.path.join(self.src_meta_parent,newmeta_filename), metadata, 'w')
        np.save(os.path.join(self.src_meta_parent,vgg16_filename), vgg16_predictions)
        np.save(os.path.join(self.src_meta_parent,vgg19_filename), vgg19_predictions)
        return metadata, vgg16_predictions, vgg19_predictions

    def readFromZip(self, source_file, metadata, datasize=None):
        logging.info('{}:Reading images from zip folder...'.format(datetime.datetime.now()))
        vgg16_predictions = []
        vgg19_predictions = []
        # walk through zip file
        archive = ZipFS(os.path.join(os.getcwd(),source_file))
        newmeta_filename = "metadata_{}.json".format(datasize)
        vgg16_filename = "vgg16_{}.npy".format(datasize)
        vgg19_filename = "vgg19_{}.npy".format(datasize)
        start_time = time.time()
        ## metadata provided  
        if metadata and len(metadata) > 0:
            # follow the sequence in metadatas
            logging.info('{}:Looping through metadata...'.format(datetime.datetime.now()))
            new_metadata = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for node in metadata:
                    apath = node['_mediaPath'][0].replace('\\','/')
                    if archive.exists(apath):
                        # new_metadata.append(node)
                        executor.submit(self.predictImageInZip, archive, apath, new_metadata, node, vgg16_predictions, vgg19_predictions, True)
                        if datasize:
                            datasize -= 1
                            if datasize == 0:
                                break
                metadata = new_metadata
        ## no metadata
        else:
            logging.info('{}:No metadata provided, creating new metadata...'.format(datetime.datetime.now()))
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for apath in archive.walk.files():
                    # apath: /folder/filename
                    apath = apath[1:]
                    # print(apath, type(apath)) #
                    ## create metadata
                    # self.appendToMetadata(apath, metadata)
                    executor.submit(self.predictImageInZip, archive, apath, metadata, apath, vgg16_predictions, vgg19_predictions, False)
                    if datasize:
                        datasize -= 1
                        if datasize == 0:
                            break
        exec_time = time.time() - start_time
        logging.info('{}:Finished processing images. Excecution time: {}'.format(datetime.datetime.now(), exec_time))
        writeJSONToFile(os.path.join(self.src_meta_parent,newmeta_filename), metadata, 'w')
        np.save(os.path.join(self.src_meta_parent,vgg16_filename), vgg16_predictions)
        np.save(os.path.join(self.src_meta_parent,vgg19_filename), vgg19_predictions)
        return metadata, vgg16_predictions, vgg19_predictions

    def clustering(self, vgg16_predictions, vgg19_predictions, metadata_out, datasize):
        if not isinstance(vgg16_predictions,list):
            vgg16_predictions = np.load(os.path.join(self.src_meta_parent, vgg16_predictions))
        if not isinstance(vgg19_predictions,list):
            vgg19_predictions = np.load(os.path.join(self.src_meta_parent, vgg19_predictions))
        if not isinstance(metadata_out,list):
            metadata_out = self.get_metadata(metadata_out, datasize)
        start_time = time.time()
        logging.info('{}:Clustering images'.format(datetime.datetime.now()))
        tree_vgg16 = clump(vgg16_predictions, metadata_out, "vgg16")
        tree_vgg19 = clump(vgg19_predictions, metadata_out, "vgg19")
        exec_time = time.time()-start_time
        clusterData = {}
        clusterData['tree_vgg16'] = tree_vgg16
        clusterData['tree_vgg19'] = tree_vgg19
        writeJSONToFile("../graph/static/clusters_{}.json".format(datasize), clusterData, 'w')
        logging.info('{}:Clusters saved to static folder. Clustering time: {}'.format(datetime.datetime.now(), exec_time))

    def predictImageInZip(self, _zipfolder, apath, metadata, node, vgg16_predictions, vgg19_predictions, isNode):
        with _zipfolder.open(apath,'rb') as image:
            ## Model Filters
            output = predict_image(Image.open(image))
            vgg16_predictions.append(output[0])
            vgg19_predictions.append(output[1])
            if isNode:
                metadata.append(node)
            else:
                self.appendToMetadata(node, metadata)

    def predictImage(self, _folder, apath, metadata, node, vgg16_predictions, vgg19_predictions, isNode):
        output = predict_image(Image.open(os.path.join(_folder,apath)))
        vgg16_predictions.append(output[0])
        vgg19_predictions.append(output[1])
        if isNode:
            metadata.append(node)
        else:
            self.appendToMetadata(node, metadata)

    def predictImageOnline(self, img, metadata, node, vgg16_predictions, vgg19_predictions):
        output = predict_image(img)
        vgg16_predictions.append(output[0])
        vgg19_predictions.append(output[1])
        metadata.append(node)

    @staticmethod
    def appendToMetadata(apath, metadata, node_meta=None, url=None):
        _mediaPath = apath.replace('/','\\')
        # add to metadata
        filemeta = {}
        if not node_meta:
            node_meta = {}
        # img = Image.open(os.path.join(dirname,outfile))
        # node['byte_size'] = os.path.getsize(filepath)
        filemeta['node'] = node_meta
        filemeta['_mediaPath'] = [_mediaPath]
        if url:
            filemeta['_mediaPath'] = [url]
        metadata.append(filemeta)  
