from django.utils.text import slugify
from .models import Article


def update_article_slugs():
    for article in Article.objects.all():
        article.save()