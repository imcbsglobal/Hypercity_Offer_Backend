from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.accounts.models import User
from apps.branches.models import Branch
from apps.notifications.models import Notification, UserNotification
from apps.notifications.tasks import (
    activate_scheduled_offers,
    deactivate_expired_offers,
    send_notification_push,
)
from apps.offers.models import Offer


class NotificationPushTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name='Main', address='Addr', phone='9999999999')
        self.user = User.objects.create_user(phone='9000000001', name='Push User', fcm_token='token-1')

    @patch('apps.notifications.tasks.send_bulk_push')
    def test_sends_to_all_users_with_tokens(self, mock_push):
        notif = Notification.objects.create(title='Hello', body='World')

        send_notification_push(notif.id)

        mock_push.assert_called_once()
        tokens, title, body, data = mock_push.call_args[0]
        self.assertEqual(list(tokens), ['token-1'])
        self.assertEqual(title, 'Hello')
        self.assertEqual(body, 'World')
        self.assertEqual(data, {})

    @patch('apps.notifications.tasks.send_bulk_push')
    def test_excludes_users_without_tokens(self, mock_push):
        User.objects.create_user(phone='9000000002', name='No Token', fcm_token='')
        User.objects.create_user(phone='9000000003', name='Null Token')
        notif = Notification.objects.create(title='Hi', body='There')

        send_notification_push(notif.id)

        tokens = mock_push.call_args[0][0]
        self.assertEqual(list(tokens), ['token-1'])

    @patch('apps.notifications.tasks.send_bulk_push')
    def test_filters_by_target_branches(self, mock_push):
        other = Branch.objects.create(name='Other', address='Addr2', phone='8888888888')
        outsider = User.objects.create_user(phone='9000000004', name='Outsider', fcm_token='token-2')
        outsider.preferred_branches.add(other)

        notif = Notification.objects.create(title='Scoped', body='Body')
        notif.target_branches.add(self.branch)
        self.user.preferred_branches.add(self.branch)

        send_notification_push(notif.id)

        tokens = list(mock_push.call_args[0][0])
        self.assertIn('token-1', tokens)
        self.assertNotIn('token-2', tokens)

    @patch('apps.notifications.tasks.send_bulk_push')
    def test_offer_notification_includes_offer_id(self, mock_push):
        offer = Offer.objects.create(
            title='Buy 2',
            description='Cheap',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1),
        )
        notif = Notification.objects.create(
            title='Buy 2', body='Cheap', type=Notification.Type.OFFER, linked_offer=offer,
        )

        send_notification_push(notif.id)

        self.assertEqual(mock_push.call_args[0][3], {'offer_id': str(offer.id)})

    @patch('apps.notifications.tasks.send_bulk_push')
    @override_settings(PUBLIC_BASE_URL='https://api.hypercity.example')
    def test_notification_image_is_included_in_push_payload(self, mock_push):
        image = SimpleUploadedFile('sale.jpg', b'image-bytes', content_type='image/jpeg')
        notif = Notification.objects.create(title='Sale', body='Details', image=image)

        send_notification_push(notif.id)

        data = mock_push.call_args.args[3]
        image_url = mock_push.call_args.kwargs['image_url']
        self.assertTrue(image_url.startswith('https://api.hypercity.example/media/notifications/'))
        self.assertEqual(data['image_url'], image_url)

    @patch('apps.notifications.tasks.send_bulk_push')
    def test_creates_user_notification_rows(self, mock_push):
        notif = Notification.objects.create(title='Hi', body='There')

        send_notification_push(notif.id)

        self.assertTrue(UserNotification.objects.filter(user=self.user, notification=notif).exists())

    @patch('apps.notifications.tasks.send_bulk_push')
    def test_is_idempotent_for_user_notifications(self, mock_push):
        notif = Notification.objects.create(title='Hi', body='There')

        send_notification_push(notif.id)
        send_notification_push(notif.id)

        self.assertEqual(UserNotification.objects.filter(notification=notif).count(), 1)

    @patch('apps.notifications.tasks.send_bulk_push')
    def test_inactive_notification_is_skipped(self, mock_push):
        notif = Notification.objects.create(title='Hi', body='There', is_active=False)

        send_notification_push(notif.id)

        mock_push.assert_not_called()


class OfferScheduleTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.user = User.objects.create_user(phone='9000000005', name='Sched', fcm_token='token-3')

    def test_deactivate_expired_marks_past_offers_inactive(self):
        offer = Offer.objects.create(
            title='Old', start_date=self.now - timedelta(days=10),
            end_date=self.now - timedelta(days=1), is_active=True,
        )

        result = deactivate_expired_offires_fix = deactivate_expired_offers()

        offer.refresh_from_db()
        self.assertFalse(offer.is_active)
        self.assertIn('1', result)

    def test_deactivate_leaves_current_offers_active(self):
        offer = Offer.objects.create(
            title='Live', start_date=self.now - timedelta(days=1),
            end_date=self.now + timedelta(days=1), is_active=True,
        )

        deactivate_expired_offers()

        offer.refresh_from_db()
        self.assertTrue(offer.is_active)

    @patch('apps.notifications.tasks.send_bulk_push')
    def test_activate_scheduled_pushes_and_creates_notification(self, mock_push):
        branch = Branch.objects.create(name='B1', address='A', phone='9111111111')
        offer = Offer.objects.create(
            title='Fresh', description='New deal', start_date=self.now - timedelta(hours=1),
            end_date=self.now + timedelta(days=1), is_active=False,
        )
        offer.branches.add(branch)
        self.user.preferred_branches.add(branch)

        result = activate_scheduled_offers()

        offer.refresh_from_db()
        self.assertTrue(offer.is_active)
        self.assertIn('1', result)
        mock_push.assert_called_once()
        self.assertEqual(mock_push.call_args[0][0], ['token-3'])
        self.assertEqual(mock_push.call_args[0][3], {'offer_id': str(offer.id)})

        notif = Notification.objects.filter(linked_offer=offer).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.type, Notification.Type.OFFER)
        self.assertTrue(UserNotification.objects.filter(user=self.user, notification=notif).exists())

    @patch('apps.notifications.tasks.send_bulk_push')
    def test_activate_skips_already_active_offers(self, mock_push):
        Offer.objects.create(
            title='Live', start_date=self.now - timedelta(hours=1),
            end_date=self.now + timedelta(days=1), is_active=True,
        )

        activate_scheduled_offers()

        mock_push.assert_not_called()
