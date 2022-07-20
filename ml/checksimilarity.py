import pandas as pd

im_data = pd.read_csv("adjacencymap.csv")
im_data = im_data.set_index('Hashtag')
sep_data = pd.read_csv("adjacencymap_separate.csv")
sep_data = sep_data.set_index('Hashtag')
for test_col in sep_data.columns.tolist():
    print("Checking ", test_col)
    im_tags = im_data.loc[(im_data[test_col]==1)].index.tolist()
    sep_tags = sep_data.loc[(im_data[test_col]==1)].index.tolist()
    im_tags.sort()
    sep_tags.sort()
    if len(set(sep_tags).difference(set(im_tags))) != 0:
        print("Different col spotted", test_col)
        break
