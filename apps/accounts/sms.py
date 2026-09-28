import hashlib
import time

import requests
from django.conf import settings

SMS_SERVICE = 'sms'
ACCOUNT_SERVICE = 'account'
URL_SHORTNER_SERVICE = 'url-shortner'

SEND_SMS_REQUEST_FOR = 'send-sms'
SEND_SMS_ARRAY_REQUEST_FOR = 'send-sms-array'
SEND_DYNAMIC_SMS_REQUEST_FOR = 'send-dynamic-sms'
GET_WALLET_BALANCE_REQUEST_FOR = 'get-wallet-balance'
GET_WALLET_TRANSACTIONS_REQUEST_FOR = 'get-wallet-transactions'
GET_DELIVERY_REPORT_REQUEST_FOR = 'get-delivery-report'

# Body field names expected by the panel. Renamed here if the account uses aliases.
FIELD_SOURCE = 'sourceAddr'
FIELD_DESTINATION = 'destinationAddr'
FIELD_MESSAGE = 'message'

DEFAULT_OTP_TEMPLATE = 'Your Hypercity OTP is {otp}. Valid for {minutes} minutes.'

SUBMISSION_ID_KEYS = ('submissionId', 'submission_id', 'id', 'messageId', 'msgId')


def build_signature(request_for, expire, service=SMS_SERVICE):
    """MD5 chain: requestFor + service@rits-v1.0 + expire, then token, then token key."""
    time_key = hashlib.md5(
        f'{request_for}{service}@rits-v1.0{expire}'.encode()
    ).hexdigest()
    time_access_token_key = hashlib.md5(
        f'{settings.SMS_ACCESS_TOKEN}{time_key}'.encode()
    ).hexdigest()
    return hashlib.md5(
        f'{time_access_token_key}{settings.SMS_ACCESS_TOKEN_KEY}'.encode()
    ).hexdigest()


def build_auth_fields(request_for, service=SMS_SERVICE):
    expire = int(time.time()) + settings.SMS_SIGNATURE_TTL
    return {
        'accessToken': settings.SMS_ACCESS_TOKEN,
        'expire': expire,
        'authSignature': build_signature(request_for, expire, service),
    }


def is_configured():
    return bool(settings.SMS_ACCESS_TOKEN and settings.SMS_ACCESS_TOKEN_KEY)


def is_enabled():
    return bool(settings.SMS_ENABLED and is_configured())


def build_otp_message(otp):
    template = settings.SMS_OTP_TEMPLATE or DEFAULT_OTP_TEMPLATE
    return template.format(otp=otp, minutes=settings.SMS_OTP_EXPIRY_MINUTES)


def _result(ok, status_code, message, submission_id='', body=None):
    return {
        'ok': ok,
        'status_code': status_code,
        'message': message,
        'submission_id': submission_id,
        'body': body,
    }


def _extract(body, keys):
    if not isinstance(body, dict):
        return ''
    for key in keys:
        value = body.get(key)
        if value not in (None, ''):
            return str(value)
    return ''


def _log_send(phone, message, result):
    from .models import SMSSendLog

    SMSSendLog.objects.create(
        phone=phone,
        body=message,
        success=result['ok'],
        status_code=result['status_code'] or None,
        provider_message=result['message'][:500],
        submission_id=result['submission_id'][:100],
    )


def _send_sms_payload(phone, message, request_for):
    payload = {
        FIELD_SOURCE: settings.SMS_SENDER_ID,
        FIELD_DESTINATION: phone,
        FIELD_MESSAGE: message,
    }
    if settings.SMS_DLT_TEMPLATE_ID:
        payload['dltTemplateId'] = settings.SMS_DLT_TEMPLATE_ID
    payload.update(build_auth_fields(request_for))
    return payload


def send_sms(phone, message, request_for=SEND_SMS_REQUEST_FOR, log=True):
    if not is_enabled():
        print(f'[SMS] Disabled. Would send to {phone}: {message}')
        result = _result(False, 0, 'SMS provider is not configured')
        if log:
            _log_send(phone, message, result)
        return result

    try:
        response = requests.post(
            f'{settings.SMS_API_BASE_URL}/{request_for}',
            data=_send_sms_payload(phone, message, request_for),
            timeout=settings.SMS_REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        result = _result(False, 0, f'Provider request failed: {exc}')
        if log:
            _log_send(phone, message, result)
        return result

    try:
        body = response.json()
    except ValueError:
        body = None

    result = _result(
        ok=response.status_code == 200,
        status_code=response.status_code,
        message=_extract(body, ('message', 'status')) or response.text[:500],
        submission_id=_extract(body, SUBMISSION_ID_KEYS),
        body=body,
    )
    if log:
        _log_send(phone, message, result)
    return result


def get_wallet_balance():
    if not is_enabled():
        return _result(False, 0, 'SMS provider is not configured')

    try:
        response = requests.get(
            f'{settings.SMS_API_ACCOUNT_URL}/{GET_WALLET_BALANCE_REQUEST_FOR}',
            params=build_auth_fields(GET_WALLET_BALANCE_REQUEST_FOR, ACCOUNT_SERVICE),
            timeout=settings.SMS_REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        return _result(False, 0, f'Provider request failed: {exc}')

    try:
        body = response.json()
    except ValueError:
        body = None

    return _result(
        ok=response.status_code == 200,
        status_code=response.status_code,
        message=_extract(body, ('message', 'status')) or response.text[:500],
        body=body,
    )
