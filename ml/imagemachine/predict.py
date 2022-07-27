#Import all of the necessary libraries for ML
import numpy as np
import tensorflow as tf

from keras.preprocessing.image import load_img
from tensorflow.keras.preprocessing.image import img_to_array, array_to_img
from tensorflow.keras.models import Model
import tensorflow.keras.applications.vgg16 as VGG16
import cv2

# import tensorflow.keras.applications.vgg19 as VGG19
# VGG16
vgg16 = VGG16.VGG16(weights='imagenet',include_top=True,classes=1000)
model_vgg16 = Model(inputs= vgg16.input, outputs=vgg16.layers[-2].output) # for clustering
conv_layer_dict = []
for layer in vgg16.layers: # Find and append all convolutional layers of model
    if type(layer).__name__ == "Conv2D":
        conv_layer_dict.append(layer)
final_conv_layer = conv_layer_dict[-1] # Grab the final convolutional layer of model
# Creating a pipeline to vgg16 to return output and final_conv_layer
vgg16_modified = tf.keras.models.Model([vgg16.inputs], [vgg16.output, final_conv_layer.output]) # for heatmap


def preprocess_img(image, rescaling=224):
    try:
        img = load_img(image, target_size=(rescaling,rescaling), interpolation='bicubic') # load and resize image
    except Exception as e:
        print(repr(e))
        return -1

    img = img_to_array(img) # shape is currently (224,224,3)
    
    reshaped_img = img.reshape(1,rescaling,rescaling,3) # the first number is batch (number of images in the batch)
    # preprocess input
    input_array_vgg16 = VGG16.preprocess_input(reshaped_img)
    return input_array_vgg16
# VGG19
# vgg19 = VGG19.VGG19(weights='imagenet',include_top=True,classes=1000)
# model_vgg19 = Model(inputs= vgg19.input, outputs=vgg19.layers[-2].output)

def model_predict(input_array_vgg16):
    # models prediction
    output = []
    output.append(model_vgg16.predict(input_array_vgg16)[0])
    # output.append(gradCAM(input_array_vgg16, vgg16_modified))

    return output

def predict_image(image):
    input_array_vgg16 = preprocess_img(image) 
    # input_array_vgg19 = VGG19.preprocess_input(reshaped_img)
    output = model_predict(input_array_vgg16)
    return output

def generateHeatmap(image):
    input_array_vgg16 = preprocess_img(image)
    return gradCAM(input_array_vgg16, vgg16_modified)

"""
The Gradient Class Activation Mapping method for explaining a CNN model's prediction.
Works by grabbing the final convolutional layer's output to see what image segments led
to the CNN classifying it a certain class/label.
"""
def gradCAM(input_image_aug, model, intensity=0.5):
    # Guided backpropogation
    with tf.GradientTape() as tape:
        
        # Creating a pipeline to follow for the model and image
        result, final_conv_layer = model(input_image_aug) # get the value of the model and final conv layer

        # Tuple (Value, index) of highest class confidence scores
        [[top_confidence],[index]] = tf.math.top_k(result[0], 1, sorted=True)
        
        # Finding the original gradients (activations)
        grads = tape.gradient(top_confidence, final_conv_layer)
        # pooled_grads = 1
        # Finding the average of the gradients (activations)
        pooled_grads = tf.keras.backend.mean(grads, axis=(0, 1, 2))
        
    # # Create and prepare the heatmap (Without matplotlib)
    # heatmap = tf.reduce_mean(tf.multiply(pooled_grads, final_conv_layer), axis = -1)
    # heatmap = np.maximum(heatmap, 0)
    # heatmap /= np.max(heatmap)
    # heatmap = heatmap.reshape((heatmap.shape[1],heatmap.shape[2]))
    # heatmap = cv2.resize(heatmap, (input_image_aug.shape[1], input_image_aug.shape[2]))
    # heatmap = cv2.applyColorMap(np.uint8(255*heatmap), cv2.COLORMAP_JET) # Multiply by 255 for RGB colormap
    # input_img = input_image_aug[0].astype(np.uint8)
    # heatmap = cv2.addWeighted(heatmap, intensity, input_img, 1, 0)
    # blended = array_to_img(heatmap)
    # return blended

    # Create and prepare the heatmap (With matplotlib)
    heatmap = tf.reduce_mean(tf.multiply(pooled_grads, final_conv_layer), axis = -1)
    heatmap = np.maximum(heatmap, 0)
    heatmap /= np.max(heatmap)
    heatmap = heatmap.reshape((heatmap.shape[1],heatmap.shape[2]))
    heatmap = cv2.resize(heatmap, (input_image_aug.shape[1], input_image_aug.shape[2]))
    heatmap = cv2.applyColorMap(np.uint8(255*heatmap), cv2.COLORMAP_JET) # Multiply by 255 for RGB colormap
    return heatmap
    