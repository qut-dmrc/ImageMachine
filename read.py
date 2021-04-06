import pandas as pd
import csv
import numpy as np
from itertools import chain

clusters = pd.read_csv("image_clusters.csv").set_index('Image ID')
# df = pd.read_csv("fb_data.csv")
# df = df[df['Images'] != 'None'] # remove rows with no images
# def chainer(s):
#     return list(chain.from_iterable(s.str.replace('"','').str.strip().str.split(',')))

# # calculate lengths of splits
# lens = df['Images'].str.split(',').map(len)

# res = pd.DataFrame({'Image_ID': chainer(df['Images']),
#                     'Image_Group_ID': np.repeat(df['ID'], lens),
#                     'Created': np.repeat(df['Created'], lens),
#                     'User': np.repeat(df['User'], lens),
#                     'Age': np.repeat(df['Age'], lens),
#                     'Gender': np.repeat(df['Gender'], lens),
#                     'Education': np.repeat(df['Education'], lens),
#                     'Income': np.repeat(df['Income'], lens),
#                     'Ethnicity': np.repeat(df['Ethnicity'], lens),
#                     'Party': np.repeat(df['Party'], lens),
#                     'Content': np.repeat(df['Content'], lens),
#                     'Links': np.repeat(df['Links'], lens)})
# res.to_csv("expanded_image_id.csv",index=None)

df = pd.read_csv("expanded_image_id.csv")
df['Clusters'] = df['Image_ID'].apply(lambda x: clusters.loc[x.split('.')[0]]['Clusters'] if x.split('.')[0] in clusters.index else 'N/A')
df.to_csv("image_info.csv",index=None)







