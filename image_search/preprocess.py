# =============================================================================
# File name: images_preprocess.py
# Author: Zichun
# Date created: 2022/08/25
# Python Version: 3.10
# Description:
#    images => hdf5
#    images => minio object storage
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

dataset_folder = "image_100x10" # change here

'''
try:
    my_bucket = Bucket(service="localhost:8000", access_key="user1", secret_key="user1password")
    if my_bucket.exists_bucket(bucket_name="images"):
        print("bucket exists")
        print(my_bucket.bucket_list_files(bucket_name="images", prefix=""))
        #my_bucket.download_file(bucket_name="images", file="gear11.JPEG", file_path="upload/test.jpeg")
        #my_bucket.fget_file(bucket_name="images", file="test11.JPEG", file_path="upload/test11.jpeg")
        
        #my_bucket.fput_file(bucket_name="images", file="test11.JPEG", file_path="upload/2022-08-23_22-09-07_046190.JPEG")
        #my_bucket.upload_file(bucket_name="images", file="test12.JPEG", file_path="upload/2022-08-23_22-09-07_046190.JPEG", content_type="image/jpeg")
    else:
        print("bucket not exists")
except S3Error as e:
    print("error:", e)
'''

if __name__ == '__main__':
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
    print("Total number of images:", length_images)

    if os.name == 'nt': # windows
        separator = '\\'
    else:
        separator = '/'

    print("Start to convert images to hdf5 file...")
    start = time.time()

    with h5py.File(os.path.join(data_folder, dataset_folder, 'train.h5'), 'w') as hf:
        for i, img_path in enumerate(img_path_list):
            # using pillow to convert data, to save space in hdf5 file
            image = Image.open(img_path)
            if (image.mode != 'RGB'): # grayscale image will be converted to RGB
                image = image.convert('RGB')
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
            hf.create_dataset(label, data=image_np)

            if i % 5 == 0:
                progress(int((i/length_images) * 100))

        hf.close()

    progress(100)

    end = time.time()
    print("\nTotal time spent: {:.1f} seconds".format(end - start))