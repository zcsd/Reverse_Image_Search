# =============================================================================
# File name: create_index.py
# Author: Zichun
# Date created: 2022/08/20
# Python Version: 3.10
# Description:
#    - Create index for collection
# How to run:
#    python image_search/create_index.py
# =============================================================================

import time

from configparser import ConfigParser

from pymilvus import connections, Collection, utility

collection_name = "imagenet_resnet_50_norm" # change here
num_nlist = 2048  # change here  4xsqrt(n) in each segment

def create_index(collection):
    # create IVF_FLAT index for collection.
    index_params = {
        'metric_type': 'L2',
        'index_type': "IVF_FLAT",
        'params':{"nlist": num_nlist}
    }
    collection.create_index(field_name="embedding", index_params=index_params)

if __name__ == '__main__':
    cfg = ConfigParser()
    cfg.read('image_search/conf/config.ini')

    print("Connecting to vector server...")
    connections.connect(alias="default",
                        host=cfg.get('vector_server', 'host'),
                        port=cfg.get('vector_server', 'port'))
    print("Connected to vector server {0}:{1} successfully.".format(cfg.get('vector_server', 'host'), cfg.get('vector_server', 'port')))

    if utility.has_collection(collection_name):
        collection = Collection(collection_name)
        print('Total number of entities in {} is {}.'.format(collection_name, collection.num_entities))
        if collection.has_index():
            print('Index exists, drop it.')
            collection.drop_index()
        print("Creating index...")
        start = time.time()
        create_index(collection)
        end = time.time()
        print("Index created successfully. Server still need some time to build index.")
        print("Total time spent on creating index: {:0.1f} seconds".format(end - start))   
    else:
        print("Collection {} does not exist.".format(collection_name))
    connections.disconnect("default")