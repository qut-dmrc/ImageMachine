import tensorflow.keras.applications.vgg16 as VGG16
import tensorflow.keras.applications.vgg19 as VGG19
from tensorflow.keras.models import Model

# supported models
vgg16 = VGG16.VGG16(weights='imagenet', include_top=True)
vgg19 = VGG19.VGG19(weights='imagenet',include_top=True)

model_vgg16 = Model(inputs= vgg16.input, outputs=vgg16.layers[-2].output)
model_vgg19 = Model(inputs= vgg19.input, outputs=vgg19.layers[-2].output)

def model_predict(reshaped_img):
    # preprocess input
    input_array_vgg16 = VGG16.preprocess_input(reshaped_img)
    input_array_vgg19 = VGG19.preprocess_input(reshaped_img)

    # models prediction
    output = []
    output.append(model_vgg16.predict(input_array_vgg16)[0])
    output.append(model_vgg19.predict(input_array_vgg19)[0])

    return output


