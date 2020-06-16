import numpy as np 
import pandas as pd 
from ..models import IntentInstance, IntentCategory
from .language.lemmatizer_tr import get_phrase_root
'''
#### augmentation_setting dataframes are of the form:
SendEmail                EXCEMPT_STEMM  EXCEMPT_SYNON EXCEMPT_SHUFF UNIQUE_VALUES
SLOT                                                                   
empty_message            NaN            NaN           NaN           NaN
empty_subject            NaN            NaN           NaN           NaN
message                  NaN            NaN          True          True
message_end              NaN            NaN          True           NaN
message_start            NaN            NaN          True           NaN
name                     NaN            NaN           NaN           NaN
send_email               NaN            NaN           NaN           NaN
subject                  NaN            NaN          True          True
subject_end              NaN            NaN          True           NaN
subject_start            NaN            NaN          True           NaN

#### intent dataframes are of the form:
                            TOKEN           SLOT  EXCEMPT_STEMM  EXCEMPT_SYNON EXCEMPT_SHUFF UNIQUE_VALUES
0                 mesaj içeriğini  message_start            NaN            NaN          True           NaN
1  hadi gel köyümüze geri dönelim        message            NaN            NaN          True          True
2                             yap     send_email            NaN            NaN           NaN           NaN 
'''


def goo_to_dataframe(seq_in,seq_out):
    seq_in_ = seq_in.split()
    seq_out_ = seq_out.split()
    seq_in_list = [seq_in_[0]]
    seq_out_list = [seq_out_[0]]
    for i, (word, token) in enumerate(zip(seq_in_[1:],seq_out_[1:])):
        if token.startswith("I-") and (seq_out_list[-1].startswith("B-") or seq_out_list[-1].startswith("I-")):
            seq_in_list[-1] += " " + word
            seq_out_list[-1] += " " + token
        else:
            seq_in_list.append(word)
            seq_out_list.append(token)
    #collaplse seq_out_list tokens into single names:
    seq_out_list = [x.split()[0].replace("B-","",1) for x in seq_out_list]
        
    df = pd.DataFrame({"TOKEN":np.array(seq_in_list),"SLOT":np.array(seq_out_list)})
    return df


def dataframe_to_goo(dataframe):
    seq_in = []
    seq_out = []
    for row in dataframe.itertuples():
        seq_in.append(row.TOKEN)
        if row.SLOT != "O":
            seq_out.append("B-"+row.SLOT)
            seq_out.extend(["I-"+row.SLOT for x in range(len(row.TOKEN.split()[1:]))])
        else:
            seq_out.extend([row.SLOT for x in range(len(row.TOKEN.split()))])
    seq_in = " ".join(seq_in)
    seq_out = " ".join(seq_out)
    return seq_in, seq_out


def get_augmentation_settings():
    '''
        returns a dictionary of augmentation setting dataframes
    '''
    augmentation_settings = {}
    intent_objects = IntentCategory.objects.all()

    def get_slot_list(querylist):
        return [x["slot_name"] for x in querylist]
    for i in range(len(intent_objects)):
        slots = intent_objects[i].intentslot_set
        columns = {}  
        columns["EXCEMPT_STEMM"] = get_slot_list(slots.filter(excempt_stemmify=True).values('slot_name'))
        columns["EXCEMPT_SYNON"] = get_slot_list(slots.filter(excempt_synonym=True).values('slot_name'))
        columns["EXCEMPT_SHUFF"]  = get_slot_list(slots.filter(excempt_shuffle=True).values('slot_name'))
        columns["UNIQUE_VALUES"] = get_slot_list(slots.filter(unique_values_only=True).values('slot_name'))
        
        df_index = get_slot_list(slots.values('slot_name'))
        df = pd.DataFrame(index=df_index)
        df.index.name = "SLOT"
        for (key, values) in columns.items():
            column =  pd.Series(np.array([True for x in range(len(values))]),index=np.array(values))
            df[key] = column
        augmentation_settings[intent_objects[i].intent_label] = df
    return augmentation_settings


synonym_cache = {}

def synonym_cacher(key,word_vectors):
    '''
        caching synonym generation
    '''
    global synonym_cache
    if key in synonym_cache:
        return synonym_cache[key]
    else:
        try:
            vec = word_vectors.most_similar(positive=[key],negative=[])
        except:
            vec = None
        synonym_cache[key] = vec
        return vec

def get_synonym(word,words_already_used,similarity,word_vectors,dont_stemmify=False):
    '''
        returns the synonym
        if can't the synonym of the root, and if still cant returns None
    '''
    def get_synonym_helper(word,words_already_used,similarity):
        vec = synonym_cacher(word,word_vectors)
        if vec is None:
            return None
        for i,(word,score) in enumerate(vec):
            if score < similarity:
                vec = vec[:i]
                break
        for word,score in vec:
            if word not in words_already_used:
                words_already_used.append(word)
                return word
        return None

    synonym = get_synonym_helper(word,words_already_used,similarity)
    if synonym:
        return synonym
    elif not dont_stemmify:
        return get_synonym_helper(get_phrase_root(word),words_already_used,similarity)
    else:
        return None

def get_phrase_synonym(phrase,words_already_used,similarity,word_vectors,dont_stemmify=False):
    phrase_synonym = []
    for word in phrase.split():
        synonym = get_synonym(phrase,words_already_used,similarity,word_vectors,dont_stemmify=False)
        phrase_synonym.append(synonym)
    return " ".join(phrase_synonym)

# def group_words_into_slots(seq_in,seq_out):
#     '''
#         returns seq_in_list and seq_out_list 
#         where the lists contain token strings that are grouped words
#     '''
#     seq_in_ = seq_in.split()
#     seq_out_ = seq_out.split()
#     seq_in_list = [seq_in[0]]
#     seq_out_list = [seq_out[0]]

#     for i, (word, token) in enumerate(zip(seq_in_[1:],seq_out_[1:])):
#         if token.startswith("I-") and (seq_out_list[-1].startswith("B-") or seq_out_list[-1].startswith("I-")):
#             seq_in_list[-1] += " " + word
#             seq_out_list[-1] += " " + token
#         else:
#             seq_in_list.append(word)
#             seq_out_list.append(token)

#     return seq_in_list, seq_out_list