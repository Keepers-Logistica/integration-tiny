# Generated by Django 4.0.3 on 2022-03-09 18:15

import core.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('token_integrator', models.CharField(max_length=200)),
                ('token_bling', models.CharField(max_length=200)),
                ('is_number_store', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Configuration',
                'verbose_name_plural': 'Configurations',
            },
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=60, null=True)),
                ('fantasy_name', models.CharField(blank=True, max_length=60, null=True)),
                ('address', models.CharField(max_length=80)),
                ('complement', models.CharField(blank=True, max_length=100, null=True)),
                ('neighbourhood', models.CharField(max_length=50)),
                ('city', models.CharField(max_length=40)),
                ('state', models.CharField(max_length=2)),
                ('postal_code', models.CharField(max_length=9)),
                ('cnpj_cpf', models.CharField(max_length=20)),
                ('number', models.CharField(blank=True, max_length=10, null=True)),
            ],
            options={
                'verbose_name': 'Customer',
                'verbose_name_plural': 'Customer',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(blank=True, null=True)),
                ('number_store', models.IntegerField(blank=True, null=True)),
                ('observation', models.CharField(blank=True, max_length=200, null=True)),
                ('cnpj_transport', models.CharField(blank=True, max_length=20, null=True)),
                ('invoice', models.IntegerField(blank=True, null=True)),
                ('sequence', models.IntegerField(blank=True, null=True)),
                ('access_key', models.CharField(blank=True, max_length=50, null=True)),
                ('xml', models.FileField(blank=True, null=True, storage=core.models.OverwriteStorage(), upload_to='')),
                ('integrator_id', models.IntegerField(blank=True, null=True)),
                ('status', models.PositiveSmallIntegerField(choices=[(0, 'Aguardando arquivos'), (1, 'Aguardando integração'), (2, 'Importado')], default=0)),
                ('invoice_status', models.PositiveSmallIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('configuration', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.configuration')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='customer', to='core.customer')),
            ],
            options={
                'verbose_name': 'Order',
                'verbose_name_plural': 'Orders',
            },
        ),
        migrations.CreateModel(
            name='OrderItems',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product', models.CharField(max_length=60)),
                ('idseq', models.IntegerField()),
                ('description', models.CharField(blank=True, max_length=120, null=True)),
                ('unit_of_measurement', models.CharField(blank=True, max_length=6, null=True)),
                ('quantity', models.IntegerField()),
                ('unit_price', models.FloatField(default=1)),
                ('total_price', models.FloatField(default=1)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.order')),
            ],
            options={
                'verbose_name': 'Order Items',
                'verbose_name_plural': 'Orders And Items',
            },
        ),
    ]
