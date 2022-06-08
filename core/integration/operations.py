import json
import os
from io import BytesIO
from typing import List
from urllib.parse import urljoin
from urllib.request import urlopen
from zipfile import BadZipfile, ZipFile

import requests
import xmltodict
from django.core.files.base import ContentFile
from django.forms import model_to_dict
from django.utils import timezone

from core import logger
from core.integration.entities import OrderItemData, ResponseSerializer
from core.models import Configuration, Customer, Order, OrderItems
from integration_tiny.settings import (BASE_URL_INTEGRATOR, BASE_URL_TINY)


def remove_ascii_character(value):
    if isinstance(value, bytes):
        try:
            value = value.decode('utf-8')
        except UnicodeDecodeError:
            value = value.decode('ISO-8859-1')

    return value


def request(resource, params):
    response = requests.get(
        urljoin(BASE_URL_TINY, resource),
        params=params
    )

    if response and response.status_code == 200:
        return response.json()

    raise ConnectionError('Connection error by Tiny')


class OperationError(Exception):
    pass


class BaseOperation(object):
    RESOURCE: str = ''

    def __init__(self, configuration):
        self.configuration: Configuration = configuration
        self.params = dict(
            formato='json',
            token=self.configuration.token
        )
        self.resource: str = self.RESOURCE

        self.update_params()

    def serializer(self, response) -> ResponseSerializer:
        serializer = ResponseSerializer(response)

        if not serializer.has_error:
            return serializer

        raise OperationError(serializer.errors)

    def update_params(self):
        pass

    def request(self) -> dict:
        response = requests.get(
            urljoin(BASE_URL_TINY, self.resource),
            params=self.params
        )

        if response and response.status_code == 200:
            return response

        raise OperationError('Connection error by Tiny')

    def after_execution(self):
        pass

    def before_execution(self):
        pass

    def save(self, serializer: ResponseSerializer):
        pass

    def execute(self):
        response = self.request()

        serializer = self.serializer(response)

        self.before_execution()

        self.save(serializer)

        self.after_execution()


class SendRequestToIntegrator:
    def __init__(self, order: Order):
        self.__order = order
        self.__configuration = order.configuration

    def __serializer_payload(self):
        payload = model_to_dict(
            self.__order,
            fields=(
                'customer',
                'observation',
                'cnpj_transport'
            )
        )

        items = [model_to_dict(
            item,
            exclude=('id',))
            for item in self.__order.items.all()
        ]
        customer = model_to_dict(
            self.__order.customer,
            exclude=('id',)
        )

        payload.update({
            'order_number': self.__order.number,
            'items': items,
            'customer': customer
        })

        return payload

    @property
    def payload(self):
        payload = self.__serializer_payload()

        return json.dumps(payload)

    def send_request_by_integrator(self):
        resource = urljoin(BASE_URL_INTEGRATOR, 'orders/simple')
        headers = {
            'content-type': 'application/json',
            'Authorization': f'Token {self.__configuration.token_integrator}'
        }
        response = requests.post(
            url=resource,
            headers=headers,
            data=self.payload
        )

        return response.json()

    def execute(self):
        content = self.send_request_by_integrator()

        if content:
            self.__order.integrator_id = content.get('id', None)
            self.__order.status = Order.IMPORTED

        self.__order.save()

        SendRequestBillingToIntegrator(
            self.__order
        ).execute()


class SendRequestLabelToIntegrator:
    def __init__(self, order: Order):
        self.__order = order
        self.__configuration = order.configuration

    @property
    def payload(self):
        return [
            ('attachment', self.__order.label.open('rb'))
        ]

    def send_request(self):
        resource = urljoin(
            BASE_URL_INTEGRATOR,
            f'orders/{self.__order.integrator_id}/attachment'
        )
        headers = {
            'Authorization': f'Token {self.__configuration.token_integrator}',
        }
        response = requests.post(
            url=resource,
            headers=headers,
            files=self.payload
        )

        return response.content

    def execute(self):
        if not self.__order.integrator_id:
            return

        self.send_request()


class SaveLabelOrder(BaseOperation):
    RESOURCE = 'expedicao.obter.etiquetas.impressao.php'

    def __init__(self, configuration, order):
        self.__order: Order = order

        super().__init__(configuration)

    def update_params(self):
        self.params.update(
            idExpedicao=self.__order.expedition_id
        )

    def generate_file(self, content):
        self.__order.label.save(
            os.path.join(
                self.__order.configuration.name,
                f'{self.__order.number}.pdf'
            ),
            ContentFile(content)
        )

    def save_label(self, labels):
        for label in labels:
            resp = urlopen(label)
            content = resp.read()
            try:
                with ZipFile(BytesIO(content)) as zipfile:
                    for filename in zipfile.namelist():
                        self.generate_file(
                            zipfile.read(filename).decode(),
                        )
            except BadZipfile:
                self.generate_file(content)

    def save(self, serializer: ResponseSerializer):
        logger.info(f'Create xml file by order {self.__order}')

        self.save_label(serializer.labels)

        SendRequestLabelToIntegrator(
            self.__order
        ).execute()


