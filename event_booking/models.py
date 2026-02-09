"""
This file is used for creating models under event_booking app.
"""
from django.db import models
from django.utils import timezone
from service.models import Service
from users.models import CustomUser
from django.contrib.postgres.fields import ArrayField


class VendorEventBooking(models.Model):
    """
    Class for creating vendor event booking table models.
    """
    vendor_id = models.ForeignKey(CustomUser, null=False, blank=False, on_delete=models.CASCADE)
    service_type = models.ForeignKey(Service, related_name='event_bookings', on_delete=models.CASCADE, null=True, blank=False)
    booking_title = models.TextField(null=False, blank=False)
    event_date = models.DateField(null=False, blank=False)
    start_time = models.TimeField(null=True, blank=False)
    end_time = models.TimeField(null=True, blank=False)
    is_all_day = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=False)
    customer_name = models.TextField(null=False, blank=False)
    customer_email = models.EmailField(null=True, blank=False)
    customer_contact = models.TextField(null=True, blank=False)
    tags = ArrayField(models.TextField(null=True, blank=False), null=True)
    is_deleted = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        """
        Function to return booking_title.
        """
        return self.booking_title
