import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
NLP_DIR =  ROOT_DIR

def get_gensim_word_vectors():
    from gensim.models import KeyedVectors
    from .lemmatizer_tr import get_phrase_root
    word_vectors = KeyedVectors.load_word2vec_format(os.path.join(NLP_DIR,"trmodel"), binary=True)
    return word_vectors