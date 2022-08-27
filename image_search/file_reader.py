from utils.minio_bucket import Bucket
from minio.error import S3Error

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
import os
import io

import h5py
import numpy as np
from PIL import Image


data_folder = os.path.join(os.getcwd(), 'image_search', 'data')

train_img_folder = os.path.join(data_folder, 'image_100x10', 'train')

img_group_folders =  os.listdir(train_img_folder)

img_path_list = []

for folder in img_group_folders:
    img_paths = os.listdir(os.path.join(train_img_folder, folder))
    for img_path in img_paths:
        img_abs_path = os.path.join(train_img_folder, folder, img_path)
        img_path_list.append(img_abs_path)

print("Total images: ", len(img_path_list))

if os.name == 'nt': # windows
    separator = '\\'
else:
    separator = '/'

with h5py.File(os.path.join(data_folder, 'image_100x10', 'train.h5'), 'w') as hf:
    for i, img_path in enumerate(img_path_list):
        # using pillow to convert data, to save space in hdf5 file
        image = Image.open(img_path)
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
        
        label = '@' + img_path.split(separator)[-2] + '@' + img_path.split(separator)[-1]

        hf.create_dataset(label, data=image_np)

        if i % 100 == 0:
            print("Saving images in HDF5: {:0.0f}%".format((i/len(img_path_list)) * 100))

print("Saving images in HDF5: 100%")    

with h5py.File(os.path.join(data_folder, 'image_100x10', 'train.h5'), 'r') as hf:
    for i, (key, value) in enumerate(hf.items()):
        #print(key)
        #img = hf[key][:]
        if (i == 0):
            print(i, key, value)
            data = np.array(hf[key]) 
            img = Image.open(io.BytesIO(data))
            print('image size:', img.size)

    hf.close()
