"""
Feedbacks views
"""
from rest_framework import serializers
from utilities import messages
from service.serializers import GetVendorBusinessSerializers
from users.serializers import UserDetailSerializer

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """
    Review serializer
    """

    user = serializers.SerializerMethodField("get_user")
    vendor_service = serializers.SerializerMethodField("get_vendor_service")

    class Meta:
        model = Review
        fields = [
            "id",
            "rating",
            "comment",
            "created_at",
            "updated_at",
            "amount_spend",
            "user",
            "vendor_service",
            "photos",
        ]

    def get_user(self, instance):
        return UserDetailSerializer(instance.user, many=False).data

    def get_vendor_service(self, instance):
        return GetVendorBusinessSerializers(instance.vendor_service, many=False).data


class AddReviewSerializer(serializers.ModelSerializer):
    """
    Review serializer
    """

    class Meta:
        model = Review
        fields = [
            "id",
            "rating",
            "comment",
            "created_at",
            "updated_at",
            "amount_spend",
            "user",
            "vendor_service",
            "photos",
        ]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Review.objects.all(),
                fields=('user', 'vendor_service'),
                message=messages.UNIQ_REVIEW,
            )
        ]