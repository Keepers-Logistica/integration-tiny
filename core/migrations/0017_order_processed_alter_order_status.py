# Generated by Django 4.0.4 on 2022-06-28 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_configuration_use_invoice_items'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='processed',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Aguardando arquivos'), (1, 'Aguardando integração'), (2, 'Importado'), (3, 'Cancelado')], default=0),
        ),
    ]
