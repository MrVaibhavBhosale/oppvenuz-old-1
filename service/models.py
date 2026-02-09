"""
This file is used for creating models under service app.
"""

from enum import unique
import random
import logging
from django.db import models
from model_utils import Choices
from django.utils import timezone
from users.models import CustomUser
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.utils.text import slugify
logger = logging.getLogger(__name__)


class Service(models.Model):
    """
    Class for creating Service table model.
    """

    service_type = models.TextField(null=False, blank=False)
    slug = models.SlugField(max_length=255, null=True, blank=True)
    service_icons_app = models.URLField(null=True, blank=False)
    service_icons_web = models.URLField(null=True, blank=False)
    service_bg_images_app = models.URLField(null=True, blank=False)
    service_type_code = models.CharField(max_length=20, null=True, blank=False)
    service_image = models.URLField(null=True, blank=True)
    is_included = models.BooleanField(default=True)

    def __str__(self):
        """
        Function to return email.
        """
        return self.service_type

    def save(self, *args, **kwargs):
        self.slug = slugify(self.service_type)
        super().save(*args, **kwargs)


class VenueType(models.Model):
    title = models.CharField(max_length=255, db_index=True, unique=True)
    slug = models.SlugField(max_length=255, null=True, blank=True, db_index=True)
    image = models.URLField(null=True, blank=True)
    sequence_number = models.IntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.title}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class ServiceSuitableFor(models.Model):
    """
    This table will include what the service is best suitable for
    """

    title = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.title}"

    def save(self, *args, **kwargs):
        self.title = str(self.title).title()
        super().save(*args, **kwargs)


class VendorServiceManager(models.Manager):
    def get_similar_vendors(self, vendor, city=None):
        if city:
            similar_vendors = list(
                self.filter(
                    city=city, service_id=vendor.service_id, approval_status="A"
                ).exclude(id=vendor.id)
            )
        else:
            similar_vendors = list(
                self.filter(service_id=vendor.service_id, approval_status="A").exclude(
                    id=vendor.id
                )
            )
        random.shuffle(similar_vendors)
        return similar_vendors[:20]


