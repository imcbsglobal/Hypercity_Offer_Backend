from django.contrib import admin
from .models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'order', 'start_date', 'end_date', 'created_at']
    list_filter = ['is_active', 'branches']
    search_fields = ['title']
    list_editable = ['is_active', 'order']
    filter_horizontal = ['branches']
