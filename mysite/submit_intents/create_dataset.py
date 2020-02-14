'''
    exports dataset from the DB into a folder containing label, seq.in, seq.out text files 
'''
from .models import IntentInstance
import os
import math
def get_dir(path,dir_name):
    path_to_dir = os.path.join(path, dir_name)
    if not os.path.exists(path_to_dir):
        os.makedirs(path_to_dir)
    return path_to_dir

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = get_dir(ROOT_DIR, 'dataset')
IMPORT_DIR = get_dir(ROOT_DIR, 'dataset_import')
SPLIT_DIRS = [get_dir(DATASET_DIR, x) for x in ["train","valid","test"] ]

def get_dataset_file_paths(dir_path):
    return (os.path.join(dir_path, 'label'), 
        os.path.join(dir_path, 'seq.in'),
        os.path.join(dir_path, 'seq.out'))
    
class CreateDataset:
    @staticmethod
    def add_to_intents_dict(intents_dict,key,value):
        '''
            if key doesnt exist in the dictionary, create
            if exists append the value to the key's array
        '''
        if key not in intents_dict:
            intents_dict[key] = [value,]
        else:
            intents_dict[key].append(value)
    
    @staticmethod
    def create_single_file_dataset(interleave_categories=True,shuffle=True):
        '''
            creates a single intents_dict and calls create_dataset
        '''
        intents_dict = {}
        # getting all submitted intents from DB
        intents = IntentInstance.objects.all()
        if shuffle:
            intents = intents.order_by('?')
        # creating a dictionary of intents labels mapped to an array of (seq_in, seq_out) tuples  
        for intent in intents:
            CreateDataset.add_to_intents_dict(intents_dict,intent.label, (intent.seq_in,intent.seq_out))
        CreateDataset.create_dataset(intents_dict,DATASET_DIR,interleave_categories,shuffle)

    @staticmethod
    def create_dataset(intents_dict,dataset_dir,interleave_categories,shuffle):
        '''
            outputs the dataset in the form of label, seq.in, seq.out text files
            each file contains one line per entry in dataset
        '''
        label_path, seq_in_path, seq_out_path = get_dataset_file_paths(dataset_dir)
        label_file = open(label_path,"w+")
        seq_in_file = open(seq_in_path,"w+")
        seq_out_file = open(seq_out_path,"w+")

        if interleave_categories:
            # iterating over the dictionry Breadth-Wise 
            # in order to output one of each intent category alternatingly into the output files
            while not all(len(intents_dict[key])==0 for key in intents_dict):
                for key in intents_dict:
                    if len(intents_dict[key]):
                        seq_in, seq_out = intents_dict[key].pop(0)
                        label_file.write(key+'\n')
                        seq_in_file.write(seq_in+'\n')
                        seq_out_file.write(seq_out+'\n')
        else:
            for key in intents_dict:
                while len(intents_dict[key]):
                    seq_in, seq_out = intents_dict[key].pop(0)
                    label_file.write(key+'\n')
                    seq_in_file.write(seq_in+'\n')
                    seq_out_file.write(seq_out+'\n')

        label_file.close()
        seq_in_file.close()
        seq_out_file.close()

    @staticmethod
    def create_dataset_split(split_ratios,interleave_categories=True,shuffle=True):
        split_dicts = [{},{},{}]
        if sum(split_ratios) != 1.0 or len(split_ratios)>3:
            print("wrong split")
            return

        unique_labels = IntentInstance.objects.values_list("label",flat=True).distinct()
        unique_labels = [x for x in unique_labels]
        
        for intent_label in unique_labels:
            '''
                splitting each intent category individually
            '''
            intents_by_label = IntentInstance.objects.filter(label=intent_label)
            if shuffle:
                intents_by_label=intents_by_label.order_by('?')
            intents_list_len = len(intents_by_label)
            slice_start_fraction = 0
            for i, ratio in enumerate(split_ratios):
                '''
                    slicing the arrays containing the data instances
                '''
                slice_end_fraction = slice_start_fraction+ratio
                slice_start = math.ceil(intents_list_len*slice_start_fraction)
                slice_end = math.ceil((intents_list_len*slice_end_fraction))
                slice_end = min(slice_end,intents_list_len)
                for intent in intents_by_label[slice_start:slice_end]:
                    CreateDataset.add_to_intents_dict(split_dicts[i], intent_label, (intent.seq_in,intent.seq_out))
                slice_start_fraction = slice_end_fraction
        
        # going over our dictionaries containing our dataset splits
        # calling create_dataset and passing our split dictionaries to it
        for split_dict,split_dir in zip(split_dicts,SPLIT_DIRS):
            CreateDataset.create_dataset(split_dict,split_dir,interleave_categories,shuffle)

    @staticmethod
    def import_dataset():
        '''
            imports from files found in ./dataset_import
        '''
        file_paths = get_dataset_file_paths(IMPORT_DIR)
        if all( os.path.isfile(file_path) for file_path in file_paths):
            open_files = (open(file_path,"r",encoding='utf-8') for file_path in file_paths)
            label_arr, seq_in_arr, seq_out_arr = (f.readlines() for f in open_files)
            (f.close() for f in open_files)
            if not (len(label_arr) == len(seq_in_arr) == len(seq_out_arr)):
                print("file line counts must be equal")
                return
            for label, seq_in, seq_out in zip (label_arr, seq_in_arr, seq_out_arr):
                # creates new intent instance in DB if it does's exist
                if not IntentInstance.objects.filter(seq_in=seq_in.strip(), seq_out=seq_out.strip()):
                    IntentInstance.objects.create(label=label.strip(), seq_in=seq_in.strip(), seq_out=seq_out.strip())


            