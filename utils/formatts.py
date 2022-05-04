import re


class Formatattr(object):

    def __init__(self, value):
        self.value = value

    def test_regex(self, expression: str) -> bool:
        math_expression = re.match(expression, self.value)

        return True if math_expression else False

    def __format_zip_code(self, value):
        return f"{value[:5]}-{value[5:8]}"

    def __format_cpf(self, value):
        return f"{value[0:3]}.{value[3:6]}.{value[6:9]}-{value[9:11]}"

    def __format_cnpj(self, value):
        return f"{value[:2]}.{value[2:5]}.{value[5:8]}/{value[8:12]}-{value[12:]}"

    def __format_date(self, value):
        return f"{value[:2]}/{value[2:4]}/{value[4:6]}"

    @property
    def is_zip_code(self):
        return self.test_regex(r"[0-9]{5}[-][\d]{3}")

    @property
    def is_cnpj(self):
        return self.test_regex(r"[0-9]{2}[\.]?[0-9]{3}[\.]?[0-9]{3}[\/]?[0-9]{4}[-]?[0-9]{2}")

    @property
    def is_cpf(self):
        return self.test_regex(r"[0-9]{3}[\.]?[0-9]{3}[\.]?[0-9]{3}[-]?[0-9]{2}")

    @property
    def is_empty(self):
        return self.value is None or len(str(self.value).strip()) <= 0

    def in_float(self):
        self.value = 0 if self.is_empty else round(float(self.value), 2)

        return self

    @property
    def remove_blank(self):
        self.value = str(self.value).strip()

        self.value = None if self.is_empty else self.value

        return self

    @property
    def remove_character(self):
        self.value = str(self.value) \
            .replace('-', '') \
            .replace('.', '') \
            .replace('/', '') \
            .replace('\r', ' ') \
            .replace('\n', ' ')

        return self

    @property
    def in_zip_code(self):
        if not self.is_zip_code:
            self.value = self.remove_character.__format_zip_code(self.value)

        return self

    @property
    def in_cpf(self):
        if len(self.remove_character.value) == 11:
            self.value = self.remove_character.__format_cpf(self.value)

        return self

    @property
    def in_date(self):
        if len(self.remove_character.value) == 8:
            self.value = self.remove_character.__format_date(self.value)

        return self

    @property
    def in_local(self):
        self.value = f"{self.value[:2]}-{self.value[2:5]}-{self.value[5:7]}-{self.value[7:]}"

        return self

    @property
    def in_cnpj(self):
        if not self.is_empty:
            if self.is_cnpj:
                self.value = self.remove_character.__format_cnpj(self.value)
            else:
                return self.in_cpf

        return self

    def remove_character_in_left(self, character):
        self.value = self.value.lstrip(character)

        return self

    def remove_character_in_right(self, character):
        self.value = self.value.rstrip(character)

        return self

    @property
    def format_float(self):
        if not self.is_empty:
            if isinstance(self.value, str):
                self.value = str(self.value).replace(',', '.')
                self.value = round(float(self.value), ndigits=2)
            else:
                self.value = round(float(self.value), ndigits=2)

        return self

    @property
    def float_string(self):
        self.value = str(self.value).replace('.', ',')

        return self

    @property
    def convert_string_in_float(self):
        if self.is_empty:
            self.value = 1
        if isinstance(self.value, str):
            self.value = float(self.value.replace(',', '.'))
        else:
            self.value = float(self.value)

        return self

    @property
    def remove_ascii_character(self):
        return ''.join([i if ord(i) < 128 else ' ' for i in self.value])

    @property
    def in_integer(self):
        if isinstance(self.value, float):
            self.value = "{:g}".format(self.value)

        return self

    @property
    def ignore_values_duplicates(self):
        output = []
        seen = set()
        for value in self.value:
            if value not in seen:
                output.append(value)
                seen.add(value)

        return output
