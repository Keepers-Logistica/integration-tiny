import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.models import Order


def update_status_order(payload):
    order_number = payload.get('order_number', None)
    integrator_id = payload.get('id', None)

    try:
        order = Order.objects.get(
            number=order_number,
            integrator_id=integrator_id
        )
        order.update_status(Order.CANCELLED)

    except Order.DoesNotExist:
        print(f"Order with number {order_number} does not exist")


# Create your views here.
@csrf_exempt
@require_POST
def receiver_webhooks(request):
    payload = json.loads(request.body)

    update_status_order(payload)

    return HttpResponse()
