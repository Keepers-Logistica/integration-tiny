from celery.signals import beat_init
from django.db import transaction

from core.integration.operations import *
from core.models import Configuration
from core.models import Order
from integration_tiny.celery import app


@app.task(rate_limit='10/m')
def task_get_order_in_integrador(order_id):
    order = Order.objects.get(
        id=order_id
    )

    GetOrderInIntegrator(
        order,
    ).execute()


@app.task(rate_limit='10/m')
def task_send_cancelation_to_integrador(order_id):
    order = Order.objects.get(
        id=order_id
    )

    SendRequestCancelationToIntegrator(
        order,
    ).execute()


@app.task(rate_limit='4/m')
def task_send_order_to_integrador(order_id):
    order = Order.objects.get(
        id=order_id
    )

    SendRequestToIntegrator(
        order,
    ).execute()


@app.task(rate_limit='4/m')
def task_update_order(order_id):
    try:
        order = Order.objects.get(
            id=order_id
        )
        try:
            UpdateOrder(
                order.configuration,
                order
            ).execute()
        except OperationError as error:
            logger.warning(
                f'[Order {order}] - Save labels: {error}'
            )
        finally:
            order.set_running(False)

    except Order.DoesNotExist:
        pass


@app.task(rate_limit='1/s')
def task_update_orders():
    orders = Order.objects.search_update_orders()
    ids = list(
        orders.values_list('id', flat=True)
    )
    orders.update(running=True)

    for _id in ids:
        transaction.on_commit(
            lambda: task_update_order.delay(
                _id
            )
        )


@app.task
def task_search_expedition(order_id):
    try:
        order = Order.objects.get(
            id=order_id
        )
        try:
            SaveExpeditionInfo(
                order.configuration,
                order
            ).execute()
        except OperationError as error:
            logger.warning(
                f'[Order {order}] - Save labels: {error}'
            )

        finally:
            order.set_running(False)
    except Order.DoesNotExist:
        pass


@app.task
def task_search_expeditions():
    orders = Order.objects.search_expedition()
    ids = list(
        orders.values_list('id', flat=True)
    )
    orders.update(running=True)

    for _id in ids:
        transaction.on_commit(
            lambda: task_search_expedition.delay(
                _id
            )
        )


@app.task
def task_sync_processed_orders(configuration_id):
    queryset = Configuration.objects.filter(
        is_active=True
    ).all()
    if configuration_id > 0:
        queryset = queryset.filter(
            id=configuration_id
        )

    for configuration in queryset:
        try:
            GetProcessedOrderInIntegrator(
                configuration
            ).execute()

        except OperationError as error:
            logger.warning(
                f'[{configuration}] - Sync orders: {error}'
            )


@app.task
def task_sync_cancelled_orders(configuration_id):
    queryset = Configuration.objects.filter(
        is_active=True
    ).all()
    if configuration_id > 0:
        queryset = queryset.filter(
            id=configuration_id
        )

    for configuration in queryset:
        try:
            GetCancelledOrders(
                configuration
            ).execute()

        except OperationError as error:
            logger.warning(
                f'[{configuration}] - Sync orders: {error}'
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
            logger.warning(
                f'[{configuration}] - Sync orders: {error}'
            )


@app.task
def task_send_labels():
    queryset = Order.objects.pending_send_labels()

    for order in queryset:
        SendRequestLabelToIntegrator(
            order
        ).execute()


@app.task
def task_send_orders_awaiting_integration():
    queryset = Order.objects.filter(
        status=Order.AWAITING_INTEGRATION,
        running=False
    )

    for order in queryset:
        SendRequestToIntegrator(
            order
        ).execute()


@beat_init.connect
def task_callback_start_beat(**kwargs):
    Order.objects.filter(
        running=True
    ).update(running=False)
