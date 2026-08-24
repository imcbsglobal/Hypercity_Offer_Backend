from django.contrib import admin
from django.utils import timezone
from .models import Offer, OfferBranch


class OfferBranchInline(admin.TabularInline):
    model = OfferBranch
    extra = 1


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'start_date',
                    'end_date', 'is_active', 'view_count', 'created_at']
    list_filter = ['is_active', 'branches']
    search_fields = ['title', 'description']
    list_editable = ['is_active']
    inlines = [OfferBranchInline]
    date_hierarchy = 'start_date'

    @admin.display(description='Status')
    def status(self, obj):
        now = timezone.now()
        if obj.end_date < now:
            return 'Expired'
        if obj.is_active and obj.start_date <= now:
            return 'Active'
        if not obj.is_active and obj.start_date > now:
            return 'Scheduled'
        return 'Inactive'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'BRANCH_MGR' and request.user.managed_branch:
            return qs.filter(branches=request.user.managed_branch)
        return qs

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(OfferBranch)
class OfferBranchAdmin(admin.ModelAdmin):
    list_display = ['offer', 'branch', 'is_active']
    list_filter = ['is_active']
