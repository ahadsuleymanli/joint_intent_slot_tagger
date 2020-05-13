'''
    augments dataset using following strategies:
    -Intent Permutation (IP): Permutate all datums in an intent
    -Root versions (RV): Copy datums n times with 1/n of their tokens replaced with their roots
    In each synthesized datum :
    -Synonym Replacement (SR): Randomly replace n non-token words in the sentences with their synonyms.
    -Random Insertion (RI): Insert random synonyms of words in a sentence, this is done n times.
    -Random Swap (RS): Two words in the sentences are randomly swapped, this is repeated n-times.
    -Random Deletion (RD): Random removal for each non-token word in the sentence with a probability p.
    Multiply each datum n times for NA:
    -Cross category noise addition (CCNA): Start and trail intents with parts from unrelated intents.  n-times per intent.
    -Noise Addition (NA): Insert random non-related words as noise.
'''
from .models import IntentInstance
import os
import math
def get_dir(path,dir_name):
    path_to_dir = os.path.join(path, dir_name)
    if not os.path.exists(path_to_dir):
        os.makedirs(path_to_dir)
    return path_to_dir

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = get_dir(ROOT_DIR, 'dataset')
IMPORT_DIR = get_dir(ROOT_DIR, 'dataset_import')
SPLIT_DIRS = [get_dir(DATASET_DIR, x) for x in ["train","valid","test"] ]

class AugmentDataset:
    @staticmethod
    def add_to_dict(intents_dict,key,value):
        '''
            if key doesnt exist in the dictionary, create
            if exists append the value to the key's array
        '''
        if key not in intents_dict:
            intents_dict[key] = [value,]
        else:
            intents_dict[key].append(value)
    @classmethod
    def do_augmentation(cls):
        # TODO: clear augmented data first
        IntentInstance.objects.filter(is_augmentation=True).delete()
        intents_dict = {}
        augmented_dict = {}
        unique_labels = IntentInstance.objects.values_list("label",flat=True).distinct()
        unique_labels = [x for x in unique_labels]
        
        for intent_label in unique_labels:
            '''
                creating a dict of intent categories mapped to an array of intents 
            '''
            intents_by_label = IntentInstance.objects.filter(label=intent_label)
            for intent in intents_by_label:
                cls.add_to_dict(intents_dict, intent_label, (intent.seq_in,intent.seq_out))

        cls.cross_category_noise(intents_dict,augmented_dict, 2, 1/2)
        # print(augmented_dict)
        for key in augmented_dict:
            for intent in augmented_dict[key]:
                seq_in = intent[0]
                seq_out = intent[1]
                if not IntentInstance.objects.filter(seq_in=seq_in, seq_out=seq_out):
                    IntentInstance.objects.create(label=key, seq_in=seq_in, seq_out=seq_out,is_augmentation=True)
    @staticmethod
    def clear_augmented_entries():
        IntentInstance.objects.filter(is_augmentation=True).delete()


    @staticmethod
    def permutate(intents_dict,augmented_dict):
        pass

    @staticmethod
    def check_duplicates(intents_dict,augmented_dict):
        pass

    @staticmethod
    def noise_addition(intents_dict,augmented_dict):
        pass
    @classmethod
    def cross_category_noise(cls,intents_dict,augmented_dict, n, fraction):
        '''
            n times per intent
            fraction of unrelated intent to add to the start and the tail of the intent
        '''
        class Counter:
            def __init__(self):
                self.counters = []
                self.key_id = 0
        counter_obj = Counter()
        for category_id, key in enumerate(list(intents_dict)):
            generator = cls.intent_head_tail_generator(counter_obj, intents_dict, category_id,fraction)
            for (seq_in, seq_out) in intents_dict[key]:
                for i in range(n):
                    start = next(generator)
                    trail = next(generator)
                    start_seq_out = " ".join(["O"]*len(start.split()))
                    trail_seq_out = " ".join(["O"]*len(trail.split()))
                    augmented_seq_in = start + " " + seq_in + " " + trail
                    augmented_seq_out = start_seq_out + " " + seq_out + " " + trail_seq_out
                    cls.add_to_dict(augmented_dict, key, (augmented_seq_in,augmented_seq_out))
        
    @staticmethod
    def intent_head_tail_generator(counter_obj, intents_dict, current_id, fraction):
        # TODO 0.5 chance to add a random word in between
        intents_count = len(intents_dict)
        assert intents_count > 1
        # initialize counters if empty
        
        if counter_obj.counters == []:
            counter_obj.counters = [0]*intents_count
        counters = counter_obj.counters
        from math import ceil, floor
        def get_next_intent():
            if counter_obj.key_id == current_id:
                counter_obj.key_id = (counter_obj.key_id+1)%intents_count
            intents = list(intents_dict.values())[counter_obj.key_id]
            seq_in_arr = intents[counters[counter_obj.key_id]][0].split()
            counters[counter_obj.key_id] = (counters[counter_obj.key_id]+1)%len(intents)
            counter_obj.key_id = (counter_obj.key_id+1)%intents_count
            return seq_in_arr
        while True:
            '''
                get a tail of intent
            '''
            seq_in_arr = get_next_intent()
            yield " ".join(seq_in_arr[floor(len(seq_in_arr)*fraction):])
            '''
                get a head of intent
            '''
            seq_in_arr = get_next_intent()
            yield " ".join(seq_in_arr[:ceil(len(seq_in_arr)*fraction)])

