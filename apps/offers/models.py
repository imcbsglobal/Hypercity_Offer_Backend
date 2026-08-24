from django.db import models
from apps.branches.models import Branch


class Offer(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='offers/', null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    terms_conditions = models.TextField(blank=True)
    branches = models.ManyToManyField(Branch, through='OfferBranch')
    is_active = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='offers_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class OfferBranch(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['offer', 'branch']

    def __str__(self):
        return f"{self.offer.title} @ {self.branch.name}"
