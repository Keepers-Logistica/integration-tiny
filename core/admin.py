from django.contrib import admin

from core.filters import OrderHasLabelFilter
from core.tasks import *


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    pass


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    actions = (
        'handle_sync_orders',
        'handle_sync_cancelled_orders',
        'handle_sync_order_processed'
    )

    def handle_sync_orders(self, request, queryset):
        for configuration in queryset:
            task_sync_orders.delay(
                configuration.id
            )

    handle_sync_orders.short_description = 'Sincronizar pedidos'

    def handle_sync_cancelled_orders(self, request, queryset):
        for configuration in queryset:
            task_sync_cancelled_orders.delay(
                configuration.id
            )

    handle_sync_cancelled_orders.short_description = 'Sincronizar pedidos cancelados'

    def handle_sync_order_processed(self, request, queryset):
        for configuration in queryset:
            task_sync_processed_orders.delay(
                configuration.id
            )

    handle_sync_order_processed.short_description = 'Sincronizar pedidos processados'


# Register your models here.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'number',
        'number_store',
        'customer',
        'status',
        'contains_xml',
        'contains_label',
        'verbose_invoice',
        'invoice_status',
        'contains_transport',
        'contains_integrator_id',
        'products',
        'created_at',
        'updated_at'
    )

    list_filter = ('configuration', 'status', 'created_at', 'sequence', OrderHasLabelFilter, 'running')
    actions = (
        'handle_get_expedition_info',
        'handle_get_update_orders',
        'handle_send_billing_to_integrator',
        'handle_send_order_to_integrator',
        'handle_send_label_to_integrator',
        'handle_send_cancelation_to_integrator'
    )
    search_fields = ('number', 'number_store')

    def contains_xml(self, obj: Order):
        return bool(obj.xml)

    contains_xml.boolean = True
    contains_xml.short_description = 'XML'

    def verbose_invoice(self, obj: Order):
        return f'{obj.invoice}/{obj.sequence}'

    verbose_invoice.short_description = 'Nota fiscal'

    def contains_transport(self, obj: Order):
        return bool(obj.cnpj_transport)

    contains_transport.boolean = True
    contains_transport.short_description = 'Transportadora'

    def contains_label(self, obj: Order):
        return bool(obj.label)

    contains_label.boolean = True
    contains_label.short_description = 'Etiqueta'

    def contains_integrator_id(self, obj: Order):
        return bool(obj.integrator_id)

    contains_integrator_id.boolean = True
    contains_integrator_id.short_description = 'Integrator Id'

    def handle_get_expedition_info(self, request, queryset):
        for order in queryset:
            print(order.id)
            task_search_expedition.delay(
                order.id
            )

    handle_get_expedition_info.short_description = 'Buscar expedição'

    def handle_get_update_orders(self, request, queryset):
        for order in queryset:
            print(order.id)
            task_update_order.delay(
                order.id
            )

    handle_get_update_orders.short_description = 'Atualizar pedidos'

    def handle_send_order_to_integrator(self, request, queryset):
        for order in queryset:
            task_send_order_to_integrador.delay(
                order.id
            )

    handle_send_order_to_integrator.short_description = 'Enviar pedido'

    def handle_send_cancelation_to_integrator(self, request, queryset):
        for order in queryset:
            task_send_cancelation_to_integrador.delay(
                order.id
            )

    handle_send_cancelation_to_integrator.short_description = 'Enviar solicitação de cancelamento'

    def handle_get_order_in_integrator(self, request, queryset):
        for order in queryset:
            task_get_order_in_integrador.delay(
                order.id
            )

    handle_get_order_in_integrator.short_description = 'Buscar pedido - Integrador'

    def handle_send_label_to_integrator(self, request, queryset):
        for order in queryset:
            SendRequestLabelToIntegrator(
                order
            ).execute()

    handle_send_label_to_integrator.short_description = 'Enviar etiqueta'

    def handle_send_billing_to_integrator(self, request, queryset):
        for order in queryset:
            SendRequestBillingToIntegrator(
                order
            ).execute()

    handle_send_billing_to_integrator.short_description = 'Enviar faturamento'


@admin.register(OrderItems)
class OrderItemAdmin(admin.ModelAdmin):
    pass
