import numpy as np 
import pandas as pd 
from ..models import IntentInstance, IntentCategory
from .utils import goo_to_dataframe, dataframe_to_goo, get_augmentation_settings, get_phrase_synonym
from .utils import RandomRecordPicker
from .utils import scramble_the_phrase
from .utils import word_vectors
from copy import deepcopy
import random
from .language import random_line_generator
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


def prevent_augmenting_self(func):
    def inner(self, *args, **kwargs):
        if "target" in kwargs:
            target = kwargs["target"]
        else:
            target = args[0]
        if target is self:
            raise Exception('Should not augment self')
        func(self,*args, **kwargs)
    return inner

class AugmentableDataset:
    print("here")
    def __init__(self):
        self._intents_dict = {}
        self._augmentation_settings_dict = get_augmentation_settings()

    @property
    def intents_dict(self):
        return self._intents_dict

    def __copy__(self):
        raise Exception('Should not be shallow copied')

    def __deepcopy__(self, memo):
        obj = AugmentableDataset()
        obj._intents_dict = deepcopy(self._intents_dict, memo)
        obj._augmentation_settings_dict = deepcopy(self._augmentation_settings_dict, memo)
        return obj

    def add_to_dict(self,intent_name,intent_df, target):
        '''
            writes the intent to the target AugmentedDataset object's dictionary
        '''
        if intent_name not in target._intents_dict:
            target._intents_dict[intent_name] = [intent_df,]
        else:
            self.handle_unique_requirement(intent_df, target._intents_dict[intent_name])
            target._intents_dict[intent_name].append(intent_df)
    
    def fill_intents_dict(self):
        '''
            fill the initial self._intents_dict from the original un-augmented dataset
        '''
        unique_labels = IntentInstance.objects.values_list("label",flat=True).distinct()
        unique_labels = [x for x in unique_labels]
        for intent_label in unique_labels:
            '''
                creating a dict of intent categories mapped to Intent objects
            '''
            intents_by_label = IntentInstance.objects.filter(label=intent_label)
            augmentation_setting_df = self._augmentation_settings_dict[intent_label]
            for intent in intents_by_label:
                df = goo_to_dataframe(intent.seq_in,intent.seq_out)
                '''
                outer join augmentation settings
                '''
                df = pd.merge(df,augmentation_setting_df,on='SLOT',how='left')
                self.add_to_dict(intent_label,df, target=self)

    #TODO: fix list creation at every step
    #TODO: implement comparison between same SLOTs instead of comparing everything with UNIQUE_VALUES like now
    def handle_unique_requirement(self,intent_df, rest_of_dfs):
        '''
            checks if specified slot values are unique amongst other intents
        '''
        uniques_series = intent_df[intent_df["UNIQUE_VALUES"]==True]["TOKEN"]
        if uniques_series.empty:
            return
        # uniques_series = intent_df[intent_df["UNIQUE_VALUES"]==True]["SLOT"]
        rest_of_items_ = [df[df["UNIQUE_VALUES"]==True]["TOKEN"] for df in rest_of_dfs]
        rest_of_items = []
        for x in rest_of_items_:
            for i,item in x.items():
                rest_of_items.append(item)
        for i, item in uniques_series.items():
            if item in rest_of_items:
                intent_df.at[i,"TOKEN"] = scramble_the_phrase(item,[])

    @prevent_augmenting_self
    def do_synonym_replacement(self, target, p=1/5, n=1, similarity=0.7):
        '''
            target: target AugmentableDataset object
            p: chance to replace each word
            n: is number of times to work on a sentence
        '''
        # TODO try to use different replacement synonyms on each intent throughout a category
        # from gensim.models import KeyedVectors

        # from .language import get_gensim_word_vectors
        # word_vectors = get_gensim_word_vectors()

        for key, intents_list in self._intents_dict.items():
            words_already_used = []
            for i in range(n):
                '''
                    do this operation n times, per specification
                '''
                for intent_df in intents_list:
                    
                    intent_df = intent_df.copy(deep=True) #creating a deep copy that will be modified
                    # allowed_intents_df = intent_df[intent_df['EXCEMPT_SYNON'] != True]
                    # unallowed_syonym_intents_df = intent_df[intent_df['EXCEMPT_SYNON'] == True]
                    for i, row in intent_df.iterrows():
                        rand = random.randint(0,10)/10
                        if rand<p or True:
                            '''
                                with p chance replace the word with its synonym or root's synonym
                                if the word is in any ignorelist, act accordingly
                            '''
                            dont_stemmify_ = True if any([x is True for x in [intent_df.at[i,"EXCEMPT_STEMM"], intent_df.at[i,"EXCEMPT_SYNON"]]]) else False
                            similarity_ = 0.95 if intent_df.at[i,"EXCEMPT_SYNON"] is True else similarity
                            intent_df.at[i,"TOKEN"] = get_phrase_synonym(row.TOKEN,words_already_used,word_vectors,similarity=similarity_,dont_stemmify = dont_stemmify_)
                        self.add_to_dict(key,intent_df, target)
    @prevent_augmenting_self
    def do_shuffle(self, target, n=1):
        '''
            n: number of times to repeat the step. each time new record is added
            target: AugmentableDataset where the records will be stored
        '''
        for key, intents_list in self._intents_dict.items():
            for i in range(n):
                for intent_df in intents_list:
                    intent_df = intent_df.copy(deep=True) #creating a deep copy that will be modified
                    allowed_indexes = list(intent_df[intent_df['EXCEMPT_SHUFF'] != True].index.values)
                    
                    #TODO: implement pushing the swappable into the indexes 0 and -1
                    if len(allowed_indexes) > 1:
                        idx1 = random.choice(allowed_indexes)
                        allowed_indexes.remove(idx1)   
                        idx2 = random.choice(allowed_indexes)
                        
                        temp = intent_df.iloc[idx1].copy(deep=True)
                        intent_df.iloc[idx1] = intent_df.iloc[idx2]
                        intent_df.iloc[idx2] = temp

                        self.add_to_dict(key,intent_df,target)
    @prevent_augmenting_self
    def do_stemmify(self, target):
        '''
            target: AugmentableDataset
        '''
        from .language.lemmatizer_tr import get_phrase_root
        for key, intents_list in self._intents_dict.items():
            for intent_df in intents_list:
                intent_df = intent_df.copy(deep=True) #creating a deep copy that will be modified
                for i, row in intent_df.iterrows():
                    intent_df.at[i,"TOKEN"] = get_phrase_root(intent_df.at[i,"TOKEN"])
                self.add_to_dict(key,intent_df,target)

    def remove_duplicates(self):
        for key, intents_list in self._intents_dict.items():
            indexes_to_pop = set()
            list_len = len(intents_list)
            for i in range(list_len):
                for j in range(i+1,list_len):
                    if intents_list[i].equals(intents_list[j]):
                        indexes_to_pop.add(j)
            for i in sorted(indexes_to_pop, reverse=True):
                self._intents_dict[key].pop(i)

    @prevent_augmenting_self
    def add_cross_category_noise(self,target,n,fraction):
        '''
            n times per intent
            fraction of unrelated intent to add to the start and the tail of the intent
        '''
        from math import ceil, floor
        chance_to_omit = 1/8
        record_picker = RandomRecordPicker(self.intents_dict)
        for key, intents_list in self._intents_dict.items():
            for intent_df in intents_list:
                seq_in,seq_out = dataframe_to_goo(intent_df)
                
                # create noise sequences to be added to head and tail of the original sequence
                noise_head,_ = dataframe_to_goo(record_picker.pick_record_randomly(key))
                noise_head = " ".join(noise_head.split()[ceil(len(noise_head.split())/2):])
                noise_head_seqout = " ".join(["O"]*len(noise_head.split()))
                noise_tail,_ = dataframe_to_goo(record_picker.pick_record_randomly(key))
                noise_tail = " ".join(noise_tail.split()[:floor(len(noise_tail.split())/2)])
                noise_tail_seqout = " ".join(["O"]*len(noise_tail.split()))

                rand = random.randint(0,10)/10
                if rand<chance_to_omit:
                    noise_head = ""
                    noise_head_seqout = ""
                elif rand<chance_to_omit*2:
                    noise_tail = ""
                    noise_tail_seqout = ""
                elif rand<chance_to_omit*5:
                    continue

                if noise_head:
                    seq_in = noise_head + " " + seq_in
                    seq_out = noise_head_seqout + " " + seq_out
                if noise_tail:
                    seq_in = seq_in + " " + noise_tail
                    seq_out = seq_out + " " + noise_tail_seqout

                resultant_intent_df = goo_to_dataframe(seq_in,seq_out)
                augmentation_setting_df = self._augmentation_settings_dict[key]
                resultant_intent_df = pd.merge(resultant_intent_df,augmentation_setting_df,on='SLOT',how='left')
                self.add_to_dict(key,resultant_intent_df,target)
    
    @prevent_augmenting_self
    def add_random_noise(self,target,n):
        '''
            n times per intent

        '''

        gen = random_line_generator()

        from math import ceil, floor
        chance_to_omit = 1/8
        for key, intents_list in self._intents_dict.items():
            for intent_df in intents_list:
                seq_in,seq_out = dataframe_to_goo(intent_df)
                seq_len = len(seq_in)
                # create noise sequences to be added to head and tail of the original sequence
                noise_head = next(gen)
                noise_head = noise_head[:80] if seq_len<60 else noise_head[:50]
                noise_head = " ".join(noise_head.split()[ceil(len(noise_head.split())/2):])
                noise_head_seqout = " ".join(["O"]*len(noise_head.split()))
                noise_tail = next(gen)
                noise_tail = noise_tail[:80] if seq_len<60 else noise_tail[:50]
                noise_tail = " ".join(noise_tail.split()[:floor(len(noise_tail.split())/2)])
                noise_tail_seqout = " ".join(["O"]*len(noise_tail.split()))

                rand = random.randint(0,10)/10
                if rand<chance_to_omit:
                    noise_head = ""
                    noise_head_seqout = ""
                elif rand<chance_to_omit*2:
                    noise_tail = ""
                    noise_tail_seqout = ""
                elif rand<chance_to_omit*5:
                    continue

                if noise_head:
                    seq_in = noise_head + " " + seq_in
                    seq_out = noise_head_seqout + " " + seq_out
                if noise_tail:
                    seq_in = seq_in + " " + noise_tail
                    seq_out = seq_out + " " + noise_tail_seqout

                resultant_intent_df = goo_to_dataframe(seq_in,seq_out)
                augmentation_setting_df = self._augmentation_settings_dict[key]
                resultant_intent_df = pd.merge(resultant_intent_df,augmentation_setting_df,on='SLOT',how='left')
                self.add_to_dict(key,resultant_intent_df,target)
