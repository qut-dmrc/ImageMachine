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

from tensorflow.python.keras.applications import vgg16

# clustering and dimensionality reduction
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import scipy.spatial.distance as dist

from .predict import predict_image
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

    def __init__(self, pca_dimensions=10, k_clusters=16):
        self.random_seed = 1
        self.pca_dimensions = pca_dimensions
        self.k_clusters = k_clusters
        self.tree = {}
        self.tree['name'] = 'root'
        self.tree['centroid'] = ''
        self.tree['dist_to_centroid'] = ''
        self.tree['children'] = {}
        self.image_to_features_map = {} # {'image1' -> [vgg16,vgg19], 'image2' -> [vgg16,vgg19]}
        self.image_to_metadata_map = {}

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
                metadata_out, vgg16_predictions, vgg19_predictions= self.readFromFolder(os.path.join(self.src_img_parent, src_img), metadata, datasize) # read from file folder
        else:
            # get images online
            metadata_out, vgg16_predictions, vgg19_predictions = self.readFromOnline(metadata, datasize)
        # vgg16_predictions [array([1 2 3 ], dtype=float32),array([1 2 3], dtype=float32)]
        # vgg16_predictions = np.array(vgg16_predictions) [[1,2,3],[1,2,3],...,[1,2,3]]
        # x = self.dimensionality_reduce(np.array(vgg16_predictions))
        # self.tree['children'] = self.cluster_files(x, np.array(list(self.image_to_features_map.keys())))
        # self.tree['children'] = self.get_features_dataset_from_images(self.tree['children'])
        # print(self.tree)
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
        # vgg16_predictions = []
        # vgg19_predictions = []
        
        newmeta_filename = "metadata_{}.json".format(datasize)
        vgg16_filename = "vgg16_{}.npy".format(datasize)
        vgg19_filename = "vgg19_{}.npy".format(datasize)
        start_time = time.time()
        ## metadata provided  
        if metadata and len(metadata) > 0:
            # follow the sequence in metadatas
            logging.info('{}:Looping through metadata...'.format(datetime.datetime.now()))
            # new_metadata = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for node in metadata:
                    apath = node['_mediaPath'][0].replace('\\','/')
                    apath = apath.split('/')[-1] # filename only
                    if os.path.exists(os.path.join(source_file,apath)):
                        # new_metadata.append(node)
                        # executor.submit(self.predictImage, source_file, apath, vgg16_predictions, vgg19_predictions)
                        executor.submit(self.predictImage, source_file, apath, node, True)
                        if datasize:
                            datasize -= 1
                            if datasize == 0:
                                break
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
                        executor.submit(self.predictImage, path, name, node, False)
                        if datasize:
                            datasize -= 1
                            if datasize == 0:
                                break
        exec_time = time.time() - start_time
        logging.info('{}:Finished processing images. Excecution time: {}'.format(datetime.datetime.now(), exec_time))
        
        # metadata = list(self.image_to_metadata_map.values())
        vgg16_predictions = [feature[0] for feature in self.image_to_features_map.values()]
        vgg19_predictions = [feature[1] for feature in self.image_to_features_map.values()]
        writeJSONToFile(os.path.join(self.src_meta_parent,newmeta_filename), self.image_to_metadata_map, 'w')
        np.save(os.path.join(self.src_meta_parent,vgg16_filename), vgg16_predictions)
        np.save(os.path.join(self.src_meta_parent,vgg19_filename), vgg19_predictions)
        np.savez(os.path.join(self.src_meta_parent,"img_to_feature.npz"), **self.image_to_features_map)
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

    def dimensionality_reduce(self, features_list):
        # Dimensionality reduction using Pricipal Component Analysis
        pca = PCA(n_components=self.pca_dimensions, random_state=self.random_seed)
        pca.fit(features_list) # Find out best components to use
        x = pca.transform(features_list) # Transform the dataset to those components
    
        return x

    # Deals with the initial dataset (dataset --> files + clusters)
    def cluster_files(self, dataset, image_filenames):

        kmeans = self.kmeans_clustering(dataset)

        [groups,root_centroid_img, root_img_to_centroid_dist] = self.image_to_cluster_file(dataset, image_filenames, kmeans, True)
        return [groups,root_centroid_img, root_img_to_centroid_dist]

    def kmeans_clustering(self, dataset):
        kmeans = KMeans(n_clusters = self.k_clusters, random_state=self.random_seed) # Create clusterer
        kmeans.fit(dataset) # Train clusterer on current data
        kmeans.predict(dataset) # Apply clusterer on current data

        return kmeans
    
    def image_to_cluster_file(self, dataset, image_filenames, kmeans, root=False):
        groups = {} # Essentially create a dictionary with cluster ids as the keys and image filenames as the values
        # group_centroid_image = {}
        
        # for file, cluster in zip(image_filenames, kmeans.labels_): # Map the image_filename to its label
        if root:
            total_centroid = [0] * len(kmeans.cluster_centers_[1])
        for i in range(len(image_filenames)):
            file = image_filenames[i]
            cluster = int(kmeans.labels_[i])
            vector = dataset[i]
            cluster_centroid = kmeans.cluster_centers_[cluster]
            if root:
                total_centroid = [sum(x) for x in zip(total_centroid,cluster_centroid)]
            dist_to_centroid = dist.euclidean(vector,cluster_centroid)
            
            if cluster not in groups.keys():
                groups[cluster] = {} # Create new key
                groups[cluster]['name'] = cluster
                groups[cluster]['centroid'] = file
                groups[cluster]['dist_to_centroid'] = dist_to_centroid
                groups[cluster]['data'] = []
                groups[cluster]['children'] = []

                # group_centroid_image[cluster].append((file, ))
            groups[cluster]['data'].append(file) # Append value to key
            if dist_to_centroid < groups[cluster]['dist_to_centroid']:
                groups[cluster]['centroid'] = file
                groups[cluster]['dist_to_centroid'] = dist_to_centroid
        if root:
            average_centroid = [x/len(image_filenames) for x in total_centroid]
            clusters_avg_centroid_diff = [dist.euclidean(x,average_centroid) for x in kmeans.cluster_centers_]
            root_centroid_index = clusters_avg_centroid_diff.index(min(clusters_avg_centroid_diff))
            [root_centroid_img, root_centroid_dist] = [groups[root_centroid_index]['centroid'],groups[root_centroid_index]['dist_to_centroid']]
        else:
            [root_centroid_img, root_centroid_dist] = [None, None]
        
        return [groups, root_centroid_img, root_centroid_dist]

    # Gets image from fileName and returns the feature set of the image
    def get_features_dataset_from_images(self, childrenToProcess):
        for cluster_index in range(len(list(childrenToProcess.keys()))):
            if len(childrenToProcess[cluster_index]['data']) <= self.k_clusters: # If less than K images, this is the end of the cluster branch (leaf)
                # add leaves to children as nodes
                for child in childrenToProcess[cluster_index]['data']:
                    node = {} # Create new key
                    node['name'] = 'leaf'
                    node['centroid'] = child
                    node['dist_to_centroid'] = 0
                    node['data'] = [child]
                    node['children'] = []
                    childrenToProcess[cluster_index]['children'].append(node)
        # for fileName in futureFileSet:
            else:
                # print('Filename',fileName)
                data = {}
                # image_filenames = []
                # fileHandle = open(fileName, "r")
                # fileData = fileHandle.read()
                # files = fileData.split("\n")[:-1]
                files = childrenToProcess[cluster_index]['data']
                data = { file: self.image_to_features_map[file][0] for file in files }
                
                image_filenames = np.array(list(data.keys()))
                features_list = np.array(list(data.values()))
                # features_list = features_list.reshape(-1,features_list.shape[-1])
                x = self.dimensionality_reduce(features_list)

                kmeans = self.kmeans_clustering(x)
                [childrenToProcess[cluster_index]['children'],_,_] = self.image_to_cluster_file(x, image_filenames, kmeans)
                childrenToProcess[cluster_index]['children'] = self.get_features_dataset_from_images(childrenToProcess[cluster_index]['children'])
                
        return list(childrenToProcess.values())

    def clustering(self, vgg16_predictions, vgg19_predictions, metadata_out, datasize, img_to_feature_file=None):
        if not isinstance(vgg16_predictions,list):
            vgg16_predictions = np.load(os.path.join(self.src_meta_parent, vgg16_predictions))
        if not isinstance(vgg19_predictions,list):
            vgg19_predictions = np.load(os.path.join(self.src_meta_parent, vgg19_predictions))
        if img_to_feature_file:
            self.image_to_features_map = dict(np.load(os.path.join(self.src_meta_parent, img_to_feature_file)))
        if not isinstance(metadata_out,list):
            metadata_out = self.get_metadata(metadata_out, datasize)
        start_time = time.time()
        logging.info('{}:Clustering images'.format(datetime.datetime.now()))
        # tree_vgg16 = clump(vgg16_predictions, metadata_out, "vgg16")
        # tree_vgg19 = clump(vgg19_predictions, metadata_out, "vgg19")
        x = self.dimensionality_reduce(np.array(vgg16_predictions))
        [self.tree['children'],root_centroid_img, root_centroid_img_dist] = self.cluster_files(x, np.array(list(self.image_to_features_map.keys()))) #first iteration
        self.tree['centroid'] = root_centroid_img
        self.tree['dist_to_centroid'] = root_centroid_img_dist
        self.tree['children'] = self.get_features_dataset_from_images(self.tree['children']) # subgroups
        exec_time = time.time()-start_time
        # clusterData = {}
        # clusterData['tree_vgg16'] = tree_vgg16
        # clusterData['tree_vgg19'] = tree_vgg19
        writeJSONToFile("../graph/static/clusters.json", self.tree, 'w')
        logging.info('{}:Clusters saved to static folder. Clustering time: {}'.format(datetime.datetime.now(), exec_time))

    def predictImageInZip(self, _zipfolder, apath, metadata, node, vgg16_predictions, vgg19_predictions, isNode):
        with _zipfolder.open(apath,'rb') as image:
            ## Model Filters
            output = predict_image(image)
            vgg16_predictions.append(output[0])
            vgg19_predictions.append(output[1])
            if isNode:
                metadata.append(node)
            else:
                self.appendToMetadata(node, metadata)

    def predictImage(self, _folder, apath, node, isNode):
        output = predict_image(os.path.join(_folder,apath))
        # vgg16_predictions.append(output[0])
        # vgg19_predictions.append(output[1])
        self.image_to_features_map[os.path.join(_folder,apath)] = output
        
        if isNode:
            # metadata.append(node)
            self.image_to_metadata_map[os.path.join(_folder,apath)] = node
        else:
            # self.appendToMetadata(node, metadata)
            filemeta = {}
            filemeta['node'] = {}
            filemeta['_mediaPath'] = [node]
            self.image_to_metadata_map[os.path.join(_folder,apath)] = filemeta

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
