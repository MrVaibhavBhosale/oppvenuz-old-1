"""oppvenuz URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.schemas import get_schema_view
from rest_framework.routers import DefaultRouter
from phone_verify.api import VerificationViewSet
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

default_router = DefaultRouter(trailing_slash=False)
default_router.register("phone", VerificationViewSet, basename="phone")
#
# schema_view = get_schema_view(title="OppVenuz Backend API", public=True,
#                               renderer_classes=[renderers.OpenAPIRenderer, renderers.SwaggerUIRenderer],
#                               permission_classes=(),)


schema_view = get_schema_view(
   openapi.Info(
      title="Oppvenuz API",
      default_version='v1',
      description="All the endpoints created for chartbiopsy backend",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', schema_view),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/user/', include('users.urls')),
    path('api/service/', include('service.urls')),
    path('api/plan/', include('plan.urls')),
    path('api/payment/', include('payment.urls')),
    path('api/booking/', include('event_booking.urls')),
    path('api/enquiry/', include('enquiry.urls')),
    path('api/article/', include('article.urls')),
    path('api/e_invites/', include('e_invites.urls')),
    path('api/pinterest/', include('pinterest.urls')),
    path('api/feedbacks/', include('feedbacks.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/', include(list(default_router.urls))),   # for twilio phone verification
    path('api/auth/oauth/', include('rest_framework_social_oauth2.urls')),
    path('api/auth/', include('drf_social_oauth2.urls', namespace='drf')),
    path('api/content_manager/', include('content_manager.urls')),
    path('api/seo/', include('seo.urls')),
]
