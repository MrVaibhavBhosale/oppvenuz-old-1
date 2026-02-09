"""
Feedback models
"""

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from service.models import Service, VendorService
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache

User = get_user_model()


class Review(models.Model):
    """
    Model for vendor rervice review
    """

    user = models.ForeignKey(
        User, related_name="reviews", on_delete=models.CASCADE, null=True, blank=False
    )
    vendor_service = models.ForeignKey(
        VendorService,
        related_name="reviews",
        on_delete=models.CASCADE,
        null=True,
        blank=False,
    )
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=timezone.now)
    updated_at = models.DateTimeField(auto_now=timezone.now)
    amount_spend = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    photos = ArrayField(
        models.URLField(max_length=500, null=True, blank=False), null=True
    )

    class Meta:
        unique_together = (('user', 'vendor_service'))

    def __str__(self) -> str:
        return f"Review for {self.vendor_service} by {self.user}"


class TrackUserAction(models.Model):
    user = models.ForeignKey(
        User,
        related_name='track_user_action',
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.SET_NULL
    )
    vendor = models.ForeignKey(
        VendorService,
        related_name='track_user_action',
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.SET_NULL
    )
    ACTIONS = (
        ('added_to_cart', 'Added to Cart'),
        ('send_enquiry', 'Send Enquiry'),
        ('view_contact', 'View Contact'),
        ('added_to_favorite', 'Added to Favorite'),
        ('liked', 'Liked')
    )
    action = models.CharField(choices=ACTIONS, max_length=20, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)


class TrackUserSession(models.Model):
    user = models.ForeignKey(
        User,
        related_name='track_user_session',
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.SET_NULL
    )
    ACTIONS = (
        ('login', 'Login'),
        ('logout', 'Logout'),
    )
    action = models.CharField(choices=ACTIONS, max_length=10, db_index=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    time = models.DateTimeField(auto_now_add=True)

class TrackingAction(models.IntegerChoices):
    VIEWED = 1, 'Viewed'
    FAVORITE = 2, 'Favorite'
    LIKED = 3, 'Liked'
    CART = 4, 'Added to Cart'
    PURCHASED = 5, 'Purchased'


class ServiceTracker(models.Model):
    user = models.ForeignKey(User, related_name='history', null=True, blank=True, db_index=True, on_delete=models.SET_NULL)
    vendor = models.ForeignKey(VendorService, related_name='history', null=True, blank=True, db_index=True, on_delete=models.SET_NULL)
    service = models.ForeignKey(Service, related_name='history', null=True, blank=True, db_index=True, on_delete=models.SET_NULL)
    city = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    ip_address = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    action = models.IntegerField(choices=TrackingAction.choices, null=True, blank=True, db_index=True)
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=timezone.now)

    def __str__(self) -> str:
        return f'{self.user} {self.action} {self.vendor} from {self.city}'


@receiver(post_save, sender=ServiceTracker)
def clear_cache_on_save(sender, instance, **kwargs):
    cache_key = 'total_points_data'
    cache.delete(cache_key)