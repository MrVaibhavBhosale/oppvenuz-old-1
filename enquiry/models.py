"""
This file is used for creating models under users app.
"""
from django.db import models
from django.utils import timezone
from model_utils import Choices
from article.models import CelebrityCategory
from users.models import CustomUser
from service.models import VendorService


class Enquiry(models.Model):
    """
    Class for creating enquiry table models.
    """
    Status_Choice = Choices(
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('IGNORED', 'Ignored'),
    )

    enquiry_status = models.CharField(max_length=10, null=False, blank=False, choices=Status_Choice)
    user_id = models.ForeignKey(CustomUser, null=True, blank=False, on_delete=models.CASCADE, related_name="user_id")
    vendor_service_id = models.ForeignKey(VendorService, null=False, blank=False, on_delete=models.CASCADE)
    email = models.EmailField(null=False, blank=False)
    fullname = models.TextField(null=False, blank=False)
    contact_number = models.TextField(max_length=40, null=False, blank=False)
    message = models.TextField(null=True, blank=False)
    event_date = models.DateTimeField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now=timezone.now)
    updated_at = models.DateTimeField(auto_now=timezone.now)

    def __str__(self):
        """
        Function to return email.
        """
        return self.email


class CelebrityEnquiry(models.Model):
    """
    Class for creating enquiry table models.
    """
    Status_Choice = Choices(
        ('O', 'Open'),
        ('C', 'Closed'),
        ('D', 'Deleted'),
        ('P', 'Pending'),
        ('S', 'Suspended'),
    )

    Celebrity_Type_Choice = Choices(
        ("BOLLYWOOD", 'Bollywood'),
        ('TV_ACTOR', 'TV Actor'),
        ('TOLLYWOOD', 'Tollywood'),
        ('MARATHI_ACTORS', 'Marathi Actors'),
        ('INFLUENCERS', 'Influencers')
    )

    user_id = models.ForeignKey(CustomUser, null=True, blank=False, on_delete=models.CASCADE)
    fullname = models.TextField(null=False, blank=False)
    location = models.TextField(null=False, blank=False)
    contact_number = models.TextField(max_length=40, null=False, blank=False)
    celebrity_type = models.CharField(max_length=20, null=False, blank=False, choices=Celebrity_Type_Choice)
    celebrity_category = models.ForeignKey(CelebrityCategory, null=True, blank=True, on_delete=models.SET_NULL)
    event_date = models.DateTimeField(null=False, blank=False)
    budget = models.FloatField(null=False, blank=False)
    message = models.TextField(null=False, blank=False)
    email = models.EmailField(null=False, blank=False)
    celebrity_name = models.TextField(null=False, blank=False)
    enquiry_status = models.CharField(max_length=10, null=False, blank=False, choices=Status_Choice)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=timezone.now)
    reason = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        """
        Function to return fullname.
        """
        return self.fullname


class ContactDetailView(models.Model):
    """
    Class for creating contact detail view models.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    service = models.ForeignKey(VendorService, on_delete=models.CASCADE, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=timezone.now)
    field = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.user.fullname} viewed {self.service.business_name}'