from django.core.management.base import BaseCommand

from apps.notifications.tasks import deactivate_expired_offers


class Command(BaseCommand):
    help = 'Deactivate offers whose end_date has passed.'

    def handle(self, *args, **options):
        result = deactivate_expired_offers()
        self.stdout.write(self.style.SUCCESS(result))