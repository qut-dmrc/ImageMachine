from PIL import Image
import keras.preprocessing.image
import numpy as np
import tensorflow.python.keras.applications.vgg16 as VGG16
import tensorflow.python.keras.applications.vgg19 as VGG19
from models import model_vgg16, model_vgg19
from squash import squash_image

def predict_image(image):
    image = squash_image(image, 224, 224)
    image_array = keras.preprocessing.image.img_to_array(image, dtype=int)

    input_array_vgg16 = VGG16.preprocess_input(np.expand_dims(image_array, axis=0))
    input_array_vgg19 = VGG19.preprocess_input(np.expand_dims(image_array, axis=0))
    output = []
    output.append(model_vgg16.predict(input_array_vgg16)[0])
    output.append(model_vgg19.predict(input_array_vgg19)[0])
    # print("Size: {}", len(output[0]))
    return output


def predict_path(input_path):
    image = Image.open(input_path)
    return predict_image(image)
