# Reverse Image Search (CBIR)

[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](http://perso.crans.org/besson/LICENSE.html)
[![](https://img.shields.io/badge/python-3.9%2B-green.svg)]()

This is a backend server to do Reverse Image Search (Content-based Image Retrieval).

[Click here](https://github.com/zcsd/reverse_image_search_web) to check the code for [frontend demo webpage](https://demo.best360.tech/).

## Run with Docker

With Docker(version>=20.0), you can quickly build and run the entire application without pre-request.

```shell
# 1. Prepare the source code
$ git clone https://github.com/zcsd/Reverse_Image_Search
$ cd Reverse_Image_Search

# 2. Build Docker image
$ docker build --no-cache -t image_search:v1.0 .

# 3. Run with Docker
# If vector database sever is installed on the same machine,
# you can run with the following command.
$ docker run -p 5000:5000 --add-host=host.docker.internal:host-gateway -it imsearch:v1.0
# If vector server is installed on the other machines.
$ docker run -p 5000:5000 -it image_search:v1.0 python3 image_search/app.py --vectorhost replace.host.ip.here

```

## Local Installation

For easy setup and better performance, I suggest you run the application in Linux.

In Windows, Windows 10 SDK for Desktop C++ and Visual C++ Build tools are required to be installed before the following steps.

```shell
# 1. Prepare the source code
$ git clone https://github.com/zcsd/Reverse_Image_Search
$ cd Reverse_Image_Search

# Python version >= 3.8
# 2. Install Python packages
$ pip3 install -r requirements.txt

# 3. Run
$ python3 image_search/app.py --vectorhost replace.host.ip.here
```


