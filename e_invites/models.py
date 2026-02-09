from django.contrib.postgres.fields import ArrayField
from django.db import models
from users.models import CustomUser
from django.utils.text import slugify
from uuid import uuid4



class InviteTemplate(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_invites")
    template_url = models.URLField(null=True, blank=False)
    template_data = models.JSONField(null=True, blank=False)

    def __str__(self):
        return f"{self.user} - {self.pk}"


class Template(models.Model):
    uuid = models.CharField(max_length=255, unique=True, primary_key=True, default=uuid4)
    uid = models.CharField(max_length=255, unique=True, null=True)
    title = models.CharField(max_length=255)
    thumbnail = models.URLField(null=True, blank=True)
    width = models.SmallIntegerField(null=True, blank=True)
    height = models.SmallIntegerField(null=True, blank=True)
    tags = ArrayField(models.CharField(max_length=255, null=True, blank=False), null=True)
    custom_data = models.JSONField(null=True, blank=True)
    collections = ArrayField(models.CharField(max_length=255, null=True, blank=False), null=True)
    layers = models.JSONField(null=True, blank=True)
    slug = models.SlugField(max_length=255, null=True, blank=True)
    tag_slugs = ArrayField(models.SlugField(max_length=255, null=True, blank=False), null=True)
    is_active = models.BooleanField(default=False)

    def __str__(self) -> str:        
        return f'{self.title}'
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        self.tag_slugs = [slugify(tag) for tag in self.tags]
        super().save(*args, **kwargs)

class SavedTemplate(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='saved_templates')
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name='template_users', null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'template')
