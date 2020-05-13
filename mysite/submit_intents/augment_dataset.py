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
import math, random
def get_dir(path,dir_name):
    path_to_dir = os.path.join(path, dir_name)
    if not os.path.exists(path_to_dir):
        os.makedirs(path_to_dir)
    return path_to_dir

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
NLP_DIR =  os.path.join(ROOT_DIR, "nlp")


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
        from copy import deepcopy
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

        # Augmentation steps here:
        cls.shuffle(intents_dict, augmented_dict, 1)
        cls.lemmatize(intents_dict, augmented_dict)
        augmented_dict_1 = deepcopy(augmented_dict)
        cls.cross_category_noise(augmented_dict_1, augmented_dict, 1, 1/2)
        cls.cross_category_noise(intents_dict, augmented_dict, 2, 1/2)
        cls.shuffle(intents_dict, augmented_dict, 1)

        for key in augmented_dict:
            '''
                adding the intents into the db with a is_augmentation flag
            '''
            for intent in augmented_dict[key]:
                seq_in = intent[0]
                seq_out = intent[1]
                if not IntentInstance.objects.filter(seq_in=seq_in, seq_out=seq_out):
                    IntentInstance.objects.create(label=key, seq_in=seq_in, seq_out=seq_out,is_augmentation=True)


    @classmethod
    def permutate(cls,intents_dict, augmented_dict):
        pass 

    @classmethod
    def synonym_replacement(cls,intents_dict, augmented_dict, p, n):
        '''
            p chance to replace each word
            n is number of times to work on a sentence
        '''
        # TODO try to use different replacement synonyms on each intent throughout a category
        from gensim.models import KeyedVectors
        word_vectors = KeyedVectors.load_word2vec_format(os.path.join(NLP_DIR,"trmodel"), binary=True)
        ret = []
        vec = word_vectors.most_similar(positive=["geliyor","gitmek"],negative=["gelmek"])
        for (word,score) in vec:
            pass
        print(vec)
    

    @classmethod
    def shuffle(cls, intents_dict, augmented_dict, n):
        for category_id, key in enumerate(list(intents_dict)):
            for (seq_in, seq_out) in intents_dict[key]:
                for i in range(n):
                    seq_in, seq_out = cls.extract_slots(seq_in, seq_out)
                    len_seq = len(seq_in)
                    idx1 = random.randint(0, len_seq-1)
                    idx2 = idx1
                    if len_seq < 2:
                        break
                    while idx2 == idx1:
                        idx2 = random.randint(0, len_seq-1)
                    temp = [seq_in[idx1],seq_out[idx1]]
                    seq_in[idx1]=seq_in[idx2]
                    seq_out[idx1]=seq_out[idx2]
                    seq_in[idx2]=temp[0]
                    seq_out[idx2]=temp[1]
                    seq_in = " ".join(seq_in)
                    seq_out = " ".join(seq_out)
                    cls.add_to_dict(augmented_dict, key, (seq_in,seq_out))

    @classmethod
    def lemmatize(cls, intents_dict, augmented_dict):
        '''
            lemmatizes each word in the sentence
        '''
        from .nlp.lemmatizer_tr import get_phrase_root
        for category_id, key in enumerate(list(intents_dict)):
            for intent in intents_dict[key]:
                seq_in, seq_out = intent
                seq_in = seq_in.split()
                for i in range(len(seq_in)):
                    seq_in[i] = get_phrase_root(seq_in[i])
                seq_in = " ".join(seq_in)
                cls.add_to_dict(augmented_dict, key, (seq_in,seq_out))

    @staticmethod
    def extract_slots(seq_in,seq_out):
        '''
            groups words into tokens a list of tokens 
        '''
        seq_in = seq_in.split()
        seq_out = seq_out.split()
        seq_in_arr = [seq_in[0]]
        seq_out_arr = [seq_out[0]]
        for word, token in zip(seq_in[1:],seq_out[1:]):
            if token.startswith("I-") and (seq_out_arr[-1].startswith("B-") or seq_out_arr[-1].startswith("I-")):
                seq_in_arr[-1] += " " + word
                seq_out_arr[-1] += " " + token
            else:
                seq_in_arr.append(word)
                seq_out_arr.append(token)
        return seq_in_arr, seq_out_arr

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
                get the tail of an intent
            '''
            seq_in_arr = get_next_intent()
            yield " ".join(seq_in_arr[floor(len(seq_in_arr)*fraction):])
            '''
                get the head of an intent
            '''
            seq_in_arr = get_next_intent()
            yield " ".join(seq_in_arr[:ceil(len(seq_in_arr)*fraction)])

    @staticmethod
    def clear_augmented_entries():
        IntentInstance.objects.filter(is_augmentation=True).delete()

if __name__ == "__main__":
    AugmentDataset.synonym_replacement(None,None,1,1)