import ssl
ssl._create_default_https_context = ssl._create_unverified_context
# from tensorflow.python.keras.applications.densenet import DenseNet201
# # from tensorflow.python.keras.applications.efficientnet import EfficientNetB7
# from tensorflow.python.keras.applications.inception_resnet_v2 import InceptionResNetV2
# from tensorflow.python.keras.applications.inception_v3 import InceptionV3
# from tensorflow.python.keras.applications.mobilenet import MobileNet
# from tensorflow.python.keras.applications.mobilenet_v2 import MobileNetV2
# from tensorflow.python.keras.applications.nasnet import NASNetMobile
# from tensorflow.python.keras.applications.resnet import ResNet101
# from tensorflow.python.keras.applications.resnet_v2 import ResNet50V2
from tensorflow.python.keras.applications.vgg16 import VGG16
from tensorflow.python.keras.applications.vgg19 import VGG19
# from tensorflow.python.keras.applications.xception import Xception
from tensorflow.python.keras.models import Model
# from enum import Enum

# supported models
# densenet = DenseNet201(weights='imagenet')
# inception_resnet_v2 = InceptionResNetV2(weights='imagenet')
# inception_v3 = InceptionV3(weights='imagenet')
# mobilenet = MobileNet(weights='imagenet')
# mobilenet_v2 = MobileNetV2(weights='imagenet')
# nasnet = NASNetMobile(weights='imagenet')
# resnet = ResNet101(weights='imagenet')
# resnet_v2 = ResNet50V2(weights='imagenet')
vgg16 = VGG16(weights='imagenet', include_top=True)
vgg19 = VGG19(weights='imagenet',include_top=True)
# xception = Xception(weights='imagenet',include_top=True)

# model_densenet = Model(inputs= densenet.input)
# model_inception_resnet_v2 = Model(inputs= inception_resnet_v2.input)
# model_inception_v3 = Model(inputs= inception_v3.input)
# model_mobilenet = Model(inputs= mobilenet.input)
# model_mobilenet_v2 = Model(inputs= mobilenet_v2.input)
# model_nasnet = Model(inputs= nasnet.input)
# model_resnet = Model(inputs= resnet.input)
# model_resnet_v2 = Model(inputs= resnet_v2.input)
model_vgg16 = Model(inputs= vgg16.input, outputs=vgg16.get_layer('fc2').output)
model_vgg19 = Model(inputs= vgg19.input, outputs=vgg19.get_layer('fc2').output)
# model_xception = Model(inputs= xception.input)

# models = [  model_densenet,
#             model_inception_resnet_v2,
#             model_inception_v3,
#             model_mobilenet,
#             model_mobilenet_v2,
#             model_nasnet,
#             model_resnet,
#             model_resnet_v2,
#             model_vgg16,
#             model_vgg19,
#             model_xception]

# models = [model_vgg16, model_vgg19]




