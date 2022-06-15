import json

filename = "adventurecore"
processed_data = []
with open('input_data/metadata/'+filename+'.json','r',encoding='utf-8') as f:
    data = json.loads(f.readline())
    urls = []
    for datum in data:
        new_datum = {}
        img_url = ''
        if 'image_versions2' in datum:
            img_url = datum['image_versions2']['candidates'][0]['url']
        else:
            img_url = datum['carousel_media'][0]['image_versions2']['candidates'][0]['url']
        img_url = img_url.split('?')[0].split('/')[-1].split('.')[0]+".jpg"
        datum['shortcode'] = img_url
        new_datum['node'] = datum
        new_datum['_mediaPath'] = [img_url]
        processed_data.append(new_datum)

with open('input_data/metadata/'+filename+'_aft.json','w') as f:
    json.dump(processed_data, f)
