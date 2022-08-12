import os

from django.core.files.storage import FileSystemStorage
from django.db import models
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from core.managers import OrderManager
from integration_tiny import settings


class OverwriteStorage(FileSystemStorage):
    """
    Muda o comportamento padrão do Django e o faz sobrescrever arquivos de
    mesmo nome que foram carregados pelo usuário ao invés de renomeá-los.
    """

    def get_available_name(self, name, **kwargs):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name


# Create your models here.
class Configuration(models.Model):
    STATUS_CHOICE = (
        ('aberto', 'Em aberto'),
        ('aprovado', 'Aprovado'),
        ('preparando_envio', 'Preparando Envio'),
        ('faturado', 'Faturado'),
        ('pronto_envio', 'Pronto para envio'),
        ('enviado', 'Enviado'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado')
    )

    name = models.CharField(max_length=50)
    token_integrator = models.CharField(max_length=200)
    token = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICE,
        null=True,
        blank=True
    )
    days = models.IntegerField(default=0)
    search_labels = models.BooleanField(default=False)
    use_invoice_items = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'Configuration {self.name}'

    class Meta:
        verbose_name = _('Configuration')
        verbose_name_plural = _('Configurations')


class Customer(models.Model):
    name = models.CharField(max_length=60, null=True, blank=True)
    fantasy_name = models.CharField(max_length=60, null=True, blank=True)
    address = models.CharField(max_length=80)

    complement = models.CharField(max_length=100, null=True, blank=True)
    neighbourhood = models.CharField(max_length=50)

    city = models.CharField(max_length=40)

    state = models.CharField(max_length=2)

    postal_code = models.CharField(max_length=9)

    cnpj_cpf = models.CharField(max_length=20)
    number = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        verbose_name = _('Customer')
        verbose_name_plural = _('Customer')

    def __str__(self):
        return f"{self.name}"


class Order(models.Model):
    AWAITING_FILES = 0
    AWAITING_INTEGRATION = 1
    IMPORTED = 2
    CANCELLED = 3

    STATUS_INVOICE = (
        (1, 'Pendente'),
        (2, 'Emitida'),
        (3, 'Cancelada'),
        (4, 'Enviada - Aguardando recibo'),
        (5, 'Rejeitada'),
        (6, 'Autorizada'),
        (7, 'Emitida DANFE'),
        (8, 'Registrada'),
        (9, 'Enviada - Aguardando protocolo'),
        (10, 'Denegada'),
    )

    STATUS_AVAILABLE_INVOICE = [6, 7]

    STATUS = (
        (AWAITING_FILES, 'Aguardando arquivos'),
        (AWAITING_INTEGRATION, 'Aguardando integração'),
        (IMPORTED, 'Importado'),
        (CANCELLED, 'Cancelado'),
    )

    identifier = models.IntegerField()
    number = models.IntegerField(null=True, blank=True)
    number_store = models.CharField(max_length=100, null=True, blank=True)
    observation = models.CharField(max_length=200, null=True, blank=True)
    customer = models.ForeignKey(
        Customer,
        related_name='customer',
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )
    cnpj_transport = models.CharField(max_length=20, null=True, blank=True)
    invoice_id = models.IntegerField(null=True, blank=True)
    invoice = models.IntegerField(null=True, blank=True)
    sequence = models.IntegerField(null=True, blank=True)
    access_key = models.CharField(max_length=50, null=True, blank=True)
    xml = models.FileField(
        null=True,
        blank=True,
        storage=OverwriteStorage()
    )
    label = models.FileField(
        null=True,
        blank=True,
        storage=OverwriteStorage()
    )
    configuration = models.ForeignKey(Configuration, on_delete=models.PROTECT)
    integrator_id = models.IntegerField(null=True, blank=True)
    expedition_id = models.IntegerField(null=True, blank=True)
    group_expedition_id = models.IntegerField(null=True, blank=True)
    status = models.PositiveSmallIntegerField(
        choices=STATUS,
        default=AWAITING_FILES
    )
    invoice_status = models.PositiveSmallIntegerField(
        default=1, choices=STATUS_INVOICE
    )
    products = models.PositiveSmallIntegerField(
        default=0
    )
    search_label = models.BooleanField(default=False)
    running = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderManager()

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        self.search_label = self.configuration.search_labels

        super(Order, self).save(
            force_insert,
            force_update,
            using,
            update_fields
        )

    def is_save_xml(self):
        return bool(
            self.invoice_status in Order.STATUS_AVAILABLE_INVOICE
            and self.access_key
        )

    def update_status(self, status, save=True):
        self.status = status

        if not save:
            return

        self.save(
            update_fields=['status']
        )

    def set_running(self, running=True):
        self.running = running
        self.save(update_fields=['running'])

    def set_processed(self, processed=True):
        self.processed = processed
        self.save(update_fields=['processed'])

    def __str__(self):
        return f'{self.number}'


class OrderItems(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.CharField(max_length=60)
    idseq = models.IntegerField()
    description = models.CharField(max_length=120, null=True, blank=True)
    unit_of_measurement = models.CharField(max_length=6, null=True, blank=True)
    quantity = models.IntegerField()
    unit_price = models.FloatField(default=1)
    total_price = models.FloatField(default=1)

    class Meta:
        verbose_name = _('Order Items')
        verbose_name_plural = _('Orders And Items')

    def __str__(self):
        return f"{self.order} - {self.product}"


def delete_file(file):
    if not file:
        return
    if os.path.isfile(file.path):
        os.remove(file.path)


@receiver(models.signals.post_delete, sender=Order)
def auto_delete_file_on_delete(sender, instance: Order, **kwargs):
    delete_file(instance.xml)
    delete_file(instance.label)
