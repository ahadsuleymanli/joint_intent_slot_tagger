import numpy as np 
import pandas as pd 
from .utils import group_words_into_slots
from ..models import IntentInstance, IntentCategory
from .utils import goo_to_dataframe, dataframe_to_goo

class Intent:
    '''
        represents one datum
        the datum is represented as a dataframe
    '''
    def __init__(self,seq_in,seq_out,label,augmentation_settings_df):
        '''
            seq_in: input string
            seq_out: ground truth of slots
            label: ground truth value of the category
        '''
        seq_in_list, seq_out_list = group_words_into_slots(seq_in,seq_out)
        self.df = pd.DataFrame({"TOKEN":np.array(seq_in_list),"SLOT":np.array(seq_out_list)})
    def get_strings(self):
        '''
            returns seq_in, seq_out, label
        '''
        pass

class AugmentableDataset:
    def __init__(self):
        self.intents_dict = {}
        self.augmentation_settings_dict = {}

    def add_to_dict(self,intent_name,intent_object):
        if intent_name not in self.intents_dict:
            self.intents_dict[intent_name] = [intent_object,]
        else:
            self.handle_unique_requirement(intent_object)
            self.intents_dict[intent_name].append(intent_object)
    @classmethod
    def create_augmentation_settings_df(cls,augmentation_settings):
        pass

    def handle_unique_requirement(self,intent_object):
        '''
            makes sure slots specified in augmentation_settings have unique contents
        '''
        pass

def get_augmentation_settings():
    augmentation_settings = {} #intent_name settings_df pairs
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

def tests():
    import time
    intents_dict = {}
    intents_dict = {}
    augmented_dict = {}
    unique_labels = IntentInstance.objects.values_list("label",flat=True).distinct()
    unique_labels = [x for x in unique_labels]
    unique_labels=["SendEmail"]
    # Get lates augmentation settings:
    augmentation_settings = get_augmentation_settings()
    # # Create intents_dict
    for intent_label in unique_labels:
        '''
            creating a dict of intent categories mapped to Intent objects
        '''
        intents_by_label = IntentInstance.objects.filter(label=intent_label)
        augmentation_settings_df = augmentation_settings[intent_label]
        for intent in intents_by_label:
            df = goo_to_dataframe(intent.seq_in,intent.seq_out)
            
            #outer join augmentation settings
            df = pd.merge(df,augmentation_settings_df,on='SLOT',how='left')


            
            # # creating ignore lists
            # slots = intent.seq_out.replace("B-","").replace("I-","").split()
            # for slot in slots:
            #     stemmify_ignorelist.append(slot in excempt_stemmify_tokens)
            #     synonym_ignorelist.append(slot in excempt_synonym_tokens)
            #     shuffle_ignorelist.append(slot in excempt_shuffle_tokens)
            #     unique_values_only_list.append(slot in unique_values_only_tokens)

            # # Verifying list lengths
            # lengths = map(len,[stemmify_ignorelist,synonym_ignorelist,shuffle_ignorelist,unique_values_only_list,intent.seq_in.split(),intent.seq_out.split()])
            # if not len(set(lengths))==1:
            #     raise Exception("All lists are not the same length!")

            # cls.add_to_dict(intents_dict, intent_label, (intent.seq_in,intent.seq_out,(stemmify_ignorelist,synonym_ignorelist, shuffle_ignorelist,unique_values_only_list)))
