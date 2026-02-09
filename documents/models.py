'''
Document model
'''
from django.db import models
from service.models import VendorService
from users.models import CustomUser
from django.utils import timezone


class VendorDocument(models.Model):
    """
    Class for creating document table models.
    """
    reference_id = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    vendor_service = models.ForeignKey(
        VendorService,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True
    )
    document_type = models.CharField(max_length=100, null=True, blank=True)
    document_base64 = models.TextField(null=True, blank=True)
    document_url = models.URLField(null=True, blank=True)
    document_id = models.CharField(max_length=255, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=timezone.now)

    def __str__(self) -> str:
        return f'{self.document_type}: {self.reference_id}'
    
