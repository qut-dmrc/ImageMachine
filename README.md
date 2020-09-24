### From your environment
```
cd anaconda
conda create --name "your_env" tensorflow
activate <your_env>
git clone https://github.com/qut-dmrc/ImageMachine.git
pip install -r requirements.txt
cd ml
pip install -e .
create static folder within graph
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

