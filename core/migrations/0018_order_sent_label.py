# Generated by Django 4.0.4 on 2022-12-05 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_order_processed_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='sent_label',
            field=models.BooleanField(default=False),
        ),
    ]