class VendorService(models.Model):
    """
    Class for creating vendor services table models.
    """

    User_Group_Service_Choice = Choices(("MC", "Middle_Class"), ("HC", "High_Class"))

    Approval_Status_Choices = Choices(
        ("A", "Active"),
        ("P", "Pending"),
        ("R", "Rejected"),
        ("D", "Deleted"),
        ("S", "Suspended"),
    )

    Payment_Choices = Choices(("PAID", "PAID"), ("UNPAID", "UNPAID"))

    vendor_id = models.ForeignKey(
        CustomUser, null=False, blank=False, on_delete=models.CASCADE
    )
    service_id = models.ForeignKey(
        Service, null=False, blank=False, on_delete=models.CASCADE
    )
    business_name = models.TextField(null=True, blank=False)
    business_image = models.URLField(max_length=500, null=True, blank=False)
    working_since = models.TextField(null=True, blank=False)
    number_of_events_done = models.IntegerField(null=True, blank=False)
    user_group_service_type = models.CharField(
        max_length=2, choices=User_Group_Service_Choice
    )
    website_url = models.URLField(null=True, blank=False, max_length=500)
    facebook_url = models.URLField(null=True, blank=False, max_length=500)
    instagram_url = models.URLField(null=True, blank=False, max_length=500)
    additional_information = models.TextField(null=True, blank=False)
    area = models.TextField(null=True, blank=False)
    city = models.TextField(null=True, blank=False)
    state = models.TextField(null=True, blank=False)
    pin_code = models.TextField(null=True, blank=False)
    is_waved_off = models.BooleanField(default=False)
    is_under_review = models.BooleanField(default=False)
    payment_status = models.CharField(
        max_length=6, choices=Payment_Choices, default="UNPAID"
    )
    service_attachments = ArrayField(
        models.URLField(max_length=500, null=True, blank=False), null=True
    )
    approval_status = models.CharField(
        max_length=2, choices=Approval_Status_Choices, default="P"
    )
    share_url = models.URLField(null=True, blank=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    about_us = models.TextField(null=True, blank=True)
    venue_area = models.CharField(max_length=255, null=True, blank=False)
    venue_capacity = models.CharField(max_length=255, null=True, blank=False)
    is_venue_only = models.BooleanField(default=False)
    venue_type = models.ManyToManyField(VenueType, related_name="venues")
    is_veg_selected = models.BooleanField(default=False)
    fix_charges_for_veg = models.IntegerField(null=True, blank=True)
    discounted_price_per_plate_veg = models.IntegerField(null=True, blank=True)
    menu_for_plate_veg = models.TextField(null=True, blank=True)
    is_nonveg_selected = models.BooleanField(default=False)
    fix_charges_for_nonveg = models.IntegerField(null=True, blank=True)
    discounted_price_per_plate_nonveg = models.IntegerField(null=True, blank=True)
    menu_for_plate_nonveg = models.TextField(null=True, blank=True)
    is_decoration_available = models.BooleanField(default=False)
    is_outdoor_decoration_selected = models.BooleanField(default=False)
    outdoor_decoration_fix_charges = models.IntegerField(null=True, blank=True)
    outdoor_decor_image_urls = ArrayField(
        models.URLField(max_length=3000, null=True, blank=False), null=True
    )
    is_indoor_decoration_selected = models.BooleanField(default=False)
    indoor_decoration_fix_charges = models.IntegerField(null=True, blank=True)
    indoor_decor_image_urls = ArrayField(
        models.URLField(max_length=3000, null=True, blank=False), null=True
    )
    best_suitable_for = models.ManyToManyField(
        ServiceSuitableFor, related_name="best_suitable_for", null=True, blank=True
    )
    additional_facilities = ArrayField(
        models.TextField(null=True, blank=False), null=True
    )
    travel_to_venue = models.CharField(max_length=255, null=True, blank=True)
    fix_charges_for_travel_to_other_city = models.IntegerField(null=True, blank=True)
    fix_charges_for_travel_to_venue = models.IntegerField(null=True, blank=True)
    makeup_bridal_actual_price = models.IntegerField(null=True, blank=True)
    makeup_bridal_discounted_price = models.IntegerField(null=True, blank=True)
    makeup_family_guest_actual_price = models.IntegerField(null=True, blank=True)
    makeup_family_guest_discounted_price = models.IntegerField(null=True, blank=True)
    is_trial_makeup_provided = models.BooleanField(default=False)
    fix_charges_for_trial_makeup = models.IntegerField(null=True, blank=True)
    is_makeup_extensions_provided = models.BooleanField(default=False)
    fix_charges_for_makeup_extensions = models.IntegerField(null=True, blank=True)
    mehendi_bridal_actual_price_per_hand = models.IntegerField(null=True, blank=True)
    mehendi_bridal_discounted_price_per_hand = models.IntegerField(
        null=True, blank=True
    )
    mehendi_guest_actual_price_per_hand = models.IntegerField(null=True, blank=True)
    mehendi_guest_discounted_price_per_hand = models.IntegerField(null=True, blank=True)
    venue_actual_price_per_event = models.IntegerField(null=True, blank=True)
    venue_discounted_price_per_event = models.IntegerField(null=True, blank=True)
    delivery_charges = models.FloatField(null=True, blank=True)
    min_capacity = models.IntegerField(null=True, blank=True)
    max_capacity = models.IntegerField(null=True, blank=True)
    favorited_users = models.ManyToManyField(CustomUser, related_name="favorites")
    share_count = models.IntegerField(default=0)
    reject_reason = models.TextField(null=True, blank=True, max_length=1000)
    is_documents_verified = models.BooleanField(default=False)
    is_share_url_updated = models.BooleanField(default=False)
    sitting_capacity = models.IntegerField(null=True, blank=True)
    floating_capacity = models.IntegerField(null=True, blank=True)
    city_wise_prices = models.JSONField(null=True, blank=True)

    objects = VendorServiceManager()

    def __str__(self):
        """
        Function to return business_name.
        """
        return f"{self.business_name}"

    def increase_share_count(self):
        self.share_count += 1
        self.save()

    def set_reject_reason(self, reason: str):
        self.reject_reason = reason
        self.save()

    def has_required_documents(self):
        """
        Checks if the given vendor_service has the required verified documents:
        1. One verified document with document_type = 'PAN'.
        2. One verified document with document_type = 'ADHAR'.
        3. At least one verified document with document_type = 'GST' or 'MSME'.
        
        :param vendor_service: VendorService instance to check documents for.
        :return: True if all required documents are present, otherwise False.
        """
        pan_exists = self.vendordocument_set.filter(
            document_type='PAN',
            is_verified=True
        ).exists()

        adhar_exists = self.vendordocument_set.filter(
            document_type='AADHAAR',
            is_verified=True
        ).exists()

        gst_or_msme_exists = self.vendordocument_set.filter(
            is_verified=True,
            document_type__in=['GST', 'MSME']
        ).exists()

        self.is_documents_verified = pan_exists and adhar_exists and gst_or_msme_exists
        self.save()
        return self.is_documents_verified


class ServiceContactDetail(models.Model):
    """
    Class for creating vendor service contact table models.
    """

    vendor_service_id = models.ForeignKey(
        VendorService, null=False, blank=False, on_delete=models.CASCADE
    )
    contact_person = models.TextField(null=False, blank=False)
    contact_email = models.EmailField(null=False, blank=False)
    contact_number = models.TextField(null=False, blank=False)

    def __str__(self):
        """
        Function to return contact_person.
        """
        return self.contact_person


class VendorServiceViewLike(models.Model):
    """
    Class for creating vendor service views and likes table models.
    """

    vendor_service_id = models.ForeignKey(
        VendorService, null=False, blank=False, on_delete=models.CASCADE
    )
    user_id = models.ForeignKey(
        CustomUser, null=True, blank=False, on_delete=models.CASCADE
    )
    is_liked = models.BooleanField(default=False)
    is_viewed = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=False)
    liked_at = models.DateTimeField(null=True, blank=False)

    class Meta:
        unique_together = ("vendor_service_id", "user_id")

    def __str__(self):
        """
        Function to return vendor_service_id.
        """
        return self.vendor_service_id


