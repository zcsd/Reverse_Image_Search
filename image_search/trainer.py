# =============================================================================
# File name: trainer.py
# Author: Zichun
# Date created: 2022/08/10
# Python Version: 3.10
# Description:
#    read images from hdf5 file
#    embedding images
#    insert embedding vectors to vector server collection
#    create index for collection
# =============================================================================

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

dataset_folder = "imagenet_1000x34" # change here
num_nlist = 750  # change here  4xsqrt(n) in each segment

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

    print("Connecting to vector server...")
    connections.connect(host=cfg.get('vector_server', 'host'),
                        port=cfg.get('vector_server', 'port'))
    print("Connected to vector server {0}:{1} successfully.".format(cfg.get('vector_server', 'host'), cfg.get('vector_server', 'port')))

    print("Creating collection...")
    collection = create_collection('imagenet_resnet_50_norm', 2048, "imagenet34000 resnet50 norm")
    print("Collection created successfully.")

    op = ops.image_embedding.timm(model_name='resnet50')

    id_list = []
    label_list = []
    vec_list = []

    start = time.time()

    with h5py.File(os.path.join(data_folder, dataset_folder, 'train.h5'), 'r') as hf:
        length = len(hf.items())
        print("Total number of images: {}".format(length))
        print("Start to embedding and insert data into vector server...")
        for i, (key, value) in enumerate(hf.items()):
            image_data = np.array(hf[key]) 
            image_pil = Image.open(io.BytesIO(image_data))
            embedding_vector = op(from_pil(image_pil))
            norm_embedding_vector = embedding_vector / np.linalg.norm(embedding_vector)
        
            id_list.append(i)
            label_list.append(key)
            vec_list.append(norm_embedding_vector)

            if i % 100 == 0: # batch size is 100
                collection.insert([id_list, label_list, vec_list])
                id_list.clear()
                label_list.clear()
                vec_list.clear()
                progress(int((i/length) * 100))

        hf.close()

    if len(id_list) != 0:
        collection.insert([id_list, label_list, vec_list])
        id_list.clear()
        label_list.clear()
        vec_list.clear()
        progress(100)

    end = time.time()
    print("\nTotal time spent on embedding and insert: {:0.1f} seconds".format(end - start))
    print('Total number of inserted data is {}.'.format(collection.num_entities))

    print("Creating index...")
    start = time.time()
    create_index(collection)
    end = time.time()
    print("Index created successfully.")
    print("Total time spent on creating index: {:0.1f} seconds".format(end - start))
    
    print("Loading collection into memory...")
    collection.load()
    print("Collection loaded successfully.")

'''
# another way to create collection
start = (
    towhee.read_csv('image_search/data/image_100x10/files_to_train.csv')
    .runas_op['id', 'id'](func=lambda x: int(x))
    .image_decode['path', 'img']()
    .image_embedding.timm['img', 'vec'](model_name='resnet50')
    .tensor_normalize['vec', 'vec']()
    .to_milvus['id', 'vec'](collection=collection, batch=100)
)
'''