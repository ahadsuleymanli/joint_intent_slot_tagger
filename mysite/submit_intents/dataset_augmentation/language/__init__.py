import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
NLP_DIR =  ROOT_DIR

def get_gensim_word_vectors():
    from gensim.models import KeyedVectors
    from .lemmatizer_tr import get_phrase_root
    word_vectors = KeyedVectors.load_word2vec_format(os.path.join(NLP_DIR,"trmodel"), binary=True)
    return word_vectors

import random
import itertools

def random_line_generator(txt_name):
    file_location = os.path.join(NLP_DIR,txt_name)
    with open(file_location, 'r+') as f:
        line = next(f)
        skips_left = 0
        for aline in itertools.cycle(f):
            # print("getting",num)
            line = aline
            if skips_left == 0:
                skips_left = random.randrange(50)
                yield line
            else:
                skips_left -= 1
