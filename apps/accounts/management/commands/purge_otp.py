from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import OTP, SMSSendLog


class Command(BaseCommand):
    help = 'Delete expired/used OTP rows and trim old SMS send logs.'

    def add_arguments(self, parser):
        parser.add_argument('--log-days', type=int, default=30, help='Keep SMS logs for this many days.')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options['log_days'])

        otp_qs = OTP.objects.filter(is_used=True) | OTP.objects.filter(expires_at__lt=timezone.now())
        log_qs = SMSSendLog.objects.filter(created_at__lt=cutoff)

        otp_count = otp_qs.count()
        log_count = log_qs.count()

        if options['dry_run']:
            self.stdout.write(f'Would delete {otp_count} OTP rows and {log_count} SMS log rows.')
            return

        otp_qs.delete()
        log_qs.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {otp_count} OTP rows and {log_count} SMS log rows.'))
