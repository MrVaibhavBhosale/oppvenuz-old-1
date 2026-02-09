"""
This file is used for creating models under users app.
"""
from django.db import models
from django.utils import timezone
from model_utils import Choices
from users.models import CustomUser
from django.utils.text import slugify
from users.models import City
from service.models import Service
import uuid
from django.db.models import Q, CheckConstraint, F
from django.contrib.auth import get_user_model
CustomUser = get_user_model()


class Article(models.Model):
    """
    Class for creating article table models.
    """
    Status_Choice = Choices(
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('DELETED', 'DELETED')
    )

    title = models.TextField(null=False, blank=False, unique=True,
                             error_messages={'unique': 'Article with this title already exists.'})
    slug = models.SlugField(null=True, blank=True, db_index=True, max_length=255)
    content = models.TextField(null=False, blank=False)
    user_id = models.ForeignKey(CustomUser, null=True, blank=False, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, null=False, blank=False, choices=Status_Choice)
    image_header = models.URLField(null=True, blank=False)
    cities = models.ManyToManyField(City, related_name='articles')
    service_types = models.ManyToManyField(Service, related_name='articles')
    created_at = models.DateTimeField(auto_now=timezone.now)
    updated_at = models.DateTimeField(auto_now=timezone.now)

    def __str__(self):
        """
        Function to return title.
        """
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class ArticleLike(models.Model):
    """
    Class for creating vendor service views and likes table models.
    """
    article_id = models.ForeignKey(Article, null=False, blank=False, on_delete=models.CASCADE)
    user_id = models.ForeignKey(CustomUser, null=True, blank=False, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('article_id', 'user_id')

    def __str__(self):
        """
        Function to return article_like_id.
        """
        return f"{self.user_id} liked {self.article_id}"


class Blog(models.Model):
    STATUS_CHOICES = Choices(
        ('PENDING', 'Pending'),
        ('PUBLISHED', 'Published'),
        ('INACTIVE', 'Inactive'),
        ('DELETED', 'Deleted')
    )

    topic = models.CharField(max_length=255)
    published_date = models.DateTimeField(null=True, blank=True)
    category = models.CharField(max_length=100)
    blog_description = models.TextField()
    image_url = models.URLField(null=True, blank=True)
    slug = models.SlugField(null=True, blank=True, db_index=True, max_length=255)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return self.topic


class Banner(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    slug = models.SlugField(max_length=255, null=True, blank=True, db_index=True)
    description = models.TextField(null=True, blank=True)
    image = models.URLField()
    is_featured = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.title}'

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Testimonial(models.Model):
    STATUS_CHOICES = (
        (1, 'Pending'),
        (2, 'Approved'),
        (3, 'Deleted'),
    )

    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True, null=True)
    media = models.JSONField(null=True, blank=True)
    status_type = models.IntegerField(choices=STATUS_CHOICES, default=1)
    comment = models.CharField(max_length=255, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    approved_by = models.EmailField(null=True, blank=True)
    created_by = models.EmailField(null=False, blank=False)

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(status_type__in=[1, 2, 3]),
                name='valid_status_type'
            )
        ]

    def __str__(self):
        return f'{self.first_name or ""} {self.last_name or ""}'.strip()


class CelebrityCategory(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.title}'

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Celebrity(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    profession = models.CharField(max_length=255)
    image = models.URLField(null=True, blank=True)
    category = models.ForeignKey(CelebrityCategory, null=True, blank=True, related_name="celebs", on_delete=models.CASCADE, db_index=True)
    x_link = models.URLField(null=True, blank=True)
    fb_link = models.URLField(null=True, blank=True)
    insta_link = models.URLField(null=True, blank=True)
    yt_link = models.URLField(null=True, blank=True)
    thread = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=timezone.now)
    updated_at = models.DateTimeField(auto_now=timezone.now)

    def __str__(self) -> str:
        return f'{self.name}'

    def get_category(self):
        if self.category:
            return str(self.category)
        else:
            return None
