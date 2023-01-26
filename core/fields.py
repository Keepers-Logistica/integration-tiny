from django.db import models


class CustomCharField(models.CharField):

    def to_python(self, value):
        value = super(CustomCharField, self).to_python(value)

        if not value:
            return value

        if isinstance(self.max_length, int):
            return value[:self.max_length]

        return value
