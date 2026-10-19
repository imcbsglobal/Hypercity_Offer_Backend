from django.test import TestCase

from .serializers import BranchDetailSerializer


class BranchPhoneValidationTests(TestCase):
    def test_rejects_incomplete_phone_number(self):
        serializer = BranchDetailSerializer(data={
            'name': 'Central Branch',
            'address': 'Main Road',
            'phone': '1',
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('phone', serializer.errors)

    def test_accepts_ten_digit_phone_number(self):
        serializer = BranchDetailSerializer(data={
            'name': 'Central Branch',
            'address': 'Main Road',
            'phone': '9876543210',
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
