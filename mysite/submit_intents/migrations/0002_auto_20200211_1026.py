# Generated by Django 3.0.3 on 2020-02-11 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submit_intents', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='intentinstance',
            name='intent_slots',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='intentinstance',
            name='intent_text',
            field=models.CharField(default='', max_length=255),
        ),
    ]