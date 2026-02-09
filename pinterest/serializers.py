from rest_framework import serializers
from pinterest.models import PinterestToken


class PinterestTokenSerializer(serializers.ModelSerializer):

    class Meta:
        model = PinterestToken
        fields = ['id', 'refresh_token']
