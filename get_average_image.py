from PIL import Image
import os
import keras.preprocessing.image
import numpy as np

def squash_image(image, width, height):
    return image.resize((width, height), Image.BICUBIC).convert('RGB')

def get_average_image(image_folder):
    for ospath, subdirs, files in os.walk(image_folder):
        images_array = np.empty((224,224,3))
        for name in files:
            image = Image.open(os.path.join(image_folder,name))
            image = squash_image(image, 224, 224)
            image_array = keras.preprocessing.image.img_to_array(image, dtype=int)
            images_array += image_array
        images_array = images_array/len(files)
        avg_img = keras.preprocessing.image.array_to_img(images_array)
        avg_img.save(os.path.join(image_folder,'mean_img.png'))

            
def main():
    folder = os.path.join(os.getcwd(),"ml\\input_data\\images\\clusters")
    for subdir in os.listdir(folder):
        if subdir.startswith("json_file"):
            break
        print("processing subfolder ", subdir)
        get_average_image(os.path.join(folder,subdir))
    # _2D = [[1,2,3],[4,5,6],[1,2,3]]
    # _average = np.sum(_2D,axis=0)/len(_2D)
    # print(_average)

main()