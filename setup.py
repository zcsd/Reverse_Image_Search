from setuptools import setup, find_packages

setup(
    name="ImageSearch",  
    version="0.2.0",
    description="Reverse Image Search",
    author="Zichun",
    python_requires=">=3.8, <4",
    packages=find_packages(include=['image_search']),
    install_requires=[
        'numpy==1.23.2',
        'opencv-python-headless==4.6.0.66',
        'pillow==9.2.0',
        'flask==2.2.2',
        'flask-cors==3.0.10',
        'gevent==21.12.0',
        'torch==1.12.1',
        'torchvision==0.13.1',
        'timm==0.6.7',
        'typing-extensions==4.3.0',
        'protobuf==3.20.0',
        'grpcio-tools',
        'pymilvus==2.1.1',
        'towhee==0.8.0',
        'towhee.models==0.8.0',
        'h5py==3.7.0',
        'minio==7.1.11'
    ],
)