"""
This file is used for creating models under plan app.
"""
from django.db import models
from model_utils import Choices
from django.utils import timezone
from service.models import Service
from users.models import CustomUser
from django.contrib.postgres.fields import ArrayField
from service.models import VendorService


class Plan(models.Model):
    """
    Class for creating plan table models.
    """
    Range_Choice = Choices(
        ('MR', 'Middle_Range_Pricing_Plan'),
        ('HR', 'High_Range_Pricing_Plan')
    )

    Subscription_type_Choices = Choices(
        ('SILVER', 'Silver'),
        ('GOLD', 'Gold'),
        ('PLATINUM', 'Platinum')
    )

    Validity_Choices = Choices(
        ('6 Month', '6 Month'),
        ('1 Year', '1 Year'),
        ('Free', 'Free'),
    )

    service_id = models.ForeignKey(Service, null=False, blank=False, on_delete=models.CASCADE)
    range_type = models.CharField(max_length=2, choices=Range_Choice)
    subscription_type = models.CharField(max_length=8, choices=Subscription_type_Choices)
    price = models.FloatField(null=False, blank=False, default=0.0)
    validity_type = models.CharField(max_length=10, choices=Validity_Choices)

    def __str__(self):
        """
        Function to return service_id.
        """
        return f"{self.service_id}"


class SubscriptionPlan(models.Model):
    """
    Class for creating subscription plan table models.
    """
    Subscription_type_Choices = Choices(
        ('SILVER', 'Silver'),
        ('GOLD', 'Gold'),
        ('PLATINUM', 'Platinum')
    )
    subscription_type = models.CharField(max_length=8, choices=Subscription_type_Choices)
    features = ArrayField(models.TextField(max_length=500, null=True, blank=False))

    def __str__(self):
        """
        Function to return service_id.
        """
        return self.subscription_type


class VendorPlan(models.Model):

    """
    Class for creating vendor plan table models.
    """
    Plan_Status_Choices = Choices(
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive')
    )
    Subscription_type_Choices = Choices(
        ('SILVER', 'Silver'),
        ('GOLD', 'Gold'),
        ('PLATINUM', 'Platinum')
    )

    vendor_service_id = models.ForeignKey(VendorService, null=False, blank=False, on_delete=models.CASCADE)
    plan_id = models.ForeignKey(Plan, null=True, blank=False, on_delete=models.CASCADE)
    subscription_id = models.CharField(max_length=50, null=True, blank=False)
    plan_status = models.CharField(max_length=8, choices=Plan_Status_Choices, default="INACTIVE")
    starts_from = models.DateTimeField(null=False)
    ends_on = models.DateTimeField(null=True)
    created_on = models.DateTimeField(auto_now_add=timezone.now)
    updated_on = models.DateTimeField(auto_now=timezone.now)
    subscription_response = models.JSONField(null=True, blank=False)
    subscription_type = models.CharField(max_length=8, choices=Subscription_type_Choices, null=True, blank=False)
    duration_in_months = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        """
        Function to return vendor_id.

        """
        return f"{self.pk} - {self.vendor_service_id.id} - {self.starts_from} - {self.ends_on}"
