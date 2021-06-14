### Software Requirements

Docker
Python

### From your environment

```
git clone https://github.com/qut-dmrc/ImageMachine.git
cd ImageMachine
pip install virtualenv
virtualenv env ##if you use ls, you'll see a directory env has been created
[Linux/MAC] source env/bin/activate  [Windows] "env/Scripts/activate.bat" env ##to activate the environment
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

-   Set up Docker on your machine
-   Prepare the data to process with ImageMachine
    -   Assuming you have a folder of images you like to process with/without their assoicated metadata in JSON/CSV file format. ( Metadata is optional)
    -   Create a folder `your_folder`. Inside `your_folder`, create subfolders named `images` and `metadata` respectively.
    -   Move your folder of images into `images` and metadata goes into `metadata` if there is any.
-   Clone the code and switch to docker branch

```
git clone https://github.com/qut-dmrc/ImageMachine.git
cd ImageMachine
git checkout docker
```

### Building docker images

-   Build first image for ml model, replace `im_ml` with what you like to name your first image. Period `.` is intended.

```
cd ml
docker build -t im_ml .
```

-   Build second image for visualizer.

```
cd ../graph
docker build -t im_viz .
```

### Running containers

-   Create a folder on your computer that will contain the images, metadata (optional), and then eventually also the clustering information that we will generate using the code below
-   Structure the image folder (you can name this folder anything but we will refer to it as **im_folder** throughout these instructions) using the following folder/subfolder structure, note that the metadata folder must exist even if you don't have any metadata (i.e. this subfolder can be left empty, but it must exist)
    ```
    im_folder/
     |images/
        |arianagrande/
            |1.jpg
            |2.jpg
            |3.jpg
            |...
     |metadata/
        |arianagrande.json
    ```
-   Open the Docker Desktop GUI, go to setting (gear icon), then navigate to **Resources/FILE SHARING**, add the im_folder to the whitelist.
-   Open a command line (as administrator), or terminal window
-   Download the docker images using the following commands (if successful these commands will fetch all required components from the Internet and install them on your machine)
    -   `docker pull xueyingt96/image_machine:viz`
    -   `docker pull xueyingt96/image_machine:ml`
-   Rename them
    -   `docker image tag xueyingt96/image_machine:viz im_viz`
    -   `docker image tag xueyingt96/image_machine:ml im_ml`
-   To create an image cluster using the im_ml
    -   (For Linux users)
        -   Type `pwd` to get to your current directory e.g Output: /home/jane
        -   `docker run -ti --rm -v /home/jane/im_folder:/im/input_data im_ml bash` Subtitute `/home/jane/im_folder` with the absolute path to your folder.
    -   (For Windows users)
        -   `docker run -ti --rm -v C:/home/jane/im_folder:/im/input_data im_ml bash` Subtitute `C:/home/jane/im_folder` with the absolute path to your folder.
-             With that command, you should now be inside your docker container. (You will see the change in your shell to `root@randomcharacters:/im#`)
-             Check if the docker container correctly hooks up with your image folder by commands `cd input_data && ls`, you should see `images` and `metadata` folders as included in im_folder and everything inside them.

    -   Go back to parent directory `cd ..`
    -   `pip install -e .` to setup the machine learning program.
    -   Run the command as shown in the command options below. e.g. `im -img arianagrande`. `arianagrande` is the folder that contains all the images. Use `/` for the filepath should you need. Press return/enter key. After the ML process is done, `clusters.json` will be stored in the `images` folder of `im_folder`.
    -   When it is finished running type `exit` and press return/enter to exit the im_ml container.
    -   If you navigate to im_folder and list the content`cd im_folder/images && ls`(`cd im_folder/images && dir` for Windows), you can see the clusters.json has appeared in the folder as a result of writing it out from the docker container.

-   View the cluster using visualiser
    -   From the command line (not the docker window) run `docker run -ti --rm -v /home/jane/im_folder/images:/viz/dist -p 88:8080 im_viz bash` (or for Windows: `docker run -ti --rm -v C:/home/jane/im_folder/images:/viz/dist -p 88:8080 im_viz bash`).
        -   The above command allows us to use the im_viz docker image to visualize the clusters of the images. The ` -v im_folder/images:/viz/dist` component of the command above mounts the external directory`im_folder/images`(notice we're using `im_folder/images` here instead of just `im_folder/`) because that connects the images and cluster information to the directory /viz/dist in our docker container.
    -   the above command should open up a docker container into which you should enter the following commands:
        -   `mv dist_src/* dist/ && rm -rf dist_src`
        -   `npm run build -- --env "clusters.json" && npm run dev` replace `clusters.json` with any other cluster json file you like to visualize. E.g. `"clusters_deadmall.json"`
    -   The commands in docker above will start a server running on your local computer, to access this server go to your browser and type `localhost:88`-> Voilà, here is the dendogram of your image clusters. Have fun exploring!

### ML Command

```

Usage: im [OPTIONS]

Options:
  -config, --config                 [string][optional] file path to config
  -img, --img                         [string][optional only when metadata contains paths to download] file path to image folder
  -zip, ---zip                           [string][optional] if the image folder in compressed
  -metadata, --metadata    [string][optional] take in JSON/CSV file, the json should have column _mediaPath for image paths of images in the image folder
  -fieldname, --fieldname  [string][optional] if metadata is CSV file, you can indicate the name of the column that contains the image paths.
  -d, --download                  [boolean][optional] If you are clustering a set of images online(image urls), toggle this if you want to download the images
  -s, --size                              [integer] You can choose to run the clustering on a smaller sample size of your image set, selected arbritarily.
  -t, --time                             [boolean] To show a line graph of the processing durations given different sample size
  -size_list                             [list] Predefined sizes to test to time the clustering process
  -log                                     [boolean] Log clustering process
  --help

Examples:
im -metadata "metadata.csv" -fieldname "media_url" -s 50 -d                      ##online image urls, processing 50 images, download images
im -metadata "metadata.csv" -fieldname "media_url" -s 50                          ##online image urls, processing 50 images
im -img instagram\user\arianagrande -s 50                                                     ## instagram\user\arianagrande image folder, no metadata, processing 50 images
im -metadata metadata.json -img instagram\user\arianagrande                ## image folder and json metadata
im -metadata metadata.json -img instagram\user\arianagrande -zip downloads.zip  ## compressed image folder and json metadata
im -metadata "metadata.csv" -fieldname "image_url" img instagram\user\arianagrande  -s 100            ## image folder and csv metadata, processing 100 images
```
