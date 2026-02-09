"""
This file is used for formatting (serializing) data interacting with the generated models.
"""
from rest_framework import serializers
from django.utils import timezone
from utilities.commonutils import verify_google_play
from .models import (Plan,
                     VendorPlan,
                     SubscriptionPlan)

from utilities import messages

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """
    Class for defining how article creation request and response object should look like.
    """
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'subscription_type', 'features']


class PricingPlanSerializer(serializers.ModelSerializer):
    """
    Class for defining how pricing plan creation request and response object should look like.
    """
    service_type = serializers.CharField(source='service_id.service_type', read_only=True)
    features = serializers.SerializerMethodField()
    is_current_plan = serializers.SerializerMethodField()
    # valid_till = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = ['id', 'service_id', 'service_type', 'range_type', 'subscription_type', 'features', 'price',
                  'validity_type', 'is_current_plan']

    def get_features(self, instance):
        features = SubscriptionPlan.objects.filter(subscription_type=instance.subscription_type).values("features")
        return features[0]["features"]

    def get_is_current_plan(self, instance):
        is_current_plan = False
        vendor_service_id = self.context['request'].data.get("vendor_service_id")
        vendor_plan = VendorPlan.objects.filter(vendor_service_id=vendor_service_id).values("plan_id")
        if vendor_plan:
            vendor_plan = vendor_plan[0]["plan_id"]
            if vendor_plan == instance.id:
                is_current_plan = True
        return is_current_plan



class UpdatePricingPlanSerializer(serializers.ModelSerializer):
    """
    Class for defining how pricing plan updating request and response object should look like.
    """
    class Meta:
        model = Plan
        fields = ['id', 'price']


class VendorPlanSerializer(serializers.ModelSerializer):
    """
    Class for defining how vendor choosen plan creation request and response objects should look like.
    """
    # subscription_type = serializers.CharField(source="plan_id.subscription_type", read_only=True)
    vendor_id = serializers.IntegerField(source="vendor_service_id.vendor_id_id", read_only=True)
    business_name = serializers.StringRelatedField(source="vendor_service_id.business_name", read_only=True)
    is_expired = serializers.SerializerMethodField()
    plan_purchased = serializers.SerializerMethodField()


    class Meta:
        model = VendorPlan
        fields = ['id', 'vendor_service_id', "subscription_id", "subscription_type", 'subscription_response', 'vendor_id', 'plan_id', 'starts_from', 'ends_on',
                  'plan_status', 'created_on', "updated_on", "duration_in_months", "business_name", "plan_purchased", "is_expired"]

    def get_is_expired(self, instance):
        today = timezone.now()
        return instance.ends_on < today if instance.ends_on else None
    
    def get_plan_purchased(self, instance):
        return True if instance.subscription_response else False


class UpdateVendorPlanSerializer(serializers.ModelSerializer):
    """
    Class for defining how extending vendor plan updation request and response objects should look like.
    """

    class Meta:
        model = VendorPlan
        fields = ['id', 'ends_on']


class PlanWaveOffSerializer(serializers.ModelSerializer):
    DURATION_CHOICES = [
        (6, '6 months'),
        (12, '12 months'),
        (0, 'UNLIMITED')
    ]
    PLAN_CHOICES = [
        ('GOLD', 'GOLD'),
        ('PLATINUM', 'PLATINUM'),
        ('SILVER', 'SILVER')
    ]
    duration = serializers.ChoiceField(choices=DURATION_CHOICES)
    subscription_type = serializers.ChoiceField(choices=PLAN_CHOICES)
    
    class Meta:
        model = VendorPlan
        fields = ['vendor_service_id', 'subscription_type', 'duration']

    # def validate_vendor_service_id(self, value):
    #     # Add your validation logic here
    #     if not VendorPlan.objects.filter(vendor_service_id=value).exists():
    #         raise serializers.ValidationError(messages.NO_PLAN)
    #     return value
