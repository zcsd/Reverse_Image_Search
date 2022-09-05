# =============================================================================
# File name: images_preprocess.py
# Author: Zichun
# Date created: 2022/08/25
# Python Version: 3.10
# Description:
#    - image resize or other processes
#    - images => hdf5 (binary data)
#    - images => minio object storage
# How to run:
#    python image_search/preprocess.py
# =============================================================================

import os
import io
import time

import h5py
import numpy as np
from PIL import Image

from utils.progress_helper import progress
from configparser import ConfigParser

from utils.minio_bucket import Bucket
from minio.error import S3Error

dataset_folder = "imagenet_1000x34" # change here
TO_MINIO = False # change here
TO_HDF5 = False  # change here

def upload_to_minio(bucket, file_path_on_minio, file_path_on_disk):
    try:
        bucket.fput_file(bucket_name="images", file=file_path_on_minio, file_path=file_path_on_disk)
        return True
    except S3Error as e:
        print(e)
        return False

if __name__ == '__main__':
    cfg = ConfigParser()
    cfg.read('image_search/conf/config.ini')

    data_folder = os.path.join(os.getcwd(), 'image_search', 'data')
    train_img_folder = os.path.join(data_folder, dataset_folder, 'train') 
    img_group_folders =  os.listdir(train_img_folder)

    img_path_list = []

    for folder in img_group_folders:
        img_paths = os.listdir(os.path.join(train_img_folder, folder))
        for img_path in img_paths:
            img_abs_path = os.path.join(train_img_folder, folder, img_path)
            img_path_list.append(img_abs_path)

    length_images = len(img_path_list)
    print("Total number of images to preprocess:", length_images)

    if os.name == 'nt': # windows
        separator = '\\'
    else:
        separator = '/'

    if TO_MINIO:
        counter_fail_to_upload = 0
        my_bucket = Bucket(service=cfg.get('minio_server', 'host')+':'+cfg.get('minio_server', 'port'),
                        access_key=cfg.get('minio_server', 'access_key'), 
                        secret_key=cfg.get('minio_server', 'secret_key'))
        print("Start to upload images to MINIO...")
    
    if TO_HDF5:
        hf = h5py.File(os.path.join(data_folder, dataset_folder, 'train.h5'), 'a')
        print("Start to convert images to HDF5 file...")

    print("\n")
    start = time.time()

    for i, img_path in enumerate(img_path_list):
        # using pillow to convert data, to save space in hdf5 file
        image = Image.open(img_path)
        if (image.mode != 'RGB'): # grayscale image will be converted to RGB
            image = image.convert('RGB')
        
        if TO_MINIO:
            if upload_to_minio(my_bucket, '/' + img_path.split(separator)[-2] + '/' + img_path.split(separator)[-1], img_path) == False:
                print("Failed to upload {} to minio storage".format(img_path))
                counter_fail_to_upload += 1
        
        if TO_HDF5:
            #image = image.resize((224, 224))
            image_buf = io.BytesIO()
            image.save(image_buf, format='JPEG')
            image_byte = image_buf.getvalue()

            # using opencv to convert data, to save space in hdf5 file
            #image = cv2.imread(img_path)
            #image = cv2.resize(image, (224,224), interpolation=cv2.INTER_CUBIC)
            #image_buffer = cv2.imencode(".jpeg", image)[1]
            #image_byte = image_buffer.tobytes()

            image_np = np.asarray(image_byte)
            
            # '\' can not be used in hdf5, so we use '@' instead
            label = '@' + img_path.split(separator)[-2] + '@' + img_path.split(separator)[-1]

            # no need to compress, because binary data is used
            hf.create_dataset(label, data=image_np,)

        if i % 5 == 0:
            progress(int((i/length_images) * 100))
    
    progress(100)
    print("\n")

    if TO_MINIO:
        print("Total number of images uploaded to MINIO:", length_images-counter_fail_to_upload)
    if TO_HDF5:
        print("Total number of images in new HDF5 file:", len(hf.items()))
        hf.close()

    end = time.time()
    print("Total time spent: {:.1f} seconds".format(end - start))
