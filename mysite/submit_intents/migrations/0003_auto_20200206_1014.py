# Generated by Django 3.0.3 on 2020-02-06 07:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('submit_intents', '0002_auto_20200206_0955'),
    ]

    operations = [
        migrations.RenameField(
            model_name='intentslot',
            old_name='intent_label',
            new_name='intent',
        ),
    ]
