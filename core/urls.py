from django.urls import path

from core.views import receiver_webhooks

urlpatterns = [
    path('receiver/hooks', receiver_webhooks, name='receiver-hooks')
]
