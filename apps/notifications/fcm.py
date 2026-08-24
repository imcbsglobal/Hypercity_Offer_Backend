from django.conf import settings
from firebase_admin import initialize_app, credentials, messaging
import os


def send_fcm_push(token, title, body, data=None):
    if not token:
        return False

    if not settings.FIREBASE_CREDENTIALS_PATH:
        print(f"[FCM] Would push to {token}: {title} - {body}")
        return True

    if not os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
        print(f"[FCM] Credentials file not found: {settings.FIREBASE_CREDENTIALS_PATH}")
        return False

    try:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        initialize_app(cred)
    except ValueError:
        pass  # Already initialized

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        token=token,
    )
    response = messaging.send(message)
    return bool(response)


def send_bulk_push(tokens, title, body, data=None):
    if not tokens:
        return

    for token in tokens:
        send_fcm_push(token, title, body, data)
