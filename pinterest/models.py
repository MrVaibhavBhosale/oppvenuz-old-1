from django.db import models
from django.utils import timezone

# Create your models here.


class PinterestToken(models.Model):
    refresh_token = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now_add=timezone.now)


class PinterestAccessToken(models.Model):
    access_token = models.TextField()
    expiry_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now_add=timezone.now)

