# Generated by Django 3.0.3 on 2020-02-11 07:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('submit_intents', '0003_auto_20200211_1026'),
    ]

    operations = [
        migrations.RenameField(
            model_name='intentinstance',
            old_name='intent_label',
            new_name='label',
        ),
    ]
