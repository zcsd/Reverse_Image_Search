from utils.minio_bucket import Bucket
from minio.error import S3Error

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
    