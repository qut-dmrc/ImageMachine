### From your environment

```
cd anaconda
conda create --name "your_env" python=3.7 tensorflow-gpu=2.3.0 cudnn=7.6.5
activate <your_env>
git clone https://github.com/qut-dmrc/ImageMachine.git
cd ImageMachine
pip install -r requirements.txt
cd ml
pip install -e .
create static folder within graph
create input_data\ folder within ml folder with two subfolders images\ and metadata\
|ml
  |imagemachine
    ...
  |input_data
    |images
      |your_img_folder
        1.jpg
        2.jpg
         ...
    |metadata
       metadata.json/metadata.csv/[None]
|graph
  |static
```

## Usage

### Command Line

```

Usage: im [OPTIONS]

Options:
  -config, --config TEXT
  -img, --img TEXT
  -zip, ---zip TEXT
  -metadata, --metadata TEXT
  -fieldname, --fieldname TEXT
  -d, --download
  -s, --size INTEGER
  -t, --time
  -size_list TEXT
  -log
  --help
```

### Visualization

```
Rename the clusters_<number>.json in graph/dist/static to clusters.json
Move the folder of images to dist if any
npm install
npm run build
npm run dev
```

