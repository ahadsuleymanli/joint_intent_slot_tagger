from .models import IntentInstance
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(ROOT_DIR, 'dataset')
if not os.path.exists(DATASET_DIR):
    os.makedirs(DATASET_DIR)


def get_output_file_paths():
    return (os.path.join(DATASET_DIR, 'label'), 
        os.path.join(DATASET_DIR, 'seq.in'),
        os.path.join(DATASET_DIR, 'seq.out'))
    
class CreateDataset:
    intents_dict = {}

    @staticmethod
    def add_to_intents_dict(key,value):
        if key not in CreateDataset.intents_dict:
            CreateDataset.intents_dict[key] = [value,]
        else:
            CreateDataset.intents_dict[key].append(value)
    
    @staticmethod
    def create_dataset():
        label_path, seq_in_path, seq_out_path = get_output_file_paths()
        label_file = open(label_path,"w+")
        seq_in_file = open(seq_in_path,"w+")
        seq_out_file = open(seq_out_path,"w+")

        intents = IntentInstance.objects.order_by('?')

        # getting unique labels
        # unique_labels = IntentInstance.objects.order_by().values_list('label',flat=True).distinct()
        # unique_labels = list(unique_labels)
        for intent in intents:
            CreateDataset.add_to_intents_dict(intent.label,(intent.seq_in,intent.seq_out))


        while not all(len(CreateDataset.intents_dict[key])==0 for key in CreateDataset.intents_dict):
            for key in CreateDataset.intents_dict:
                if len(CreateDataset.intents_dict[key]):
                    seq_in, seq_out = CreateDataset.intents_dict[key].pop(0)
                    label_file.write(key+'\n')
                    seq_in_file.write(seq_in+'\n')
                    seq_out_file.write(seq_out+'\n')

        
        print(CreateDataset.intents_dict)
        # for key in CreateDataset.intents_dict:
        # for intent in intents:
        #     print (intent.label)

        label_file.close()
        seq_in_file.close()
        seq_out_file.close()

