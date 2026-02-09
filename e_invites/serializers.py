from rest_framework import serializers
from e_invites.models import InviteTemplate, Template, SavedTemplate


class InviteTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = InviteTemplate
        fields = ['id', 'user', 'template_url', 'template_data']


class InviteTemplateDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = InviteTemplate
        fields = ['template_data', 'template_url']


class TemplateSerializer(serializers.ModelSerializer):
    is_saved = serializers.SerializerMethodField()
    saved_count = serializers.SerializerMethodField()
    class Meta:
        model = Template
        fields = [
            'uuid', 'uid', 'title', 'thumbnail', 'width', 'height', 'tags', 'custom_data',
            'collections', 'layers', "is_saved", "saved_count", "slug", "tag_slugs", "is_active"
        ]

    def get_is_saved(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return SavedTemplate.objects.filter(template=instance, user=user).exists()
        return False
    
    def get_saved_count(self, instance):
        return SavedTemplate.objects.filter(template=instance).count()


class SavedTemplateSerializer(serializers.ModelSerializer):
    template = TemplateSerializer(required=False)
    
    class Meta:
        model = SavedTemplate
        fields = [
            'id', 'user', 'template', 'created_at'
        ]

    