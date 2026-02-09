from django.contrib import admin
from pinterest.models import PinterestToken, PinterestAccessToken
# Register your models here.

admin.site.register(PinterestToken)
admin.site.register(PinterestAccessToken)