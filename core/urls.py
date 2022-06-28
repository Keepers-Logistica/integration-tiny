from django.urls import path

from core.views import receiver_processed_order, receiver_webhooks

urlpatterns = [
    path('receiver/hooks', receiver_webhooks, name='receiver-hooks'),
    path(
        'receiver/hooks/processed',
        receiver_processed_order,
        name='receiver-hooks-processed'
    )
]
