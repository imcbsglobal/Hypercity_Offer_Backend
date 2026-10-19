from django.core.management.base import BaseCommand

from apps.notifications.tasks import activate_scheduled_offers


class Command(BaseCommand):
    help = 'Activate scheduled offers whose start_date has passed and push them to FCM devices.'

    def handle(self, *args, **options):
        result = activate_scheduled_offers()
        self.stdout.write(self.style.SUCCESS(result))