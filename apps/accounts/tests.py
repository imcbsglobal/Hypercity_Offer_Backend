import hashlib
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import OTP, SMSSendLog, User
from apps.accounts.sms import build_signature
from apps.accounts.views import generate_otp

PHONE = '9876543210'
KNOWN_CUSTOMER_PATH = 'apps.accounts.views.is_known_customer'


def known_customer(phone):
    return True


class KnownCustomerMixin:
    """Patches is_known_customer for the whole test, including setUp."""

    def setUp(self):
        patcher = patch(KNOWN_CUSTOMER_PATH, known_customer)
        patcher.start()
        self.addCleanup(patcher.stop)
        super().setUp()


def make_otp(phone=PHONE, code='123456', minutes_left=5):
    entry = OTP.objects.create(
        phone=phone,
        otp='',
        expires_at=timezone.now() + timedelta(minutes=minutes_left),
    )
    entry.set_code(code)
    entry.save(update_fields=['otp'])
    return entry


def ok_result(submission_id=''):
    return {'ok': True, 'status_code': 200, 'message': 'sent',
            'submission_id': submission_id, 'body': None}


@override_settings(SMS_ENABLED=False, DEBUG=True)
class SMSSignatureTests(TestCase):
    def test_signature_matches_documented_md5_chain(self):
        with override_settings(SMS_ACCESS_TOKEN='TOKEN', SMS_ACCESS_TOKEN_KEY='TOKENKEY'):
            expire = 1724837000
            time_key = hashlib.md5(f'send-smssms@rits-v1.0{expire}'.encode()).hexdigest()
            token_key = hashlib.md5(f'TOKEN{time_key}'.encode()).hexdigest()
            expected = hashlib.md5(f'{token_key}TOKENKEY'.encode()).hexdigest()

            self.assertEqual(build_signature('send-sms', expire), expected)
            self.assertEqual(len(expected), 32)

    def test_signature_uses_account_service_tag(self):
        with override_settings(SMS_ACCESS_TOKEN='TOKEN', SMS_ACCESS_TOKEN_KEY='TOKENKEY'):
            expire = 1724837000
            self.assertNotEqual(
                build_signature('get-wallet-balance', expire, 'account'),
                build_signature('get-wallet-balance', expire, 'sms'),
            )


class GenerateOTPTests(TestCase):
    def test_generates_six_digits(self):
        for _ in range(200):
            code = generate_otp()
            self.assertEqual(len(code), 6)
            self.assertTrue(code.isdigit())


