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
    original_dataset.do_shuffle(target = augmented_dataset, n=1)
    copy_of_shuffled = deepcopy(original_dataset)

    # 2. Add synonym replaced copies of the original and shuffled entries
    original_dataset.do_synonym_replacement(target = augmented_dataset, p=1/5, n=1, similarity=0.65)
    copy_of_shuffled.do_synonym_replacement(target = augmented_dataset, p=1/5, n=1, similarity=0.90)

    # 3. Add stemmified copies
    original_dataset.do_stemmify(target=augmented_dataset)

    # 4. Remove duplicates from the augmented list so far
    augmented_dataset.remove_duplicates()

    # 5. Add noise that are partial intents
    # augmented_dict_1 = deepcopy(augmented_dict)
    deepcopy(augmented_dataset).add_cross_category_noise(target=augmented_dataset, n=1, fraction=1/2)

    # 6. Add noise that are partial intents
    original_dataset.add_cross_category_noise(target=augmented_dataset, n=2, fraction=1/2)

    # 7. Add noise that is complete random texts from some book
    deepcopy(augmented_dataset).add_random_noise(target=augmented_dataset, n=2)

    # 8. Add one more copy of the original dataset
    original_dataset.do_shuffle(target = augmented_dataset, n=1)

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