from unittest.mock import patch

from django.db import DatabaseError
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import User


class MyPointsViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone='+91 81291 91379', name='Points User')
        self.client.force_authenticate(self.user)
        self.now = timezone.now()

    @staticmethod
    def set_rows(mock_model, rows):
        mock_model.objects.exclude.return_value.exclude.return_value.values_list.return_value = rows

    @patch('apps.synctool.my_points.AccMaster')
    def test_returns_one_entry_per_matching_account(self, mock_model):
        self.set_rows(mock_model, [
            ('13744', 'AFHAM IMC', '8129191379', '1,250.500', 'client-a', self.now),
            ('13745', 'ANZIL', '+91 81291 91379', '80', 'client-b', self.now),
        ])

        response = self.client.get('/api/synctool/my-points/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['customerid'], '13744')
        self.assertEqual(response.data['customer_name'], 'AFHAM IMC')
        self.assertEqual(len(response.data['accounts']), 2)
        self.assertEqual(response.data['accounts'][1]['customerid'], '13745')
        self.assertEqual(response.data['accounts'][0]['points'], 1250.5)
        self.assertEqual(response.data['accounts'][0]['points_raw'], '1,250.500')
        self.assertEqual(response.data['accounts'][1]['points'], 80)

    @patch('apps.synctool.my_points.AccMaster')
    def test_null_blank_and_invalid_points_are_not_treated_as_zero(self, mock_model):
        self.set_rows(mock_model, [
            ('1', 'Null', '8129191379', None, 'client-a', self.now),
            ('2', 'Blank', '8129191379', '', 'client-a', self.now),
            ('3', 'Invalid', '8129191379', 'N/A', 'client-a', self.now),
        ])

        response = self.client.get('/api/synctool/my-points/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['points'] for item in response.data['accounts']], [None, None, None])
        self.assertEqual(response.data['accounts'][0]['points_raw'], None)
        self.assertEqual(response.data['accounts'][2]['points_raw'], 'N/A')

    @patch('apps.synctool.my_points.AccMaster')
    def test_no_matching_account_returns_404(self, mock_model):
        self.set_rows(mock_model, [
            ('1', 'Other', '9999999999', '10', 'client-a', self.now),
        ])

        response = self.client.get('/api/synctool/my-points/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data['detail'],
            'No customer account found with this number. Please contact admin.',
        )

    @patch('apps.synctool.my_points.AccMaster')
    def test_database_error_returns_503(self, mock_model):
        mock_model.objects.exclude.return_value.exclude.return_value.values_list.side_effect = (
            DatabaseError('sync down')
        )

        response = self.client.get('/api/synctool/my-points/')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['detail'], 'Account sync data unavailable.')

    @patch('apps.synctool.my_points.AccMaster')
    def test_short_phone_returns_404(self, mock_model):
        self.user.phone = '12345'
        self.user.save(update_fields=['phone'])

        response = self.client.get('/api/synctool/my-points/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        mock_model.objects.exclude.assert_not_called()

    def test_unauthenticated_request_is_rejected(self):
        response = APIClient().get('/api/synctool/my-points/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
