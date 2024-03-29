from django.contrib.admin import SimpleListFilter

from core.models import Order


class OrderHasLabelFilter(SimpleListFilter):
    title = 'Tem etiqueta ?'  # a label for our filter
    parameter_name = 'has_label'  # you can put anything here

    def lookups(self, request, model_admin):
        # This is where you create filter options; we have two:
        return (
            (1, 'Sim'),
            (-1, 'Não'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        queryset = queryset.select_related(
            'configuration'
        )
        if value and int(value) > 0:
            return queryset.filter(
                configuration__search_labels=True
            ).exclude(
                label__in=[None, '']
            )
        if value and int(value) < 0:
            return queryset.filter(
                configuration__search_labels=True,
                label__in=[None, '']
            ).exclude(
                status=Order.CANCELLED
            ).exclude(processed=True)

        return queryset
