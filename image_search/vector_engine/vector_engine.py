# =============================================================================
# File name: vector_engine.py
# Author: Zichun
# Date created: 2022/08/12
# Python Version: 3.10
# Description:
#    - Class VectorEngine
# =============================================================================

import time
import numpy as np
from pymilvus import connections, Collection, utility
from towhee.types.image_utils import from_pil
from towhee import ops
from towhee.functional.entity import Entity

class VectorEngine:
    def __init__(self, host, port, collection_name):
        connections.connect('default', host=host, port=port)

        print("Connected to vector server {0}:{1} successfully.".format(host, port))

        if utility.has_collection(collection_name):
            self.collection = Collection(collection_name)
            self.num_entities = self.collection.num_entities
            print('Total number of entities in {} is {}.'.format(collection_name, self.num_entities))
            
            # preload the model
            self.op = ops.image_embedding.timm(model_name='resnet50')
        else:
            print('Collection {} does not exist.'.format(collection_name))
            return

        print('Vector Engine is ready to search.')

    def get_number_of_entities(self):
        self.num_entities = self.collection.num_entities
        return self.num_entities

    # insert single image into collection
    def insert(self, pil_img, location):
        vector = self.op(from_pil(pil_img))
        norm_vector = vector / np.linalg.norm(vector) # normalize the vector
        self.collection.insert([[self.num_entities], [location],[norm_vector]])
        print("Inserted entity {0} into collection {1} successfully.""".format(self.num_entities, self.collection.name))
        self.num_entities += 1

    def create_index(self, num_nlist=2048):
        index_params = {
            'metric_type': 'L2',
            'index_type': "IVF_FLAT",
            'params':{"nlist": num_nlist}
        }
        print("Creating index...")
        self.collection.create_index(field_name="embedding", index_params=index_params)
        print("Created index successfully.")

    def search(self, pil_img, nprobe=6):
        start_time = time.time() 

        vector = self.op(from_pil(pil_img))
        norm_vector = vector / np.linalg.norm(vector)

        end_time = time.time() 
        embedding_time = int((end_time - start_time)*1000) 
        print("Total time spent on embedding: {} ms".format(embedding_time)) 

        start_time = time.time() 
        # retrieve top 5 results, change limit to change the number of results
        raw_results = self.collection.search([norm_vector], anns_field="embedding", param = {"metric_type": "L2", "params": {"nprobe": nprobe}}, limit=5, output_fields=['id', 'label'])
        
        end_time = time.time() 
        search_time = int((end_time - start_time)*1000)
        print("Total time spent on search: {} ms".format(search_time))
        
        results = []

        # convert raw results to Entity
        for re in raw_results:
            for hit in re:
                dicts = dict(id=hit.id, distance=hit.distance)
                dicts.update(hit.entity._row_data)
                results.append(Entity(**dicts))
        # add time spent to the results entity     
        results.append(Entity(search_time=search_time, embedding_time=embedding_time))

        return results

    def disconnect(self):
        connections.disconnect('default')
        print('Disconnected from vector server.')