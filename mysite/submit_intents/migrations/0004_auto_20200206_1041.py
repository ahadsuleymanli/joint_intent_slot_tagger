# Generated by Django 3.0.3 on 2020-02-06 07:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('submit_intents', '0003_auto_20200206_1014'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='intentslot',
            unique_together={('intent', 'slot_name')},
        ),
    ]
