from django.contrib import admin
from django.utils.html import format_html
from .models import ServiceCategory, Service

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    """Giao diện quản trị cho Loại dịch vụ."""
    list_display = ('name', 'description', 'image')
    search_fields = ('name',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Giao diện quản trị cho Dịch vụ."""
    list_display = ('name', 'category', 'price', 'description')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')