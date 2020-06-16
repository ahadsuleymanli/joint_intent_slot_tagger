import numpy as np 
import pandas as pd 
from ..models import IntentInstance, IntentCategory
from .utils import goo_to_dataframe, dataframe_to_goo, get_augmentation_settings, get_phrase_synonym
from copy import deepcopy
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
# class Intent:
#     '''
#         represents one datum
#         the datum is represented as a dataframe
#     '''
#     def __init__(self,seq_in,seq_out,label,augmentation_setting_df):
#         '''
#             seq_in: input string
#             seq_out: ground truth of slots
#             label: ground truth value of the category
#         '''
#         seq_in_list, seq_out_list = group_words_into_slots(seq_in,seq_out)
#         self.df = pd.DataFrame({"TOKEN":np.array(seq_in_list),"SLOT":np.array(seq_out_list)})
#     def get_strings(self):
#         '''
#             returns seq_in, seq_out, label
#         '''
#         pass

class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance

class AugmentableDataset:
    def __init__(self):
        self._intents_dict = {}
        self._augmentation_settings_dict = get_augmentation_settings()

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
        # unique_labels=["SendEmail"]
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


    def handle_unique_requirement(self,intent_df, rest_of_dfs):
        '''
            checks if specified slot values are unique amongst other intents
        '''
        pass

    
    def do_synonym_replacement(self, target, p=1/5, n=1, similarity=0.7):
        '''
            target: target AugmentableDataset object
            p: chance to replace each word
            n: is number of times to work on a sentence
        '''
        # TODO try to use different replacement synonyms on each intent throughout a category
        # from gensim.models import KeyedVectors

        from .language import get_gensim_word_vectors
        word_vectors = get_gensim_word_vectors()
        cache = {}

        for key, intent_df in self._intents_dict.items():
            words_already_used = []
            for i in range(n):
                '''
                    do this operation n times, per specification
                '''
                intent_df = intent_df.copy(deep=True)
                allowed_intents_df = intent_df[intent_df['EXCEMPT_SYNON'] != True]
                unallowed_syonym_intents_df = intent_df[intent_df['EXCEMPT_SYNON'] == True]
                print(allowed_intents_df)
                print(unallowed_syonym_intents_df)
                resultant_array = []
                for i, row in allowed_intents_df:
                    for i in range(len(seq_in)):
                        rand = random.randint(0,10)/10
                        if rand<p:
                            '''
                                with p chance replace the word with its synonym or root's synonym
                                if the word is in any ignorelist, act accordingly
                            '''
                            dont_stemmify_ = False
                            similarity_ = similarity
                            if synonym_ignorelist[i] is True:
                                similarity_ = 0.95
                                dont_stemmify_ = True
                            if stemmify_ignorelist[i] is True:
                                dont_stemmify_ = True
                            row.at[i,"TOKEN"] = get_phrase_synonym(row.TOKEN,words_already_used,similarity_,word_vectors,dont_stemmify = False)
                    if None not in seq_in:
                        seq_in = " ".join(seq_in)
                        self.add_to_dict(key,intent_df, target)

                    pass
                for seq_in,seq_out,augment_settings in intents_dict[key]:
                    stemmify_ignorelist,synonym_ignorelist,shuffle_ignorelist,unique_values_only_list = augment_settings
                    # stemmify_ignorelist_,synonym_ignorelist_,shuffle_ignorelist_ = cls.get_deepcopies((stemmify_ignorelist,synonym_ignorelist,shuffle_ignorelist))
                    seq_in = seq_in.split()
                    for i in range(len(seq_in)):
                        rand = random.randint(0,10)/10
                        if rand<p:
                            '''
                                with p chance replace the word with its synonym or root's synonym
                                if the word is in any ignorelist, act accordingly
                            '''
                            dont_stemmify_ = False
                            similarity_ = similarity
                            if synonym_ignorelist[i] is True:
                                similarity_ = 0.95
                                dont_stemmify_ = True
                            if stemmify_ignorelist[i] is True:
                                dont_stemmify_ = True
                            seq_in[i] = get_synonym(seq_in[i],words_already_used,similarity_,dont_stemmify_) or seq_in[i]
                    if None not in seq_in:
                        seq_in = " ".join(seq_in)
                        self.add_to_dict(intent_name,intent_df, target)
                        # self.add_to_dict(augmented_dict, key, (seq_in,seq_out,cls.get_deepcopies(augment_settings)))

def tests():
    from copy import copy
    import time
    original_dataset = AugmentableDataset()
    augmented_dataset = deepcopy(original_dataset)
    original_dataset.fill_intents_dict()
    
    for key, x in original_dataset._intents_dict.items():
        # original_dataset._intents_dict
        
        for y in x:
            print(y,"\n")
            break
        break

    # intents_dict = {}
    # intents_dict = {}
    # augmented_dict = {}
    # unique_labels = IntentInstance.objects.values_list("label",flat=True).distinct()
    # unique_labels = [x for x in unique_labels]
    # unique_labels=["SendEmail"]
    # # Get lates augmentation settings:
    # augmentation_settings = get_augmentation_settings()
    # # # Create intents_dict

    # for intent_label in unique_labels:
    #     '''
    #         creating a dict of intent categories mapped to Intent objects
    #     '''
    #     intents_by_label = IntentInstance.objects.filter(label=intent_label)
    #     augmentation_setting_df = augmentation_settings[intent_label]
    #     for intent in intents_by_label:
    #         df = goo_to_dataframe(intent.seq_in,intent.seq_out)
            
    #         #outer join augmentation settings
    #         df = pd.merge(df,augmentation_setting_df,on='SLOT',how='left')

    #         # # creating ignore lists
    #         # slots = intent.seq_out.replace("B-","").replace("I-","").split()
    #         # for slot in slots:
    #         #     stemmify_ignorelist.append(slot in excempt_stemmify_tokens)
    #         #     synonym_ignorelist.append(slot in excempt_synonym_tokens)
    #         #     shuffle_ignorelist.append(slot in excempt_shuffle_tokens)
    #         #     unique_values_only_list.append(slot in unique_values_only_tokens)

    #         # # Verifying list lengths
    #         # lengths = map(len,[stemmify_ignorelist,synonym_ignorelist,shuffle_ignorelist,unique_values_only_list,intent.seq_in.split(),intent.seq_out.split()])
    #         # if not len(set(lengths))==1:
    #         #     raise Exception("All lists are not the same length!")

    #         # cls.add_to_dict(intents_dict, intent_label, (intent.seq_in,intent.seq_out,(stemmify_ignorelist,synonym_ignorelist, shuffle_ignorelist,unique_values_only_list)))
