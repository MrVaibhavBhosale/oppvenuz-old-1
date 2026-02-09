"""
This file is used for formatting (serializing) data interacting with the generated models.
"""
from rest_framework import serializers
from .models import (Enquiry,
                     CelebrityEnquiry, ContactDetailView
                     )


class ContactDetailViewSerializer(serializers.ModelSerializer):
    """
    Class for defining how contact detail view creation request and response object should look like.
    """
    class Meta:
        model = ContactDetailView
        fields = ['id', 'user', 'service', 'is_deleted', 'created_at', 'field']

    def to_representation(self, instance):
        resp = super().to_representation(instance)
        resp['user'] = {
            'fullname': instance.user.fullname,
            'email': instance.user.email,
            'contact_number': instance.user.contact_number,
        }
        resp['service'] = {
            'business_name': instance.service.business_name,
            'business_image': instance.service.business_image,
            'service_type': instance.service.service_id.service_type,
        }
        return resp
    

class CelebrityEnquirySerializer(serializers.ModelSerializer):
    """
    Class for defining how celebrity enquiry creation request and response object should look like.
    """
    category = serializers.StringRelatedField(source='celebrity_category', read_only=True)
    class Meta:
        model = CelebrityEnquiry
        fields = ['id', 'user_id', 'fullname', 'contact_number', 'celebrity_type', 'event_date', 'budget',
                  'celebrity_name', 'enquiry_status', 'location', 'email', 'message', 'created_at', 'celebrity_category', 'category', 'reason']


class UpdateCelebrityEnquiryStatusSerializer(serializers.ModelSerializer):
    """
    Class for defining how celebrity enquiry creation request and response object should look like.
    """
    class Meta:
        model = CelebrityEnquiry
        fields = ['id', 'enquiry_status', 'reason']


class UserEnquirySerializer(serializers.ModelSerializer):
    """
    Class for defining how user enquiry creation request and response object should look like.
    """
    business_name = serializers.CharField(source='vendor_service_id.business_name', read_only=True)
    business_image = serializers.CharField(source='vendor_service_id.business_image', read_only=True)
    area = serializers.CharField(source='vendor_service_id.area', read_only=True)
    city = serializers.CharField(source='vendor_service_id.city', read_only=True)
    state = serializers.CharField(source='vendor_service_id.state', read_only=True)
    pin_code = serializers.CharField(source='vendor_service_id.pin_code', read_only=True)

    class Meta:
        model = Enquiry
        fields = ['id', 'user_id', 'vendor_service_id', 'fullname', 'email', 'message', 'contact_number',
                  'enquiry_status', 'event_date', "business_name", "business_image", "area", "city", "state", "pin_code"]


class UpdateUserEnquirySerializer(serializers.ModelSerializer):
    """
    Class for defining how update user enquiry status request and response object should look like.
    """

    class Meta:
        model = Enquiry
        fields = ['id', 'enquiry_status']
