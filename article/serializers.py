"""
This file is used for formatting (serializing) data interacting with the generated models.
"""

from rest_framework import serializers
from service.serializers import GetServiceSerializers

from users.serializers import CitySerializer
from .models import (
    Article,
    ArticleLike,
    Banner,
    Testimonial,
    Celebrity,
    CelebrityCategory,
    Blog,
)


class CelebrityCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CelebrityCategory
        fields = [
            "id",
            "title",
            "slug",
        ]


class CelebritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Celebrity
        fields = [
            "id",
            "name",
            "description",
            "profession",
            "image",
            "category",
            "x_link",
            "fb_link",
            "insta_link",
            "yt_link",
            "thread",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["category"] = instance.get_category()
        return response


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = [
            "id",
            "title",
            "description",
            "image",
            "is_featured",
            "slug",
        ]


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = [
            "id", 
            "first_name", 
            "last_name", 
            "state", 
            "city", 
            "description",
            "media", 
            "status_type", 
            "comment", 
            "approved_at",
            "created_at",
            "approved_by",
            "created_by"
        ]
        read_only_fields = [
            "comment", "approved_at",
            "created_at", "approved_by", "created_by"
        ]


class ArticleSerializer(serializers.ModelSerializer):
    """
    Class for defining how article creation request and response object should look like.
    """

    is_liked = serializers.SerializerMethodField()
    cities = CitySerializer(many=True, read_only=True)
    service_types = GetServiceSerializers(many=True, read_only=True)
    like_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "user_id",
            "status",
            "is_liked",
            "image_header",
            "created_at",
            "slug",
            "cities",
            "service_types",
            "like_count",
        ]

    def get_is_liked(self, instance):
        user = self.context["request"].user
        if user.is_authenticated:
            return ArticleLike.objects.filter(
                article_id=instance, user_id=user
            ).exists()
        return False

    def get_like_count(self, instance):
        return ArticleLike.objects.filter(article_id=instance.id).count()


class DeleteArticleSerializer(serializers.ModelSerializer):
    """
    Class for defining how article deletion request and response object should look like.
    """

    class Meta:
        model = Article
        fields = ["id", "status"]


class LikeArticleSerializers(serializers.ModelSerializer):
    """
    Class for serializing article likes.
    """

    class Meta:
        model = ArticleLike
        fields = ["id", "article_id", "user_id"]


class DisLikeArticleSerializers(serializers.ModelSerializer):
    """
    Class for serializing vendor service updating views and likes.
    """

    class Meta:
        model = ArticleLike
        fields = ["id", "article_id", "user_id"]


class ArticleSlugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = [
            "id",
            "slug",
        ]


class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = "__all__"

    def create(self, validated_data):
        validated_data["status"] = "PENDING"
        return super().create(validated_data)
