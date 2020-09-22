from PIL import Image


def squash_image(image, width, height):
    return image.resize((width, height), Image.BICUBIC).convert('RGB')


def squash_path(input_path, output_path, width, height):
    image = Image.open(input_path)
    new_image = squash_image(image, width, height)
    new_image.save(output_path)
