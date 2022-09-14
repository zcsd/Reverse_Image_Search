# =============================================================================
# File name: app.py
# Author: Zichun
# Date created: 2022/08/10
# Python Version: 3.10
# Description:
#    This is the main file for the reverse image search application.
#    It contains the main function and the main loop.
#    The main loop is responsible for the following:
#       - Initializing the application.
#       - Loading the image search engine.
#       - Handle vector server status query request.
#       - Handle image search request.
#       - Handle insert new image request.
#       - Handle create new index request.
# How to run:
#    python image_search/app.py
# =============================================================================

import sys
from datetime import datetime
from configparser import ConfigParser

from gevent.pywsgi import WSGIServer
from flask import Flask, jsonify, request
from flask_cors import CORS

from vector_engine.vector_engine import VectorEngine
from utils.image_util import base64_to_pil

collection_name = "imagenet_resnet_50_norm" # change here
SERVER = 2 # change here

app = Flask(__name__)

# /status endpoint
# Query the status of vector server
# HTTP GET request
# Return: JSON object
@app.route('/status/', methods=['GET'])
def status():
    entities_num = vector_engine.get_number_of_entities()

    if (SERVER == 0):
        cpu = "Intel Xeon @ 2.80GHz, 8 cores"
        memory = "32GB"
        gpu = "NONE"
    elif (SERVER == 1):
        cpu = "Intel i5-12600K @ 3.70GHz, 10 cores"
        memory = "32GB"
        gpu = "NVIDIA RTX 3070"
    elif (SERVER == 2):
        cpu = "Intel i5-9600K @ 3.70GHz, 6 cores"
        memory = "32GB"
        gpu = "NONE"
    
    if (isinstance(entities_num, int) and entities_num > 0):
        return jsonify({"ok": True, "entities_num": str(entities_num), "cpu": cpu, "memory": memory, "gpu": gpu})
    else:
        return jsonify({'ok': False})

# /insert endpoint
# insert new image into collection
# HTTP POST request
# Return: JSON object
@app.route('/insert/', methods=['POST'])
def insert():
    data = request.json
    if data["key"] == admin_key:
        print('Valid Admin Key Provided.')
        img = base64_to_pil(data["image"])
        vector_engine.insert(img, data["location"])
        return jsonify({'ok': True})
    else:
        print('Invalid Admin Key Provided.')
        return jsonify({'ok':False, 'result':'Invalid Key.'})

# /create_index endpoint
# create index for collection
# HTTP POST request
# Return: JSON object
@app.route('/indexing/', methods=['POST'])
def indexing():
    data = request.json
    if data["key"] == admin_key:
        vector_engine.create_index() # TODO: async
        return jsonify({'ok': True})
    else:
        print('Invalid Admin Key Provided.')
        return jsonify({'ok':False, 'result':'Invalid Key.'}) 

# /search endpoint
# search for similar images
# HTTP POST request
# Return: JSON object
@app.route("/search/", methods=['POST'])
def search():
    data = request.json
    if data["key"] == user_key:
        print('Valid User Key Provided.')
        img = base64_to_pil(data["image"])
        results = vector_engine.search(img, 10) # nprobe = 10

        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S_%f")
        img.save("image_search/data/upload/" + timestamp +".JPEG") 
        print('A query image saved.')

        # image_base_url is the base url for the bucket in the MinIO server (where to store the image library)
        image_base_url = cfg.get('url', 'image_base')
        
        resp = jsonify({'ok':True,
                'image1': image_base_url + results[0].label.replace("@", "/"),
                'image2': image_base_url + results[1].label.replace("@", "/"),
                'image3': image_base_url + results[2].label.replace("@", "/"),
                'image4': image_base_url + results[3].label.replace("@", "/"),
                'image5': image_base_url + results[4].label.replace("@", "/"),
                'embedding_time': results[5].embedding_time,
                'search_time': results[5].search_time,
                })
    else:
        print('Invalid Key.')
        resp = jsonify({'ok':False, 'result':'Invalid Key.'})
    return resp

if __name__ == '__main__':
    cfg = ConfigParser()
    cfg.read('image_search/conf/config.ini')

    user_key = cfg.get('key_validation', 'user')
    admin_key = cfg.get('key_validation', 'admin')
    # read the arguments
    if (len(sys.argv) > 2 and sys.argv[1] == "--vectorhost"):
        vector_server_host = sys.argv[2]
    else:
        vector_server_host = cfg.get('vector_server', 'host')
    
    print(vector_server_host, "will be served as vector host.")

    vector_engine = VectorEngine(vector_server_host, 
                          cfg.get('vector_server', 'port'),
                          collection_name)

    CORS(app, resources=r'/*')

    http_server = WSGIServer((cfg.get('http_server', 'host'), 
                            cfg.getint('http_server', 'port')),
                            app)

    print('Web server started at port {}.'.format(cfg.getint('http_server', 'port')))
    http_server.serve_forever() 