@override_settings(
    SMS_ENABLED=False,
    DEBUG=True,
    SMS_RESEND_COOLDOWN=60,
    SMS_OTP_EXPIRY_MINUTES=5,
    SMS_MAX_ATTEMPTS=3,
)
class SendOTPViewTests(KnownCustomerMixin, TestCase):
    url = reverse('send-otp')

    def setUp(self):
        super().setUp()
        self.response = self.client.post(self.url, {'phone': PHONE}, format='json')
        self.assertEqual(self.response.status_code, 200)
        self.entry = OTP.objects.get(phone=PHONE)

    def test_creates_pending_otp_with_expiry(self):
        self.assertFalse(self.entry.is_used)
        self.assertEqual(self.entry.attempts, 0)
        self.assertTrue(self.entry.expires_at > timezone.now())

    def test_code_is_hashed_in_database(self):
        self.assertTrue(self.entry.otp.startswith('pbkdf2_'))
        self.assertNotEqual(self.entry.otp, self.response.data['otp'])

    def test_otp_exposed_in_response_only_when_sms_disabled(self):
        self.assertIn('otp', self.response.data)

        with override_settings(SMS_ENABLED=True, SMS_ACCESS_TOKEN='t', SMS_ACCESS_TOKEN_KEY='k'):
            with patch('apps.accounts.views.send_sms', return_value=ok_result()):
                res = self.client.post(self.url, {'phone': '9000000001'}, format='json')

        self.assertEqual(res.status_code, 200)
        self.assertNotIn('otp', res.data)

    def test_sms_log_records_disabled_send(self):
        log = SMSSendLog.objects.get(phone=PHONE)
        self.assertIn('OTP', log.body)
        self.assertFalse(log.success)

    def test_resend_within_cooldown_is_rejected(self):
        res = self.client.post(self.url, {'phone': PHONE}, format='json')
        self.assertEqual(res.status_code, 429)
        self.assertIn('wait', res.data['error'])

    def test_resend_allowed_after_cooldown(self):
        OTP.objects.filter(phone=PHONE).update(
            created_at=timezone.now() - timedelta(seconds=120)
        )
        res = self.client.post(self.url, {'phone': PHONE}, format='json')
        self.assertEqual(res.status_code, 200)

    def test_unknown_phone_rejected(self):
        with patch(KNOWN_CUSTOMER_PATH, return_value=False):
            res = self.client.post(self.url, {'phone': '9000000002'}, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertFalse(OTP.objects.filter(phone='9000000002').exists())

    def test_invalid_phone_rejected_by_serializer(self):
        res = self.client.post(self.url, {'phone': '123'}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_submission_id_persisted_on_entry(self):
        OTP.objects.all().delete()
        with override_settings(SMS_ENABLED=True, SMS_ACCESS_TOKEN='t', SMS_ACCESS_TOKEN_KEY='k'):
            with patch('apps.accounts.views.send_sms', return_value=ok_result('sub-123')):
                self.client.post(self.url, {'phone': '9000000003'}, format='json')
        self.assertEqual(OTP.objects.get(phone='9000000003').sms_submission_id, 'sub-123')

    def test_provider_failure_returns_502_and_removes_otp(self):
        OTP.objects.all().delete()
        failure = {'ok': False, 'status_code': 402, 'message': 'Insufficient balance',
                   'submission_id': '', 'body': None}
        with override_settings(SMS_ENABLED=True, SMS_ACCESS_TOKEN='t', SMS_ACCESS_TOKEN_KEY='k'):
            with patch('apps.accounts.views.send_sms', return_value=failure):
                res = self.client.post(self.url, {'phone': PHONE}, format='json')

        self.assertEqual(res.status_code, 502)
        self.assertFalse(OTP.objects.filter(phone=PHONE).exists())


@override_settings(SMS_ENABLED=False, DEBUG=True, SMS_MAX_ATTEMPTS=3, SMS_OTP_EXPIRY_MINUTES=5)
class VerifyOTPViewTests(KnownCustomerMixin, TestCase):
    url = reverse('verify-otp')

    def setUp(self):
        super().setUp()
        self.entry = make_otp()

    def test_valid_code_returns_tokens(self):
        res = self.client.post(self.url, {'phone': PHONE, 'otp': '123456'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('access', res.data)
        self.entry.refresh_from_db()
        self.assertTrue(self.entry.is_used)

    def test_known_customer_gets_auto_created(self):
        res = self.client.post(self.url, {'phone': PHONE, 'otp': '123456'}, format='json')
        self.assertEqual(res.status_code, 200)
        user = User.objects.get(phone=PHONE)
        self.assertTrue(user.is_customer)
        self.assertEqual(user.role, 'CUSTOMER')

    def test_code_cannot_be_replayed(self):
        self.client.post(self.url, {'phone': PHONE, 'otp': '123456'}, format='json')
        res = self.client.post(self.url, {'phone': PHONE, 'otp': '123456'}, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['error'], 'Invalid OTP')

    def test_wrong_code_rejected(self):
        res = self.client.post(self.url, {'phone': PHONE, 'otp': '000000'}, format='json')
        self.assertEqual(res.status_code, 400)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.attempts, 1)

    def test_lockout_after_max_attempts(self):
        for _ in range(settings.SMS_MAX_ATTEMPTS):
            res = self.client.post(self.url, {'phone': PHONE, 'otp': '000000'}, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('Too many', res.data['error'])
        self.assertFalse(OTP.objects.filter(phone=PHONE).exists())

    def test_correct_code_blocked_after_lockout(self):
        for _ in range(settings.SMS_MAX_ATTEMPTS):
            self.client.post(self.url, {'phone': PHONE, 'otp': '000000'}, format='json')
        res = self.client.post(self.url, {'phone': PHONE, 'otp': '123456'}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_expired_code_rejected(self):
        make_otp(code='654321', minutes_left=-1)
        res = self.client.post(self.url, {'phone': PHONE, 'otp': '654321'}, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('expired', res.data['error'].lower())

    def test_short_code_rejected_by_serializer(self):
        res = self.client.post(self.url, {'phone': PHONE, 'otp': '1234'}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_otp_for_other_phone_rejected(self):
        res = self.client.post(self.url, {'phone': '9000000009', 'otp': '123456'}, format='json')
        self.assertEqual(res.status_code, 400)


@override_settings(SMS_ENABLED=False, DEBUG=True, SMS_MAX_ATTEMPTS=3)
class SignupViewTests(TestCase):
    url = reverse('signup')

    def setUp(self):
        make_otp()

    def test_signup_creates_customer_with_real_name(self):
        res = self.client.post(
            self.url, {'phone': PHONE, 'otp': '123456', 'name': 'Asha'}, format='json'
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(User.objects.get(phone=PHONE).name, 'Asha')

    def test_existing_user_rejected(self):
        User.objects.create_user(phone=PHONE, name='Existing')
        res = self.client.post(
            self.url, {'phone': PHONE, 'otp': '123456', 'name': 'Asha'}, format='json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn('already exists', res.data['error'])

    def test_invalid_code_rejected(self):
        res = self.client.post(
            self.url, {'phone': PHONE, 'otp': '000000', 'name': 'Asha'}, format='json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertFalse(User.objects.filter(phone=PHONE).exists())

    def test_blank_name_rejected(self):
        res = self.client.post(
            self.url, {'phone': PHONE, 'otp': '123456', 'name': '   '}, format='json'
        )
        self.assertEqual(res.status_code, 400)


@override_settings(SMS_ENABLED=False, SMS_ACCESS_TOKEN='', SMS_ACCESS_TOKEN_KEY='')
class SendSmsClientTests(TestCase):
    def test_disabled_client_does_not_call_provider(self):
        from apps.accounts.sms import send_sms

        with patch('apps.accounts.sms.requests.post') as post:
            result = send_sms(PHONE, 'hello')

        post.assert_not_called()
        self.assertFalse(result['ok'])
        self.assertEqual(result['status_code'], 0)
        self.assertEqual(SMSSendLog.objects.count(), 1)

    def test_build_otp_message_uses_template(self):
        from apps.accounts.sms import build_otp_message

        with override_settings(SMS_OTP_TEMPLATE='Code {otp} in {minutes}m', SMS_OTP_EXPIRY_MINUTES=4):
            self.assertEqual(build_otp_message('123456'), 'Code 123456 in 4m')

    def test_build_otp_message_falls_back_to_default(self):
        from apps.accounts.sms import build_otp_message

        with override_settings(SMS_OTP_TEMPLATE='', SMS_OTP_EXPIRY_MINUTES=5):
            self.assertEqual(build_otp_message('123456'),
                             'Your Hypercity OTP is 123456. Valid for 5 minutes.')


@override_settings(SMS_ENABLED=True, SMS_ACCESS_TOKEN='TOKEN', SMS_ACCESS_TOKEN_KEY='TOKENKEY',
                   SMS_SENDER_ID='HYPER')
class SendSmsEnabledTests(TestCase):
    @staticmethod
    def _response(status_code, payload):
        return type('R', (), {'status_code': status_code, 'text': 'raw',
                              'json': lambda self: payload})()

    def test_successful_send_passes_auth_fields(self):
        from apps.accounts.sms import send_sms

        response = self._response(200, {'submissionId': 'abc123', 'message': 'sent'})
        with patch('apps.accounts.sms.requests.post', return_value=response) as post:
            result = send_sms(PHONE, 'hello')

        self.assertTrue(result['ok'])
        self.assertEqual(result['submission_id'], 'abc123')

        body = post.call_args.kwargs['data']
        self.assertEqual(body['accessToken'], 'TOKEN')
        self.assertEqual(body['sourceAddr'], 'HYPER')
        self.assertEqual(body['destinationAddr'], PHONE)
        self.assertEqual(len(body['authSignature']), 32)
        self.assertGreater(body['expire'], 0)
        self.assertTrue(post.call_args.args[0].endswith('/send-sms'))
        self.assertEqual(SMSSendLog.objects.first().submission_id, 'abc123')

    def test_provider_error_is_reported(self):
        from apps.accounts.sms import send_sms

        response = self._response(402, {'message': 'Insufficient balance'})
        with patch('apps.accounts.sms.requests.post', return_value=response):
            result = send_sms(PHONE, 'hello')

        self.assertFalse(result['ok'])
        self.assertEqual(result['status_code'], 402)
        self.assertEqual(SMSSendLog.objects.first().status_code, 402)

    def test_request_exception_is_captured(self):
        import requests as requests_lib
        from apps.accounts.sms import send_sms

        with patch('apps.accounts.sms.requests.post', side_effect=requests_lib.Timeout('boom')):
            result = send_sms(PHONE, 'hello')

        self.assertFalse(result['ok'])
        self.assertIn('failed', result['message'])


class PurgeOTPCommandTests(TestCase):
    def test_purges_used_and_expired_rows(self):
        from django.core.management import call_command

        used = make_otp(code='111111', minutes_left=60)
        OTP.objects.filter(pk=used.pk).update(is_used=True)
        expired = make_otp(phone='9000000001', code='222222', minutes_left=-10)
        fresh = make_otp(phone='9000000002', code='333333', minutes_left=60)

        call_command('purge_otp')

        self.assertFalse(OTP.objects.filter(pk=used.pk).exists())
        self.assertFalse(OTP.objects.filter(pk=expired.pk).exists())
        self.assertTrue(OTP.objects.filter(pk=fresh.pk).exists())
