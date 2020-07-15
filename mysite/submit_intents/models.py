from django.db import models

class IntentInstance(models.Model):
    label = models.CharField(max_length=50)
    seq_in = models.CharField(max_length=255,default='')
    seq_out = models.CharField(max_length=255,default='')
    is_synthetic = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        '''
            creates label in IntentCategory table if it does not exist
        '''
        if len(self.seq_in.split()) != len(self.seq_out.split()):
            print("wrong intent format", self.seq_in)
            return
        slot_list = self.seq_out.replace('B-','').replace('I-','').split()
        obj, created = IntentCategory.objects.get_or_create(intent_label=self.label)
        for slot in slot_list:
            if slot!="O" and not self.is_synthetic:
                IntentSlot.objects.get_or_create(intent=obj, slot_name=slot)
        super().save(*args, **kwargs)

class IntentCategory(models.Model):
    intent_label = models.CharField(max_length=50)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields= ['intent_label'], name="unique constraint"),
            ]
        ordering = ('intent_label',)
    def save(self, *args, **kwargs):
        '''
            ensures the unique key
        '''
        if not IntentCategory.objects.filter(intent_label=self.intent_label):
            super().save(*args, **kwargs)

class IntentCCIgnore(models.Model):
    '''
        list of intent categories to ignore in cross category augmentation step
    '''
    intent = models.ForeignKey(IntentCategory, on_delete=models.CASCADE)
    ignore_intent = models.CharField(max_length=50)
    class Meta:
        unique_together = (('intent', 'ignore_intent'),)
    def save(self, *args, **kwargs):
        '''
            ensures the unique key and existance of intent counterpart
        '''
        if self.ignore_intent not in list(IntentCategory.objects.all().values_list('intent_label',flat=True)):
            return
        super().save(*args, **kwargs)

class IntentSlot(models.Model):
    intent = models.ForeignKey(IntentCategory, on_delete=models.CASCADE)
    slot_name = models.CharField(max_length=50)
    color_hex = models.CharField(max_length=9 , default='#4b4b4b')
    excempt_stemmify = models.BooleanField(default=False)
    excempt_synonym = models.BooleanField(default=False)
    excempt_shuffle = models.BooleanField(default=False)
    unique_values_only = models.BooleanField(default=False)
    dont_export = models.BooleanField(default=False)
    class Meta:
        unique_together = (('intent', 'slot_name'),)
        ordering = ('slot_name',)
    # def __str__(self):
    #     return (self.slot_name)
    
    @classmethod
    def save_slots(self,intent,new_slot_names):
        slot_objects = intent.intentslot_set.all()
        slot_names = [entry['slot_name'] for entry in slot_objects.values('slot_name')]
        new_slot_names = list(dict.fromkeys(new_slot_names))
        new_slot_names = [i for i in new_slot_names if i not in slot_names]

        existing_colors_in_intent = [entry['color_hex'] for entry in slot_objects.values('color_hex')]
        
        other_colors_for_slot = [entry['color_hex'] for entry in IntentSlot.objects.filter(slot_name=self.slot_name).values('color_hex')]

        other_colors_for_slot = IntentSlot.objects.filter(slot_name=self.slot_name).values('color_hex')
        existing_colors_in_intent = [entry['color_hex'] for entry in existing_colors_in_intent]
        other_colors_for_slot = [entry['color_hex'] for entry in other_colors_for_slot]

    def save(self, *args, **kwargs):
        '''
            ensures the unique key pair constraint
            assigns a unique color for each slot in an intent
            tries to keep slot colors same across intents
        '''
        if IntentSlot.objects.filter(intent=self.intent,slot_name=self.slot_name):
            return
        # existing_colors_in_intent = IntentSlot.objects.filter(intent=self.intent).values('color_hex')
        existing_colors_in_intent = self.intent.intentslot_set.all().values('color_hex')
        existing_colors_in_intent = [entry['color_hex'] for entry in existing_colors_in_intent]
        # other_colors_for_slot = IntentSlot.objects.filter(slot_name=self.slot_name).values('color_hex')
        # other_colors_for_slot = [entry['color_hex'] for entry in other_colors_for_slot]
        # most_frequent_color = None
        # if len(other_colors_for_slot):
        #     most_frequent_color = max(set(other_colors_for_slot), key = other_colors_for_slot.count)
        #     print ("1",most_frequent_color)
        #     print(existing_colors_in_intent)
        # if most_frequent_color and most_frequent_color not in existing_colors_in_intent:
        #     print ("2",most_frequent_color)
        #     self.color_hex = most_frequent_color
        # else:
        for key in colors:
            if colors[key] not in existing_colors_in_intent:
                self.color_hex = colors[key]
        super().save(*args, **kwargs)
            

colors = {
    "aqua": "#00ffff",
    "azure": "#f0ffff",
    "beige": "#f5f5dc",
    "blue": "#0000ff",
    "brown": "#a52a2a",
    "cyan": "#00ffff",
    "darkblue": "#00008b",
    "darkcyan": "#008b8b",
    "darkgrey": "#a9a9a9",
    "darkgreen": "#006400",
    "darkkhaki": "#bdb76b",
    "darkmagenta": "#8b008b",
    "darkolivegreen": "#556b2f",
    "darkorange": "#ff8c00",
    "darkorchid": "#9932cc",
    "darkred": "#8b0000",
    "darksalmon": "#e9967a",
    "darkviolet": "#9400d3",
    "fuchsia": "#ff00ff",
    "gold": "#ffd700",
    "green": "#008000",
    "indigo": "#4b0082",
    "khaki": "#f0e68c",
    "lightblue": "#add8e6",
    "lightcyan": "#e0ffff",
    "lightgreen": "#90ee90",
    "lightgrey": "#d3d3d3",
    "lightpink": "#ffb6c1",
    "lightyellow": "#ffffe0",
    "lime": "#00ff00",
    "magenta": "#ff00ff",
    "maroon": "#800000",
    "navy": "#000080",
    "olive": "#808000",
    "orange": "#ffa500",
    "pink": "#ffc0cb",
    "purple": "#844484",
    "red": "#ff0000",
    "yellow": "#ffff00"
}