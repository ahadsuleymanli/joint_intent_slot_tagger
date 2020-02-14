from django.http import  HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.template import loader
from django.urls import reverse
from django.db.models import F
from django.db import models
from django.views import generic
from django.utils import timezone
from django import forms
from .models import *
from .forms import *
from .create_dataset import CreateDataset, DATASET_DIR


def add_intent_to_db(label, seq_in, seq_out, id=None):
    seq_in = seq_in.strip().lower().split()
    seq_out = seq_out.strip().split()
    if len(seq_in) != len(seq_out):
        print("seq_in seq_out lengths don't match")
    else:
        seq_in = ' '.join(seq_in)
        seq_out = ' '.join(seq_out)
        if id and id.isdigit():
            found_object = IntentInstance.objects.get(pk=id)
            if found_object:
                found_object.seq_in=seq_in
                found_object.seq_out=seq_out
                found_object.save()
        else:
            IntentInstance.objects.create(label=label,seq_in=seq_in,seq_out=seq_out)

def delete_intent_from_db(id):
    if id.isdigit():
        IntentInstance.objects.filter(pk=id).delete()

def index(request):
    if request.method == 'POST':
        intent_label = ''
        form = SubmitIntentsForm(request.POST)
        valid = form.is_valid()
        cd = form.cleaned_data
        print(cd)
        if "intent_label_choices" in cd:
            intent_label = cd["intent_label_choices"]
        if 'submit_btn' in request.POST:
            if "intent_id_to_modify" in cd :
                add_intent_to_db(cd["intent_label_choices"],cd["seq_in_field"],cd["seq_out_field"],cd["intent_id_to_modify"])
            else:
                add_intent_to_db(cd["intent_label_choices"],cd["seq_in_field"],cd["seq_out_field"])
        elif "intent_id_to_delete" in cd:
            delete_intent_from_db(cd["intent_id_to_delete"])

        return HttpResponseRedirect('/index?intent_label='+intent_label)
    else:
        if 'intent_label' in request.GET and request.GET["intent_label"]:
            intent = IntentCategory.objects.filter(intent_label=request.GET["intent_label"]).first()
            form = SubmitIntentsForm(instance=intent)
        else:
            form = SubmitIntentsForm(request.POST)

    return render(request, 'submit_intents/index.html', {'form': form})

def edit_intents(request):
    if request.method == 'POST':

        form = EditIntentLabelsForm(request.POST)
        form.is_valid()
        cd = form.cleaned_data
        if "new_intent_label_field" in cd:
            if 'remove_intent_label' in request.POST:
                IntentCategory.objects.filter(intent_label=cd["new_intent_label_field"]).delete()
            elif 'add_intent_label' in request.POST:
                IntentCategory.objects.create(intent_label=cd["new_intent_label_field"])
        elif "intent_label_choices" in cd and 'update_slots' in request.POST:
            intent = get_object_or_404(IntentCategory, intent_label=cd["intent_label_choices"])
            intent.intentslot_set.all().delete()
            if "slots_field" in cd:
                for word in cd["slots_field"].split():
                    IntentSlot.objects.create(intent=intent,slot_name=word)

        return HttpResponseRedirect('/index/edit_intents')
    else:
        form = EditIntentLabelsForm()
    return render(request, 'submit_intents/edit_intents.html', {'form': form})


def view(request):
    template = loader.get_template('submit_intents/view.html')
    context = {}
    return HttpResponse(template.render(context, request))


def export_dataset(request):
    interleave_categories = False
    shuffle = False
    if request.method == 'POST':
        if 'interleave_categories' in request.POST:
            interleave_categories = request.POST['interleave_categories']=='interleave_categories'
        if 'shuffle_intents' in request.POST:
            shuffle = request.POST['shuffle_intents']=='shuffle_intents'
        if "export_dataset" in request.POST: 
            CreateDataset.create_single_file_dataset(interleave_categories,shuffle)
        elif "import_dataset" in request.POST:
            CreateDataset.import_dataset()
        elif "create_dataset_split" in request.POST:
            if request.POST["create_dataset_split"] == "create_dataset_split_70%-15%-15%":
                CreateDataset.create_dataset_split([0.7,0.15,0.15],interleave_categories,shuffle)
            elif request.POST["create_dataset_split"] == "create_dataset_split_80%-20%":
                CreateDataset.create_dataset_split([0.8,0.2],interleave_categories,shuffle)
        elif "clear_dataset" in request.POST:
            IntentInstance.objects.all().delete()
        elif "clear_categories" in request.POST:
            IntentSlot.objects.all().delete()
            IntentCategory.objects.all().delete()

        return HttpResponseRedirect('/index/export_dataset')

    return render(request, 'submit_intents/export_dataset.html',{"dataset_dir":DATASET_DIR})