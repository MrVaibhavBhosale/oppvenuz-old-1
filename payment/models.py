"""
This file is used for creating models under service app.
"""
from django.db import models
from django.utils import timezone
from users.models import CustomUser
from service.models import VendorService
from plan.models import (Plan,
                         VendorPlan
                         )


class Payment(models.Model):
    """
    Class for creating payment table models.
    """
    vendor_plan_id = models.ForeignKey(VendorPlan, null=False, blank=False, on_delete=models.DO_NOTHING)
    amount_received = models.FloatField(null=False, blank=False)
    transaction_id = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        """
        Function to return vendor.
        """
        return f"{self.transaction_id} - {self.created_at}"


class PaymentCancellation(models.Model):
    """
    Class for creating payment table models.
    """
    vendor_service_id = models.ForeignKey(VendorService, null=False, blank=False, on_delete=models.CASCADE)
    advance_for_booking = models.TextField(null=True, blank=False)
    payment_on_event_date = models.TextField(null=True, blank=False)
    payment_on_delivery = models.TextField(null=True, blank=False)
    cancellation_policy = models.TextField(null=True, blank=False)
    created_at = models.DateTimeField(default=timezone.now)

    # def __str__(self):
    #     """
    #     Function to return vendor_service.
    #     """
    #     return self.id


class PayuTemp(models.Model):
    amount = models.TextField(null=True, blank=False)
    paymentMode = models.TextField(null=True, blank=True)
