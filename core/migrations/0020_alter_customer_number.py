# Generated by Django 4.0.4 on 2023-01-26 11:19

import core.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_set_field_sent_label'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='number',
            field=core.fields.CustomCharField(blank=True, max_length=10, null=True),
        ),
    ]
