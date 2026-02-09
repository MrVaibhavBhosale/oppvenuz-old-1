from rest_framework import serializers
from .models import DownlaodAppMobileNumbers, Faq, ContactDetail

class SmsRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownlaodAppMobileNumbers
        fields = ['id', 'phone_number', 'message', 'timestamp']

class AllFieldsSmsRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownlaodAppMobileNumbers
        fields = '__all__'

class FaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faq
        fields = '__all__'


class ContactDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactDetail
        fields = '__all__'