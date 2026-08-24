from django.db import models
from apps.branches.models import Branch
from apps.offers.models import Offer
from apps.accounts.models import User


class Notification(models.Model):
    class Type(models.TextChoices):
        COMMON = 'COMMON', 'Common'
        OFFER = 'OFFER', 'Offer'
        PROMO = 'PROMO', 'Promo'

    title = models.CharField(max_length=200)
    body = models.TextField()
    image = models.ImageField(upload_to='notifications/', null=True, blank=True)
    type = models.CharField(max_length=10, choices=Type.choices, default=Type.COMMON)
    linked_offer = models.ForeignKey(
        Offer, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='notifications'
    )
    target_branches = models.ManyToManyField(Branch, blank=True, related_name='notifications')
    is_active = models.BooleanField(default=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='notifications_created'
    )

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return self.title


class UserNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-notification__sent_at']
        unique_together = ['user', 'notification']

    def __str__(self):
        return f"{self.user.phone} - {self.notification.title}"