class SaveExpeditionInfo(BaseOperation):
    RESOURCE = 'expedicao.obter.php'

    def __init__(self, configuration, order):
        self.__order: Order = order

        super().__init__(configuration)

    def update_params(self):
        self.params.update(
            idObjeto=self.__order.invoice_id,
            tipoObjeto='notafiscal'
        )

    def save(self, serializer: ResponseSerializer):
        logger.info(f'Save expedition info by order {self.__order}')

        payload = serializer.expedition

        for field, value in payload.items():
            setattr(self.__order, field, value)

        self.__order.save(
            update_fields=list(payload.keys())
        )

        SaveLabelOrder(
            self.configuration,
            self.__order
        ).execute()

    def before_execution(self):
        if not self.__order.running:
            self.__order.set_running()

    def after_execution(self):
        if self.__order.running:
            self.__order.set_running(False)


class SaveInvoiceFile(BaseOperation):
    RESOURCE = 'nota.fiscal.obter.xml.php'

    def __init__(self, configuration, order):
        self.__order: Order = order

        super().__init__(configuration)

    def update_params(self):
        self.params.update(
            id=self.__order.invoice_id
        )

    def extract_content_invoice(self, content):
        content = xmltodict.parse(content)
        content = content.get('retorno').get('xml_nfe')

        return xmltodict.unparse(content)

    def save(self, serializer: ResponseSerializer):
        logger.info(f'Create xml file by order {self.__order}')

        filename = f'NFE_{self.__order.number}.xml'
        self.__order.xml.save(
            os.path.join(
                self.__order.configuration.name,
                filename
            ),
            ContentFile(
                self.extract_content_invoice(
                    serializer.data
                )
            )
        )

        self.__order.update_status(
            Order.AWAITING_INTEGRATION
        )

        SendRequestToIntegrator(
            self.__order
        ).execute()


class SaveInvoice(BaseOperation):
    RESOURCE = 'nota.fiscal.obter.php'

    def __init__(self, configuration, order):
        self.__order: Order = order

        super().__init__(configuration)

    def update_params(self):
        self.params.update(
            id=self.__order.invoice_id
        )

    def save_items(self, order: Order, items: List[OrderItemData]):
        logger.info(items)

        order.items.all().delete()

        bulk_items = [
            OrderItems(
                idseq=idseq,
                order=order, **item.to_dict()
            )
            for idseq, item in enumerate(items, start=1)
        ]
        OrderItems.objects.bulk_create(bulk_items)

    def save(self, serializer: ResponseSerializer):
        logger.info(f'Save invoice by order {self.__order}')

        payload = serializer.invoice

        items = payload.pop('items')

        for field, value in payload.items():
            setattr(self.__order, field, value)

        if self.configuration.use_invoice_items:
            self.save_items(self.__order, items)

            self.__order.products = len(items)

        self.__order.save()

        if self.__order.is_save_xml():
            SaveInvoiceFile(
                self.configuration,
                self.__order
            ).execute()


class UpdateOrder(BaseOperation):
    RESOURCE = 'pedido.obter.php'

    def __init__(self, configuration, order):
        self.__order: Order = order

        super().__init__(configuration)

    def save_items(self, order: Order, items: List[OrderItemData]):
        logger.info(items)

        order.items.all().delete()

        bulk_items = [
            OrderItems(
                idseq=idseq,
                order=order, **item.to_dict()
            )
            for idseq, item in enumerate(items, start=1)
        ]
        OrderItems.objects.bulk_create(bulk_items)

    def save_customer(self, customer: dict):
        instance, created = Customer.objects.update_or_create(
            cnpj_cpf=customer.pop('cnpj_cpf'),
            postal_code=customer.pop('postal_code'),
            defaults=customer
        )
        instance.save()

        return instance

    def update_params(self):
        self.params.update(
            id=self.__order.identifier
        )

    def save(self, serializer: ResponseSerializer):
        logger.info(f"Update order {self.__order}")

        payload = serializer.order
        customer = self.save_customer(
            payload.pop('customer')
        )
        items = payload.pop('items')

        self.__order.customer = customer

        for field, value in payload.items():
            setattr(self.__order, field, value)

        if not self.configuration.use_invoice_items:
            self.save_items(self.__order, items)

            self.__order.products = len(items)

        self.__order.update_status(Order.AWAITING_FILES)

        try:
            SaveInvoice(
                configuration=self.configuration,
                order=self.__order
            ).execute()
        except OperationError as error:
            logger.warning(
                f'[Save Invoice - {self.__order}] - {error}'
            )

    def before_execution(self):
        self.__order.set_running()

    def after_execution(self):
        self.__order.set_running(False)


