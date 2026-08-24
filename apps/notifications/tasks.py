from celery import shared_task
from django.utils import timezone
from .models import Notification, UserNotification
from .fcm import send_bulk_push
from apps.accounts.models import User
from apps.offers.models import Offer


@shared_task
def send_notification_push(notification_id):
    try:
        notif = Notification.objects.get(id=notification_id, is_active=True)
    except Notification.DoesNotExist:
        return

    users = User.objects.exclude(fcm_token='').exclude(fcm_token__isnull=True)

    if notif.target_branches.exists():
        users = users.filter(preferred_branches__in=notif.target_branches.all()).distinct()

    tokens = list(users.values_list('fcm_token', flat=True))
    data = {}
    if notif.type == 'OFFER' and notif.linked_offer_id:
        data['offer_id'] = str(notif.linked_offer_id)

    send_bulk_push(tokens, notif.title, notif.body, data)

    for user in users:
        UserNotification.objects.get_or_create(user=user, notification=notif)


@shared_task
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
        send_bulk_push(
            tokens,
            offer.title,
            offer.description[:100] if offer.description else 'New offer available!',
            {'offer_id': str(offer.id)},
        )

        notification = Notification.objects.create(
            title=offer.title,
            body=offer.description[:200] if offer.description else 'New offer available!',
            image=offer.image,
            type=Notification.Type.OFFER,
            linked_offer=offer,
            is_active=True,
            created_by=offer.created_by,
        )
        if branch_ids:
            notification.target_branches.set(branch_ids)
        for user in users:
            UserNotification.objects.get_or_create(user=user, notification=notification)

    return f"Activated {activated_count} scheduled offers"


@shared_task
def deactivate_expired_offers():
    now = timezone.now()
    expired = Offer.objects.filter(is_active=True, end_date__lte=now)
    count = expired.update(is_active=False)
    return f"Deactivated {count} expired offers"
