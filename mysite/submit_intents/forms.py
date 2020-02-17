from django.forms import ModelForm
from django import forms
from .models import *
from django.shortcuts import get_object_or_404
import json
from django.core import serializers

class EditIntentLabelsForm(forms.ModelForm):
    class Meta:
        model = IntentCategory
        fields = ('slots_field',"new_intent_label_field")
    slots_filed_widget = forms.Textarea(attrs={'autocomplete':'off','class':'intent-sentence','placeholder':'slot names here, space speparated'})
    slots_field = forms.CharField(label='', widget=slots_filed_widget)
    new_intent_label_widget = forms.TextInput(attrs={'autocomplete':'off','placeholder':'new intent label'})
    
    new_intent_label_field = forms.CharField(label='', widget=new_intent_label_widget)
    INTENT_LABELS = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
                
        INTENTS = IntentCategory.objects.all()
        self.INTENT_LABELS = []
        INTENT_SLOTS_DICT = {}
        for i in range(len(INTENTS)):
            self.INTENT_LABELS.append((INTENTS[i].intent_label,INTENTS[i].intent_label))
            slots = INTENTS[i].intentslot_set.all().values('slot_name','color_hex')
            slots = [entry for entry in slots]
            INTENT_SLOTS_DICT[INTENTS[i].intent_label] = slots

        self.intents_json = json.dumps(INTENT_SLOTS_DICT)
        self.fields["intent_label_choices"] = forms.ChoiceField(choices=self.INTENT_LABELS,widget=forms.Select(attrs={'onChange':'updateForm()'}))
        

# class CustomModelChoiceIterator(forms.models.ModelChoiceIterator):
#     def choice(self, obj):
#         return (self.field.prepare_value(obj),
#                 self.field.label_from_instance(obj), obj)
# class CustomModelChoiceField(forms.ModelChoiceField):
#     def _get_choices(self):
#         if hasattr(self, '_choices'):
#             return self._choices
#         return CustomModelChoiceIterator(self)
#     choices = property(_get_choices,  
#                        forms.ChoiceField._set_choices)


class SubmitIntentsForm(forms.ModelForm):
    class Meta:
        model = IntentCategory
        fields = "__all__"
    seq_in_field_widget = forms.TextInput(attrs={'autocomplete':'off','class':'intent-sentence','placeholder':'enter intent here',"onChange":"updateMask()"})
    seq_in_field = forms.CharField(label='', widget=seq_in_field_widget)
    seq_out_field_widget = forms.TextInput(attrs={'style':"font-size: 12px;", "readonly":"", 'autocomplete':'off','class':'intent-sentence','placeholder':'mask will be generated here'})
    seq_out_field = forms.CharField(label='', widget=seq_out_field_widget)
    intent_id_to_delete = forms.CharField(widget = forms.HiddenInput(), required = False)
    intent_id_to_modify = forms.CharField(widget = forms.HiddenInput(), required = False)

    INTENT_LABELS = []
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        INTENTS = IntentCategory.objects.all()
        self.INTENT_LABELS = [('', '----'),]
        INTENT_SLOTS_DICT = {}
        for i in range(len(INTENTS)):
            self.INTENT_LABELS.append((INTENTS[i].intent_label,INTENTS[i].intent_label))
            slots = INTENTS[i].intentslot_set.all().values('slot_name','color_hex')
            slotsDict = {}
            slots = [entry for entry in slots]
            for entry in slots:
                slotsDict[entry["slot_name"]]=entry["color_hex"]
            INTENT_SLOTS_DICT[INTENTS[i].intent_label] = slotsDict
        self.intents_json = json.dumps(INTENT_SLOTS_DICT)
        self.fields["intent_label_choices"] = forms.ChoiceField(choices=self.INTENT_LABELS,widget=forms.Select(attrs={'onChange':'updateForm()'}))
        self.fields["slots_choices"] = forms.ModelChoiceField(queryset=self.instance.intentslot_set.values('slot_name','color_hex'),empty_label=None, widget=forms.RadioSelect(attrs={}))
        existing_intens = IntentInstance.objects.all().filter(label=self.instance.intent_label).values('id','label','seq_in','seq_out')
        existing_intens = [intent for intent in existing_intens]
        self.existing_intents_json = json.dumps(existing_intens)

