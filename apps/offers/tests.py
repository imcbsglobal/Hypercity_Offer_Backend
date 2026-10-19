from django.test import TestCase
from datetime import timedelta
from django.utils import timezone

from .models import Offer
from .serializers import OfferCreateSerializer


class OfferDateValidationTests(TestCase):
    def test_update_requires_both_dates(self):
        now = timezone.now()
        offer = Offer(title='Weekend sale', start_date=now, end_date=now + timedelta(days=1))
        serializer = OfferCreateSerializer(instance=offer, data={'title': 'Updated sale'}, partial=True)

        self.assertFalse(serializer.is_valid())
        self.assertIn('start_date', serializer.errors)
        self.assertIn('end_date', serializer.errors)
