from django.db import models


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('BULK_DELETE', 'Bulk Deleted'),
        ('BULK_UPDATE', 'Bulk Updated'),
        ('LOGIN', 'Logged In'),
    ]

    user_id = models.IntegerField()
    user_name = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=50)
    entity_id = models.IntegerField(null=True, blank=True)
    entity_name = models.CharField(max_length=200, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['entity_type', '-created_at']),
            models.Index(fields=['user_id', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user_name} {self.get_action_display()} {self.entity_type} #{self.entity_id}"
