from django.db.models import Manager


class OrderManager(Manager):
    def search_expedition(self):
        queryset = self.get_queryset()

        queryset = queryset.filter(
            label__in=['', None],
            search_label=True,
            running=False
        )

        return queryset

    def search_update_orders(self):
        queryset = self.get_queryset()

        queryset = queryset.filter(
            status=self.model.AWAITING_FILES,
            running=False
        )

        return queryset
