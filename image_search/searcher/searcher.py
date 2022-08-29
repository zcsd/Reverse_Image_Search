import time
import numpy as np
from pymilvus import connections, Collection, utility
from towhee.types.image_utils import from_pil
from towhee import ops
from towhee.functional.entity import Entity

class Searcher:
    def __init__(self, host, port, collection_name):
        connections.connect(alias="default", host=host, port=port)

        print("Connected to vector server {0}:{1} successfully.".format(host, port))

        if utility.has_collection(collection_name):
            self.collection = Collection(collection_name)
            print('Total number of entities in {} is {}.'.format(collection_name, self.collection.num_entities))
            
            self.op = ops.image_embedding.timm(model_name='resnet50')
        else:
            print('Collection {} does not exist.'.format(collection_name))
            return

        # another way to search vector
        #with towhee.api() as api:
        #    self.search = (
        #        api.runas_op(func=lambda img: from_pil(img))
        #        .image_embedding.timm(model_name='resnet50')
        #        .tensor_normalize()
        #        .milvus_search(collection=self.collection, limit=5, output_fields=['id', 'label'])
        #        .runas_op(func=lambda res: [[x.id, x.score, x.label] for x in res])
        #        .as_function()
        #    )

        print('Image Searcher is ready to search.')

    def disconnect(self):
        connections.disconnect("default")
        print('Disconnected from vector server.')

    def get_numer_of_entities(self):
        return self.collection.num_entities

    def search(self, pil_img, nprobe=6):
        start_time = time.time() #####

        vector = self.op(from_pil(pil_img))
        norm_vector = vector / np.linalg.norm(vector)

        end_time = time.time() #####
        embedding_time = int((end_time - start_time)*1000) #####
        print("Total time spent on embedding: {} ms".format(embedding_time)) #####

        start_time = time.time() #####

        raw_results = self.collection.search([norm_vector], anns_field="embedding", param = {"metric_type": "L2", "params": {"nprobe": nprobe}}, limit=5, output_fields=['id', 'label'])
        
        end_time = time.time() #####
        search_time = int((end_time - start_time)*1000) #####
        print("Total time spent on search: {} ms".format(search_time))
        
        results = []

        for re in raw_results:
            for hit in re:
                dicts = dict(id=hit.id, distance=hit.distance)
                dicts.update(hit.entity._row_data)
                results.append(Entity(**dicts))
        # add time spent to the results       
        results.append(Entity(search_time=search_time, embedding_time=embedding_time))

        return results


