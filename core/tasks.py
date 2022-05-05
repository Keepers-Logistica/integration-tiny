from core.integration.operations import (OperationError, SaveExpeditionInfo, SaveOrders, SendRequestToIntegrator,
                                         UpdateOrder)
from core.models import Configuration
from core.models import Order
from integration_tiny.celery import app


@app.task(rate_limit='10/m')
def task_send_order_to_integrador(order_id):
    order = Order.objects.get(
        id=order_id
    )

    SendRequestToIntegrator(
        order,
    ).execute()


@app.task(rate_limit='10/m')
def task_update_order(order_id):
    order = Order.objects.get(
        id=order_id
    )

    UpdateOrder(
        order.configuration,
        order
    ).execute()


@app.task(rate_limit='1/s')
def task_update_orders():
    orders = Order.objects.search_update_orders()

    for order in orders:
        task_update_order.delay(
            order.id
        )


@app.task
def task_search_expedition(order_id):
    order = Order.objects.get(
        id=order_id
    )
    try:
        SaveExpeditionInfo(
            order.configuration,
            order
        ).execute()
    except OperationError as error:
        print(f'[Order {order}] - Save labels: {error}')


@app.task
def task_search_expeditions():
    orders = Order.objects.search_expedition()

    for order in orders:
        task_search_expedition.delay(
            order.pk
        )


@app.task
def task_sync_orders(configuration_id):
    queryset = Configuration.objects.filter(
        is_active=True
    ).all()
    if configuration_id > 0:
        queryset = queryset.filter(
            id=configuration_id
        )

    for configuration in queryset:
        try:
            SaveOrders(configuration).execute()

            task_update_orders.delay()

        except OperationError as error:
            print(f'[{configuration}] - Sync orders: {error}')
