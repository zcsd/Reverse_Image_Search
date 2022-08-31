import os
from minio import Minio
from minio.error import S3Error
from datetime import timedelta
from minio.deleteobjects import DeleteObject

class Bucket(object):
    client = None
    policy = '{"Version":"2022-05-22","Statement":[{"Effect":"Allow","Principal":{"AWS":["*"]},"Action":["s3:GetBucketLocation","s3:ListBucket"],"Resource":["arn:aws:s3:::%s"]},{"Effect":"Allow","Principal":{"AWS":["*"]},"Action":["s3:GetObject"],"Resource":["arn:aws:s3:::%s/*"]}]}'
    
    def __new__(cls, *args, **kwargs):
        if not cls.client:
            cls.client = object.__new__(cls)
        return cls.client

    def __init__(self, service, access_key, secret_key, secure=False):
        self.service = service
        self.client = Minio(service, access_key=access_key, secret_key=secret_key, secure=secure)
        
    def exists_bucket(self, bucket_name):
        """
        check if bucket exists
        :param bucket_name:
        :return:
        """
        return self.client.bucket_exists(bucket_name=bucket_name)

    def create_bucket(self, bucket_name:str, is_policy:bool=True):
        """
        create bucket and set policy
        :param bucket_name:
        :param is_policy: 
        :return:
        """
        if self.exists_bucket(bucket_name=bucket_name):
            return False
        else:
            self.client.make_bucket(bucket_name = bucket_name)
        if is_policy:
            policy = self.policy % (bucket_name, bucket_name)
            self.client.set_bucket_policy(bucket_name=bucket_name, policy=policy)
        return True

    def get_bucket_list(self):
        """
        list buckets
        :return:
        """
        buckets = self.client.list_buckets()
        bucket_list = []
        for bucket in buckets:
            bucket_list.append(
                {"bucket_name": bucket.name, "create_time": bucket.creation_date}
            )
        return bucket_list

    def remove_bucket(self, bucket_name):
        """
        remove bucket
        :param bucket_name:
        :return:
        """
        try:
            self.client.remove_bucket(bucket_name=bucket_name)
        except S3Error as e:
            print("[error]:", e)
            return False
        return True

    def bucket_list_files(self, bucket_name, prefix):
        """
        list all files in bucket
        :param bucket_name: 
        :param prefix: 
        :return:
        """
        try:
            files_list = self.client.list_objects(bucket_name=bucket_name, prefix=prefix, recursive=True)
            files_name = []
            for obj in files_list:
                files_name.append(obj.object_name)
                #print(obj.bucket_name, obj.object_name.encode('utf-8'), obj.last_modified,
                #      obj.etag, obj.size, obj.content_type)
            return files_name
        except S3Error as e:
            print("[error]:", e)
            return []

    def bucket_policy(self, bucket_name):
        """
        get bucket policy
        :param bucket_name:
        :return:
        """
        try:
            policy = self.client.get_bucket_policy(bucket_name)
        except S3Error as e:
            print("[error]:", e)
            return None
        return policy

    def download_file(self, bucket_name, file, file_path, stream=1024*32):
        """
        download file from bucket and write to file
        :return:
        """
        try:
            data = self.client.get_object(bucket_name, file)
            with open(file_path, "wb") as fp:
                for d in data.stream(stream):
                    fp.write(d)
        except S3Error as e:
            print("[error]:", e)

    def fget_file(self, bucket_name, file, file_path):
        """
        download file from bucket and save to local file
        :param bucket_name:
        :param file:
        :param file_path:
        :return:
        """
        self.client.fget_object(bucket_name, file, file_path)

    def copy_file(self, bucket_name, file, file_path):
        """
        copy file from bucket to local file (max 5GB)
        :param bucket_name:
        :param file:
        :param file_path:
        :return:
        """
        self.client.copy_object(bucket_name, file, file_path)

    def upload_file(self,bucket_name, file, file_path, content_type):
        """
        upload file and write to bucket
        :param bucket_name: 
        :param file: 
        :param file_path: 
        :param content_type: 
        :return:
        """
        try:
            with open(file_path, "rb") as file_data:
                file_stat = os.stat(file_path)
                self.client.put_object(bucket_name, file, file_data, file_stat.st_size, content_type=content_type)
            return True
        except S3Error as e:
            print("[error]:", e)
            return False

    def fput_file(self, bucket_name, file, file_path):
        """
        upload file 
        :param bucket_name:
        :param file: 
        :param file_path: 
        :return:
        """
        try:
            self.client.fput_object(bucket_name, file, file_path)
            return True
        except S3Error as e:
            print("[error]:", e)
            return False

    def stat_object(self, bucket_name, file):
        """
        get metadata of object
        :param bucket_name:
        :param file:
        :return:
        """
        try:
            data = self.client.stat_object(bucket_name, file)
            print(data.bucket_name)
            print(data.object_name)
            print(data.last_modified)
            print(data.etag)
            print(data.size)
            print(data.metadata)
            print(data.content_type)
        except S3Error as e:
            print("[error]:", e)

    def remove_file(self, bucket_name, file):
        """
        remove single file
        :return:
        """
        self.client.remove_object(bucket_name, file)

    def remove_files(self, bucket_name, file_list):
        """
        remove mutiple files
        :return:
        """
        delete_object_list = [DeleteObject(file) for file in file_list]
        for del_err in self.client.remove_objects(bucket_name, delete_object_list):
            print("del_err", del_err)

    def presigned_get_file(self, bucket_name, file, days=7):
        """
        presigned a http get operation, signed URL for 7 days
        :return:
        """
        return self.client.presigned_get_object(bucket_name, file, expires=timedelta(days=days))
