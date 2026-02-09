from django.contrib import admin

from .models import Review, ServiceTracker

admin.site.register(Review)

@admin.register(ServiceTracker)
class ServiceTrackerAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'vendor', 'service', 'city','ip_address','action','created_at',
        'points',
    ]