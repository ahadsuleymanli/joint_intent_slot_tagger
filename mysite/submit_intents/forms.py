from django.forms import ModelForm
from django import forms
from .models import *
from django.shortcuts import get_object_or_404
import json
from django.core import serializers

class IntentModelForm(forms.ModelForm):
    class Meta:
        model = IntentModel
        fields = ('slots_field',"new_intent_label_field")
    slots_filed_widget = forms.Textarea(attrs={'autocomplete':'off','class':'intent-sentence','placeholder':'slot names here, space speparated'})
    slots_field = forms.CharField(label='', widget=slots_filed_widget)
    new_intent_label_widget = forms.TextInput(attrs={'autocomplete':'off','placeholder':'new intent label'})
    new_intent_label_field = forms.CharField(label='', widget=new_intent_label_widget)
    INTENT_LABELS = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
                
        INTENTS = IntentModel.objects.all()
        self.INTENT_LABELS = []
        INTENT_SLOTS_DICT = {}
        for i in range(len(INTENTS)):
            self.INTENT_LABELS.append((INTENTS[i].intent_label,INTENTS[i].intent_label))
            slots = INTENTS[i].intentslot_set.all().values('slot_name','color_hex')
            slots = [entry for entry in slots]
            INTENT_SLOTS_DICT[INTENTS[i].intent_label] = slots

        self.intents_json = json.dumps(INTENT_SLOTS_DICT)
        self.fields["intent_label_choices"] = forms.ChoiceField(choices=self.INTENT_LABELS,widget=forms.Select(attrs={'onChange':'updateForm()'}))
        

class IntentForm(forms.ModelForm):
    class Meta:
        model = IntentModel
        fields = "__all__"
    intent_filed_widget = forms.Textarea(attrs={'autocomplete':'off','class':'intent-sentence','placeholder':'enter intent here'})
    intent_field = forms.CharField(label='', widget=intent_filed_widget)
    mask_field = forms.CharField(widget=forms.HiddenInput())  # A hidden input for internal use
    # slots_choices = forms.ChoiceField( widget=forms.RadioSelect)
    
    INTENT_LABELS = []
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        INTENTS = IntentModel.objects.all()
        self.INTENT_LABELS = []
        for i in range(len(INTENTS)):
            self.INTENT_LABELS.append((INTENTS[i].intent_label,INTENTS[i].intent_label))

        print(self.instance)
        slots = self.instance.intentslot_set.all().values('slot_name','color_hex')
        slots_choices = [(entry["slot_name"],entry["slot_name"]) for entry in slots]
        print("here",slots_choices)
        self.fields["intent_label_choices"] = forms.ChoiceField(choices=self.INTENT_LABELS,widget=forms.Select(attrs={'onChange':'updateForm()'}))
        self.fields["slots_choices"] = forms.ChoiceField(choices=slots_choices, widget=forms.RadioSelect(attrs={}))

    # def clean(self):
    #     cleaned_data = self.cleaned_data
    #     super(IntentForm, self).clean()
    #     return cleaned_data
    # def save(self):
    #     intent = self.instance
    #     intent.intent_label = self.cleaned_data["intent_label"]
    #     intent.intentslot_set.all().delete()
    #     for slot in self.cleaned_data["slots"]:
    #        IntentSlot.objects.create(
    #            intent=intent,
    #            slot_name=slot,
    #        )