from django.db import models

class IntentModel(models.Model):
    intent_label = models.CharField(max_length=50)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields= ['intent_label'], name="unique constraint"),
            ]
    def save(self, *args, **kwargs):
        '''
            ensures the unique key
        '''
        if not IntentModel.objects.filter(intent_label=self.intent_label):
            super().save(*args, **kwargs)

class IntentSlot(models.Model):
    intent = models.ForeignKey(IntentModel, on_delete=models.CASCADE)
    slot_name = models.CharField(max_length=50)
    color_hex = models.CharField(max_length=9 , default='#4b4b4b')
    class Meta:
        unique_together = (('intent', 'slot_name'),)
    def __str__(self):
        return (self.slot_name)
    
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
    "black": "#000000",
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
    "purple": "#800080",
    "violet": "#800080",
    "red": "#ff0000",
    "silver": "#c0c0c0",
    "white": "#ffffff",
    "yellow": "#ffff00"
}