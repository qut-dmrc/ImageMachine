import json
import os
from fs.zipfs import ZipFS
from PIL import Image
import pandas as pd
import numpy as np
import time
import concurrent.futures
import zipfile

from imagemachine import * 

def main():
    source_meta = 'metadata.json'
    # source_meta = 'test2.csv'
    url_fieldname = 'media_url'
    im = ImageMachine()
    # im.download_images(source_meta, url_fieldname, size = 20)
    im.process_images('test2')
    
if __name__ == "__main__":
    main()
