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
from ..models import IntentInstance, IntentCategory
import os
import math, random
from threading import Lock
from copy import deepcopy
from . import language
from . import dataset
from copy import deepcopy
from .utils import dataframe_to_goo


def clear_augmented_entries():
    IntentInstance.objects.filter(is_synthetic=True).delete()

def do_augmentation():
    
    clear_augmented_entries()
    
    original_dataset = dataset.AugmentableDataset()
    augmented_dataset = deepcopy(original_dataset)  # is empty for now
    original_dataset.fill_intents_dict()            # filling the original dataset


    # Augmentation steps here:
    # 1. Add shuffled copies
    # cls.shuffle(intents_dict, augmented_dict, 1)

    # shuffle_dict = deepcopy(augmented_dict)
    # # 2. Add synonym replaced copies of the original and shuffled entries
    original_dataset.do_synonym_replacement(target = augmented_dataset, p=1/5, n=1, similarity=0.65)

    # cls.synonym_replacement(intents_dict, augmented_dict, p=1/5, n=1, similarity=0.85)
    # # cls.synonym_replacement(intents_dict, augmented_dict, p=1/8, n=1, similarity=0.65)
    # # cls.synonym_replacement(intents_dict, augmented_dict, p=1/10, n=1, similarity=0.55)
    # # cls.synonym_replacement(shuffle_dict, augmented_dict, p=1/10, n=1, similarity=0.85)

    # # 3. Add stemmified copies
    # cls.stemmify(intents_dict, augmented_dict)

    # # 4. Remove duplicates from the augmented list so far
    # cls.remove_duplicates(augmented_dict)

    # # 5. Add noise added copies of the augmented dataset
    # augmented_dict_1 = deepcopy(augmented_dict)
    # cls.cross_category_noise(augmented_dict_1, augmented_dict, 1, 1/2)

    # # 6. Add noise added copies of the original dataset
    # cls.cross_category_noise(intents_dict, augmented_dict, 2, 1/2)

    # # # 7. Add one more copy of the original dataset
    # cls.shuffle(intents_dict, augmented_dict, 1)

    for key, intents_list in augmented_dataset.intents_dict.items():
        '''
            adding the intents into the db with a is_synthetic flag
        '''
        
        for intent_df in intents_list:
            seq_in, seq_out = dataframe_to_goo(intent_df)
            if not IntentInstance.objects.filter(seq_in=seq_in, seq_out=seq_out):
                IntentInstance.objects.create(label=key, seq_in=seq_in, seq_out=seq_out,is_synthetic=True)



if __name__ == "__main__":
    pass