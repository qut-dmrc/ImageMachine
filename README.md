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
npm run dev
```
## Docker 
To build two separate docker images with the Dockerfiles provided. One for building a tree cluster for your image collection through unsupervised clustering, one for visualization.

- Set up Docker on your machine
- Prepare the data to process with ImageMachine 
  * Assuming you have a folder of images you like to process with/without their assoicated metadata in JSON/CSV file format. ( Metadata is optional)
  * Create a folder `your_folder`. Inside `your_folder`, create subfolders named `images` and `metadata` respectively.
  * Move your folder of images into `images` and metadata goes into `metadata` if there is any.
- Clone the code and switch to docker branch
```
git clone https://github.com/qut-dmrc/ImageMachine.git
git checkout docker
```

### Building docker images 
- Build first image for ml model, replace `im_ml` with what you like to name your first image. Period `.` is intended.
```
cd ml
docker build -t im_ml .
```
- Build second image for visualizer.
```
cd ../graph
docker build -t im_viz .
```

### Running containers
- Create cluster using im_ml
  * `docker run -ti --rm -v your_folder:/im/input_data <im_ml> bash` Subtitute `your_folder` with the absolute path to your folder and `im_ml` to the name you named your ml image. 
  * `pip install -e .`
  * `export LC_ALL=C.UTF-8`
  * Run the command as shown in the command options. e.g. `im -metadata john_doe.json -img john_doe`. `john_doe.json` is the metadata and `john_doe` is the folder that contains all the images. Use `/` for the filepath. Press <return>, after finish processing, `clusters.json` will be stored in the `images` folder of `your_folder`. 
  * Type `exit` and press return/enter to exit the im_ml container.

- View the cluster using visualiser
  * `docker run -ti --rm -v your_folder/images:/viz/dist -p 88:8080 im_viz bash`. Replace `im_viz` with the name you name your visualizer
  * `mv dist_src/* dist/ && rm -rf dist_src`
  * `npm run build && npm run dev`
