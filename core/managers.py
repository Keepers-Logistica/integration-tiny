from django.db.models import Manager


class OrderManager(Manager):
    def search_expedition(self):
        queryset = self.get_queryset()

        queryset = queryset.filter(
            label__in=['', None],
            status=self.model.IMPORTED,
            search_label=True,
            running=False
        ).exclude(status=self.model.CANCELLED)

        return queryset

    def search_update_orders(self):
        queryset = self.get_queryset()

        queryset = queryset.filter(
            xml__in=['', None],
            status=self.model.AWAITING_FILES,
            running=False
        ).exclude(status=self.model.CANCELLED)

        return queryset
