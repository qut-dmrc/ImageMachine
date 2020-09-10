import json
import os
# from argparse import ArgumentParser

from predict import predict_path
from clump import clump

# parser = ArgumentParser(
#     description="Create a hierarchical cluster of images and their associated metadata."
# )

# parser.add_argument("input", type=str, help="Input metadata path")


def main():
    # args = parser.parse_args()
    # input_file = args.input

    input_file = os.path.join(os.getcwd(), "../data/jane.txy.json")

    with open(input_file, 'r', encoding="utf8") as f:
        metadata = json.load(f)
        vgg16_predictions = []
        vgg19_predictions = []
        for node in metadata:
            # print(node['_mediaPath'][0], type(node['_mediaPath'][0]))
            output = predict_path(node['_mediaPath'][0])
            vgg16_predictions.append(output[0])
            vgg19_predictions.append(output[1])
        # print("vgg16", vgg16_predictions)
        # print("vgg19", vgg19_predictions)
        tree_vgg16 = clump(vgg16_predictions, metadata)
        tree_vgg19 = clump(vgg19_predictions, metadata)
        # metadata['tree_vgg16'] = tree_vgg16
        # metadata['tree_vgg169'] = tree_vgg19

    # metadata = json.dumps(metadata)
    # f = open(input_file,'w')
    # f.write(metadata)
    with open('tree_vgg16.json', 'w') as f:
        json.dump(tree_vgg16, f)
    with open('tree_vgg19.json', 'w') as f:
        json.dump(tree_vgg19, f)

if __name__ == "__main__":
    main()
