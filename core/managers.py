from django.db.models import Manager


class OrderManager(Manager):
    def search_expedition(self):
        queryset = self.get_queryset()

        queryset = queryset.filter(
            label__in=['', None],
            status=self.model.IMPORTED,
            search_label=True,
            running=False,
            configuration__is_active=True
        ).exclude(
            status=self.model.CANCELLED,
        ).exclude(
            processed=True
        )

        return queryset

    def search_update_orders(self):
        queryset = self.get_queryset()

        queryset = queryset.filter(
            xml__in=['', None],
            status=self.model.AWAITING_FILES,
            running=False,
            configuration__is_active=True
        ).exclude(
            status=self.model.CANCELLED
        ).exclude(
            processed=True
        )

        return queryset

    def pending_send_labels(self):
        queryset = self.get_queryset()

        queryset = queryset.filter(
            search_label=True,
            sent_label=False,
            configuration__is_active=True
        ).exclude(
            processed=True
        ).exclude(
            status=self.model.CANCELLED
        ).exclude(
            label__in=['', None]
        )

        return queryset