class GetCancelledOrders(BaseOperation):
    RESOURCE = 'pedidos.pesquisa.php'

    def update_params(self):
        before = (
            timezone.now() - timezone.timedelta(days=self.configuration.days)
        ).strftime('%d/%m/%Y')
        now = timezone.now().strftime('%d/%m/%Y')

        self.params.update(
            dataInicialOcorrencia=before,
            dataFinalOcorrencia=now,
            situacao='cancelado',
            sort="DESC"
        )

    def save(self, serializer: ResponseSerializer):
        logger.info('Starting the search for canceled orders...')

        orders = serializer.orders
        identifiers = [order.get('identifier', None) for order in orders]
        identifiers = list(filter(None, identifiers))

        orders = Order.objects.filter(
            identifier__in=identifiers,
            configuration=self.configuration,
        ).exclude(status=Order.CANCELLED)

        if orders:
            logger.info(
                f"{orders.count()} Orders canceled of "
                f"{self.configuration}"
            )
            orders.update(status=Order.CANCELLED)

        logger.info(f"End of search for canceled orders")


class SaveOrders(BaseOperation):
    RESOURCE = 'pedidos.pesquisa.php'

    def update_params(self):
        before = (
            timezone.now() - timezone.timedelta(days=self.configuration.days)
        ).strftime('%d/%m/%Y')
        now = timezone.now().strftime('%d/%m/%Y')

        self.params.update(
            dataInicialOcorrencia=before,
            dataFinalOcorrencia=now,
            sort="DESC"
        )
        if self.configuration.status:
            self.params.update(
                situacao=self.configuration.status
            )

    def save(self, serializer: ResponseSerializer):
        logger.info('Starting an order sync...')

        orders = serializer.orders

        for informations_order in orders:
            order = Order(
                number=informations_order.pop('number'),
                number_store=informations_order.pop('number_store'),
                configuration=self.configuration,
                **informations_order
            )

            Order.objects.get_or_create(
                number=order.number,
                number_store=order.number_store,
                configuration=self.configuration,
                defaults=informations_order
            )

        logger.info(f"Sync finished with {len(orders)} orders saved")


class SendRequestBillingToIntegrator:
    def __init__(self, order: Order):
        self.__order = order
        self.__configuration = order.configuration

    @property
    def payload(self):
        return [
            ('xml', self.__order.xml.open('rb'))
        ]

    def send_request(self):
        resource = urljoin(
            BASE_URL_INTEGRATOR,
            f'orders/{self.__order.integrator_id}/billing'
        )
        headers = {
            'Authorization': f'Token {self.__configuration.token_integrator}',
        }
        response = requests.post(
            url=resource,
            headers=headers,
            files=self.payload
        )

        return response.content

    def execute(self):
        if not self.__order.integrator_id:
            return

        self.send_request()

        try:
            if self.__order.search_label:
                SaveExpeditionInfo(
                    self.__order.configuration,
                    self.__order
                ).execute()

        except OperationError as error:
            logger.warning(f'[Save Expedition - {self.__order}] - {error}')


class SendRequestCancelationToIntegrator:
    def __init__(self, order: Order):
        self.__order = order
        self.__configuration = order.configuration

    def send_request(self):
        resource = urljoin(
            BASE_URL_INTEGRATOR,
            f'orders/{self.__order.integrator_id}/cancelation'
        )
        headers = {
            'Authorization': f'Token {self.__configuration.token_integrator}',
        }
        response = requests.post(
            url=resource,
            headers=headers
        )

        return response.content

    def execute(self):
        if not self.__order.integrator_id:
            return

        self.send_request()


class GetOrderInIntegrator:
    def __init__(self, order: Order):
        self.__order = order
        self.__configuration = order.configuration

    def send_request(self):
        resource = urljoin(
            BASE_URL_INTEGRATOR,
            f'orders?order_number={self.__order.number}'
        )
        headers = {
            'Authorization': f'Token {self.__configuration.token_integrator}',
        }
        response = requests.get(
            url=resource,
            headers=headers
        )

        if response and response.status_code == 200:
            return response.json()

        return None

    def execute(self):
        data = self.send_request()

        if data:
            results = data.get('results', [])

            if not results:
                self.__order.update_status(Order.CANCELLED)
                return

            self.__order.integrator_id = results[0]['id']
            self.__order.save(
                update_fields=['integrator_id']
            )
