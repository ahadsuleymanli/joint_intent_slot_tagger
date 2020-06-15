import numpy as np 
import pandas as pd 
from ..models import IntentInstance, IntentCategory

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