import os

from django.conf import settings
from firebase_admin import credentials, initialize_app, messaging
from firebase_admin.exceptions import FirebaseError

MULTICAST_CHUNK_SIZE = 500

_app_initialized = False


def _ensure_app():
    global _app_initialized
    if _app_initialized:
        return True

    if not settings.FIREBASE_CREDENTIALS_PATH:
        return False

    if not os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
        print(f"[FCM] Credentials file not found: {settings.FIREBASE_CREDENTIALS_PATH}")
        return False

    try:
        initialize_app(credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH))
    except ValueError:
        pass
    except FirebaseError as exc:
        print(f"[FCM] Failed to initialize Firebase app: {exc}")
        return False

    _app_initialized = True
    return True


def send_fcm_push(token, title, body, data=None, image_url=None):
    if not token:
        return False

    if not _ensure_app():
        if not settings.FIREBASE_CREDENTIALS_PATH:
            print(f"[FCM] Would push to {token}: {title} - {body}")
            return True
        return False

    message_kwargs = {
        'notification': messaging.Notification(title=title, body=body, image=image_url or None),
        'data': data or {},
        'token': token,
    }
    if image_url:
        message_kwargs['android'] = messaging.AndroidConfig(
            notification=messaging.AndroidNotification(image=image_url)
        )
        message_kwargs['apns'] = messaging.APNSConfig(
            fcm_options=messaging.APNSFCMOptions(image=image_url)
        )
    message = messaging.Message(**message_kwargs)

    try:
        response = messaging.send(message)
    except FirebaseError as exc:
        print(f"[FCM] Failed to push to {token}: {exc}")
        return False

    print(f"[FCM] Push sent successfully. Message ID: {response}")
    return bool(response)


def send_bulk_push(tokens, title, body, data=None, image_url=None):
    if not tokens:
        return

    if not _ensure_app():
        if not settings.FIREBASE_CREDENTIALS_PATH:
            for token in tokens:
                print(f"[FCM] Would push to {token}: {title} - {body}")
        return

    unique_tokens = list(dict.fromkeys(t for t in tokens if t))

    for start in range(0, len(unique_tokens), MULTICAST_CHUNK_SIZE):
        chunk = unique_tokens[start:start + MULTICAST_CHUNK_SIZE]
        message_kwargs = {
            'notification': messaging.Notification(title=title, body=body, image=image_url or None),
            'data': data or {},
            'tokens': chunk,
        }
        if image_url:
            message_kwargs['android'] = messaging.AndroidConfig(
                notification=messaging.AndroidNotification(image=image_url)
            )
            message_kwargs['apns'] = messaging.APNSConfig(
                fcm_options=messaging.APNSFCMOptions(image=image_url)
            )
        message = messaging.MulticastMessage(**message_kwargs)

        try:
            response = messaging.send_each_for_multicast(message)
        except FirebaseError as exc:
            print(f"[FCM] Multicast push failed for {len(chunk)} tokens: {exc}")
            continue

        print(
            f"[FCM] Multicast response: {response.success_count} succeeded, "
            f"{response.failure_count} failed out of {len(chunk)} tokens."
        )
        for item in response.responses:
            if not item.success:
                print(f"[FCM] Device push failed: {item.exception}")
