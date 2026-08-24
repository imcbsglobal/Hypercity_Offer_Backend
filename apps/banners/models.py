from django.db import models
from apps.branches.models import Branch
from apps.offers.models import Offer


class Banner(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='banners/', null=True, blank=True)
    link_url = models.URLField(blank=True)
    linked_offer = models.ForeignKey(
        Offer, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='banners'
    )
    branches = models.ManyToManyField(Branch, blank=True, related_name='banners')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title
