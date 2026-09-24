from django.contrib import admin

from .models import AccMaster, Misel, AccInvMast


@admin.register(AccMaster)
class AccMasterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'place', 'client_id', 'synced_at']
    search_fields = ['code', 'name']
    readonly_fields = [f.name for f in AccMaster._meta.fields]


@admin.register(Misel)
class MiselAdmin(admin.ModelAdmin):
    list_display = ['firm_name', 'address1', 'client_id', 'synced_at']
    search_fields = ['firm_name']
    readonly_fields = [f.name for f in Misel._meta.fields]


@admin.register(AccInvMast)
class AccInvMastAdmin(admin.ModelAdmin):
    list_display = ['slno', 'invdate', 'customerid', 'nettotal', 'client_id']
    search_fields = ['customerid']
    readonly_fields = [f.name for f in AccInvMast._meta.fields]