# =============================================================================
# File name: trainer.py
# Author: Zichun
# Date created: 2022/08/10
# Python Version: 3.10
# Description:
#    - Read images (binary data) from hdf5 file
#    - Embedding images
#    - Insert embedding vectors to vector server collection
#    - Create index for collection
# How to run:
#    python image_search/trainer.py
# =============================================================================

import sys
import os
import io
import time

import h5py
import numpy as np
from PIL import Image

from configparser import ConfigParser
from utils.progress_helper import progress

from towhee import ops
from towhee.types.image_utils import from_pil
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility

dataset_folder = "imagenet" # change here
collection_name = "imagenet_resnet_50_norm" # change here
num_nlist = 2048  # change here  4xsqrt(n) in each segment
INSERT_VECTOR_TO_COLLECTION = True # change here
CREATE_NEW_COLLECTION = True # change here
CREATE_INDEX = True # change here
INSERT_VECTOR_TO_HDF5 = False # change here

def create_collection(collection_name, dim, description):
    if utility.has_collection(collection_name):
        print('Collection exsits, drop and create a new one.')
        utility.drop_collection(collection_name)
    
    fields = [
    FieldSchema(name='id', dtype=DataType.INT64, descrition='ids', is_primary=True, auto_id=False),
    FieldSchema(name='label', dtype=DataType.VARCHAR, max_length=50, descrition='labels', auto_id=False),
    FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, descrition='embedding vectors', dim=dim)
    ]
    schema = CollectionSchema(fields=fields, description=description)
    collection = Collection(name=collection_name, schema=schema)

    return collection

def create_index(collection):
    # create IVF_FLAT index for collection.
    index_params = {
        'metric_type': 'L2',
        'index_type': "IVF_FLAT",
        'params':{"nlist": num_nlist}
    }
    collection.create_index(field_name="embedding", index_params=index_params)

if __name__ == '__main__':
    data_folder = os.path.join(os.getcwd(), 'image_search', 'data')
    train_img_folder = os.path.join(data_folder, dataset_folder, 'train')

    cfg = ConfigParser()
    cfg.read('image_search/conf/config.ini')

    if INSERT_VECTOR_TO_COLLECTION:
        print("Connecting to vector server...")
        connections.connect(alias="default",
                            host=cfg.get('vector_server', 'host'),
                            port=cfg.get('vector_server', 'port'))
        print("Connected to vector server {0}:{1} successfully.".format(cfg.get('vector_server', 'host'), cfg.get('vector_server', 'port')))

        if CREATE_NEW_COLLECTION:
            print("Creating collection...")
            collection = create_collection(collection_name, 2048, "test description") # 2048 is feature dimension
            print("Collection {} created successfully.".format(collection_name))
        else:
            if utility.has_collection(collection_name):
                collection = Collection(collection_name)
                print("Connected to collection {} successfully.".format(collection_name))
                print("Total number of entities in collection {} is {}.".format(collection_name, collection.num_entities))
            else:
                print("Collection {} is not existed, please check.".format(collection_name))
                sys.exit("The selected collection is not existed, please check")

    op = ops.image_embedding.timm(model_name='resnet50')

    id_list = []
    label_list = []
    vec_list = []

    start = time.time()

    hf = h5py.File(os.path.join(data_folder, dataset_folder, 'train.h5'), 'r')
    length = len(hf.items())
    print("Total number of images in HDF5 file: {}".format(length))
    print("Start to embedding and insert vector data...")

    if INSERT_VECTOR_TO_HDF5:
        hf_vector = h5py.File(os.path.join(data_folder, dataset_folder, 'vector.h5'), 'a')
        print("Start to save embedding vector to HDF5 file...")

    for i, (key, value) in enumerate(hf.items()):
        # convert binary data to pil image
        image_data = np.array(hf[key]) 
        image_pil = Image.open(io.BytesIO(image_data))

        embedding_vector = op(from_pil(image_pil))
        norm_embedding_vector = embedding_vector / np.linalg.norm(embedding_vector)

        if INSERT_VECTOR_TO_HDF5:
            hf_vector.create_dataset(key, data=norm_embedding_vector, chunks=(2048,), compression="gzip", compression_opts=9)

        if INSERT_VECTOR_TO_COLLECTION:
            id_list.append(i)
            label_list.append(key)
            vec_list.append(norm_embedding_vector)

        if i % 100 == 0: # batch size is 100
            if INSERT_VECTOR_TO_COLLECTION:
                collection.insert([id_list, label_list, vec_list])
                id_list.clear()
                label_list.clear()
                vec_list.clear()
            progress(int((i/length) * 100))

    hf.close()
    if INSERT_VECTOR_TO_HDF5:
        hf_vector.close()

    if len(id_list) != 0:
        if INSERT_VECTOR_TO_COLLECTION:
            collection.insert([id_list, label_list, vec_list])
            id_list.clear()
            label_list.clear()
            vec_list.clear()
    progress(100)

    end = time.time()
    print("\nTotal time spent on embedding and insert: {:0.1f} seconds".format(end - start))
    if INSERT_VECTOR_TO_COLLECTION:
        print("Total number of entities in updated collection {} is {}.".format(collection_name, collection.num_entities))

    if CREATE_INDEX:
        print("Creating index...")
        start = time.time()
        create_index(collection)
        end = time.time()
        print("Index created successfully.")
        print("Total time spent on creating index: {:0.1f} seconds".format(end - start))
    
        print("Loading collection into memory...")
        collection.load()
        print("Collection loaded successfully.")
    
    connections.disconnect("default")
