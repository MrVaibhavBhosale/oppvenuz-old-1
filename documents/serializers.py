'''
Document serializers
'''
from rest_framework import serializers
from .models import VendorDocument
from utilities import messages
from .utils import mask_document_number


class DocumentListingDetailSerializer(serializers.ModelSerializer):
    '''
    Vendor Document Serializer
    '''
    class Meta:
        model = VendorDocument
        fields = ['id', 'document_type', 'document_url', 'document_id', 'is_verified']

    def to_representation(self, instance):
        response =  super().to_representation(instance)
        response['document_id'] = mask_document_number(instance.document_id) if instance.document_id else None
        return response


class VendorDocumentUpdateSerializer(serializers.ModelSerializer):
    '''
    Vendor Document Serializer for updating vendor
    '''
    class Meta:
        model = VendorDocument
        fields = ['document_url',]

    def validate(self, attrs):
        document_url = attrs.get('document_url')
        if not document_url:
            raise serializers.ValidationError({'message': messages.DOC_REQUIRED})
        return attrs


class VendorDocumentSerializer(serializers.ModelSerializer):
    '''
    Vendor Document Serializer
    '''
    class Meta:
        model = VendorDocument
        fields = ['id', 'reference_id', 'vendor_service', 'user', 'document_type', 'document_base64', 'document_url', 'document_id', 'is_verified', 'created_at']
    
    def to_representation(self, instance):
        response =  super().to_representation(instance)
        response['document_id'] = mask_document_number(instance.document_id) if instance.document_id else None
        return response


class AadhaarRequestOtpSerializer(serializers.ModelSerializer):
    '''
    Vendor Document Serializer for otp requests
    '''
    class Meta:
        model = VendorDocument
        fields = ['vendor_service', 'document_type', 'document_base64', 'document_id']

    def validate(self, attrs):
        document_base64 = attrs.get('document_base64')
        document_id = attrs.get('document_id')
        if not document_base64 and not document_id:
            raise serializers.ValidationError({'message': messages.DOC_REQUIRED})
        return attrs


class AdharVerifyOtpSerializer(serializers.ModelSerializer):
    '''
    Adhar otp verification serializer
    '''
    otp = serializers.IntegerField(required=True)
    transaction_id = serializers.CharField(required=True)
    
    class Meta:
        model = VendorDocument
        fields = ['transaction_id', 'reference_id', 'otp']