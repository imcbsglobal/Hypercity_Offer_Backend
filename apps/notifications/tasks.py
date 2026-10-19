from django.utils import timezone
from django.conf import settings
from .models import Notification, UserNotification
from .fcm import send_bulk_push
from apps.accounts.models import User
from apps.offers.models import Offer


def notification_image_url(notification):
    if not notification.image or not settings.PUBLIC_BASE_URL:
        return ''

    image_url = notification.image.url
    if image_url.startswith(('http://', 'https://')):
        return image_url
    return f"{settings.PUBLIC_BASE_URL}/{image_url.lstrip('/')}"


def send_notification_push(notification_id):
    try:
        notif = Notification.objects.get(id=notification_id, is_active=True)
    except Notification.DoesNotExist:
        return

    users = User.objects.exclude(fcm_token='').exclude(fcm_token__isnull=True)

    if notif.target_branches.exists():
        users = users.filter(preferred_branches__in=notif.target_branches.all()).distinct()

    tokens = list(users.values_list('fcm_token', flat=True))
    print(f"[Notifications] Notification #{notif.id}: {len(tokens)} eligible FCM token(s).")
    if not tokens:
        print('[Notifications] Push skipped because no eligible users have an FCM token.')
        return

    data = {}
    if notif.type == 'OFFER' and notif.linked_offer_id:
        data['offer_id'] = str(notif.linked_offer_id)
    image_url = notification_image_url(notif)
    if image_url:
        data['image_url'] = image_url

    send_bulk_push(tokens, notif.title, notif.body, data, image_url=image_url)

    for user in users:
        UserNotification.objects.get_or_create(user=user, notification=notif)


def activate_scheduled_offers():
    now = timezone.now()
    scheduled = Offer.objects.filter(
        is_active=False,
        start_date__lte=now,
        end_date__gte=now,
    )

    activated_count = 0
    for offer in scheduled:
        offer.is_active = True
        offer.save(update_fields=['is_active'])
        activated_count += 1

        branch_ids = list(offer.offerbranch_set.values_list('branch_id', flat=True))

        users = User.objects.exclude(fcm_token='').exclude(fcm_token__isnull=True)
        if branch_ids:
            users = users.filter(preferred_branches__in=branch_ids).distinct()

        tokens = list(users.values_list('fcm_token', flat=True))
        print(f"[Notifications] Offer #{offer.id}: {len(tokens)} eligible FCM token(s).")
        if not tokens:
            print('[Notifications] Offer push skipped because no eligible users have an FCM token.')
        notification = Notification.objects.create(
            title=offer.title,
            body=offer.description[:200] if offer.description else 'New offer available!',
            image=offer.image,
            type=Notification.Type.OFFER,
            linked_offer=offer,
            is_active=True,
            created_by=offer.created_by,
        )
        image_url = notification_image_url(notification)
        data = {'offer_id': str(offer.id)}
        if image_url:
            data['image_url'] = image_url
        if tokens:
            send_bulk_push(
                tokens,
                offer.title,
                offer.description[:100] if offer.description else 'New offer available!',
                data,
                image_url=image_url,
            )

        if branch_ids:
            notification.target_branches.set(branch_ids)
        for user in users:
            UserNotification.objects.get_or_create(user=user, notification=notification)

    return f"Activated {activated_count} scheduled offers"


def deactivate_expired_offers():
    now = timezone.now()
    expired = Offer.objects.filter(is_active=True, end_date__lte=now)
    count = expired.update(is_active=False)
    return f"Deactivated {count} expired offers"
