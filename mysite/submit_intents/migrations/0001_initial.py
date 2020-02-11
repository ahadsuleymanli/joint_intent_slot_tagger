# Generated by Django 3.0.3 on 2020-02-11 07:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='IntentCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intent_label', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='IntentInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intent_label', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='IntentSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slot_name', models.CharField(max_length=50)),
                ('color_hex', models.CharField(default='#4b4b4b', max_length=9)),
                ('intent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submit_intents.IntentCategory')),
            ],
        ),
        migrations.AddConstraint(
            model_name='intentcategory',
            constraint=models.UniqueConstraint(fields=('intent_label',), name='unique constraint'),
        ),
        migrations.AlterUniqueTogether(
            name='intentslot',
            unique_together={('intent', 'slot_name')},
        ),
    ]
