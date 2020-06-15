import numpy as np 
import pandas as pd 
from ..models import IntentInstance, IntentCategory
from .utils import goo_to_dataframe, dataframe_to_goo, get_augmentation_settings
from copy import deepcopy
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
#     def __init__(self,seq_in,seq_out,label,augmentation_settings_df):
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

    def add_to_dict(self,intent_name,intent_df):
        if intent_name not in self._intents_dict:
            self._intents_dict[intent_name] = [intent_df,]
        else:
            self.handle_unique_requirement(intent_df, self._intents_dict[intent_name])
            self._intents_dict[intent_name].append(intent_df)
    
    def fill_intents_dict(self):
        unique_labels = IntentInstance.objects.values_list("label",flat=True).distinct()
        unique_labels = [x for x in unique_labels]
        unique_labels=["SendEmail"]
        for intent_label in unique_labels:
            '''
                creating a dict of intent categories mapped to Intent objects
            '''
            intents_by_label = IntentInstance.objects.filter(label=intent_label)
            augmentation_settings_df = self._augmentation_settings_dict[intent_label]
            for intent in intents_by_label:
                df = goo_to_dataframe(intent.seq_in,intent.seq_out)
                '''
                outer join augmentation settings
                '''
                df = pd.merge(df,augmentation_settings_df,on='SLOT',how='left')
                self.add_to_dict(intent_label,df)


    def handle_unique_requirement(self,intent_df, rest_of_dfs):
        '''
            checks if specified slot values are unique amongst other intents
        '''
        pass

def tests():
    from copy import copy
    import time
    original_dataset = AugmentableDataset()
    original_dataset.fill_intents_dict()
    cpy = deepcopy(original_dataset)
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
    #     augmentation_settings_df = augmentation_settings[intent_label]
    #     for intent in intents_by_label:
    #         df = goo_to_dataframe(intent.seq_in,intent.seq_out)
            
    #         #outer join augmentation settings
    #         df = pd.merge(df,augmentation_settings_df,on='SLOT',how='left')

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
