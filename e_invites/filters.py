import django_filters
from e_invites.models import InviteTemplate, Template
from django.db.models import Q

class CustomInviteTemplateFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title', method='get_title')

    class Meta:
        model = InviteTemplate
        fields = ("id", )

    def get_title(self, queryset, field_name, value):
        if not value:
            return queryset
        queryset = queryset.filter(template_data__title__icontains=value)
        return queryset
    

class TemplateFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title')
    tags = django_filters.CharFilter(field_name='tag_slugs', method='filter_tags')

    def filter_tags(self, queryset, name, value):
        # Check if value is a list
        if isinstance(value, list):
            # Filter by tags that contain any of the values in the list
            return queryset.filter(tag_slugs__contains=value)
        # If value is not a list, filter by exact match
        return queryset.filter(tag_slugs__contains=[value])

    class Meta:
        model = Template
        fields = ("title", "tags")
