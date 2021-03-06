# DeepDanbooru
[![Python](https://img.shields.io/badge/python-3.6-green)](https://www.python.org/doc/versions/)
[![GitHub](https://img.shields.io/github/license/KichangKim/DeepDanbooru)](https://opensource.org/licenses/MIT)
[![Web](https://img.shields.io/badge/web%20demo-20191108-brightgreen)](http://kanotype.iptime.org:8003/deepdanbooru/)

**DeepDanbooru** is anime-style girl image tag estimation system. You can estimate your images on my live demo site, [DeepDanbooru Web](http://kanotype.iptime.org:8003/deepdanbooru/).

## Requirements
DeepDanbooru is written by Python 3.6. Following packages are need to be installed.
- tensorflow>=2.1.0
- Click>=7.0
- numpy>=1.16.2
- requests>=2.22.0
- scikit-image>=0.15.0
- six>=1.13.0

Or just use `requirements.txt`.
```
> pip install -r requirements.txt
```

alternatively you can install it with pip. Note that by default, tensorflow is not included.

To install it with tensorflow, add `tensorflow` extra package.

```
> # default installation
> pip install .
> # with tensorflow package
> pip install .[tensorflow]
```

While developing use the editable option so that every change can be made available without reinstalling:
```bash
pip install -e .
```

## Usage
1. Prepare dataset. If you don't have, you can use [DanbooruDownloader](https://github.com/KichangKim/DanbooruDownloader) for download the dataset of [Danbooru](https://danbooru.donmai.us/). If you want to make your own dataset, see [Dataset Structure](#dataset-structure) section.
2. Create training project folder.
```
> deepdanbooru create-project [your_project_folder]
```
3. Prepare tag list. If you want to use latest tags, use following command. It downloads tag from Danbooru server.
```
> deepdanbooru download-tags [your_project_folder]
```
4. (Option) Filtering dataset. If you want to train with optional tags (rating and score), you should convert it as system tags.
```
> deepdanbooru make-training-database [your_dataset_sqlite_path] [your_filtered_sqlite_path]
```
5. Modify `project.json` in the project folder. You should change `database_path` setting to your actual sqlite file path.
6. Start training.
```
> deepdanbooru train-project [your_project_folder]
```
7. Enjoy it.
```
> deepdanbooru evaluate [image_file_path or folder]... --project-path [your_project_folder] --allow-folder
```

## Dataset Structure
DeepDanbooru uses following folder structure for input dataset. SQLite file can be any name, but must be located in same folder to `images` folder.
```
MyDataset/
├── images/
│   ├── 00/
│   │   ├── 00000000000000000000000000000000.jpg
│   │   ├── ...
│   ├── 01/
│   │   ├── ...
│   └── ff/
│       ├── ...
└── my-dataset.sqlite
```
The core is SQLite database file. That file must be contains following table structure.
```
posts
├── id (INTEGER)
├── md5 (TEXT)
├── file_ext (TEXT)
├── tag_string (TEXT)
└── tag_count_general (INTEGER)
```
The filename of image must be `[md5].[file_ext]`. If you use your own images, `md5` don't have to be actual MD5 hash value.

`tag_string` is space splitted tag list, like `1girl ahoge long_hair`.

`tag_count_general` is used for the project setting, `minimum_tag_count`. Images which has equal or larger value of `tag_count_general` are used for training.

## Project Structure
**Project** is minimal unit for training on DeepDanbooru. You can modify various parameters for training.
```
MyProject/
├── project.json
└── tags.txt
```
`tags.txt` contains all tags for estimating. You can make your own list or download latest tags from Danbooru server. It is simple newline-separated file like this:
```
1girl
ahoge
...
```


## Additions
We have a csv option `--output-csv <path-to-csv>` where you can specify a CSV file.
For example, you can output a CSV of the predictions using:
```bash
deepdanbooru evaluate ./data/test/images/ --allow-folder --project-path deepdanbooru-v3-20200101-sgd-e30 --output-csv ./data/test/predictions/predictions.csv
deepdanbooru evaluate ./data/tfod/images/ --allow-folder --project-path deepdanbooru-v3-20200101-sgd-e30 --output-csv ./data/tfod/predictions/predictions.csv
```

## Download Specific Files Rsync
Download using `rsync` specific files. We look at the metadata and filter ahead of time.


#### Reinstall
To force a reinstall after changing this then use
```bash
pip install --upgrade --no-deps --force-reinstall .
```


## Train Small Dataset
Let's start out with a small dataset to train. Let's call the project `project-small`.
Let's download all images from **Danbooru2019** with tag `transparent_background`.

### 1. Download Metadata
We use `rsync` to download the metadata.
```bash
rsync --verbose \
    rsync://78.46.86.149:873/danbooru2019/metadata.json.tar.xz \
    ./data/danbooru/danbooru2019/
```
Unzip into directory `data/danbooru/danbooru2019/metadata`:
```bash
tar -xvf ./data/danbooru/danbooru2019/metadata.json.tar.xz -C ./data/danbooru/danbooru2019/metadata
```

### 2. Make Training Database
We use the metadata to create a training database. 
The first argument is a `glob` so that you can search for patterns.
For example, since we are training on 201:
```bash
deepdanbooru make-training-database-metadata \
    "./data/danbooru/danbooru2019/metadata/*/2019*" \
    "./data/sqlite/danbooru-2019.sqlite" \
    --image_path_glob="/mnt/e/downloads/danbooru2019/original/*/*"
```



### 3. Download Images
We use `rsync` to download a subset of images.

```bash
rsync --verbose --recursive --prune-empty-dirs \
	--include-from='data/filters/include_dragon_ball.txt' \
	--exclude='*' \
	rsync://78.46.86.149:873/danbooru2019/ ./data/danbooru/danbooru2019/
```

### 4. Make a Project
Start a project directory 
```bash
deepdanbooru create-project project-small
```
Modify `project.json` in the project folder. You should change `database_path` setting to your actual sqlite file path.

In this notebook this is found in `sqlite_path_subset` but the absolute path of the folder.
For example `G:/AI/shazam/DeepDanbooru/data/sqlite/danbooru-dev-subset.sqlite`

Also, if you downloaded the image somewhere else on your system add to the `project.json` the attribute `image_folder_path` with the absolute path to the
images with 3 digit has subfolder `"image_folder_path": "G:/AI/shazam/DeepDanbooru/data/danbooru/danbooru2019/original"`


### 5. Download Tags
We need to define the tags to be our labels. Sometimes you want to restrict the training to only tags with greater than 
a set number of images `--minimum-post-count`. To download tags from Dabooru use:
```bash
deepdanbooru download-tags [your_project_folder]
```


### 6. Train Model
Continue to modify `project.json` to the the training settings you want. To train the model simply run:
```bash
deepdanbooru train-project [your_project_folder]
```


# Miscellaneous
### Filter Images by Tag
For easy viewing we filter the dataset using a jupyter notebook `notebooks/danbooru_eda.ipynb`
We filtered using the tag `dragon_ball` to create the file `data/filters/include_dragon_ball.txt` which will be an 
argument for `rsync`. 