class VendorPricing(models.Model):
    """
    Class for creating vendor service pricing table models.
    """
    HOTEL_STAR_CHOICES = Choices(
        ("1", "1 Star"),
        ("2", "2 Star"),
        ("3", "3 Star"),
        ("4", "4 Star"),
        ("5", "5 Star"),
        ("7", "7 Star"),
        ("0", "No Star"),
    )

    hotel_stars = models.CharField(max_length=255, choices=HOTEL_STAR_CHOICES, default="0")
    additional_rooms_available = models.BooleanField(default=False)
    available_rooms_qty = models.PositiveIntegerField(null=True, blank=True)
    per_room_rate = models.FloatField(null=True, blank=True)
    venue_type = models.CharField(max_length=200, null=True, blank=True)

    vendor_service_id = models.ForeignKey(
        VendorService, null=False, blank=False, on_delete=models.CASCADE
    )
    package_name = models.TextField(null=False, blank=False)
    package_details = models.TextField(null=True, blank=False)
    actual_price = models.FloatField(null=True, blank=False)
    discounted_price = models.FloatField(null=True, blank=False)
    events = ArrayField(
        models.CharField(max_length=255, null=True, blank=False), null=True
    )
    attachments = ArrayField(
        models.URLField(max_length=500, null=True, blank=False), null=True
    )
    include_serve_executives = models.BooleanField(default=False) 
    created_at = models.DateTimeField(default=timezone.now)
    update_at = models.DateTimeField(auto_now=True)


