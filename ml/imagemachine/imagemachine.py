import json
import csv
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
import re
# from pathlib import Path
import matplotlib.pyplot as plt


# clustering and dimensionality reduction
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import scipy.spatial.distance as dist
from keras.preprocessing.image import load_img

from .predict import predict_image, generateHeatmap
from .clump import *
from .tools import *

class ImageMachine:
    # class attributes
    sys.setrecursionlimit(2**20)
    logging.basicConfig(filename='tracking.log', level=logging.DEBUG)
    src_img_parent = os.path.join("input_data","images")
    src_meta_parent = os.path.join("input_data","metadata")
    dest_meta_parent = "./"
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
        self.image_to_heatmap_map = {}
        self.img_to_hashtags_map = {}
        self.cluster_hashtag_map = {}
        self.hashtags = []
        self.hasMetadata = False

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
            # check if metadata has _mediaPath attribute, specifically for metadata collected from instagram
            if '_mediaPath' not in metadata[0]:
                processed_data = []
                for datum in metadata:
                    new_datum = {}
                    img_url = ''
                    if 'image_versions2' in datum:
                        img_url = datum['image_versions2']['candidates'][0]['url']
                    else:
                        img_url = datum['carousel_media'][0]['image_versions2']['candidates'][0]['url']
                    img_url = img_url.split('?')[0].split('/')[-1].split('.')[0]+".jpg"
                    # read from zip
                    datum['shortcode'] = img_url
                    new_datum['node'] = datum
                    new_datum['_mediaPath'] = [img_url]
                    processed_data.append(new_datum)
                metadata = processed_data
        if src_img:
            if zip_folder != "":
                metadata_out, vgg16_predictions, vgg19_predictions = self.readFromZip(os.path.join(self.src_img_parent, zip_folder), metadata, datasize) # read from zip
            else:
                self.readFromFolder(os.path.join(self.src_img_parent, src_img), metadata, datasize) # read from file folder
        else:
            # get images online
            metadata_out, vgg16_predictions, vgg19_predictions = self.readFromOnline(metadata, datasize)
        # vgg16_predictions [array([1 2 3 ], dtype=float32),array([1 2 3], dtype=float32)]
        # vgg16_predictions = np.array(vgg16_predictions) [[1,2,3],[1,2,3],...,[1,2,3]]
        # x = self.dimensionality_reduce(np.array(vgg16_predictions))
        # self.tree['children'] = self.cluster_files(x, np.array(list(self.image_to_features_map.keys())))
        # self.tree['children'] = self.get_features_dataset_from_images(self.tree['children'])
        # print(self.tree)
        self.clustering()

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
        self.hasMetadata = True     
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
        writeJSONToFile(os.path.join(self.dest_meta_parent,newmeta_filename), metadata, 'w')
        np.save(os.path.join(self.src_meta_parent,vgg16_filename), vgg16_predictions)
        np.save(os.path.join(self.src._meta_parent,vgg19_filename), vgg19_predictions)
        return metadata, vgg16_predictions, vgg19_predictions

    def readFromFolder(self, source_file, metadata, datasize=None):
        logging.info('{}:Reading images from folder...'.format(datetime.datetime.now()))
        
        newmeta_filename = "imgtometadata.json"
        start_time = time.time()
        thumbnail_folder = source_file+"_thumbnail"
        if not os.path.isdir(thumbnail_folder):
            os.mkdir(thumbnail_folder)
        ## metadata provided  
        if metadata and len(metadata) > 0:
            # follow the sequence in metadatas
            logging.info('{}:Looping through metadata...'.format(datetime.datetime.now()))
            # new_metadata = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for node in metadata:
                    # new_metadata.append(node)
                    apath = parseFilePath(node['_mediaPath'][0])
                    apath = apath.split('/')[-1] # filename only
                    if os.path.exists(os.path.join(source_file,apath)):
                        # new_metadata.append(node)
                        # executor.submit(self.predictImage, source_file, apath, vgg16_predictions, vgg19_predictions)
                        executor.submit(self.predictImage, source_file, apath, node, True, thumbnail_folder)
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
                        # self.appendToMetadata(node, metadata)
                        # executor.submit(self.predictImage, path, name, vgg16_predictions, vgg19_predictions)
                        executor.submit(self.predictImage, path, name, name, False, thumbnail_folder)
                        if datasize:
                            datasize -= 1
                            if datasize == 0:
                                break
        exec_time = time.time() - start_time
        logging.info('{}:Finished processing images. Excecution time: {}'.format(datetime.datetime.now(), exec_time))
        writeJSONToFile(os.path.join(self.dest_meta_parent,"metadata.json"), list(self.image_to_metadata_map.values()), 'w')
        np.savez(os.path.join(self.src_meta_parent,"img_to_feature.npz"), **self.image_to_features_map)
        logging.info('{}:Generating heatmap images. Excecution time: {}'.format(datetime.datetime.now(), exec_time))
        self.generateHeatmapForImages(source_file)
        
        # metadata = list(self.image_to_metadata_map.values())

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
                    apath = parseFilePath(node['_mediaPath'][0])
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

        [groups,root_centroid_img, root_img_to_centroid_dist] = self.image_to_cluster_file(dataset, image_filenames, kmeans, root=True)
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
            total_centroid = [0] * len(kmeans.cluster_centers_[1]) # which cluster center doesnt matter, the length is the same for all centers
            # root cluster maps to every single hashtag
            for hashtag in self.hashtags:
                self.cluster_hashtag_map["root"] = [1]*len(self.hashtags)
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
    def get_features_dataset_from_images(self, childrenToProcess, prevClusters="root"):
        for cluster_index in range(len(list(childrenToProcess.keys()))):
            cluster_index = list(childrenToProcess.keys())[cluster_index]
            current_clusters_string = prevClusters+"-"+str(cluster_index)
            if self.hasMetadata: # only generate cluster hashtag map when metadata is provided
                cluster_hashtags_map = dict(zip(self.hashtags,[0]*len(self.hashtags)))
                #adjacency map
                for child in childrenToProcess[cluster_index]['data']:
                    # child = child.replace('/','\\')    
                    hashtags = self.img_to_hashtags_map[child]
                    for hashtag in hashtags:
                        cluster_hashtags_map[hashtag] = 1
                self.cluster_hashtag_map[current_clusters_string] = list(cluster_hashtags_map.values())
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
                # data = { file: self.image_to_features_map[file][0] for file in files }
                data = { file: self.image_to_features_map[file] for file in files }
                
                image_filenames = np.array(list(data.keys()))
                feature_list = np.array(list(data.values()))
                previousFeature = np.array([None])
                diffImgFoundIncluster = False
                for feature in feature_list:
                    if previousFeature.all() != None:
                        if not ((feature == previousFeature).all()):
                            diffImgFoundIncluster = True
                            break
                    previousFeature = feature
                if not diffImgFoundIncluster:
                    for child in childrenToProcess[cluster_index]['data']:
                        node = {} # Create new key
                        node['name'] = 'leaf'
                        node['centroid'] = child
                        node['dist_to_centroid'] = 0
                        node['data'] = [child]
                        node['children'] = []
                        childrenToProcess[cluster_index]['children'].append(node)
                    return list(childrenToProcess.values())
                # feature_list = list(data.values())
                # feature_list_str =  [[str(i) for i in feature] for feature in feature_list]
                # feature_list_set = set([",".join(list(feature)) for feature in feature_list_str])
                # if (len(feature_list_set) < self.k_clusters):
                #     for child in childrenToProcess[cluster_index]['data']:
                #         node = {} # Create new key
                #         node['name'] = 'leaf'
                #         node['centroid'] = child
                #         node['dist_to_centroid'] = 0
                #         node['data'] = [child]
                #         node['children'] = []
                #         childrenToProcess[cluster_index]['children'].append(node)
                #     return list(childrenToProcess.values())
                # features_list = features_list.reshape(-1,features_list.shape[-1])
                x = self.dimensionality_reduce(feature_list)

                kmeans = self.kmeans_clustering(x)
                [childrenToProcess[cluster_index]['children'],_,_] = self.image_to_cluster_file(x, image_filenames, kmeans)
                childrenToProcess[cluster_index]['children'] = self.get_features_dataset_from_images(childrenToProcess[cluster_index]['children'],current_clusters_string)
                
        return list(childrenToProcess.values())

    def clustering(self, img_to_feature_file=None, img_to_metadata_file=None):
        if img_to_feature_file:
            self.image_to_features_map = dict(np.load(os.path.join(self.src_meta_parent, img_to_feature_file)))
        if img_to_metadata_file:
            with open(os.path.join(self.src_meta_parent, img_to_metadata_file), 'r', encoding="utf8") as f:
                self.image_to_metadata_map = json.load(f)
                self.hasMetadata = True
        if self.hasMetadata: # only if metadata is provided
            self.imgToHashtags() # create map from image to hashtags
        start_time = time.time()
        logging.info('{}:Clustering images'.format(datetime.datetime.now()))
        vgg16_predictions = list(self.image_to_features_map.values())
        # vgg19_predictions = [feature[1] for feature in self.image_to_features_map.values()]
        x = self.dimensionality_reduce(np.array(vgg16_predictions)) #(m, 4096)-> (m,PCA-Value)
        [self.tree['children'],root_centroid_img, root_centroid_img_dist] = self.cluster_files(x, np.array(list(self.image_to_features_map.keys()))) #first iteration
        self.tree['centroid'] = root_centroid_img
        self.tree['dist_to_centroid'] = root_centroid_img_dist
        self.tree['children'] = self.get_features_dataset_from_images(self.tree['children']) # subgroups
        exec_time = time.time()-start_time
        writeJSONToFile(os.path.join(self.dest_meta_parent,"clusters.json"), self.tree, 'w')
        logging.info('{}:Clusters saved to static folder. Clustering time: {}'.format(datetime.datetime.now(), exec_time))
        if self.hasMetadata: # only if metadata is provided
            self.convertClusterHashtagMapToCSV()

    def generateHeatmapForImages(self, source_file):
        explainer_folder = source_file+"_explainer"
        if not os.path.isdir(explainer_folder):
            os.mkdir(explainer_folder)
        for path, subdirs, files in os.walk(source_file):
            for name in files:
                self.storeGradCam(path, name, explainer_folder)
                # self.generateThumbnail(path, name, thumbnail_folder)
    
    def convertClusterHashtagMapToCSV(self):
        rows = []
        clusters = list(self.cluster_hashtag_map.keys())
        title = ["Hashtag"]+clusters
        # print(title)
        # print(list(self.cluster_hashtag_map.values()))
        cluster_hashtag_map_transpose = list(map(list, zip(*list(self.cluster_hashtag_map.values()))))
        rows= [title] + [[hashtag]+clusters for (hashtag, clusters) in zip(self.hashtags,cluster_hashtag_map_transpose)]
        with open(os.path.join(self.dest_meta_parent,"adjacencymap.csv"),'w', encoding='utf-8', errors='ignore', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    ## adjacency map
    def imgToHashtags(self):
        hashtag_set = set()
        for image,metadata in self.image_to_metadata_map.items():
            node = metadata['node']
            caption = keys_exists(node,"edge_media_to_caption.edges.0.node.text") or \
            keys_exists(node,"caption.text") or \
            keys_exists(node,"description") # get caption
            caption = caption.replace('\n',' ') if caption != None else None
            hashtags = re.findall(r"#(\w+)",caption) if caption != None else [] # retrieve hashtags
            hashtags = [str(hashtag).lower() for hashtag in hashtags]
            hashtag_set.update(hashtags)
            self.img_to_hashtags_map[image] = hashtags
        self.hashtags = list(hashtag_set)
        self.hashtags.sort()
            
    def predictImageInZip(self, _zipfolder, apath, metadata, node, vgg16_predictions, vgg19_predictions, isNode):
        with _zipfolder.open(apath,'rb') as image:
            ## Model Filters
            output = predict_image(image)
            vgg16_predictions.append(output[0])
            # vgg19_predictions.append(output[1])
            if isNode:
                metadata.append(node)
            else:
                self.appendToMetadata(node, metadata)

    def predictImage(self, _folder, apath, node, isNode, thumbnail_folder):
        output = predict_image(os.path.join(_folder,apath))
        filepath = parseFilePath(os.path.join(_folder,apath)) #input_data/images/folder/img1.jpg

        # getting original aspect ratio
        img = Image.open(os.path.join(_folder,apath))
        w, h = img.size
        # generating thumbnail
        img.thumbnail((50,50))
        img.save(os.path.join(thumbnail_folder, apath))
        img.close()

        # vgg16_predictions.append(output[0])
        # vgg19_predictions.append(output[1])
        self.image_to_features_map[filepath] = output[0]
        if isNode:
            # metadata.append(node)
            node['node']['ori_width'] = w
            node['node']['ori_height'] = h
            self.image_to_metadata_map[filepath] = node
        else:
            # self.appendToMetadata(node, metadata)
            filemeta = {}
            filemeta['node'] = {}
            filemeta['node']['ori_width'] = w
            filemeta['node']['ori_height'] = h
            filemeta['_mediaPath'] = [filepath]
            self.image_to_metadata_map[filepath] = filemeta

    def predictImageOnline(self, img, metadata, node, vgg16_predictions, vgg19_predictions):
        output = predict_image(img)
        vgg16_predictions.append(output[0])
        vgg19_predictions.append(output[1])
        metadata.append(node)

    def storeGradCam(self, folder, ori_img_filename, dest_folder):
        rescaling = 224
        # Plotting
        ori_img = load_img(os.path.join(folder, ori_img_filename), target_size=(rescaling,rescaling), interpolation='bicubic')
        # ori_img = Image.open(os.path.join(folder, ori_img_filename))
        heatmap = generateHeatmap(os.path.join(folder, ori_img_filename))
        plt.figure(figsize=(15,15))
        plt.axis("off")
        plt.imshow(ori_img)
        plt.imshow(heatmap.reshape(224,224,3), alpha=0.5) # Overlap with nice colouring
        plt.savefig(os.path.join(dest_folder, ori_img_filename), bbox_inches='tight')
        plt.clf()
        plt.close()
        # blendedImg = generateHeatmap(os.path.join(folder, ori_img_filename))
        # blendedImg.save(os.path.join(dest_folder, ori_img_filename)) 

    # def generateThumbnail(self, path, name, dest_folder):
    #     img = Image.open(os.path.join(path, name))
    #     img.thumbnail((50,50))
    #     img.save(os.path.join(dest_folder, name))
    #     img.close()

    # @staticmethod
    # def appendToMetadata(apath, metadata, node_meta=None, url=None):
    #     _mediaPath = apath.replace('/','\\')
    #     # add to metadata
    #     filemeta = {}
    #     if not node_meta:
    #         node_meta = {}
    #     # img = Image.open(os.path.join(dirname,outfile))
    #     # node['byte_size'] = os.path.getsize(filepath)
    #     filemeta['node'] = node_meta
    #     filemeta['_mediaPath'] = [_mediaPath]
    #     if url:
    #         filemeta['_mediaPath'] = [url]
    #     metadata.append(filemeta)  
