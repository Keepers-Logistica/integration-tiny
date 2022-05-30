from json.decoder import JSONDecodeError

from utils.formatts import Formatattr


class Base:

    def to_dict(self):
        attribs = [(k, v) for k, v in self.__dict__.items() if not k.startswith("_")]

        for name in dir(self.__class__):
            if name.startswith("_"):
                continue
            obj = getattr(self.__class__, name)

            if isinstance(obj, property):
                val = obj.__get__(self, self.__class__)
                attribs.append((name, val))

        return dict(attribs)


class CustomerData(Base):

    def __init__(self, data):
        self.__name = data.get('nome', None)
        self.__cnpj_cpf = data.get('cpf_cnpj', None)
        self.__postal_code = data.get('cep', None)
        self.__address = data.get('endereco', None)
        self.__complement = data.get('complemento', None)
        self.__neighbourhood = data.get('bairro', None)
        self.__postal_code = data.get('cep', None)
        self.__state = data.get('uf', None)
        self.__city = data.get('cidade', None)
        self.__number = data.get('numero', None)

    @property
    def name(self):
        return str(self.__name).upper()

    @property
    def address(self):
        return str(self.__address).upper()

    @property
    def complement(self):
        return str(self.__complement).upper()

    @property
    def neighbourhood(self):
        return str(self.__neighbourhood).upper()

    @property
    def state(self):
        return str(self.__state).upper()

    @property
    def number(self):
        return str(self.__number)

    @property
    def city(self):
        return str(self.__city).upper()

    @property
    def cnpj_cpf(self):
        return Formatattr(self.__cnpj_cpf).in_cnpj.value

    @property
    def postal_code(self):
        return Formatattr(
            self.__postal_code
        ).remove_character.in_zip_code.value


class OrderItemData(Base):
    def __init__(self, data: dict):
        self.product = data.get('codigo', None)
        self.description = data.get('descricao', None)
        self.unit_of_measurement = data.get('unidade', None)
        self.__quantity = data.get('quantidade', 0)
        self.__unity_price = data.get('valor_unitario', 0)

    @property
    def quantity(self):
        return Formatattr(self.__quantity).format_float.value

    @property
    def unit_price(self):
        return Formatattr(self.__unity_price).format_float.value

    @property
    def total_price(self):
        return float(self.quantity * self.unit_price)


class OrderResumeData(Base):
    def __init__(self, data: dict):
        self.identifier = data.get('id', None)
        self.__number = data.get('numero', None)
        self.__number_store = data.get('numero_ecommerce', None)

    @property
    def number(self):
        try:
            return int(self.__number)
        except ValueError:
            return None

    @property
    def number_store(self):
        return self.__number_store


class OrderData(Base):

    def __init__(self, data: dict):
        self.__number = data.get('numero', None)
        self.__number_store = data.get('numero_ecommerce', None)
        self.__observation = data.get('obs', None)
        self.__customer = data.get('cliente', {})
        self.__items = data.get('itens', [])

        self.invoice_id = data.get('id_nota_fiscal')

    @property
    def number(self):
        try:
            return int(self.__number)
        except ValueError:
            return None

    @property
    def number_store(self):
        return self.__number_store

    @property
    def customer(self):
        customer = CustomerData(self.__customer)

        return customer.to_dict()

    @property
    def items(self):
        items = []

        for item in self.__items:
            informations_item = item.get('item', {})

            items.append(OrderItemData(informations_item))

        return items

    @property
    def observation(self):
        return Formatattr(
            self.__observation
        ).remove_character.remove_blank.value


class InvoiceData(Base):
    def __init__(self, data: dict):
        self.sequence = data.get('serie', None)
        self.access_key = data.get('chave_acesso', None)
        self.invoice = data.get('numero', None)

        self.__invoice_status = data.get('situacao', 1)
        self.__transport = data.get('transport', {})
        self.__items = data.get('itens', [])

    @property
    def invoice_status(self):
        return int(self.__invoice_status)

    @property
    def cnpj_transport(self):
        cnpj = self.__transport.get('cpf_cnpj', None)

        if cnpj:
            return Formatattr(
                cnpj
            ).in_cnpj.value

        return cnpj

    @property
    def items(self):
        items = []

        for item in self.__items:
            informations_item = item.get('item', {})

            items.append(OrderItemData(informations_item))

        return items


class OrderExpeditionInfo(Base):
    def __init__(self, data: dict):
        self.expedition_id = data.get('id', None)
        self.group_expedition_id = data.get('idAgrupamento', None)


class ResponseSerializer:
    def __init__(self, response):
        self.__errors = []
        try:
            self.data = response.json()
            self.__root = self.data.get('retorno', {})
            self.__orders = self.__root.get('pedidos', [])
            self.__order = self.__root.get('pedido', {})
            self.__invoice = self.__root.get('nota_fiscal', {})
            self.__errors = self.__root.get('erros', None)
            self.__expedition = self.__root.get('expedicao', {})
            self.__labels = self.__root.get('links', [])

        except JSONDecodeError:
            self.data = response.content

    def __serializer_orders(self):
        return [OrderResumeData(
            order.get('pedido')
        ).to_dict() for order in self.__orders]

    def __serializer_order(self):
        return OrderData(self.__order).to_dict()

    def __serializer_invoice(self):
        return InvoiceData(self.__invoice).to_dict()

    def __serializer_errors(self):
        if self.__errors:
            if isinstance(self.__errors, list):
                return self.__errors[0].get('erro')

            return self.__errors.get('erro')

    def __serializer_expedition(self):
        return OrderExpeditionInfo(self.__expedition).to_dict()

    def __serializer_labels(self):
        return [label.get('link') for label in self.__labels]

    @property
    def invoice(self):
        return self.__serializer_invoice()

    @property
    def orders(self):
        return self.__serializer_orders()

    @property
    def order(self):
        return self.__serializer_order()

    @property
    def errors(self):
        return self.__serializer_errors()

    @property
    def labels(self):
        return self.__serializer_labels()

    @property
    def expedition(self):
        return self.__serializer_expedition()

    @property
    def has_error(self):
        if self.__errors:
            return bool(len(self.__errors))

        return False

    @property
    def status(self):
        return self.__root.get(
            'status_processamento',
            None
        )

    @property
    def verbose_status(self):
        return self.__root.get(
            'status',
            None
        )

    @property
    def code(self):
        return self.__root.get(
            'codigo_erro',
            None
        )
