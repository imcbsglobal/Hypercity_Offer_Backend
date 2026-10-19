from django.contrib import admin

from .models import CustomForm, CustomFormField, CustomFormResponse


class CustomFormFieldInline(admin.TabularInline):
    model = CustomFormField
    extra = 0


@admin.register(CustomForm)
class CustomFormAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'created_by', 'created_at', 'published_at']
    list_filter = ['status']
    search_fields = ['title', 'description']
    readonly_fields = ['public_id', 'created_at', 'updated_at', 'published_at']
    inlines = [CustomFormFieldInline]


@admin.register(CustomFormResponse)
class CustomFormResponseAdmin(admin.ModelAdmin):
    list_display = ['id', 'form', 'submitted_at']
    list_filter = ['form']
    readonly_fields = ['form', 'answers', 'schema_snapshot', 'submitted_at']
