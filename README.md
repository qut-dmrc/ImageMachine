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
      |example_image_set
        1.jpg
        2.jpg
         ...
    |metadata
       example.json/example.csv/[None]
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

### Example

```
im -metadata example.json -img example_image_set
```

