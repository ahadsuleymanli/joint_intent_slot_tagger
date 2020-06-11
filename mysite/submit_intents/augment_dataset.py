'''
    augments dataset using following strategies:
    -Intent Permutation (IP): Permutate all datums in an intent
    -Root versions (RV): Copy datums n times with 1/n of their tokens replaced with their roots
    In each synthesized datum :
    -Synonym Replacement (SR): Randomly replace n non-token words in the sentences with their synonyms.
    -Random Insertion (RI): Insert random synonyms of words in a sentence, this is done n times.
    -Random Swap (RS): Two words in the sentences are randomly swapped, this is repeated n-times.
    -Random Deletion (RD): Random removal for each non-token word in the sentence with a probability p.
    Multiply each datum n times for NA:
    -Cross category noise addition (CCNA): Start and trail intents with parts from unrelated intents.  n-times per intent.
    -Noise Addition (NA): Insert random non-related words as noise.
'''
from .models import IntentInstance, IntentCategory
import os
import math, random
from threading import Lock
from copy import deepcopy
def get_dir(path,dir_name):
    path_to_dir = os.path.join(path, dir_name)
    if not os.path.exists(path_to_dir):
        os.makedirs(path_to_dir)
    return path_to_dir

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
NLP_DIR =  os.path.join(ROOT_DIR, "nlp")

class AugmentationSettings:
    def __init__(self,settings):
        self.settings = settings

class Token:
    def __init__(self,content,slot_name,augmentation_settings):
        '''
            seq_in and seq_out are parts of the actual seq_in and seq_out corresponding to the token
        '''
        self.content = slot_name

class Intent:
    def __init__(self,seq_in,seq_out,label,augmentation_settings):
        pass