class VendorServiceOffer(models.Model):
    """
    Class for creating vendor service offer models.
    """

    vendor_service_id = models.OneToOneField(
        VendorService,
        primary_key=True,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    image_url = models.URLField(null=True, blank=False, max_length=500)
    start_date = models.DateField(null=True, blank=False)
    end_date = models.DateField(null=True, blank=False)
    percentage = models.CharField(null=True, blank=True, max_length=20)


class Cart(models.Model):
    """
    Class for creating  model for user cart.
    """

    user_id = models.ForeignKey(
        CustomUser, null=False, blank=False, on_delete=models.CASCADE
    )
    vendor_service_id = models.ForeignKey(
        VendorService, null=False, blank=False, on_delete=models.CASCADE
    )
    service_type = models.ForeignKey(
        Service,
        related_name="cart_services",
        on_delete=models.CASCADE,
        null=True,
        blank=False,
    )
    guest_quantity = models.BigIntegerField(null=False, blank=False)
    actual_price = models.FloatField(null=False, blank=False)
    discounted_price = models.FloatField(null=True, blank=False)
    text_to_represent = models.TextField(null=True, blank=False)
    package_id = models.ForeignKey(
        VendorPricing, null=True, blank=False, on_delete=models.DO_NOTHING
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_manual_package = models.BooleanField(default=False)
    is_pre_defined_package = models.BooleanField(default=False)
    venue_no_of_days = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
    venue_is_rental_only = models.BooleanField(default=False)
    venue_is_non_veg = models.BooleanField(default=False)
    veue_is_veg = models.BooleanField(default=False)
    is_with_decoration = models.BooleanField(default=False)
    is_bridal_selected = models.BooleanField(default=False)
    is_family_guest_selected = models.BooleanField(default=False)
    is_makeup_extensions = models.BooleanField(default=False)
    is_trial_makeup = models.BooleanField(default=False)
    is_travel = models.BooleanField(default=False)
    is_other_city = models.BooleanField(default=False)
    total_cart_value = models.DecimalField(decimal_places=2, max_digits=100, default=0)
    cart_details = models.JSONField(null=True, blank=False)


class ServiceSubTypeDetail(models.Model):
    """
    Additional Service Details
    """

    title = models.CharField(max_length=255, null=True, blank=True)
    service_subtype = models.CharField(max_length=255, null=True, blank=True)
    service = models.ForeignKey(
        VendorService,
        related_name="subtypes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    actual_price = models.FloatField(null=True, blank=True)
    discounted_price = models.FloatField(null=True, blank=True)
    min_order_qty = models.IntegerField(null=True, blank=True)
    max_order_qty = models.IntegerField(null=True, blank=True)
    images = ArrayField(
        models.URLField(max_length=500, null=True, blank=False), null=True
    )
    selected_services = ArrayField(
        models.CharField(max_length=255, null=True, blank=False), null=True
    )
    cake_available_in_shapes_and_sizes = models.BooleanField(default=False)
    purchase_type = models.CharField(max_length=255, null=True, blank=True)
    actual_price_per_hour = models.FloatField(null=True, blank=True)
    discounted_price_per_hour = models.FloatField(null=True, blank=True)
    min_duration = models.IntegerField(null=True, blank=True)
    pandit_pooja_samagree_included = models.BooleanField(default=False)
    sitting_capacity = models.IntegerField(null=True, blank=True)
    floating_capacity = models.IntegerField(null=True, blank=True)
    outfit_name = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=255, null=True, blank=True)
    card_type = models.CharField(max_length=255, null=True, blank=True)
    package_details = models.TextField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    local_price = models.FloatField(null=True, blank=True)
    city_price = models.FloatField(null=True, blank=True)
    delivery_charge = models.FloatField(null=True, blank=True)


    def __str__(self) -> str:
        return f"{self.title}"


class ServiceEvent(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(max_length=255, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.title}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class CatererServiceMenu(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(max_length=255, null=True, blank=True)
    service = models.ForeignKey(
        VendorService,
        related_name="cater_menu",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    min_capacity = models.IntegerField(null=True, blank=True)
    max_capacity = models.IntegerField(null=True, blank=True)
    is_veg_selected = models.BooleanField(default=False)
    veg_actual_price = models.FloatField(null=True, blank=True)
    veg_discounted_price = models.FloatField(null=True, blank=True)
    veg_menu = models.TextField(null=True, blank=True)
    is_non_veg_selected = models.BooleanField(default=False)
    non_veg_actual_price = models.FloatField(null=True, blank=True)
    non_veg_discounted_price = models.FloatField(null=True, blank=True)
    non_veg_menu = models.TextField(null=True, blank=True)
    images = ArrayField(
        models.URLField(max_length=500, null=True, blank=False), null=True
    )
    menu_name = models.CharField(max_length=255, null=True, blank=True)
    include_serve_executives = models.BooleanField(default=False)


    def __str__(self) -> str:
        return f"{self.title}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class Category(models.Model):
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    service_name = models.CharField(max_length=100)

    def _str_(self):
        return self.service_name


class ServiceRegistrationChargesDetail(models.Model):
    service_id = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='service_charges')
    registration_charges = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    created_by = models.CharField(max_length=100)
    updated_by = models.CharField(max_length=100)
    created_when = models.DateTimeField(auto_now_add=True)
    updated_when = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.service_id.service_type} Charges"
    
class ServiceVendorRegistrationCharges(models.Model):
    service_id = models.ForeignKey(Service, on_delete=models.CASCADE)
    vendor_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    registration_charges = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)
    STATUS_CHOICES = [
        (0,'Pending'),
        (1,'Success'),
        (2,'Failed'),
        (3,'Refunded')
    ]
    payment_status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    registration_remark = models.CharField(max_length=255, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=False, null=False)
    transaction_date = models.DateTimeField(auto_now=True)
    transaction_remark = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.EmailField(blank=False, null=False)
    created_when = models.DateTimeField(auto_now_add=True)
    updated_by = models.EmailField(null=False, blank=False)
    updated_when = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Vendor {self.vendor_id} - {self.service_id}- {self.payment_status}"
    