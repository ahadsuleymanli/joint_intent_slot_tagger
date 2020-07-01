import numpy as np 
import pandas as pd 
from ..models import IntentInstance, IntentCategory
from .language.lemmatizer_tr import get_phrase_root
import random
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
#TODO: singleton this in a way that it leaves scope after augmentation is done?
from .language import get_gensim_word_vectors
word_vectors = get_gensim_word_vectors()

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
        except KeyError:
            vec = None
        synonym_cache[key] = vec
        return vec

def get_word_synonym(word,words_already_used,word_vectors,similarity,dont_stemmify=False):
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
        print(synonym)
        return synonym
    elif not dont_stemmify:
        return get_synonym_helper(get_phrase_root(word),words_already_used,similarity)
    else:
        return None

def get_phrase_synonym(phrase,words_already_used,word_vectors,similarity,dont_stemmify=False):
    phrase_synonym = []
    for word in phrase.split():
        synonym = get_word_synonym(phrase,words_already_used,word_vectors,similarity,dont_stemmify=False)
        synonym = synonym or word
        phrase_synonym.append(synonym)
    return " ".join(phrase_synonym)

class RandomRecordPicker:
    def __init__(self,_intents_dict):
        self._intents_dict = _intents_dict
        self._counters_dict = {x:0 for x in self._intents_dict}
        # self.intent_exceptions = IntentCCIgnore.objects.filter(intent.intent_name=self.ignore_intent)
    def pick_record_randomly(self,key_to_omit):
        keys_to_omit = [key_to_omit]
        IntentCategory
        excempt_keys = IntentCategory.objects.get(intent_label=key_to_omit).intentccignore_set.all().values("ignore_intent")
        print("excempt keys: ", excempt_keys)
        allowed_keys = list(self._counters_dict.keys())
        allowed_keys.remove(key_to_omit)
        # pick a key
        choice = random.choice(allowed_keys)
        # pick a record from the list
        records_list = self._intents_dict[choice]
        record = records_list[self._counters_dict[choice]]
        # increment index at the counter
        self._counters_dict[choice] = (self._counters_dict[choice] + 1)%len(records_list)

        return record     

def scramble_the_phrase(phrase, scramble_words_already_used = []):
    #swap paces:
    phrase = phrase.split()
    indexes = [i for i in range(len(phrase))]
    if len(indexes) > 1:
        idx1 = random.choice(indexes)
        indexes.remove(idx1)   
        idx2 = random.choice(indexes)
        temp = phrase[idx1]
        phrase[idx1] = phrase[idx2]
        phrase[idx2] = temp
    phrase = " ".join(phrase)
    # phrase = get_phrase_synonym(phrase,scramble_words_already_used,word_vectors,0.35,dont_stemmify=False)
    return phrase