class AugmentDataset:
    synonym_cache = {}

    @classmethod
    def handle_unique_requirement(cls,intents_list,value):
        '''
            before adding to intents_list, checks if the fields with unique requirement need to be "uniquefied" and does it
        '''
        seq_in,seq_out,augment_settings = value
        stemmify_ignorelist,synonym_ignorelist,shuffle_ignorelist,unique_values_only_list = augment_settings
        seq_in,seq_out,augment_settings_slots = cls.extract_slots(seq_in, seq_out, augment_settings)
        _,_,_,unique_values_only_list_slots = augment_settings_slots

    @staticmethod
    def add_to_dict(intents_dict,key,value):
        '''
            if key doesnt exist in the dictionary, create
            if exists append the value to the key's array
        '''
        if key not in intents_dict:
            intents_dict[key] = [value,]
        else:
            AugmentDataset.handle_unique_requirement(intents_dict[key],value)
            intents_dict[key].append(value)

    @classmethod
    def get_augmentation_settings(cls):
        augmentation_settings = {}
        intent_objects = IntentCategory.objects.all()
        for i in range(len(intent_objects)):
            slots = intent_objects[i].intentslot_set
            def get_slot_list(querylist):
                return [x["slot_name"] for x in querylist]
            excempt_stemmify_list = get_slot_list(slots.filter(excempt_stemmify=True).values('slot_name'))
            excempt_synonym_list = get_slot_list(slots.filter(excempt_synonym=True).values('slot_name'))
            excempt_shuffle_list = get_slot_list(slots.filter(excempt_shuffle=True).values('slot_name'))
            unique_values_only_list = get_slot_list(slots.filter(unique_values_only=True).values('slot_name'))

            augmentation_settings[intent_objects[i].intent_label] = {"excempt_stemmify_tokens": excempt_stemmify_list,
                                                                "excempt_synonym_tokens": excempt_synonym_list,
                                                                "excempt_shuffle_tokens": excempt_shuffle_list,
                                                                "unique_values_only_tokens": unique_values_only_list}
        return augmentation_settings


    @classmethod
    def do_augmentation(cls):
        from copy import deepcopy
        IntentInstance.objects.filter(is_synthetic=True).delete()
        intents_dict = {}
        intents_dict = {}
        augmented_dict = {}
        unique_labels = IntentInstance.objects.values_list("label",flat=True).distinct()
        unique_labels = [x for x in unique_labels]
        
        # Get lates augmentation settings:
        augmentation_settings = cls.get_augmentation_settings()

        # Create intents_dict
        for intent_label in unique_labels:
            '''
                creating a dict of intent categories mapped to an array of intents 
            '''
            intents_by_label = IntentInstance.objects.filter(label=intent_label)
            for intent in intents_by_label:
                # create ignore lists that represent the status of the tokens in seq_in and seq_out
                stemmify_ignorelist = [] 
                synonym_ignorelist = []
                shuffle_ignorelist = []
                unique_values_only_list = []
                excempt_stemmify_tokens = augmentation_settings[intent.label]["excempt_stemmify_tokens"]
                excempt_synonym_tokens = augmentation_settings[intent.label]["excempt_synonym_tokens"]
                excempt_shuffle_tokens = augmentation_settings[intent.label]["excempt_shuffle_tokens"]
                unique_values_only_tokens = augmentation_settings[intent.label]["unique_values_only_tokens"]

                # creating ignore lists
                slots = intent.seq_out.replace("B-","").replace("I-","").split()
                for slot in slots:
                    stemmify_ignorelist.append(slot in excempt_stemmify_tokens)
                    synonym_ignorelist.append(slot in excempt_synonym_tokens)
                    shuffle_ignorelist.append(slot in excempt_shuffle_tokens)
                    unique_values_only_list.append(slot in unique_values_only_tokens)

                # Verifying list lengths
                lengths = map(len,[stemmify_ignorelist,synonym_ignorelist,shuffle_ignorelist,unique_values_only_list,intent.seq_in.split(),intent.seq_out.split()])
                if not len(set(lengths))==1:
                    raise Exception("All lists are not the same length!")

                cls.add_to_dict(intents_dict, intent_label, (intent.seq_in,intent.seq_out,(stemmify_ignorelist,synonym_ignorelist, shuffle_ignorelist,unique_values_only_list)))

        # Augmentation steps here:
        # 1. Add shuffled copies
        cls.shuffle(intents_dict, augmented_dict, 1)
        if True:
            shuffle_dict = deepcopy(augmented_dict)
            synonym_replacement_p = 1/4
            # 2. Add synonym replaced copies of the original and shuffled entries
            cls.synonym_replacement(intents_dict, augmented_dict, p=1/5, n=1, similarity=0.85)
            # cls.synonym_replacement(intents_dict, augmented_dict, p=1/8, n=1, similarity=0.65)
            # cls.synonym_replacement(intents_dict, augmented_dict, p=1/10, n=1, similarity=0.55)
            # cls.synonym_replacement(shuffle_dict, augmented_dict, p=1/10, n=1, similarity=0.85)

            # 3. Add stemmified copies
            cls.stemmify(intents_dict, augmented_dict)

            # 4. Remove duplicates from the augmented list so far
            cls.remove_duplicates(augmented_dict)

            # 5. Add noise added copies of the augmented dataset
            augmented_dict_1 = deepcopy(augmented_dict)
            cls.cross_category_noise(augmented_dict_1, augmented_dict, 1, 1/2)

            # 6. Add noise added copies of the original dataset
            cls.cross_category_noise(intents_dict, augmented_dict, 2, 1/2)

            # # 7. Add one more copy of the original dataset
            cls.shuffle(intents_dict, augmented_dict, 1)

        for key in augmented_dict:
            '''
                adding the intents into the db with a is_synthetic flag
            '''
            for intent in augmented_dict[key]:
                seq_in = intent[0]
                seq_out = intent[1]
                if not IntentInstance.objects.filter(seq_in=seq_in, seq_out=seq_out):
                    IntentInstance.objects.create(label=key, seq_in=seq_in, seq_out=seq_out,is_synthetic=True)


    @classmethod
    def permutate(cls,intents_dict, augmented_dict):
        pass 

    @classmethod
    def remove_duplicates(cls, augmented_dict):
        for category_id, key in enumerate(list(augmented_dict)):
            indexes_to_pop = set()
            for i, (seq_in_i, seq_out_i,*_) in enumerate(augmented_dict[key]):
                for j, (seq_in_j,seq_out_j,*_) in enumerate(augmented_dict[key][i:]):
                    if i!=j and seq_in_i==seq_in_j:
                        indexes_to_pop.add(j)
            indexes_to_pop = sorted(indexes_to_pop, reverse=True)
            for i in indexes_to_pop:
                augmented_dict[key].pop(i) 

    @classmethod
    def get_synonym_cached(cls,key,word_vectors):
        if key in cls.synonym_cache:
            return cls.synonym_cache[key]
        else:
            try:
                vec = word_vectors.most_similar(positive=[key],negative=[])
            except:
                vec = None
            cls.synonym_cache[key] = vec
            return vec

    @classmethod
    def synonym_replacement(cls,intents_dict, augmented_dict, p=1/5, n=1, similarity=0.7):
        '''
            p chance to replace each word
            n is number of times to work on a sentence
        '''
        # TODO try to use different replacement synonyms on each intent throughout a category
        from gensim.models import KeyedVectors
        from .nlp.lemmatizer_tr import get_phrase_root
        word_vectors = KeyedVectors.load_word2vec_format(os.path.join(NLP_DIR,"trmodel"), binary=True)
        cache = {}

        def get_synonym(word,words_already_used,similarity, dont_stemmify=False):
            '''
                returns the synonym
                if can't the synonym of the root, and if still cant returns None
            '''
            def get_synonym_(word,words_already_used,similarity):
                vec = cls.get_synonym_cached(word,word_vectors)
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

            synonym = get_synonym_(word,words_already_used,similarity)
            if synonym:
                return synonym
            elif not dont_stemmify:
                return get_synonym_(get_phrase_root(word),words_already_used,similarity)
            else:
                return None

        for category_id, key in enumerate(list(intents_dict)):
            words_already_used = []
            for i in range(n):
                '''
                    do this n times
                '''
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
                        cls.add_to_dict(augmented_dict, key, (seq_in,seq_out,cls.get_deepcopies(augment_settings)))
    @staticmethod
    def get_deepcopies(list_of_objects):
        return [deepcopy(x) for x in list_of_objects]
    @classmethod
    def shuffle(cls, intents_dict, augmented_dict, n):
        def joint_swap(idx1, idx2, *args):
            '''
                swaps indexes jointly in a number of given lists
            '''
            for arg in args:
                temp = arg[idx1]
                arg[idx1]=arg[idx2]
                arg[idx2]=temp

        for category_id, key in enumerate(list(intents_dict)):
            for (seq_in, seq_out,augment_settings) in intents_dict[key]:
                stemmify_ignorelist,synonym_ignorelist,shuffle_ignorelist,unique_values_only_list = augment_settings
                stemmify_ignorelist_,synonym_ignorelist_,shuffle_ignorelist_,unique_values_only_list_ = cls.get_deepcopies(augment_settings)

                seq_in,seq_out,(stemmify_ignorelist_slots,synonym_ignorelist_slots,shuffle_ignorelist_slots,unique_values_only_list_slots) = cls.extract_slots(seq_in, seq_out, augment_settings)
                len_seq = len(seq_in)
                for i in range(n):
                    choicelist = list(range(0, len(seq_in)))

                    # remove the excemptions from the random pool
                    for ignore_idx, x in enumerate(shuffle_ignorelist_slots):
                        if "True" in x:
                            assert "False" not in x
                            choicelist.remove(ignore_idx)
                    if len(choicelist) < 2:
                        break
                    idx1 = random.choice(choicelist)
                    choicelist.remove(idx1)   
                    idx2 = random.choice(choicelist)

                    lists = stemmify_ignorelist_slots,synonym_ignorelist_slots,shuffle_ignorelist_slots
                    for list_ in lists:
                        str_ = " ".join(stemmify_ignorelist_slots).split()
                        list_ = [True if x=="True" else False for x in str_]

                    # if shuffle_ignorelist[idx1] is not True and shuffle_ignorelist[idx2] is not True:
                    joint_swap(idx1,idx2,seq_in,seq_out,stemmify_ignorelist_,synonym_ignorelist_,shuffle_ignorelist_,unique_values_only_list_)
                    seq_in = " ".join(seq_in)
                    seq_out = " ".join(seq_out)
                    cls.add_to_dict(augmented_dict, key, (seq_in,seq_out,(stemmify_ignorelist_,synonym_ignorelist_,shuffle_ignorelist_,unique_values_only_list_)))

    @classmethod
    def stemmify(cls, intents_dict, augmented_dict):
        '''
            stemmifies each word in the sentence
        '''
        from .nlp.lemmatizer_tr import get_phrase_root
        for category_id, key in enumerate(list(intents_dict)):
            for seq_in,seq_out,augment_settings in intents_dict[key]:
                
                stemmify_ignorelist,synonym_ignorelist,shuffle_ignorelist,unique_values_only_list = augment_settings
                seq_in = seq_in.split()
                for i in range(len(seq_in)):
                    if stemmify_ignorelist[i] is not True:
                        seq_in[i] = get_phrase_root(seq_in[i])
                seq_in = " ".join(seq_in)
                cls.add_to_dict(augmented_dict, key, (seq_in,seq_out,cls.get_deepcopies(augment_settings)))

    @staticmethod
    def extract_slots(seq_in,seq_out,augment_settings):
        '''
            groups words into tokens a list of tokens 
        '''
        seq_in = seq_in.split()
        seq_out = seq_out.split()
        seq_in_arr = [seq_in[0]]
        seq_out_arr = [seq_out[0]]
        augment_settings_slots = lists = [[str(x[0])] for x in augment_settings]
        # for lst in augment_settings_slots:

        # stemmify_ignorelist_slots = [str(stemmify_ignorelist_[0])]
        # synonym_ignorelist_slots = [str(synonym_ignorelist_[0])]
        # shuffle_ignorelist_slots = [str(shuffle_ignorelist_[0])]
        for i, (word, token) in enumerate(zip(seq_in[1:],seq_out[1:])):
            if token.startswith("I-") and (seq_out_arr[-1].startswith("B-") or seq_out_arr[-1].startswith("I-")):
                seq_in_arr[-1] += " " + word
                seq_out_arr[-1] += " " + token
                for setting_slots,setting in zip(augment_settings_slots,augment_settings):
                    setting_slots[-1] += " " + str(setting[i+1])
            else:
                seq_in_arr.append(word)
                seq_out_arr.append(token)
                for setting_slots,setting in zip(augment_settings_slots,augment_settings):
                    setting_slots.append(str(setting[i+1]))

        return seq_in_arr, seq_out_arr, augment_settings_slots

    @classmethod
    def cross_category_noise(cls,intents_dict,augmented_dict, n, fraction):
        '''
            n times per intent
            fraction of unrelated intent to add to the start and the tail of the intent
        '''
        chance_to_omit = 1/8
        class Counter:
            def __init__(self):
                self.counters = []
                self.key_id = 0
        counter_obj = Counter()
        for category_id, key in enumerate(list(intents_dict)):
            generator = cls.intent_head_tail_generator(counter_obj, intents_dict, category_id,fraction)
            for (seq_in,seq_out,augment_settings) in intents_dict[key]:
                stemmify_ignorelist,synonym_ignorelist,shuffle_ignorelist,unique_values_only_list = augment_settings
                for i in range(n):
                    start = next(generator) + " "
                    trail = " " + next(generator)
                    start_seq_out = " ".join(["O"]*len(start.split())) + " "
                    trail_seq_out = " " + " ".join(["O"]*len(trail.split()))
                    start_ignorelist = [False]*len(start.split())
                    trail_ignorelist = [False]*len(trail.split())
                    rand = random.randint(0,10)/10
                    if rand<chance_to_omit:
                        start = ""
                        start_seq_out = ""
                        start_ignorelist = []
                    elif rand<chance_to_omit*2:
                        trail = ""
                        trail_seq_out = ""
                        trail_ignorelist = []
                    augmented_seq_in = start + seq_in + trail
                    augmented_seq_out = start_seq_out + seq_out + trail_seq_out
                    for x in [stemmify_ignorelist,synonym_ignorelist,shuffle_ignorelist]:
                        x = start_ignorelist + x + trail_ignorelist
                    cls.add_to_dict(augmented_dict, key, (augmented_seq_in,augmented_seq_out,cls.get_deepcopies(augment_settings)))
        
    @staticmethod
    def intent_head_tail_generator(counter_obj, intents_dict, current_id, fraction):
        # TODO 0.5 chance to add a random word in between
        intents_count = len(intents_dict)
        assert intents_count > 1
        # initialize counters if empty
        
        if counter_obj.counters == []:
            counter_obj.counters = [0]*intents_count
        counters = counter_obj.counters
        from math import ceil, floor
        def get_next_intent():
            if counter_obj.key_id == current_id:
                counter_obj.key_id = (counter_obj.key_id+1)%intents_count
            intents = list(intents_dict.values())[counter_obj.key_id]
            seq_in_arr = intents[counters[counter_obj.key_id]][0].split()
            counters[counter_obj.key_id] = (counters[counter_obj.key_id]+1)%len(intents)
            counter_obj.key_id = (counter_obj.key_id+1)%intents_count
            return seq_in_arr
        while True:
            '''
                get the tail of an intent
            '''
            seq_in_arr = get_next_intent()
            yield " ".join(seq_in_arr[floor(len(seq_in_arr)*fraction):])
            '''
                get the head of an intent
            '''
            seq_in_arr = get_next_intent()
            yield " ".join(seq_in_arr[:ceil(len(seq_in_arr)*fraction)])

    @staticmethod
    def clear_augmented_entries():
        IntentInstance.objects.filter(is_synthetic=True).delete()

if __name__ == "__main__":
    AugmentDataset.synonym_replacement(None,None,1,1)