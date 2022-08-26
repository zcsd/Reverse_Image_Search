from configparser import ConfigParser

import towhee
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility

def create_milvus_collection(collection_name, dim):
    if utility.has_collection(collection_name):
        #utility.drop_collection(collection_name)
        print('collection exsits')
        return
    
    fields = [
    FieldSchema(name='id', dtype=DataType.INT64, descrition='ids', is_primary=True, auto_id=False),
    FieldSchema(name='embedding', dtype=DataType.FLOAT_VECTOR, descrition='embedding vectors', dim=dim)
    ]
    schema = CollectionSchema(fields=fields, description='resnet50 with norm')
    collection = Collection(name=collection_name, schema=schema)

    # create IVF_FLAT index for collection.
    index_params = {
        'metric_type':'L2',
        'index_type':"IVF_FLAT",
        'params':{"nlist":2048}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    
    return collection

if __name__ == '__main__':
    cfg = ConfigParser()
    cfg.read('image_search/conf/config.ini')

    connections.connect(host=cfg.get('vector_server', 'host'),
                        port=cfg.get('vector_server', 'port'))

    collection = create_milvus_collection('resnet_50_norm', 2048)

    start = (
        towhee.read_csv('image_search/data/image_100x10/files_to_train.csv')
        .runas_op['id', 'id'](func=lambda x: int(x))
        .image_decode['path', 'img']()
        .image_embedding.timm['img', 'vec'](model_name='resnet50')
        .tensor_normalize['vec', 'vec']()
        .to_milvus['id', 'vec'](collection=collection, batch=100)
    )

    print('Total number of inserted data is {}.'.format(collection.num_entities))