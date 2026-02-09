from django.db import models

# Create your models here.
class DownlaodAppMobileNumbers(models.Model):
    phone_number = models.CharField(max_length=20)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number} - {self.timestamp}"


class Faq(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    priority = models.IntegerField(default=0)
    inserted_by = models.CharField(max_length=100)
    inserted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question


class ContactDetail(models.Model):
    phone_numbers = models.JSONField()
    emails = models.JSONField()
    address = models.TextField()

    def __str__(self):
        return f"ContactDetail {self.id}"