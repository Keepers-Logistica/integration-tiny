import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.models import Order


def get_order(payload):
    order_number = payload.get('order_number', None)
    integrator_id = payload.get('id', None)

    order = Order.objects.get(
        number=order_number,
        integrator_id=integrator_id
    )

    return order


# Create your views here.
@csrf_exempt
@require_POST
def receiver_webhooks(request):
    payload = json.loads(request.body)

    try:
        order = get_order(payload)
        order.update_status(Order.CANCELLED)

    except Order.DoesNotExist:
        pass

    return HttpResponse()


@csrf_exempt
@require_POST
def receiver_processed_order(request):
    payload = json.loads(request.body)

    try:
        order = get_order(payload)
        order.set_processed()

    except Order.DoesNotExist:
        pass

    return HttpResponse()
