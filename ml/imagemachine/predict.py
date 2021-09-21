from keras.preprocessing.image import load_img
import numpy as np
from .models import model_predict

def predict_image(image, rescaling=224):
    try:
        img = load_img(image, target_size=(rescaling,rescaling), interpolation='bicubic') # load and resize image
    except Exception as e:
        print(repr(e))
        return -1
    img = np.array(img) # shape is currently (224,224,3)
    reshaped_img = img.reshape(1,rescaling,rescaling,3) # the first number is batch (number of images in the batch)
    output = model_predict(reshaped_img)
    return output
