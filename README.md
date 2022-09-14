# Reverse Image Search (CBIR)

[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](http://perso.crans.org/besson/LICENSE.html)
[![](https://img.shields.io/badge/python-3.9%2B-green.svg)]()

This is an out-of-the-box backend server for Reverse Image Search (Content-based Image Retrieval). You can quicky depoly entire application by using Docker.

![](https://github.com/zcsd/Reverse_Image_Search/tree/master/doc/demo.gif)

## Quick Start

### 1. Install Vector Database

Vector database is the core part of reverse image search. [Milvus](https://milvus.io/) is selected as vector database here, Milvus is a good database built for scalable embedding similarity search, now it only supports Intel CPU.

Before installation, make sure you have installed Docker (version>=20.0) and Docker Compose.

```shell
# 1. Prepare the source code
$ git clone https://github.com/zcsd/Reverse_Image_Search
$ cd Reverse_Image_Search/doc

# 2. Prepare the docker-compose file
$ cp vector-engine-docker-compose.yml docker-compose.yml

# 3. Executing docker-compose and install the services
$ docker-compose up -d
```

Vector database server exposes port 19530 for gRPC communication with clients.

### 2. Prepare the Images

For demo purpose, I use [ImageNet-1K dataset](https://www.image-net.org/download.php) (1,281,167 training images) to build images library to search. You can [download ImageNet-1K dataset](https://www.kaggle.com/competitions/imagenet-object-localization-challenge/data) here, I recommend you select a mini-set from ImageNet-1K or prepare your own images, because full ImageNet-1K is too big. Copy training images folder to folder */Reverse_Image_Search/image_search/data/imagenet/*.

```sh
# structure your dataset folder like this
├── Reverse_Image_Search/
│   ├── image_search/
│   │   ├── data/
│   │   │   ├── upload/
│   │   │   └── imagenet/
│   │   │       └── train/
│   │   │           ├── n01440764/
│   │   │           │   ├── n01440764_18.JPEG
│   │   │           │   ├── n01440764_36.JPEG
│   │   │           │   └── ......
│   │   │           └── ......
│   │   └── ......
│   └── ......
│      
```

### 3. Upload Images to MinIO Object Storage

I recommend you upload all training images to MinIO Object Storage, so that we can view images results easily (access the image from an URL). You can skip this part if you don't want to view images in search results.

```sh
# 1. prepare minio docker-compose file
$ cd Reverse_Image_Search/doc
$ cp minio-docker-compose.yml docker-compose.yml

# 2. Executing docker-compose and install MinIO
$ docker-compose up -d
```

Now you can access MinIO control panel from *http://127.0.0.1:8001* (default username: user1, password: user1password).

Login to the MinIO control panel website, create a new Bucket with name "images". After creating the new Bucket, change the Access Policy of the Bucket to "public", so that we can access any file or image in this bucket from *http://127.0.0.1:8000/images/XXXXXX*.

Now we can upload images to MinIO, there are two ways: Manaully upload images from MinIO control panel (*http://127.0.0.1:8001*), we can select whole dataset folder to upload; Or you can use */Reverse_Image_Search/image_search/preprocess.py* to upload images using MinIO API.

After uploading, you can view the image by accessing the URL: *http://127.0.0.1:8000/images/n01440764/n01440764_18.JPEG* (example only).

### 4. Run the Reverse Image Search Server

For easy setup and better performance, I suggest you run the application in Linux.

In Windows, Windows 10 SDK for Desktop C++ and Visual C++ Build tools are required to be installed before the following steps.

```shell
# 1. go to work folder
$ cd Reverse_Image_Search

# Python version >= 3.8
# 2. Install Python packages
$ pip3 install -r requirements.txt

# You can change configuration in /Reverse_Image_Search/image_search/conf/config.ini

# 3. Preprocess the images
# this step will save all images to HDF5 file and upload images to MinIO bucket
$ python3 image_search/preprocess.py

# 4. Embedding images and insert vectors to database
# it may take half day if you use full imagenet-1K dataset.
$ python3 image_search/trainer.py

# Now the vector database should have the vectors collection and index.
# It's ready to start image search.

# 5. Start reverse image search
$ python3 image_search/app.py

# Now port 5000 serves as the http request port for image search.
# You can access http://127.0.0.1:5000/status/ to check the vector database status.
# Check app.py for more API Endpoint and how to use.
```

After vector database has the the vectors collection and index (above step 4), you can also run the application (image search) with Docker.

By using Docker, you can quickly build and run the entire application without pre-request.

```shell
# 1. Build Docker image
$ cd Reverse_Image_Search
$ docker build --no-cache -t image_search:v1.0 .

# 2. Run with Docker
# If vector database sever is installed on the same machine,
# you can run with the following command.
$ docker run -p 5000:5000 --add-host=host.docker.internal:host-gateway -it image_search:v1.0
# If vector server is installed on the other machines.
$ docker run -p 5000:5000 -it image_search:v1.0 python3 image_search/app.py --vectorhost replace.host.ip.here
```

#### API Endpoint

Check app.py for more using details.

```shell
# Vector server status: 
http://127.0.0.1:5000/status/

# Image search: 
http://127.0.0.1:5000/search/

# Insert new image to vector database:
http://127.0.0.1:5000/insert/

# Create new index for collection
http://127.0.0.1:5000/indexing/

```

### 5. Run the Frontend Website

You can run a demo webpage to test the image search. [Click here](https://github.com/zcsd/reverse_image_search_web) to check the code for [frontend demo webpage](https://demo.best360.tech/). 

Download the [Reverse_Image_Search_Web code](https://github.com/zcsd/Reverse_Image_Search_Web), [dist folder](https://github.com/zcsd/Reverse_Image_Search_Web/tree/master/dist) will work as your webpage source folder, you can ignore functions/api and package.json in the main directory.

Change the baseURL to *http://127.0.0.1:5000/* in /dist/assets/js/helper.js [line 223](https://github.com/zcsd/Reverse_Image_Search_Web/blob/master/dist/assets/js/helper.js#L223).

Now you can open the frontend webpage to try the image search!

