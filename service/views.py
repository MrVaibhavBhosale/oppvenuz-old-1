"""
This file is used for creating a view for the API,
which takes a web request and returns a web response.
"""
import logging
import os
import csv
import datetime
import json
import branchio
import pandas as pd
from random import shuffle
from itertools import chain
from dateutil.relativedelta import relativedelta
from django.http import HttpResponse
from datetime import datetime as dt
from feedbacks.models import ServiceTracker, TrackingAction
from utilities import constants
from decouple import config

from utilities import messages
from utilities.commonutils import send_email
from utilities.constants import SUPER_ADMIN, VENDOR
from .filters import (
    ReportFilter,
    CustomRecordFilter,
    ServiceFilter,
    VendorServiceFitlter,
)
from utilities.mixins import CSVDownloadMixin
from django.db.models.functions import TruncYear, TruncMonth
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from django.db import transaction
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, F, Case, When, Value, CharField, Sum
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.generics import (
    GenericAPIView,
    DestroyAPIView,
    UpdateAPIView,
    ListAPIView,
    CreateAPIView,
    RetrieveAPIView,
)
from .models import (
    Cart,
    Category,
    CatererServiceMenu,
    Service,
    ServiceSubTypeDetail,
    ServiceSuitableFor,
    VendorService,
    VendorPricing,
    VendorServiceOffer,
    ServiceContactDetail,
    VendorServiceViewLike,
    ServiceEvent,
    VenueType,
    ServiceRegistrationChargesDetail,
    ServiceVendorRegistrationCharges
)
from feedbacks.models import TrackUserAction, TrackUserSession
from .utils import (
    CustomPerCategoryPagination,
    track_action,
    get_recommended_services,
    is_all_services_verified,
    update_user_cart_url,
    update_service_share_url,
    track_user_action,
)
from rest_framework.exceptions import ValidationError, NotFound
from users.models import CustomUser
from fcm_django.models import FCMDevice
from plan.models import VendorPlan, Plan
from enquiry.models import Enquiry
from payment.models import PaymentCancellation
from oppvenuz.settings.settings import DEV_API_URL, STAGING_API_URL, PROD_API_URL
from .serializers import (
    CartItemSerializers,
    CatererServiceMenuSerializer,
    GetServiceSerializers,
    AddCartItemSerializers,
    ServiceByTypeSerializer,
    ServiceSubtypeDetailSerializer,
    ServiceSuitableForSerializer,
    UserCartUrlSerializers,
    ServiceDetailsSerializers,
    ServicePricingSerializers,
    ServiceShareUrlSerializers,
    ServiceViewLikeSerializers,
    ServiceBusinessSerializers,
    AddVendorServiceSerializers,
    GetVendorBusinessSerializers,
    UpdateServiceOfferSerializers,
    GetApprovedServiceSerializers,
    VendorServiceOfferSerializers,
    UpdateServiceStatusSerializers,
    PlatinumServiceOfferSerializers,
    ServiceReportDetailsSerializers,
    VendorServiceLikeReportSerializer,
    UpdateContactDetailsSerializers,
    UpdateServiceWaveOffSerializers,
    ServiceContactDetailsSerializers,
    GetUserServiceMappingSerializers,
    UpdateServiceViewLikeSerializers,
    SuperAdminServiceDetailsSerializers,
    SuperAdminVendorSerializer,
    ServiceEventSerializer,
    VenueTypeSerializer,
    ListVendorServicesSerializer,
    UserActivityReportSerializer,
    UserSessionReportSerializer,
    ServiceRegistrationChargesDetailSerializer,
    RegPaymentStatusSerializer,
    ServiceRegistrationChargesSerializer,
    VendorServicePendingPayStatusSerializer,
    ServiceRegistrationStatusSerializer,
    GetVendorServicePaymentDetails
)
from plan.serializers import VendorPlanSerializer
from users.serializers import (
    CityDetailSerializer,
    CitySerializer,
    NotificationSerializer,
)
from rest_framework.filters import SearchFilter
from users.permissions import IsSuperAdmin, IsTokenValid, IsPlatinumUser
from users.utils import ResponseInfo, CustomPagination, send_sms
from payment.serializers import ServicePaymentCancellationSerializers
from users.views import UserLoginAPIView, ForgotPasswordRequestView
from utilities.commonutils import send_email
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication

dev_client = branchio.Client(config("DEVELOP_BRANCH_API_KEY"))
staging_client = branchio.Client(config("DEVELOP_BRANCH_API_KEY"))
logger = logging.getLogger('django')

from rest_framework.views import APIView
from rest_framework.response import Response
import requests
import random
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date

class HotelBookingToVenuesConversion(CreateAPIView):
    serializer_class = ServiceDetailsSerializers
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (AllowAny,)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(HotelBookingToVenuesConversion, self).__init__(**kwargs)

    def create(self, request, *args, **kwargs):
        venue = Service.objects.get(slug="venue")
        hotel_booking = Service.objects.get(slug="hotel-booking")

        with transaction.atomic():
            hb_services = VendorService.objects.filter(service_id=hotel_booking)
            for service in hb_services:
                service.service_id = venue
                service.save()
                if service.vendorpricing_set.exists():
                    pricing = service.vendorpricing_set.first()
                    ServiceSubTypeDetail.objects.create(
                        title="Hotel",
                        service_subtype="venueType",
                        service=service,
                        discounted_price=pricing.discounted_price or None,
                    )

        self.response_format["data"] = messages.SUCCESS
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_200_OK)


class VendorVerifiedAllServices(ListAPIView):
    serializer_class = ServiceDetailsSerializers
    authentication_classes = (OAuth2Authentication, JWTAuthentication)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(VendorVerifiedAllServices, self).__init__(**kwargs)

    def get_queryset(self):
        return VendorService.objects.filter(vendor_id=self.request.user)

    def list(self, request, *args, **kwargs):
        self.response_format["data"] = dict(
            is_documents_verified=is_all_services_verified(request.user)
        )
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_200_OK)


class ServiceMergerAPI(CreateAPIView):
    serializer_class = ServiceDetailsSerializers
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        dj_slug = "band-and-dj-artist"
        live_perf_slug = "live-performer-entertainer"

        # find all distinct users with both the services
        users_with_both_services = (
            CustomUser.objects.filter(vendorservice__service_id__slug=dj_slug)
            .filter(vendorservice__service_id__slug=live_perf_slug)
            .distinct()
        )

        # iterate over each of the users
        for user in users_with_both_services:
            user_services_band_dj = VendorService.objects.filter(
                vendor_id=user.id, service_id__slug=dj_slug
            ).first()

            user_services_live_performer = VendorService.objects.filter(
                vendor_id=user.id, service_id__slug=live_perf_slug
            ).first()

            # merge the fields from both the services
            if user_services_band_dj and user_services_live_performer:
                for field in VendorService._meta.get_fields():
                    if hasattr(user_services_band_dj, field.name) and hasattr(
                        user_services_live_performer, field.name
                    ):
                        band_dj_value = getattr(user_services_band_dj, field.name)
                        live_performer_value = getattr(
                            user_services_live_performer, field.name
                        )

                        if band_dj_value and not live_performer_value:
                            setattr(
                                user_services_live_performer, field.name, band_dj_value
                            )

                # Save the merged instance
                user_services_live_performer.save()
                print(user_services_live_performer, "updated")

                # update related objects of dj services
                VendorPricing.objects.filter(
                    vendor_service_id=user_services_band_dj
                ).update(vendor_service_id=user_services_live_performer)
                ServiceSubTypeDetail.objects.filter(
                    service=user_services_band_dj
                ).update(service=user_services_live_performer)
                ServiceContactDetail.objects.filter(
                    vendor_service_id=user_services_band_dj
                ).update(vendor_service_id=user_services_live_performer)

                # mark band and dj service as deleted
                user_services_band_dj.approval_status = "D"
                user_services_band_dj.save()

        lf_service = Service.objects.get(slug=live_perf_slug)
        # switch all band services to live performer services
        band_dj_services = (
            VendorService.objects.filter(service_id__slug=dj_slug)
            .exclude(vendor_id__in=users_with_both_services)
            .update(service_id=lf_service)
        )
        return Response({"message": "Completed"}, status=status.HTTP_200_OK)


class RecommendedServiceBasedOnCartAPI(ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = ServiceDetailsSerializers
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = CustomRecordFilter
    pagination_class = PageNumberPagination
    pagination_class.page_size = 10
    search_fields = ["business_name"]

    def get_queryset(self):
        user = self.request.user
        return get_recommended_services(user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ListFavoriteServicesAPI(ListAPIView):
    serializer_class = ServiceByTypeSerializer
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (IsAuthenticated, IsTokenValid)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = (
        "area",
        "city",
        "state",
    )
    search_fields = (
        "business_name",
        "area",
        "city",
        "state",
    )
    http_method_names = ("get",)
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return user.favorites.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AddOrRemoveFavoriteServiceAPI(CreateAPIView):
    serializer_class = ServiceByTypeSerializer
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (IsAuthenticated, IsTokenValid)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddOrRemoveFavoriteServiceAPI, self).__init__(**kwargs)

    def get_queryset(self):
        user = self.request.user
        return user.favorites.all()

    def create(self, request, *args, **kwargs):
        user = self.request.user
        service = VendorService.objects.get(id=self.kwargs["pk"])
        r = user.add_service_to_favorites(service)
        if r == 1:
            track_action(request, service, TrackingAction.FAVORITE)
            track_user_action(request, service, "added_to_favorite")
            msg = messages.SERVICE_FAV_BY_USER.format(
                service.business_name, user.fullname
            )
            params = json.dumps({"service_id": service.id})
            notification_data = {
                "message": msg,
                "status": "UR",
                "user_id": service.vendor_id_id,
                "notification_type": "SERVICE_FAV",
                "params": params,
            }
            req = NotificationSerializer(data=notification_data)
            if req.is_valid(raise_exception=True):
                req.save()
                is_device = FCMDevice.objects.filter(user_id=request.user.id)
                if is_device:
                    UserLoginAPIView.generate_fcm_token(
                        self, service.vendor_id_id, notification_data
                    )

        message = (
            messages.FAV_SERVICE_ADDED.format(service.business_name)
            if r == 1
            else messages.FAV_SERVICE_REMOVED.format(service.business_name)
        )
        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["error"] = None
        self.response_format["message"] = message
        return Response(self.response_format)


class VenueTypeCreateAPIView(CreateAPIView):
    serializer_class = VenueTypeSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    http_method_names = ("post",)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(VenueTypeCreateAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        return VenueType.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["error"] = None
        self.response_format["message"] = messages.ADDED.format("Venue type")
        return Response(self.response_format)


class UpdateVenueTypeAPIView(UpdateAPIView):
    """
    Class for updating existing article
    """

    serializer_class = VenueTypeSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    http_method_names = ("patch", "put")

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateVenueTypeAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        return VenueType.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_205_RESET_CONTENT
        self.response_format["error"] = None
        self.response_format["message"] = messages.UPDATE.format("Venue type")
        return Response(self.response_format)


class ListVenueTypesAPIView(ListAPIView, CSVDownloadMixin):
    serializer_class = VenueTypeSerializer
    permission_classes = (AllowAny,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ("title",)
    http_method_names = ("get",)
    pagination_class = CustomPagination

    def get_queryset(self):
        return VenueType.objects.all().order_by("sequence_number")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Check if 'download=csv' is in the query parameters
        if request.GET.get("download") == "csv":
            return self.download_csv(request, queryset, self.serializer_class)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ServiceFilterAPIView(ListAPIView, CSVDownloadMixin):
    serializer_class = ServiceByTypeSerializer
    permission_classes = (AllowAny,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    pagination_class = CustomPagination
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ("business_name", "area", "city", "state")
    filterset_class = ServiceFilter

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(ServiceFilterAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        title = self.request.query_params.get("title", None)
        if title:
            return (
                VendorService.objects.select_related("service_id")
                .filter(
                    Q(subtypes__title__iexact=title, approval_status="A")
                    | Q(vendorpricing__venue_type__icontains=title, approval_status="A")
                )
                .distinct()
            )
        return (
            VendorService.objects.select_related("service_id")
            .filter(approval_status="A")
            .distinct()
        )

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if request.GET.get("download") == "csv":
            return self.download_csv(request, queryset, self.serializer_class)

        today = datetime.datetime.now().date()

        vendor_with_active_plan = queryset.filter(
            vendorplan__subscription_type__in=["PLATINUM", "GOLD", "SILVER"],
            vendorplan__plan_status="ACTIVE",
            vendorplan__ends_on__date__gte=today,
        ).distinct()

        no_subscription_vendors = queryset.exclude(
            id__in=vendor_with_active_plan
        ).distinct()

        platinum_vendor_services = list(
            vendor_with_active_plan.filter(
                vendorplan__subscription_type="PLATINUM",
                vendorplan__plan_status="ACTIVE",
                vendorplan__ends_on__date__gte=today,
            ).distinct()
        )

        gold_vendor_services = list(
            vendor_with_active_plan.filter(
                vendorplan__subscription_type="GOLD",
                vendorplan__plan_status="ACTIVE",
                vendorplan__ends_on__date__gte=today,
            ).distinct()
        )

        silver_vendor_services = list(
            vendor_with_active_plan.filter(
                vendorplan__subscription_type="SILVER",
                vendorplan__plan_status="ACTIVE",
                vendorplan__ends_on__date__gte=today,
            ).distinct()
        )

        no_subscription_vendors = list(no_subscription_vendors)

        print(
            len(platinum_vendor_services),
            len(gold_vendor_services),
            len(silver_vendor_services),
            len(no_subscription_vendors),
        )

        shuffle_seed = request.GET.get("shuffle", None)
        random.seed(shuffle_seed)

        random.shuffle(platinum_vendor_services)
        random.shuffle(gold_vendor_services)
        random.shuffle(silver_vendor_services)
        random.shuffle(no_subscription_vendors)

        queryset = list(
            chain(
                platinum_vendor_services,
                gold_vendor_services,
                silver_vendor_services,
                no_subscription_vendors,
            )
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DeleteVendorServiceAPI(DestroyAPIView):
    serializer_class = ServiceDetailsSerializers
    permission_classes = (AllowAny,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(DeleteVendorServiceAPI, self).__init__(**kwargs)

    def get_queryset(self):
        return VendorService.objects.filter(id=self.kwargs["pk"])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_204_NO_CONTENT
        self.response_format["error"] = None
        self.response_format["message"] = messages.DELETE.format("Service")
        return Response(self.response_format)


class AddServiceEventView(CreateAPIView):
    serializer_class = ServiceEventSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddServiceEventView, self).__init__(**kwargs)

    def get_queryset(self):
        return ServiceEvent.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self.response_format["data"] = serializer.data
        self.response_format["errors"] = serializer.errors
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["message"] = messages.ADDED.format(constants.EVENT)
        return Response(
            self.response_format,
            status=status.HTTP_201_CREATED,
        )


class GetServiceEventsListAPI(ListAPIView):
    serializer_class = ServiceEventSerializer
    permission_classes = ()
    authentication_classes = ()
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ["title"]

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetServiceEventsListAPI, self).__init__(**kwargs)

    def get_queryset(self):
        return ServiceEvent.objects.all().order_by("title")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        self.response_format["data"] = serializer.data
        self.response_format["errors"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)


class DeleteServiceSubTypeDetailView(DestroyAPIView):
    serializer_class = ServiceSubtypeDetailSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(DeleteServiceSubTypeDetailView, self).__init__(**kwargs)

    def get_queryset(self):
        return ServiceSubTypeDetail.objects.all()

    def destroy(self, request, *args, **kwargs):
        instace = self.get_object()
        self.perform_destroy(instace)
        self.response_format["data"] = []
        self.response_format["errors"] = None
        self.response_format["status_code"] = status.HTTP_204_NO_CONTENT
        self.response_format["message"] = messages.DELETE.format(
            "Service sub type details"
        )
        return Response(
            self.response_format,
            status=status.HTTP_204_NO_CONTENT,
        )


class AddServiceSubTypeDetailView(CreateAPIView):
    serializer_class = ServiceSubtypeDetailSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddServiceSubTypeDetailView, self).__init__(**kwargs)

    def get_queryset(self):
        return ServiceSubTypeDetail.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self.response_format["data"] = serializer.data
        self.response_format["errors"] = serializer.errors
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["message"] = messages.ADDED.format(
            "Service sub type details"
        )
        return Response(
            self.response_format,
            status=status.HTTP_201_CREATED,
        )


class UpdateServiceSubTypeDetailView(UpdateAPIView):
    serializer_class = ServiceSubtypeDetailSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateServiceSubTypeDetailView, self).__init__(**kwargs)

    def get_queryset(self):
        return ServiceSubTypeDetail.objects.all()

    def patch(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self.response_format["data"] = serializer.data
        self.response_format["errors"] = serializer.errors
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = messages.UPDATE.format(
            "Service sub type details"
        )
        return Response(
            self.response_format,
            status=status.HTTP_200_OK,
        )


class VendorServiceListAPI(ListAPIView):
    serializer_class = PlatinumServiceOfferSerializers
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPagination
    pagination_class.page_size = 10

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(VendorServiceListAPI, self).__init__(**kwargs)

    def get_queryset(self):
        user_id = self.kwargs.get("pk", None)
        return VendorService.objects.filter(vendor_id=user_id).order_by("business_name")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        self.response_format["data"] = serializer.data
        self.response_format["errors"] = None
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)


class AddBestSuitedForOptionAPI(CreateAPIView):
    serializer_class = ServiceSuitableForSerializer
    permission_classes = ()
    authentication_classes = ()

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddBestSuitedForOptionAPI, self).__init__(**kwargs)

    def get_queryset(self):
        return ServiceSuitableFor.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self.response_format["data"] = serializer.data
        self.response_format["errors"] = serializer.errors
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["message"] = messages.ADDED.format("Best Suitable Option")
        return Response(
            self.response_format,
            status=status.HTTP_201_CREATED,
        )


class GetBestSuitedForListAPI(ListAPIView):
    serializer_class = ServiceSuitableForSerializer
    permission_classes = ()
    authentication_classes = ()
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = [
        "title",
    ]

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetBestSuitedForListAPI, self).__init__(**kwargs)

    def get_queryset(self):
        return ServiceSuitableFor.objects.all().order_by("title")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        self.response_format["data"] = serializer.data
        self.response_format["errors"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)


class GetServiceListView(ListAPIView, CSVDownloadMixin):
    serializer_class = GetServiceSerializers
    authentication_classes = ()
    permission_classes = ()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("is_included",)
    http_method_names = ("get",)
    # pagination_class = CustomPagination

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetServiceListView, self).__init__(**kwargs)

    def get_queryset(self):
        return Service.objects.all().order_by("service_type")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if request.GET.get("download") == "csv":
            return self.download_csv(request, queryset, self.serializer_class)

        service_list_serialized = self.get_serializer(queryset, many=True)
        self.response_format["data"] = service_list_serialized.data
        return Response(self.response_format)

        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)

        # serializer = self.get_serializer(queryset, many=True)
        # return Response(serializer.data)


# class GetServiceListView(ListAPIView, CSVDownloadMixin):
#     """
#     Class for creating API view for getting service list.
#     """

#     permission_classes = ()
#     authentication_classes = ()
#     filter_backends = (DjangoFilterBackend,)
#     filterset_fields = ('is_included',)
#     serializer_class = GetServiceSerializers

#     def __init__(self, **kwargs):
#         """
#         Constructor function for formatting the web response to return.
#         """
#         self.response_format = ResponseInfo().response
#         super(GetServiceListView, self).__init__(**kwargs)

#     def get_queryset(self):
#         if getattr(self, "swagger_fake_view", False):
#             return Service.objects.none()
#         return Service.objects.all().order_by("service_type")

#     def get(self, request):
#         """
#         Function for getting service list.
#         Authorization Header required.
#         """
#         queryset = self.get_queryset()

#         if request.GET.get("download") == "csv":
#             return self.download_csv(request, queryset, self.serializer_class)

#         service_list_serialized = self.get_serializer(queryset, many=True)

#         self.response_format["data"] = service_list_serialized.data

#         return Response(self.response_format)


class GetVendorServiceListView(ListAPIView):
    """
    Class for creating API view for getting vendor service.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = GetUserServiceMappingSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetVendorServiceListView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the services offered by vendor.
        """
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        user_id = self.request.user
        return VendorService.objects.filter(vendor_id=user_id)

    def get(self, request, *args, **kwargs):
        """
        Function for getting vender services list.
        """
        serialized = super().list(request, *args, **kwargs)

        self.response_format["data"] = serialized.data
        return Response(self.response_format)


class GetVendorBusinessListView(ListAPIView):
    """
    Class for creating API view for getting vendor business.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = GetVendorBusinessSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetVendorBusinessListView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the vendor business.
        """
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        user_id = self.request.user
        return VendorService.objects.filter(vendor_id=user_id).filter(
            approval_status="A"
        )

    def get(self, request, *args, **kwargs):
        """
        Function for getting vendor business list.
        """
        serialized = super().list(request, *args, **kwargs)

        self.response_format["data"] = serialized.data
        return Response(self.response_format)


class AddVendorServiceAPIView(GenericAPIView):
    """
    Class for creating API view for getting vendor service.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = AddVendorServiceSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddVendorServiceAPIView, self).__init__(**kwargs)

    def post(self, request):
        """
        Function for creating new project.
        Authorization Header required.
        """
        services = request.data["service_ids"]

        for service in services:
            request.data["vendor_id"] = request.user.id
            request.data["service_id"] = service

            serialized = self.get_serializer(data=request.data)

            if serialized.is_valid(raise_exception=True):
                serialized.save()
                self.response_format["data"] = serialized.data
                self.response_format["message"] = "Service added successfully."
            else:
                self.response_format["data"] = None
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                self.response_format["error"] = serialized.errors
                self.response_format["message"] = "Failure."
        return Response(self.response_format)


class UpdateVendorServiceAPIView(GenericAPIView):
    """
    Class for adding service details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ServiceDetailsSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateVendorServiceAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        vendor_service_id = self.kwargs["pk"]
        return VendorService.objects.filter(id=vendor_service_id)

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        feature_check = (
            True
            if instance.approval_status == "A" and instance.payment_status == "PAID"
            else False
        )
        instance.business_name = request.data.get("business_name")
        instance.business_image = request.data.get("business_image")
        instance.working_since = request.data.get("working_since")
        instance.number_of_events_done = request.data.get("number_of_events_done")
        instance.user_group_service_type = request.data.get("user_group_service_type")
        instance.additional_information = request.data.get("additional_information")
        instance.area = request.data.get("area")
        instance.city = request.data.get("city")
        instance.state = request.data.get("state")
        instance.pin_code = request.data.get("pin_code")
        instance.approval_status = request.data.get("approval_status")
        service_attachments = request.data.get("service_attachments")
        service_is_edited = request.data.get("service_is_edited", None)
        if service_is_edited:
            request.data["updated_at"] = datetime.datetime.now()
        if feature_check:
            vendor_plan = (
                VendorPlan.objects.filter(vendor_service_id=instance.id)
                .order_by("-created_on")
                .first()
            )
            subscription_type = vendor_plan.subscription_type
            if subscription_type == "SILVER":
                video_ext = ("mp4", "flv")
                [
                    service_attachments.remove(file)
                    for file in service_attachments
                    if file.endswith(video_ext)
                ]
                instance.service_attachments = service_attachments
            elif subscription_type == "GOLD" or subscription_type == "PLATINUM":
                instance.service_attachments = service_attachments
                instance.website_url = request.data.get("website_url")
                instance.facebook_url = request.data.get("facebook_url")
                instance.instagram_url = request.data.get("instagram_url")
        else:
            instance.service_attachments = service_attachments[0]
            instance.website_url = None
            instance.facebook_url = None
            instance.instagram_url = None

        vendor_service_serializer = self.get_serializer(instance, data=request.data)
        if vendor_service_serializer.is_valid(raise_exception=True):
            venue_types = request.data.get("venue_types", None)
            if venue_types:
                instance.venue_type.add(*venue_types)
            caterer_services = request.data.get("caterer_services", None)
            if caterer_services:
                instance.cater_menu.all().delete()
                for cater in caterer_services:
                    cater_menu = CatererServiceMenu.objects.create(
                        **cater, service=instance
                    )
            subtype_services = request.data.get("subtype_services", None)
            if subtype_services:
                instance.subtypes.all().delete()
                for subtype in subtype_services:
                    subtype_obj = ServiceSubtypeDetailSerializer(data=subtype)
                    if subtype_obj.is_valid(raise_exception=True):
                        subtype_obj.save()
            contact_details_list = request.data.get("contact_details")
            instance.servicecontactdetail_set.all().delete()
            for contact_detail in contact_details_list:
                contact_detail_serializer = ServiceContactDetailsSerializers(
                    data=contact_detail
                )
                if contact_detail_serializer.is_valid(raise_exception=True):
                    contact_detail_serializer.save()
            service_pricing_list = request.data.get("service_pricing_list", None)
            service_price_data = []
            if service_pricing_list:
                for service_price in service_pricing_list:
                    service_price_id = service_price.get("service_pricing_id", 0)
                    if service_price_id == 0:
                        service_pricing_serializer = ServicePricingSerializers(
                            data=service_price
                        )
                    else:
                        vendor_price_obj = VendorPricing.objects.get(
                            id=service_price_id
                        )
                        service_pricing_serializer = ServicePricingSerializers(
                            instance=vendor_price_obj, data=service_price
                        )
                    if service_pricing_serializer.is_valid(raise_exception=True):
                        obj = service_pricing_serializer.save()
                        Cart.objects.filter(
                            vendor_service_id=instance.id, package_id=obj.id
                        ).update(
                            actual_price=obj.actual_price,
                            discounted_price=obj.discounted_price,
                        )
                        service_price_data.append(obj.id)

            vendor_price_deleted_data = VendorPricing.objects.filter(
                vendor_service_id=instance.id
            ).exclude(id__in=service_price_data)
            if vendor_price_deleted_data:
                Cart.objects.filter(
                    vendor_service_id=instance.id,
                    package_id__in=vendor_price_deleted_data,
                ).delete()
                vendor_price_deleted_data.delete()

            if request.data.get("payment_cancellation_policy"):
                payment_cancellation = request.data.get("payment_cancellation_policy")
                payment_cancellation_object = PaymentCancellation.objects.filter(
                    vendor_service_id=instance.id
                )
                if payment_cancellation_object.count() > 1:
                    payment_cancellation_object.delete()
                if payment_cancellation_object:
                    payment_cancellation_serializer = (
                        ServicePaymentCancellationSerializers(
                            instance=payment_cancellation_object.first(),
                            data=payment_cancellation,
                        )
                    )
                else:
                    payment_cancellation_serializer = (
                        ServicePaymentCancellationSerializers(data=payment_cancellation)
                    )
                if payment_cancellation_serializer.is_valid(raise_exception=True):
                    payment_cancellation_serializer.save()
            vendor_service_serializer.save()
            if instance.approval_status == "P":
                instance.is_under_review = True
                instance.save()

            self.response_format["data"] = vendor_service_serializer.data
        if service_is_edited:
            self.response_format["message"] = messages.UPDATE.format("Service details")
        else:
            self.response_format["message"] = messages.ADDED.format("Service details")
        return Response(self.response_format)


class GetVendorServiceDetailsListAPIView(ListAPIView):
    """
    Class for creating API view for getting vendor service details.
    """

    permission_classes = (IsAuthenticated,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = ServiceDetailsSerializers
    filter_backends = (DjangoFilterBackend,)
    filter_class = CustomRecordFilter
    pagination_class = CustomPagination

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetVendorServiceDetailsListAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        user_type = self.request.user.role
        user_status = self.request.query_params.get("user_status", None)

        if user_status == "ACTIVE" and user_type == "VENDOR":
            return VendorService.objects.filter(
                vendor_id=self.request.user.id, vendor_id__status=user_status
            ).exclude(approval_status__in=["R", "D", "P"])
        return VendorService.objects.filter(vendor_id__status=user_status).exclude(
            approval_status__in=["R", "D", "P"]
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        self.response_format["data"] = serializer.data
        self.response_format["error"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_200_OK)


class ListVendorServiceDetailsAPI(ListAPIView):
    """
    Class for creating API view for getting vendor service details.
    """

    permission_classes = (IsAuthenticated,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = ListVendorServicesSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = CustomRecordFilter
    pagination_class = CustomPagination

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(ListVendorServiceDetailsAPI, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        user_type = self.request.user.role
        user_status = self.request.query_params.get("user_status", None)

        if user_status == "ACTIVE" and user_type == "VENDOR":
            return VendorService.objects.filter(
                vendor_id=self.request.user.id, vendor_id__status=user_status
            ).exclude(approval_status__in=["R", "D", "P"])
        return VendorService.objects.filter(vendor_id__status=user_status).exclude(
            approval_status__in=["R", "D", "P"]
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        self.response_format["data"] = serializer.data
        self.response_format["error"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_200_OK)


class GetVendorServiceDetailsListView(ListAPIView):
    """
    Class for creating API view for getting vendor service details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ServiceDetailsSerializers
    filter_backends = (DjangoFilterBackend,)
    filter_class = CustomRecordFilter
    pagination_class = CustomPagination

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetVendorServiceDetailsListView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        user_type = self.request.user.role
        user_status = self.request.query_params.get("user_status", None)
        if user_type == "SUPER_ADMIN":
            return (
                VendorService.objects.filter(approval_status__in=["P", "A"])
                .exclude(business_name=None)
                .order_by("-created_at")
            )

        if user_status == "ACTIVE" and user_type == "VENDOR":
            return VendorService.objects.filter(
                vendor_id=self.request.user.id, vendor_id__status=user_status
            ).exclude(approval_status__in=["R", "D", "P"])

        else:
            return VendorService.objects.filter(vendor_id__status=user_status).exclude(
                approval_status__in=["R", "D", "P"]
            )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        self.response_format["data"] = serializer.data
        self.response_format["error"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_200_OK)


class GetVendorServiceDetailListView(ListAPIView):
    """
    Class for creating API view for getting vendor service details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ServiceDetailsSerializers
    filter_backends = (DjangoFilterBackend,)
    filter_class = CustomRecordFilter

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        user_type = self.request.user.role
        user_status = self.request.data["user_status"]
        if user_type == "SUPER_ADMIN":
            vendor_details = (
                VendorService.objects.filter(approval_status__in=["P", "A"])
                .exclude(business_name=None)
                .order_by("-created_at")
            )
        elif user_status == "ACTIVE":
            if user_type == "VENDOR":
                vendor_details = (
                    VendorService.objects.filter(vendor_id=self.request.user.id)
                    .filter(vendor_id__status=user_status)
                    .exclude(approval_status="R")
                    .exclude(approval_status="D")
                    .exclude(approval_status="P")
                )
            else:
                vendor_details = (
                    VendorService.objects.filter(vendor_id__status=user_status)
                    .exclude(approval_status="R")
                    .exclude(approval_status="D")
                    .exclude(approval_status="P")
                )
        return vendor_details

    def generate_service_detail_data(self, service_data):
        main_data = list()
        for element in service_data:
            contact_details = ServiceContactDetail.objects.filter(
                vendor_service_id=element["id"]
            )
            contact_detail_serialized = ServiceContactDetailsSerializers(
                contact_details, many=True
            )
            vendor_service_pricing = VendorPricing.objects.filter(
                vendor_service_id=element["id"]
            )
            vendor_service_pricing_serialized = ServicePricingSerializers(
                vendor_service_pricing, many=True
            )
            payment_cancellation = PaymentCancellation.objects.filter(
                vendor_service_id=element["id"]
            )
            payment_cancellation_serialized = ServicePaymentCancellationSerializers(
                payment_cancellation, many=True
            )
            data = {
                "id": element["id"],
                "vendor_id": element["vendor_id"],
                "vendor_name": element["vendor_name"],
                "service_id": element["service_id"],
                "business_name": element["business_name"],
                "business_image": element["business_image"],
                "working_since": element["working_since"],
                "number_of_events_done": element["number_of_events_done"],
                "user_group_service_type": element["user_group_service_type"],
                "website_url": element["website_url"],
                "facebook_url": element["facebook_url"],
                "instagram_url": element["instagram_url"],
                "additional_information": element["additional_information"],
                "area": element["area"],
                "city": element["city"],
                "state": element["state"],
                "pin_code": element["pin_code"],
                "service_attachments": element["service_attachments"],
                "approval_status": element["approval_status"],
                "payment_status": element["payment_status"],
                "share_url": element["share_url"],
                "is_waved_off": element["is_waved_off"],
                "created_at": element["created_at"],
                "updated_at": element["updated_at"],
                "service_type": element["service_type"],
                "service_type_code": element["service_type_code"],
                "vendor_contact": element["vendor_contact"],
                "contact_details": contact_detail_serialized.data,
                "service_pricing": vendor_service_pricing_serialized.data,
                "payment_cancellation_policy": payment_cancellation_serialized.data,
                "is_liked": element["is_liked"],
                "service_views": element["service_views"],
                "service_likes": element["service_likes"],
                "plan_data": element["plan_data"],
            }
            main_data.append(data)
        return main_data

    def post(self, request, *args, **kwargs):
        """
        Function for getting vendor service details.
        """
        paginator = PageNumberPagination()
        paginator.page_size = 30

        vendor_service_serialized = super().list(request, *args, **kwargs)
        data = GetVendorServiceDetailListView.generate_service_detail_data(
            self, vendor_service_serialized.data
        )

        result_projects = paginator.paginate_queryset(data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects)


# class GetVendorServiceDetailsAPIView(ListAPIView):
#     """
#     Class for creating API view for getting vendor service details.
#     """
#     permission_classes = (IsAuthenticated, IsTokenValid)
#     authentication_classes = (OAuth2Authentication, JWTAuthentication)
#     serializer_class = ServiceDetailsSerializers

#     def __init__(self, **kwargs):
#         """
#          Constructor function for formatting the web response to return.
#         """
#         self.response_format = ResponseInfo().response
#         super(GetVendorServiceDetailsAPIView, self).__init__(**kwargs)

#     def get_queryset(self):
#         if getattr(self, 'swagger_fake_view', False):
#             return VendorService.objects.none()
#         return VendorService.objects.filter(id=self.kwargs['pk'])

#     def post(self, request, *args, **kwargs):
#         """
#         Function for getting vendor service details.
#         """
#         vendor_service_serialized = super().list(request, *args, **kwargs)
#         data = GetVendorServiceDetailListView.generate_service_detail_data(self, vendor_service_serialized.data)

#         self.response_format["data"] = data
#         return Response(self.response_format)


class GetVendorServiceDetailsAPIView(CreateAPIView):
    """
    Class for creating API view for getting vendor service details.
    """

    permission_classes = (AllowAny,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = ServiceDetailsSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetVendorServiceDetailsAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        return VendorService.objects.filter(id=self.kwargs["pk"])

    def post(self, request, *args, **kwargs):
        """
        Function for getting vendor service details.
        """
        pk = kwargs.get("pk")
        if not pk or pk == "null":
            self.response_format["data"] = None
            self.response_format["error"] = "Invalid ID"
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["message"] = "Invalid ID provided."
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        vendor = VendorService.objects.filter(id=self.kwargs["pk"])
        if vendor.exists():
            update_service_share_url(vendor.first(), request.get_host())
            track_action(request, vendor.first(), TrackingAction.VIEWED)
        serializer = self.get_serializer(vendor, many=True)
        self.response_format["data"] = serializer.data
        self.response_format["error"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = "Success"
        return Response(self.response_format)


class UpdateServiceShareUrlAPIView(GenericAPIView):
    """
    Class for adding service details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = ServiceShareUrlSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateServiceShareUrlAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        vendor_service_id = self.kwargs["pk"]
        return VendorService.objects.filter(id=vendor_service_id)

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.share_url:
            url = instance.share_url
        else:
            if request.META["HTTP_HOST"] == PROD_API_URL:
                client = staging_client
            else:
                client = dev_client
            response = client.create_deep_link_url(
                data={
                    "link_type": "service",
                    "redirect_url_path": "/home/shared-service-detail",
                    "vendor_service_id": instance.id,
                }
            )
            url = response[branchio.RETURN_URL]

        instance.share_url = url

        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            instance.increase_share_count()
            self.response_format["data"] = serializer.data

        return Response(self.response_format)


class GetServiceListByTypeAPIView(ListAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = ServiceByTypeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("city", "state")

    def get_queryset(self):
        service_type = self.kwargs["service_type"]
        return (
            VendorService.objects.select_related("service_id", "vendor_id")
            .prefetch_related("vendorpricing_set", "vendorpricing_set")
            .filter(approval_status="A", service_id__slug=service_type)
        )

    def get_serializer_context(self):
        """
        Add request object to serializer context.
        """
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def list(self, request, *args, **kwargs):
        """
        Function for getting vendor service details.
        """
        paginator = PageNumberPagination()
        paginator.page_size = 20
        services = super().list(request, *args, **kwargs)
        result_projects = paginator.paginate_queryset(services.data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects)


class GetServiceByTypeListView(ListAPIView):
    """
    Class for creating API view for getting vendor service details.
    """

    permission_classes = ()
    authentication_classes = ()
    serializer_class = ServiceDetailsSerializers
    filter_backends = (DjangoFilterBackend,)
    filter_class = CustomRecordFilter

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        service_type = self.kwargs["service_type"]
        # return VendorService.objects.filter(service_id__service_type=service_type, approval_status="A", payment_status="PAID")
        return VendorService.objects.filter(
            approval_status="A", service_id__slug=service_type.replace("%", "")
        )

    def post(self, request, *args, **kwargs):
        """
        Function for getting vendor service details.
        """
        paginator = PageNumberPagination()
        paginator.page_size = 20
        services = super().list(request, *args, **kwargs)
        result_projects = paginator.paginate_queryset(services.data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects)


class SearchServiceByTypeListView(ListAPIView):
    """
    Class for creating API view for searching vendor service by type.
    """

    permission_classes = ()
    authentication_classes = ()
    serializer_class = ServiceDetailsSerializers
    filter_backends = (SearchFilter, DjangoFilterBackend)
    filterset_class = VendorServiceFitlter
    search_fields = ["business_name", "city"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        service_type = self.kwargs["service_type"]
        return VendorService.objects.filter(
            approval_status="A", service_id__slug=service_type
        )

    def post(self, request, *args, **kwargs):
        """
        Function for getting vendor service details.
        """
        paginator = PageNumberPagination()
        paginator.page_size = 20
        vendors = super().list(request, *args, **kwargs)
        result_projects = paginator.paginate_queryset(vendors.data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects)


class SearchServiceListByTypeView(ListAPIView):
    """
    Class for creating API view for searching vendor service by type.
    """

    permission_classes = ()
    authentication_classes = ()
    serializer_class = ServiceByTypeSerializer
    filter_backends = (SearchFilter, DjangoFilterBackend)
    filterset_class = VendorServiceFitlter
    search_fields = ["business_name", "city"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        service_type = self.kwargs["service_type"]
        return VendorService.objects.filter(
            approval_status="A", service_id__slug=service_type
        )

    def get(self, request, *args, **kwargs):
        """
        Function for getting vendor service details.
        """
        paginator = PageNumberPagination()
        paginator.page_size = 20
        vendors = super().list(request, *args, **kwargs)
        result_projects = paginator.paginate_queryset(vendors.data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects)


class GetServiceContactListView(ListAPIView):
    """
    Class for creating API view for getting vendor service contact details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ServiceContactDetailsSerializers

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ServiceContactDetail.objects.none()

    def get(self, request, *args, **kwargs):
        """
        Function for getting vendor service contact details.
        """
        paginator = PageNumberPagination()
        paginator.page_size = 10
        vendor_service_id = self.kwargs["vendor_service_id"]
        vendor_service_contact_list = ServiceContactDetail.objects.filter(
            vendor_service_id=vendor_service_id
        )

        vendor_service_contact_serialized = self.get_serializer(
            vendor_service_contact_list, many=True
        )
        data = vendor_service_contact_serialized.data

        result_projects = paginator.paginate_queryset(data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects)


class UpdateServiceContactAPIView(UpdateAPIView):
    """
    Class for updating service vendor contact details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UpdateContactDetailsSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateServiceContactAPIView, self).__init__(**kwargs)

    def get_objectt(self, contact_id):
        try:
            return ServiceContactDetail.objects.get(id=contact_id)
        except ServiceContactDetail.DoesNotExist:
            return status.HTTP_404_NOT_FOUND

    def patch(self, request, *args, **kwargs):
        contact_list = request.data.get("contact_list")

        for contact in contact_list:
            instance = self.get_objectt(contact["id"])
            instance.contact_person = contact["contact_person"]
            instance.contact_email = contact["contact_email"]
            instance.contact_number = contact["contact_number"]
            instance.vendor_service_id_id = contact["vendor_service_id"]

            service_contact_serializer = self.get_serializer(instance, data=contact)
            if service_contact_serializer.is_valid(raise_exception=True):
                service_contact_serializer.update(
                    instance, service_contact_serializer.data
                )
                # self.partial_update(service_contact_serializer)
                self.response_format["data"] = service_contact_serializer.data

        return Response(self.response_format)


class UpdateServiceBusinessAPIView(UpdateAPIView):
    """
    Class for updating service vendor contact details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ServiceBusinessSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateServiceBusinessAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        service_id = self.kwargs["pk"]
        return VendorService.objects.filter(id=service_id)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.business_name = request.data.get("business_name")

        service_serializer = self.get_serializer(instance, data=request.data)
        if service_serializer.is_valid(raise_exception=True):
            self.partial_update(service_serializer)
            self.response_format["data"] = service_serializer.data

        return Response(self.response_format)


class GetServicePricingListView(ListAPIView):
    """
    Class for creating API view for getting vendor service contact details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ServicePricingSerializers

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorPricing.objects.none()

    def get(self, request, *args, **kwargs):
        """
        Function for getting vendor service contact details.
        """
        paginator = PageNumberPagination()
        paginator.page_size = 10
        vendor_service_id = self.kwargs["vendor_service_id"]
        vendor_service_pricing_list = VendorPricing.objects.filter(
            vendor_service_id=vendor_service_id
        )

        vendor_service_pricing_serialized = self.get_serializer(
            vendor_service_pricing_list, many=True
        )
        data = vendor_service_pricing_serialized.data

        result_projects = paginator.paginate_queryset(data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects)


class UpdateServicePriceAPIView(UpdateAPIView):
    """
    Class for updating service vendor contact details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ServicePricingSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateServicePriceAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorPricing.objects.none()
        service_price_id = self.kwargs["pk"]
        return VendorPricing.objects.filter(id=service_price_id)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.package_name = request.data.get("package_name")
        instance.package_details = request.data.get("package_details")
        instance.actual_price = request.data.get("actual_price")
        instance.vendor_service_id_id = request.data.get("vendor_service_id")
        instance.discounted_price = request.data.get("discounted_price")

        service_price_serializer = self.get_serializer(instance, data=request.data)
        if service_price_serializer.is_valid(raise_exception=True):
            self.partial_update(service_price_serializer)
            self.response_format["data"] = service_price_serializer.data

        return Response(self.response_format)


class UpdateServiceStatusAPIView(GenericAPIView):
    """
    Class for updating service vendor contact details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UpdateServiceStatusSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateServiceStatusAPIView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        service_id_list = request.data.get("vendor_service_ids")
        approval_status = request.data.get("approval_status")
        reject_reason = request.data.get("reject_reason", None)

        if approval_status == "R" or approval_status == "S":
            if reject_reason is None:
                self.response_format["message"] = messages.REJECT_REASON
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                return Response(
                    self.response_format, status=status.HTTP_400_BAD_REQUEST
                )

        for service_id in service_id_list:
            instance = VendorService.objects.filter(id=service_id).first()
            instance.approval_status = approval_status
            vendor_id = instance.vendor_id_id
            vendor_service_serializer = self.get_serializer(instance, data=request.data)
            if vendor_service_serializer.is_valid(raise_exception=True):
                vendor_service_serializer.save()
                if approval_status == "A":
                    CustomUser.objects.filter(id=instance.vendor_id_id).update(
                        status="ACTIVE"
                    )
                    v = VendorPlan.objects.create(
                        vendor_service_id=instance,
                        plan_status="ACTIVE",
                        starts_from=dt.now(),
                        ends_on=dt.now() + relativedelta(months=12),
                        subscription_type="SILVER",
                    )
                    instance.is_under_review = False
                    instance.save()
                    message = messages.SERVICE.format(
                        instance.business_name, messages.ACCEPTED
                    )
                    params = "{" + '"service_id": {}'.format(service_id) + "}"

                    notification_data = {
                        "message": message,
                        "status": "UR",
                        "user_id": vendor_id,
                        "notification_type": "SERVICE_APPROVAL",
                        "params": params,
                    }

                    req = NotificationSerializer(data=notification_data)
                    if req.is_valid(raise_exception=True):
                        req.save()

                    is_device = FCMDevice.objects.filter(user_id=vendor_id)
                    if is_device:
                        UserLoginAPIView.generate_fcm_token(
                            self, vendor_id, notification_data
                        )

                    # Send notifications to all users
                    message = "🚀 New Vendor Added! 🛒 Check out the latest addition to our marketplace. Tap to explore now!"
                    params = "{" + '"vendor_id": {}'.format(instance.id) + "}"
                    all_users = CustomUser.objects.filter(
                        role="USER", status="ACTIVE"
                    ).values_list("id", flat=True)
                    for user in all_users:
                        notification_data = {
                            "message": message,
                            "status": "UR",
                            "user_id": user,
                            "notification_type": "VENDOR_ADDED",
                            "params": params,
                        }
                        req = NotificationSerializer(data=notification_data)
                        if req.is_valid(raise_exception=True):
                            req.save()
                            is_device = FCMDevice.objects.filter(user_id=user)
                            if is_device:
                                UserLoginAPIView.generate_fcm_token(
                                    self, user, notification_data, True
                                )

                    user = CustomUser.objects.filter(id=instance.vendor_id_id).values(
                        "email", "fullname"
                    )
                    email = user[0]["email"]
                    template_id = constants.VENDOR_APPROVAL_TEMPLATE
                    data_dict = {
                        "user": instance.business_name,
                    }
                    send_email(template_id, email, data_dict)
                elif approval_status == "D":
                    instance.delete()
                elif approval_status == "S":
                    instance.is_under_review = False
                    instance.set_reject_reason(reject_reason)
                    instance.save()
                    message = messages.SERVICE.format(
                        instance.business_name, messages.SUSPENDED
                    )
                    params = json.dumps(
                        {"service_id": service_id, "reject_reason": reject_reason}
                    )

                    notification_data = {
                        "message": message,
                        "status": "UR",
                        "user_id": vendor_id,
                        "notification_type": "SERVICE_SUSPENDED",
                        "params": params,
                    }

                    req = NotificationSerializer(data=notification_data)
                    if req.is_valid(raise_exception=True):
                        req.save()

                    is_device = FCMDevice.objects.filter(user_id=vendor_id)
                    if is_device:
                        UserLoginAPIView.generate_fcm_token(
                            self, vendor_id, notification_data
                        )
                else:
                    instance.is_under_review = False
                    instance.set_reject_reason(reject_reason)
                    instance.save()

                    message = messages.SERVICE.format(
                        instance.business_name, messages.REJECTED
                    )
                    params = json.dumps(
                        {"service_id": service_id, "reject_reason": reject_reason}
                    )

                    notification_data = {
                        "message": message,
                        "status": "UR",
                        "user_id": vendor_id,
                        "notification_type": "SERVICE_REJECTED",
                        "params": params,
                    }

                    req = NotificationSerializer(data=notification_data)
                    if req.is_valid(raise_exception=True):
                        req.save()

                    is_device = FCMDevice.objects.filter(user_id=vendor_id)
                    if is_device:
                        UserLoginAPIView.generate_fcm_token(
                            self, vendor_id, notification_data
                        )

                    """
                    user = CustomUser.objects.filter(id=instance.vendor_id_id).values("email", "fullname")
                    email = user[0]['email']
                    template_id = "d-1bcc459726ec4cf2b8b948c623a96f0a"
                    sender = DEFAULT_FROM_EMAIL
                    data_dict = {"user_name": user[0]['fullname'], "service_name": instance.business_name}
                    ForgotPasswordRequestView.send_mail(self, template_id, sender, email, data_dict)
                    """

                self.response_format["data"] = vendor_service_serializer.data

        return Response(self.response_format)


class UpdateServiceWaveOffAPIView(UpdateAPIView):
    """
    Class for updating service vendor contact details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UpdateServiceWaveOffSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateServiceWaveOffAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        service_id = self.kwargs["pk"]
        return VendorService.objects.filter(id=service_id)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_waved_off = True

        service_serializer = self.get_serializer(instance, data=request.data)
        if service_serializer.is_valid(raise_exception=True):
            vendor_service = self.partial_update(service_serializer)
            current_time = datetime.datetime.now()
            two_years_later_time = datetime.datetime.now() + relativedelta(years=2)
            data = [
                {
                    "vendor_service_id": vendor_service.data["id"],
                    "plan_id": request.data["plan_id"],
                    "starts_from": current_time,
                    "ends_on": two_years_later_time,
                    "plan_status": "ACTIVE",
                }
            ]
            plan_serializer = VendorPlanSerializer(data=data, many=True)
            if plan_serializer.is_valid(raise_exception=True):
                plan_serializer.save()
            self.response_format["data"] = service_serializer.data

        return Response(self.response_format)


class GetDashboardDetailsAPIView(ListAPIView):
    """
    Class for creating API view for getting project list.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ServiceDetailsSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetDashboardDetailsAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()

    def get(self, request):
        data = list()
        total_vendor_services = VendorService.objects.filter(
            approval_status="A"
        ).count()
        total_users = CustomUser.objects.filter(role="USER").count()
        vendor_services_list = list()
        services = Service.objects.filter(is_included=True).order_by("service_type")

        year = datetime.date.today().year
        current = datetime.date.today()
        start_week = current - datetime.timedelta(current.weekday())
        end_week = start_week + datetime.timedelta(7)
        entries = CustomUser.objects.filter(
            date_joined__range=[start_week, end_week]
        ).values_list("date_joined", flat=True)
        day_list = []
        temp = []
        day_data = []
        for e in entries:
            try:
                new_start_time = dt.strptime(
                    str(e).split("+")[0], "%Y-%m-%d %H:%M:%S.%f"
                )
            except:
                e = str(e) + ".4"
                new_start_time = dt.strptime(
                    str(e).split("+")[0], "%Y-%m-%d %H:%M:%S.%f"
                )
            day_list.append(new_start_time.strftime("%A"))
            day_data.append(new_start_time)
        vendor_year_list = []
        vendor_month_list = []
        vendor_week_list = []

        user_year_list = []
        user_month_list = []
        user_week_list = []
        user_week = list()

        vendor_year = (
            CustomUser.objects.filter(role="VENDOR")
            .annotate(year=TruncYear("date_joined"))
            .values("year")
            .annotate(c=Count("date_joined"))
        )

        vendor_month = (
            CustomUser.objects.filter(role="VENDOR")
            .annotate(month=TruncMonth("date_joined"))
            .filter(date_joined__year=year)
            .values("month")
            .annotate(c=Count("date_joined"))
        )

        for i in day_data:
            new_i = dt.strptime(str(i).split("+")[0], "%Y-%m-%d %H:%M:%S.%f")
            count = (
                CustomUser.objects.filter(role="VENDOR")
                .filter(date_joined__day=new_i.strftime("%d"))
                .count()
            )
            case = {str(i.strftime("%A")): count}
            vendor_week_list.append(case)

        for i in vendor_year:
            case = {i.get("year").year: i.get("c")}
            vendor_year_list.append(case)
        for i in vendor_month:
            new_i = dt.strptime(str(i.get("month").month), "%m")
            case = {new_i.strftime("%B"): i.get("c")}

            vendor_month_list.append(case)
        [temp.append(x) for x in vendor_week_list if x not in temp]

        user_year = (
            CustomUser.objects.filter(role="USER")
            .annotate(year=TruncYear("date_joined"))
            .values("year")
            .annotate(c=Count("date_joined"))
        )

        user_month = (
            CustomUser.objects.filter(role="USER")
            .annotate(month=TruncMonth("date_joined"))
            .filter(date_joined__year=year)
            .values("month")
            .annotate(c=Count("date_joined"))
        )

        for i in day_data:
            new_i = dt.strptime(str(i).split("+")[0], "%Y-%m-%d %H:%M:%S.%f")
            count = (
                CustomUser.objects.filter(role="USER")
                .filter(date_joined__day=new_i.strftime("%d"))
                .count()
            )
            case = {str(i.strftime("%A")): count}
            user_week_list.append(case)

        for i in user_year:
            case = {i.get("year").year: i.get("c")}
            user_year_list.append(case)
        for i in user_month:
            new_i = dt.strptime(str(i.get("month").month), "%m")
            case = {new_i.strftime("%B"): i.get("c")}

            user_month_list.append(case)
        [user_week.append(x) for x in user_week_list if x not in temp]

        # for service in services:
        #     vendor_services = VendorService.objects.filter(service_id_id=service.id, approval_status='A').count()
        #     service_data = {
        #         "service_id": service.id,
        #         "service_type": service.service_type,
        #         "service_icon": service.service_icons_web,
        #         "count": vendor_services
        #     }
        #     vendor_services_list.append(service_data)

        for service in services:
            vendor_count = (
                VendorService.objects.filter(
                    service_id_id=service.id, approval_status="A"
                )
                .distinct()
                .count()
            )
            service_data = {
                "service_id": service.id,
                "service_type": service.service_type,
                "service_icon": service.service_icons_web,
                "count": vendor_count,
            }
            vendor_services_list.append(service_data)

        data.append(
            {
                "total_vendor_services": total_vendor_services,
                "total_users": total_users,
                "vendor_service_count": vendor_services_list,
                "vendor_week_data": temp,
                "vendor_month_data": vendor_month_list,
                "vendor_year_data": vendor_year_list,
                "user_week_data": user_week,
                "user_month_data": user_month_list,
                "user_year_data": user_year_list,
            }
        )
        self.response_format["data"] = data
        return Response(self.response_format)


class GetVendorDashboardDetailsAPIView(ListAPIView):
    """
    Class for creating API view for getting project list.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ServiceDetailsSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetVendorDashboardDetailsAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()

    def get(self, request, *args, **kwargs):
        data = list()
        # vendor_services = VendorService.objects.filter(approval_status="A").filter(
        #     vendor_id=request.user.id).values("id", "business_name")

        # vendor_services = VendorService.objects.filter(approval_status="A").filter(
        #     vendor_id=request.user.id).filter(payment_status='PAID').values("id", "business_name")

        vendor_services = (
            VendorService.objects.filter(approval_status="A", vendor_id=request.user.id)
            .filter(Q(payment_status="PAID") | Q(is_waved_off=True))
            .values("id", "business_name")
        )
        for service in vendor_services:
            s_id = service["id"]
            views = (
                VendorServiceViewLike.objects.filter(vendor_service_id=s_id)
                .filter(is_viewed=True)
                .count()
            )
            ongoing = (
                Enquiry.objects.filter(enquiry_status="ONGOING")
                .filter(vendor_service_id=s_id)
                .count()
            )
            completed = (
                Enquiry.objects.filter(enquiry_status="COMPLETED")
                .filter(vendor_service_id=s_id)
                .count()
            )
            ignored = (
                Enquiry.objects.filter(enquiry_status="IGNORED")
                .filter(vendor_service_id=s_id)
                .count()
            )
            data.append(
                {
                    "vendor_service_id": s_id,
                    "business_name": service["business_name"],
                    "service_views": views,
                    "ongoing_deals": ongoing,
                    "completed_deals": completed,
                    "ignored_deals": ignored,
                }
            )
        self.response_format["data"] = data
        return Response(self.response_format)


class GetServiceViewLikeAPIView(GenericAPIView):
    """
    Class for creating API view for getting vendor service.
    """

    permission_classes = ()
    authentication_classes = ()
    serializer_class = ServiceViewLikeSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetServiceViewLikeAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorServiceViewLike.objects.none()

    def post(self, request, *args, **kwargs):
        """
        Function for getting service views and likes.
        """
        data = list()
        user_id = request.data["user_id"]
        vendor_service_id = self.kwargs["pk"]
        vendor_service_like_count = (
            VendorServiceViewLike.objects.filter(vendor_service_id=vendor_service_id)
            .filter(is_liked=True)
            .count()
        )
        vendor_service_view_count = (
            VendorServiceViewLike.objects.filter(vendor_service_id=vendor_service_id)
            .filter(is_viewed=True)
            .count()
        )
        user_liked = False
        is_liked = (
            VendorServiceViewLike.objects.filter(vendor_service_id=vendor_service_id)
            .filter(user_id=user_id)
            .filter(is_liked=True)
        )
        if user_id and is_liked:
            user_liked = True
        data.append(
            {
                "service_likes": vendor_service_like_count,
                "service_views": vendor_service_view_count,
                "service_liked_by_user": user_liked,
            }
        )

        self.response_format["data"] = data
        return Response(self.response_format)


class UpdateServiceViewLikeAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = UpdateServiceViewLikeSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateServiceViewLikeAPIView, self).__init__(**kwargs)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            vendor = VendorService.objects.get(id=request.data.get("vendor_service_id"))
            track_action(request, vendor, TrackingAction.LIKED)
            if request.data.get("is_liked"):
                track_user_action(request, vendor, "liked")
                message = messages.SERVICE_LIKE_BY_USER.format(
                    vendor.business_name, request.user.fullname
                )
                params = json.dumps({"service_id": vendor.id})
                notification_data = {
                    "message": message,
                    "status": "UR",
                    "user_id": vendor.vendor_id_id,
                    "notification_type": "SERVICE_LIKED",
                    "params": params,
                }
                req = NotificationSerializer(data=notification_data)
                if req.is_valid(raise_exception=True):
                    req.save()
                    is_device = FCMDevice.objects.filter(user_id=request.user.id)
                    if is_device:
                        UserLoginAPIView.generate_fcm_token(
                            self,
                            vendor.vendor_id_id,
                            notification_data,
                        )

        self.response_format["data"] = None
        self.response_format["error"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = "Success."
        return Response(self.response_format)


class AddVendorServiceOfferAPIView(GenericAPIView):
    """
    Class for creating API view for getting vendor service.
    """

    permission_classes = (IsAuthenticated, IsTokenValid, IsPlatinumUser)
    authentication_classes = (JWTAuthentication,)
    serializer_class = VendorServiceOfferSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddVendorServiceOfferAPIView, self).__init__(**kwargs)

    def post(self, request):
        """
        Function for creating new service offer.
        Authorization Header required.
        """
        serialized = self.get_serializer(data=request.data)

        if serialized.is_valid(raise_exception=True):
            serialized.save()
            self.response_format["data"] = serialized.data
            self.response_format["message"] = ["Service Offer added successfully."]
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = serialized.errors
            self.response_format["message"] = ["Failure."]
            return Response(self.response_format)


class GetVendorOfferListView(ListAPIView):
    """
    Class for creating API view for getting vendor offers.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = VendorServiceOfferSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetVendorOfferListView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the services offered by vendor.
        """
        if getattr(self, "swagger_fake_view", False):
            return VendorServiceOffer.objects.none()
        vendor_id = self.request.user
        vendor_service_ids = VendorService.objects.filter(vendor_id=vendor_id).filter(
            approval_status="A"
        )
        return VendorServiceOffer.objects.filter(
            vendor_service_id__in=vendor_service_ids
        )

    def get(self, request, *args, **kwargs):
        """
        Function for getting vendor offer list.
        """
        serialized = super().list(request, *args, **kwargs)

        self.response_format["data"] = serialized.data
        return Response(self.response_format)


class GetVendorServiceOfferAPIView(ListAPIView):
    """
    Class for creating API view for getting vendor service offer.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = VendorServiceOfferSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetVendorServiceOfferAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the services offered by vendor.
        """
        if getattr(self, "swagger_fake_view", False):
            return VendorServiceOffer.objects.none()
        return VendorServiceOffer.objects.filter(vendor_service_id=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        """
        Function for getting vendor service offer.
        """
        serialized = super().list(request, *args, **kwargs)

        self.response_format["data"] = serialized.data
        return Response(self.response_format)


class GetServicesForOfferListView(ListAPIView):
    """
    Class for creating API view for getting vendor service offer.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = PlatinumServiceOfferSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetServicesForOfferListView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the services offered by vendor.
        """
        vendor_id = self.request.user.id
        platinum_plan = VendorPlan.objects.filter(
            vendor_service_id__vendor_id=vendor_id,
            plan_status="ACTIVE",
            subscription_type="PLATINUM",
        ).values_list("vendor_service_id", flat=True)
        vendor_service_ids = list(platinum_plan)
        return VendorService.objects.filter(id__in=vendor_service_ids)

    def get(self, request, *args, **kwargs):
        """
        Function for getting vendor service offer.
        """
        data = list()
        serialized = super().list(request, *args, **kwargs)
        for value in serialized.data:
            image_url = None
            start_date = None
            end_date = None
            percentage = None
            offer = VendorServiceOffer.objects.filter(
                vendor_service_id_id=value["id"]
            ).values("image_url", "start_date", "end_date", "percentage")
            if offer:
                image_url = offer[0]["image_url"]
                start_date = offer[0]["start_date"]
                end_date = offer[0]["end_date"]
                percentage = offer[0]["percentage"]
            data.append(
                {
                    "vendor_service_id": value["id"],
                    "business_name": value["business_name"],
                    "image_url": image_url,
                    "start_date": start_date,
                    "end_date": end_date,
                    "percentage": percentage,
                }
            )

        self.response_format["data"] = data
        return Response(self.response_format)


class AddCartItemAPIView(GenericAPIView):
    """
    Class for creating API view for adding items to user cart.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = AddCartItemSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddCartItemAPIView, self).__init__(**kwargs)

    def post(self, request):
        """
        Function for creating new cart items.
        Authorization Header required.
        """
        request.data["user_id"] = request.user.id
        vendor_service_id = request.data.get("vendor_service_id")
        serialized = self.get_serializer(data=request.data)

        if serialized.is_valid(raise_exception=True):
            cart = serialized.save()
            # vendor_service_id = serialized.data['vendor_service_id']
            vendor_service = VendorService.objects.get(id=vendor_service_id)
            track_user_action(request, vendor_service, "added_to_cart")
            service = VendorService.objects.filter(id=vendor_service_id).values(
                "business_name",
                "vendor_id__fullname",
                "vendor_id__email",
                "vendor_id__contact_number",
                "business_image",
            )
            # print(service)
            # plan_type = VendorPlan.objects.filter(vendor_service_id_id=vendor_service_id).first().subscription_type
            # vendor_plan = VendorPlan.objects.filter(vendor_service_id=vendor_service_id).values(
            #     "plan_id_id__subscription_type")
            # subscription_type = vendor_plan[0]["plan_id_id__subscription_type"]
            # if subscription_type == "PLATINUM":
            vendor_name = service[0]["vendor_id__fullname"]
            business_name = service[0]["business_name"]
            business_image = service[0]["business_image"]
            email = service[0]["vendor_id__email"]
            contact_number = service[0]["vendor_id__contact_number"]
            user = request.user
            template_id = constants.VENDOR_ADDED_TO_CART_TEMPLATE
            data_dict = {
                "vendor_name": vendor_name,
                "service_name": business_name,
                "user_name": user.fullname,
                "user_email": user.email,
                "user_phone": user.contact_number,
            }
            if email:
                send_email(template_id, email, data_dict)

            user_data = {
                "user": user.fullname,
                "service_name": business_name,
                "price": str(cart.total_cart_value),
                "service_img": business_image,
                "cart_url": user.cart_url,
            }
            if user.email:
                send_email(constants.USER_ADS_SERVICE_TO_CART, user.email, user_data)

            if contact_number:
                # send sms
                try:
                    message = messages.VEND_REC_ON_USER_ADD_SERV_CART.format(
                        business_name,
                    )
                    resp = send_sms(
                        config("TEXT_LOCAL_API_KEY"),
                        contact_number,
                        "OPPVNZ",
                        message,
                    )
                except Exception as e:
                    print("Error", e)

            if request.user.contact_number:
                try:
                    message = constants.USER_ADD_SERVICE_CART
                    resp = send_sms(
                        config("TEXT_LOCAL_API_KEY"),
                        request.user.contact_number,
                        "OPPVNZ",
                        message,
                    )
                    print(resp)
                except Exception as e:
                    print("Error", e)

            """
            vendor_plan = VendorPlan.objects.filter(vendor_service_id=vendor_service_id).values(
                "plan_id_id__subscription_type")
            subscription_type = vendor_plan[0]["plan_id_id__subscription_type"]
            if subscription_type == "PLATINUM":
                vendor_name = service[0]['vendor_id__fullname']
                business_name = service[0]['business_name']
                email = service[0]['vendor_id__email']
                user = request.user
                template_id = "d-29b21a5af7d84f2b8b948c623a96f0a"
                sender = DEFAULT_FROM_EMAIL
                data_dict = {"vendor_name": vendor_name, "service_name": business_name, "user_name": user.fullname,
                             "user_email": user.email, "user_phone": user.contact_number}

                 New Template ID
                template_id = "d-afad66169b4641988665b0e82dde62a4"
                sender = DEFAULT_FROM_EMAIL
                data_dict = {"vendor_name": vendor_name, "service_name": business_name, "user_name": user.fullname,
                             "user_email": user.email, "user_phone": user.contact_number}

                ForgotPasswordRequestView.send_mail(self, template_id, sender, email, data_dict)
            """

            self.response_format["data"] = serialized.data
            self.response_format["message"] = "Cart item added successfully."
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = serialized.errors
            self.response_format["message"] = "Failure."
            return Response(self.response_format)


class GetUserCartListView(ListAPIView):
    """
    Class for creating API view for getting user cart list.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = CartItemSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetUserCartListView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the services offered by vendor.
        """
        if getattr(self, "swagger_fake_view", False):
            return Cart.objects.none()
        return Cart.objects.filter(user_id=self.kwargs["user_id"]).order_by(
            "-updated_at"
        )

    def get(self, request, *args, **kwargs):
        """
        Function for getting vendor service offer.
        """
        users = CustomUser.objects.filter(id=self.kwargs["user_id"])
        host = request.get_host()
        if users.exists():
            update_user_cart_url(users.first(), host=host)
        serialized = super().list(request, *args, **kwargs)

        self.response_format["data"] = serialized.data
        return Response(self.response_format)


class DeleteCartItemAPIView(DestroyAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = CartItemSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(DeleteCartItemAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Cart.objects.none()

    def delete(self, request, *args, **kwargs):
        instance = Cart.objects.filter(id=self.kwargs["pk"])
        self.perform_destroy(instance)

        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_204_NO_CONTENT
        self.response_format["error"] = None
        self.response_format["message"] = messages.DELETE.format("Item")
        return Response(self.response_format)


class UpdateUserCartUrlAPIView(GenericAPIView):
    """
    Class for adding service details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = UserCartUrlSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateUserCartUrlAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CustomUser.objects.none()
        user_id = self.kwargs["pk"]
        return CustomUser.objects.filter(id=user_id)

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        host = request.get_host()
        update_user_cart_url(instance, host)
        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            self.response_format["data"] = serializer.data

        return Response(self.response_format)


class GetApprovedServiceListView(ListAPIView, CSVDownloadMixin):
    """
    Class for creating API view for getting vendor service.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = GetApprovedServiceSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetApprovedServiceListView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the services offered by vendor.
        """
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        user_id = self.request.user
        return VendorService.objects.filter(vendor_id=user_id).filter(
            approval_status="A"
        )

    def get(self, request, *args, **kwargs):
        """
        Function for getting vendor approved services list.
        """
        if request.GET.get("download") == "csv":
            return self.download_csv(self.get_queryset())

        serialized = super().list(request, *args, **kwargs)
        self.response_format["data"] = serialized.data
        return Response(self.response_format)


class GenerateReportAPIView(ListAPIView):
    """
    Class for creating API view for getting vendor service.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ServiceReportDetailsSerializers
    filter_backends = (DjangoFilterBackend,)
    filter_class = ReportFilter

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GenerateReportAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the services offered by vendor.
        """
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        all_service = VendorService.objects.all()
        city = self.request.data.get("city", None)
        service = self.request.data["service"]
        if city:
            return all_service.filter(city=city, service_id__service_type=service)

        return all_service.filter(service_id__service_type=service)

    def post(self, request, *args, **kwargs):
        """
        Function for getting vendor approved services list.
        """
        serialized = super().list(request, *args, **kwargs)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="OppvenuzReports.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Vendor Name",
                "Business Name",
                "Vendor Email",
                "Vendor Contact Number",
                "Service Type",
                "User Group Service Type",
                "Area",
                "City",
                "State",
                "Pin-Code",
                "Subscription Type",
                "status",
            ]
        )
        for row in serialized.data:
            writer.writerow(
                [
                    row["vendor_name"],
                    row["business_name"],
                    row["email"],
                    row["contact"],
                    row["service_type"],
                    row["user_group_service_type"],
                    row["area"],
                    row["city"],
                    row["state"],
                    row["pin_code"],
                    row["subscription_type"],
                    row["service_status"],
                ]
            )

        return response


class GenerateLikeReportAPIView(ListAPIView):
    """
    API view for generating a vendor service report ordered by likes.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = VendorServiceLikeReportSerializer

    def get_queryset(self):
        start = int(self.request.data.get("start", 0))
        end = start + 1000
        service_type = self.request.data.get("service", None)
        city = self.request.data.get("city", None)
        parameter = self.request.data.get("parameter", "Likes")

        filtered_services = VendorService.objects.all()
        if service_type:
            filtered_services = filtered_services.filter(
                service_id__service_type=service_type
            )
        if city:
            filtered_services = filtered_services.filter(city=city)

        if parameter == "All":
            annotated_services = filtered_services.annotate(
                like_count=Count(
                    "vendorserviceviewlike",
                    filter=Q(vendorserviceviewlike__is_liked=True),
                    distinct=True,
                ),
                favorite_count=Count("favorited_users", distinct=True),
                added_to_cart_count=Count(
                    "track_user_action",
                    filter=Q(track_user_action__action="added_to_cart"),
                    distinct=True,
                ),
                send_enquiry_count=Count(
                    "track_user_action",
                    filter=Q(track_user_action__action="send_enquiry"),
                    distinct=True,
                ),
                view_contact_count=Count(
                    "track_user_action",
                    filter=Q(track_user_action__action="view_contact"),
                    distinct=True,
                ),
            ).order_by("-like_count")
        elif parameter == "favorite":
            annotated_services = filtered_services.annotate(
                favorite_count=Count("favorited_users", distinct=True)
            ).order_by("-favorite_count")
        elif parameter == "added_to_cart":
            annotated_services = filtered_services.annotate(
                added_to_cart_count=Count(
                    "track_user_action",
                    filter=Q(track_user_action__action="added_to_cart"),
                    distinct=True,
                )
            ).order_by("-added_to_cart_count")
        elif parameter == "send_enquiry":
            annotated_services = filtered_services.annotate(
                send_enquiry_count=Count(
                    "track_user_action",
                    filter=Q(track_user_action__action="send_enquiry"),
                    distinct=True,
                )
            ).order_by("-send_enquiry_count")
        elif parameter == "view_contact":
            annotated_services = filtered_services.annotate(
                view_contact_count=Count(
                    "track_user_action",
                    filter=Q(track_user_action__action="view_contact"),
                    distinct=True,
                )
            ).order_by("-view_contact_count")
        else:
            annotated_services = filtered_services.annotate(
                like_count=Count(
                    "vendorserviceviewlike",
                    filter=Q(vendorserviceviewlike__is_liked=True),
                    distinct=True,
                )
            ).order_by("-like_count")

        return annotated_services[start:end]

    def post(self, request, *args, **kwargs):
        """
        Generates the CSV report with total row count and data from get_queryset().
        """
        service_type = request.data.get("service", None)
        city = request.data.get("city", None)
        start = int(request.data.get("start", 0))
        parameter = request.data.get("parameter", "Likes")

        filtered_services = VendorService.objects.all()
        if service_type:
            filtered_services = filtered_services.filter(
                service_id__service_type=service_type
            )
        if city:
            filtered_services = filtered_services.filter(city=city)

        total_count = filtered_services.count()

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        response = HttpResponse(content_type="text/csv")
        filename = "VendorLikeReports.csv"
        if parameter == "favorite":
            filename = "VendorFavoriteReports.csv"
        elif parameter == "added_to_cart":
            filename = "VendorAddedToCartReports.csv"
        elif parameter == "send_enquiry":
            filename = "VendorEnquiryReports.csv"
        elif parameter == "view_contact":
            filename = "VendorContactViewReports.csv"
        elif parameter == "All":
            filename = "VendorAllReports.csv"

        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)

        writer.writerow(["Total Rows", total_count])
        writer.writerow(["Showing Rows", start + 1, "to", start + len(serializer.data)])
        writer.writerow([])

        base_headers = [
            "Vendor Name",
            "Business Name",
            "Vendor Email",
            "Vendor Contact Number",
            "Area",
            "City",
            "State",
            "Pin-Code",
            "Service Type",
            "Subscription Type",
            "Status",
        ]
        if parameter == "favorite":
            headers = base_headers + ["Favorite Count"]
        elif parameter == "added_to_cart":
            headers = base_headers + ["Added To Cart Count"]
        elif parameter == "send_enquiry":
            headers = base_headers + ["Send Enquiry Count"]
        elif parameter == "view_contact":
            headers = base_headers + ["View Contact Count"]
        elif parameter == "All":
            headers = base_headers + [
                "Like Count",
                "Favorite Count",
                "Added To Cart Count",
                "Send Enquiry Count",
                "View Contact Count",
            ]
        else:
            headers = base_headers + ["Like Count"]

        writer.writerow(headers)

        for row in serializer.data:
            row_data = [
                row["vendor_name"],
                row["business_name"],
                row["email"],
                row["contact"],
                row["area"],
                row["city"],
                row["state"],
                row["pin_code"],
                row["service_type"],
                row["subscription_type"],
                row["service_status"],
            ]
            if parameter == "favorite":
                row_data.append(row["favorite_count"])
            elif parameter == "added_to_cart":
                row_data.append(row.get("added_to_cart_count", 0))
            elif parameter == "send_enquiry":
                row_data.append(row.get("send_enquiry_count", 0))
            elif parameter == "view_contact":
                row_data.append(row.get("view_contact_count", 0))
            elif parameter == "All":
                row_data += [
                    row.get("like_count", 0),
                    row.get("favorite_count", 0),
                    row.get("added_to_cart_count", 0),
                    row.get("send_enquiry_count", 0),
                    row.get("view_contact_count", 0),
                ]
            else:
                row_data.append(row["like_count"])
            writer.writerow(row_data)

        return response


class GenerateUserActivityReportAPIView(ListAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UserActivityReportSerializer

    def get_queryset(self):
        start = int(self.request.data.get("start", 0))
        end = start + 1000
        service_type = self.request.data.get("service", None)
        city = self.request.data.get("city", None)
        start_date_str = self.request.data.get("startDate")
        end_date_str = self.request.data.get("endDate")

        india_tz = timezone.pytz.timezone("Asia/Kolkata")

        default_now = timezone.now().astimezone(india_tz)
        default_start = default_now - timezone.timedelta(days=1)

        start_date_obj = parse_datetime(start_date_str)
        if start_date_obj is not None:
            if not timezone.is_aware(start_date_obj):
                start_date_obj = timezone.make_aware(start_date_obj, india_tz)
            start_date_obj = start_date_obj.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            date_part = parse_date(start_date_str)
            if date_part:
                start_date_obj = datetime.datetime.combine(date_part, datetime.time.min)
                start_date_obj = india_tz.localize(start_date_obj)
            else:
                start_date_obj = default_start

        end_date_obj = parse_datetime(end_date_str)
        if end_date_obj is not None:
            if not timezone.is_aware(end_date_obj):
                end_date_obj = timezone.make_aware(end_date_obj, india_tz)
            end_date_obj = end_date_obj.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
        else:
            date_part = parse_date(end_date_str)
            if date_part:
                end_date_obj = datetime.datetime.combine(date_part, datetime.time.max)
                end_date_obj = india_tz.localize(end_date_obj)
            else:
                end_date_obj = default_now

        qs = TrackUserAction.objects.filter(
            created_at__range=(start_date_obj, end_date_obj)
        )
        if service_type:
            qs = qs.filter(vendor__service_id__service_type=service_type)
        if city:
            qs = qs.filter(vendor__city=city)
        return qs.order_by("-created_at")[start:end]

    def post(self, request, *args, **kwargs):
        start = int(request.data.get("start", 0))
        queryset = self.get_queryset()
        total_count = self.get_queryset().count()
        serializer = self.get_serializer(queryset, many=True)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="UserActivityReport.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(["Total Rows", total_count])
        writer.writerow(["Showing Rows", start + 1, "to", start + len(serializer.data)])
        writer.writerow([])

        headers = [
            "Username",
            "Mobile",
            "Email",
            "Vendor Name",
            "Vendor City",
            "Action",
            "Action Date",
        ]
        writer.writerow(headers)

        for record in serializer.data:
            writer.writerow(
                [
                    record["username"],
                    record["mobile"],
                    record["email"],
                    record["vendor_name"],
                    record["vendor_city"],
                    record["action"],
                    record["action_date"],
                ]
            )

        return response


class GenerateUserSessionReportAPIView(ListAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UserSessionReportSerializer

    def get_queryset(self):
        start = int(self.request.data.get("start", 0))
        end = start + 1000
        city_filter = self.request.data.get("city", None)
        start_date_str = self.request.data.get("startDate")
        end_date_str = self.request.data.get("endDate")

        india_tz = timezone.pytz.timezone("Asia/Kolkata")
        default_now = timezone.now().astimezone(india_tz)
        default_start = default_now - timezone.timedelta(days=1)

        # Parse start date
        start_date_obj = parse_datetime(start_date_str)
        if start_date_obj is not None:
            if not timezone.is_aware(start_date_obj):
                start_date_obj = timezone.make_aware(start_date_obj, india_tz)
            start_date_obj = start_date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            date_part = parse_date(start_date_str)
            if date_part:
                start_date_obj = datetime.datetime.combine(date_part, datetime.time.min)
                start_date_obj = india_tz.localize(start_date_obj)
            else:
                start_date_obj = default_start

        # Parse end date
        end_date_obj = parse_datetime(end_date_str)
        if end_date_obj is not None:
            if not timezone.is_aware(end_date_obj):
                end_date_obj = timezone.make_aware(end_date_obj, india_tz)
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            date_part = parse_date(end_date_str)
            if date_part:
                end_date_obj = datetime.datetime.combine(date_part, datetime.time.max)
                end_date_obj = india_tz.localize(end_date_obj)
            else:
                end_date_obj = default_now

        qs = TrackUserSession.objects.filter(time__range=(start_date_obj, end_date_obj))
        if city_filter:
            qs = qs.filter(city=city_filter)
        return qs.order_by("-time")[start:end]

    def post(self, request, *args, **kwargs):
        start = int(request.data.get("start", 0))
        queryset = self.get_queryset()
        total_count = self.get_queryset().count()
        serializer = self.get_serializer(queryset, many=True)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="UserSessionReport.csv"'

        writer = csv.writer(response)
        writer.writerow(["Total Rows", total_count])
        writer.writerow(["Showing Rows", start + 1, "to", start + len(serializer.data)])
        writer.writerow([])

        headers = ["Name", "Email", "Mobile", "Address", "Action", "City", "Time"]
        writer.writerow(headers)

        for record in serializer.data:
            writer.writerow([
                record["username"],
                record["email"],
                record["mobile"],
                record["address"],
                record["action"],
                record["city"],
                record["session_time"],
            ])

        return response


class UpdateOfferDetailsAPIView(UpdateAPIView):
    """
    Class for updating service vendor contact details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UpdateServiceOfferSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateOfferDetailsAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorServiceOffer.objects.none()
        service_offer_id = self.kwargs["pk"]
        return VendorServiceOffer.objects.filter(vendor_service_id=service_offer_id)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.image_url = request.data.get("image_url")
        instance.start_date = request.data.get("start_date")
        instance.end_date = request.data.get("end_date")
        instance.percentage = request.data.get("percentage")
        instance.vendor_service_id_id = self.kwargs["pk"]

        service_offer_serializer = self.get_serializer(instance, data=request.data)
        if service_offer_serializer.is_valid(raise_exception=True):
            self.partial_update(service_offer_serializer)
            self.response_format["data"] = service_offer_serializer.data
            self.response_format["message"] = messages.UPDATE.format("Service offer")
        return Response(self.response_format)


class SuperAdminVendorListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = SuperAdminVendorSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ("fullname",)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(SuperAdminVendorListAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CustomUser.objects.none()
        user_type = self.request.user.role
        if user_type == "SUPER_ADMIN":
            all_vendor_list = CustomUser.objects.filter(role=VENDOR).order_by(
                "-date_joined"
            )
            city = self.request.data.get("city", None)
            if city:
                all_vendor_list = all_vendor_list.filter(address=city)
        return all_vendor_list

    def post(self, request, *args, **kwargs):
        paginator = PageNumberPagination()
        paginator.page_size = 10
        all_user = super().list(request, *args, **kwargs)
        result_projects = paginator.paginate_queryset(all_user.data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects)


class SearchVendorAPIView(ListAPIView, CSVDownloadMixin):
    serializer_class = SuperAdminServiceDetailsSerializers
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = ServiceFilter
    pagination_class = PageNumberPagination
    pagination_class.page_size = 20
    search_fields = ["business_name"]

    def get_queryset(self):
        return VendorService.objects.all().order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if request.GET.get("download") == "csv":
            fields = [
                "business_name",
                "service_type",
                "city",
                "state",
                "vendor_contact",
                "created_at",
                "approval_status",
                "vendor_email",
            ]
            return self.download_csv(request, queryset, self.serializer_class, fields)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# class GetSuperAdminVendorServiceDetailList(ListAPIView, CSVDownloadMixin):
#     serializer_class = ServiceByTypeSerializer
#     permission_classes = (IsAuthenticated,)
#     authentication_classes = (OAuth2Authentication, JWTAuthentication)
#     pagination_class = CustomPagination
#     filter_backends = (SearchFilter, DjangoFilterBackend)
#     search_fields = ("business_name", "area", "city", "state")
#     filterset_class = ServiceFilter

#     def __init__(self, **kwargs):
#         """
#         Constructor function for formatting the web response to return.
#         """
#         self.response_format = ResponseInfo().response
#         super(GetSuperAdminVendorServiceDetailList, self).__init__(**kwargs)

#     def get_queryset(self):
#         return (
#             VendorService.objects.select_related("service_id")
#             .filter(approval_status="A")
#             .distinct()
#         )

#     def get(self, request, *args, **kwargs):
#         queryset = self.filter_queryset(self.get_queryset())

#         if request.GET.get("download") == "csv":
#             return self.download_csv(request, queryset, self.serializer_class)

#         page = self.paginate_queryset(queryset)
#         if page is not None:
#             serializer = self.get_serializer(page, many=True)
#             return self.get_paginated_response(serializer.data)

#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data)


class GetSuperAdminVendorServiceDetailList(ListAPIView, CSVDownloadMixin):
    """
    Class for creating API view for getting vendor service details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = SuperAdminServiceDetailsSerializers
    filter_backends = (DjangoFilterBackend,)
    filter_class = CustomRecordFilter
    pagination_class = PageNumberPagination
    pagination_class.page_size = 20

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorService.objects.none()
        approval_status = self.request.query_params.get("approval_status")
        status_data = self.request.query_params.get("status")

        if approval_status:
            queryset = VendorService.objects.filter(approval_status=approval_status)
        elif status_data:
            queryset = (
                VendorService.objects.filter(approval_status=status_data)
                .exclude(business_name=None)
                .select_related("vendor_id")
                .order_by("-updated_at")
            )
        else:
            queryset = (
                VendorService.objects.filter(approval_status__in=["P", "A"])
                .exclude(business_name=None)
                .select_related("vendor_id")
                .order_by("-updated_at")
            )
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if request.GET.get("download") == "csv":
            fields = [
                "business_name",
                "service_type",
                "city",
                "state",
                "vendor_contact",
                "created_at",
                "approval_status",
                "vendor_email",
            ]
            return self.download_csv(request, queryset, self.serializer_class, fields)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SimilarServiceListAPI(ListAPIView):
    """
    Lists out similar services
    """

    authentication_classes = ()
    permission_classes = ()
    serializer_class = ServiceDetailsSerializers
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = CustomRecordFilter
    pagination_class = PageNumberPagination
    pagination_class.page_size = 10
    search_fields = ["business_name"]

    def get_queryset(self):
        vendorservice_id = self.kwargs.get("pk", None)
        city = self.request.query_params.get("city", None)
        instance = VendorService.objects.get(id=vendorservice_id)
        if city:
            queryset = VendorService.objects.get_similar_vendors(instance, city=city)
        else:
            queryset = VendorService.objects.get_similar_vendors(
                instance, city=instance.city
            )
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UpdateSlugForService(ListAPIView):
    serializer_class = GetServiceSerializers
    authentication_classes = ()
    permission_classes = ()

    def get_queryset(self):
        return Service.objects.all()

    def list(self, request, *args, **kwargs):
        for service in Service.objects.all():
            service.save()
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ServiceUpdateAPIView(UpdateAPIView, RetrieveAPIView):
    serializer_class = GetServiceSerializers
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    http_method_names = ("patch", "put", "get")

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(ServiceUpdateAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        # slugs = ['accessories-and-gift-store', 'doli-and-tent-rental', '']
        return Service.objects.filter(id=self.kwargs["pk"])

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_205_RESET_CONTENT
        self.response_format["error"] = None
        self.response_format["message"] = messages.UPDATE.format("Celebrity")
        return Response(self.response_format)


class VendorServiceOffersListAPI(ListAPIView):
    serializer_class = VendorServiceOfferSerializers
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ["vendor_service_id__business_name"]
    pagination_class = CustomPagination
    pagination_class.page_size = 10

    def get_queryset(self):
        today = datetime.datetime.now().date()
        queryset = VendorServiceOffer.objects.filter(end_date__gte=today)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class AllServicesView(APIView):
    def get(self, request):

        data = []

        top_categories = Category.objects.filter(parent=None)

        for top_cat in top_categories:
            subcategories = top_cat.children.all()

            subcategory_list = [
                {
                  "id": subcat.id,
                  "name": subcat.service_name
                }
                for subcat in subcategories
            ]

            data.append(
                {
                "id": top_cat.id,
                "category": top_cat.service_name,
                "subcategories": subcategory_list
            }
            )
        return Response({"data" : data, "message" : 'success'})
    
class SearchFilterAPIView(ListAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    filter_backends = (SearchFilter, DjangoFilterBackend)     
  
    VENDOR_CATEGORY = "vendor"
    VENUE_CATEGORY = "venue"
    category_serializer_map = {
        VENDOR_CATEGORY : ServiceByTypeSerializer,        
        VENUE_CATEGORY : ServiceByTypeSerializer,
        #!Todo Replace dummy serializer with actual category-specific serializer
        # 'gallary': ServiceByTypeSerializer,
        # 'blogs': ArticleSerializer,
        # "celebrity booking": ServiceByTypeSerializer,
        # 'e-invites': ServiceByTypeSerializer
        # Add more categories and serializers as needed
    }

    category_filterset_class_map = {
        VENDOR_CATEGORY : ServiceFilter,            
        VENUE_CATEGORY : ServiceFilter,
        #!Todo Replace dummy filter class with actual category-specific filterclass
        # 'gallary': ServiceFilter,
        # 'blogs': ServiceFilter,
        # "celebrity booking": ServiceFilter,
        # 'e-invites': ServiceFilter
        # Add more categories and filterset_class as needed
    }

    category_search_fields_map = {
        VENDOR_CATEGORY : ("business_name", "area", "city", "state"),  
        VENUE_CATEGORY : ("business_name", "area", "city", "state"),
        #!Todo Replace dummy search_fields with actual category-specific search_fields
        # 'gallary': ("business_name", "area", "city", "state"),
        # 'blogs': ( "title"),
        # 'celebrity booking': ("business_name", "area", "city", "state"),
        # 'e-invites': ("business_name", "area", "city", "state"),
        # Add more categories and search fields
    }
    def __init__(self, **kwargs):
        self.response_format = ResponseInfo().response
        super(SearchFilterAPIView, self).__init__(**kwargs)
    def get_queryset(self):
        return VendorService.objects.none()
    def get_serializer_for_category(self, category_name):
        return self.category_serializer_map.get(category_name)
    def get_filterset_class_for_category(self, category_name):
        return self.category_filterset_class_map.get(category_name)
    def get_search_fields_for_category(self, category_name):
        return self.category_search_fields_map.get(category_name, ())
    
    def get_category_queryset(self, category_name):
        try:
            if category_name == self.VENDOR_CATEGORY:
                base_queryset = VendorService.objects.select_related("service_id") \
                .filter(approval_status="A") \
                .exclude(service_id__service_type="Venue") \
                .distinct().order_by('id')
                return base_queryset
            
            elif category_name == self.VENUE_CATEGORY:
                base_queryset = VendorService.objects.select_related("service_id") \
                .filter(approval_status="A", service_id__service_type="Venue") \
                .distinct() \
                .order_by("id")
                return base_queryset
            else:
                logger.warning(f"Unrecognized category: {category_name}")
                return VendorService.objects.none()
        except Exception as e:
            logger.error(f"Error fetching queryset for category '{category_name}': {e}")
            return VendorService.objects.none()
        
    def get_category_data(self, request, category_name, category_id):
   
        self.search_fields = self.get_search_fields_for_category(category_name)
        queryset = self.get_category_queryset(category_name)

        self.filterset_class = self.get_filterset_class_for_category(category_name)
        filtered_queryset = self.filter_queryset(queryset)
        
        paginator = CustomPerCategoryPagination()
        return paginator.paginate_category(request, filtered_queryset, self, category_name, category_id)
    
    def get(self, request, *args, **kwargs):
        logger.info("Processing GET request in SearchFilterAPIView")
        try:
            category_id = int(request.GET.get('category')) if request.GET.get('category') else None
        except ValueError:
            logger.error("Invalid category ID in request. It must be an integer.")
            return Response(
                {"error": "Invalid category ID. It must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            subcategory_id = int(request.GET.get('subcategory')) if request.GET.get('subcategory') else None
        except ValueError:
            logger.error("Invalid subcategory ID in request. It must be an integer.")
            return Response(
                {"error": "Invalid subcategory ID. It must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not category_id:
            logger.error("Missing category ID in request")
            return Response({'error': 'Please provide category'}, status=status.HTTP_400_BAD_REQUEST)
      
        category_obj = Category.objects.filter(id=category_id, parent__isnull=True).first()
        if not category_obj:
            logger.error(f"Category ID {category_id} not found or invalid")
            return Response({'error': 'Invalid category'}, status=status.HTTP_400_BAD_REQUEST)
        category_name = category_obj.service_name.lower()

        if subcategory_id:
            if category_name == "all":
                subcategory_obj = Category.objects.filter(id=subcategory_id, parent__isnull=False).first()
            else:
                subcategory_obj = Category.objects.filter(id=subcategory_id, parent_id=category_id).first()

            if not subcategory_obj:
                logger.error(f"Invalid subcategory ID {subcategory_id} for category {category_id}")
                return Response({'error': 'Invalid sub category'}, status=status.HTTP_400_BAD_REQUEST)
   
        # Get a list of top-level categories in lowercase
        valid_categories = Category.objects.filter(parent__isnull=True).values_list('service_name', flat=True)
        valid_categories = [cat.lower() for cat in valid_categories]

        try:
            response_data = []
            if category_name == "all":
                for cat in valid_categories:
                    if cat in self.category_serializer_map:                       
                        category_obj = Category.objects.filter(service_name__iexact=cat, parent__isnull=True).first()
                        cat_data = self.get_category_data(request, cat, category_obj.id)
                        if cat_data:
                            response_data.append(cat_data)
                logger.info("Returning data for all categories")
                return Response(response_data)
            else:
                if category_name not in self.category_serializer_map:
                    logger.error(f"Category '{category_name}' not in serializer map")
                    return Response({'error': 'Invalid category'}, status=status.HTTP_400_BAD_REQUEST)

                cat_data = self.get_category_data(request, category_name, category_id)
                logger.info(f"Returning data for category: {category_name}")
                if cat_data:
                    return Response([cat_data])
                else:
                    return Response([])

        except Exception as e:
            logger.critical(f"Unexpected error in SearchFilterAPIView.get: {e}", exc_info=True)
            return Response({
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": str(e),
                "data": None,
                "message": "An error occurred while processing your request."
            })
               
class SuggestionView(APIView):
    def get(self, request):
        logger.info("Processing GET request in SuggestionView")
        text = request.query_params.get('text', '')
        category_id = request.query_params.get('category')
        subcategory_id = request.query_params.get('subcategory')

        if not category_id and not subcategory_id:
            logger.info("No category or subcategory provided, returning empty response.")
            return Response({'data': []}, status=status.HTTP_200_OK)

        if category_id:
            try:
                category_id = int(category_id)
                if category_id != 1 and not Category.objects.filter(id=category_id, parent__isnull=True).exists():
                    logger.error("Invalid category ID,Category ID not found in database.")
                    return Response(
                        {'error': f'Invalid category ID.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                logger.error("Invalid category ID. It must be a valid integer")
                return Response(
                    {'error': 'Invalid category ID.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if subcategory_id:
            try:
                subcategory_id = int(subcategory_id)
                if not Category.objects.filter(id=subcategory_id).exists():
                    logger.error(f"Invalid Subcategory with ID {subcategory_id} against provided category ID {category_id}")
                    return Response(
                        {'error': f'Invalid subcategory ID.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if category_id and category_id != 1:
                    if not Category.objects.filter(id=subcategory_id, parent_id=category_id).exists():
                        logger.error(f"Subcategory with ID {subcategory_id} does not belong to category ID {category_id}")
                        return Response(
                            {'error': f'Subcategory ID does not belong to category ID'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            except (ValueError, TypeError):
                logger.error("Invalid subcategory ID. It must be a valid integer")
                return Response(
                    {'error': 'Invalid subcategory ID.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        queryset = VendorService.objects.select_related('service_id').prefetch_related('venue_type').all()

        if text:
            queryset = queryset.filter(
                Q(business_name__icontains=text) |
                Q(service_id__service_type__icontains=text) |
                Q(venue_type__title__icontains=text)
            )

        if category_id and category_id != 1:
            subcategories = Category.objects.filter(parent_id=category_id).values_list('service_name', flat=True)
            parent_category = Category.objects.get(id=category_id)
            subcategory_names = list(subcategories) + [parent_category.service_name]
            queryset = queryset.filter(
                Q(service_id__service_type__in=subcategory_names) |
                Q(venue_type__title__in=subcategory_names)
            )

        if subcategory_id and category_id != 1:
            subcat = Category.objects.get(id=subcategory_id)
            parent_service_name = subcat.parent.service_name if subcat.parent else None
            queryset = queryset.filter(
                Q(service_id__service_type__iexact=subcat.service_name) |
                Q(venue_type__title__iexact=subcat.service_name) |
                (Q(service_id__service_type__iexact=parent_service_name) if parent_service_name else Q()) |
                (Q(venue_type__title__iexact=parent_service_name) if parent_service_name else Q())
            )

        service_types = {v.service_id.service_type for v in queryset}
        service_types.update(venue.title for v in queryset for venue in v.venue_type.all())
        category_map = {
            cat.service_name: cat
            for cat in Category.objects.filter(service_name__in=service_types).select_related('parent')
        }

        result = []
        for vendor in queryset:
            service_type = vendor.service_id.service_type
            venue_types = list(vendor.venue_type.all())

            for venue in venue_types or [None]:
                category_name = 'All'
                sub_category_name = venue.title if venue else service_type
                cat_obj = category_map.get(sub_category_name)
                if cat_obj:
                    category_name = cat_obj.parent.service_name if cat_obj.parent else cat_obj.service_name
                    sub_category_name = cat_obj.service_name
                result.append({
                    'id': vendor.id,
                    'name': vendor.business_name,
                    'category': category_name,
                    'sub_category': sub_category_name
                })

        if not result:
            logger.info("No matching services found for the given criteria.")
            return Response({'data': []}, status=status.HTTP_200_OK)
        
        logger.info("Successfully processed GET request in SuggestionView.")
        return Response({'data': result}, status=status.HTTP_200_OK)


class ServiceRegistrationChargesCreateAPIView(CreateAPIView):
    serializer_class = ServiceRegistrationChargesDetailSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid)
    http_method_names = ("post",)

    def __init__(self, **kwargs):
        self.response_format = ResponseInfo().response
        super(ServiceRegistrationChargesCreateAPIView, self).__init__(**kwargs)

    def create(self, request, *args, **kwargs):
        logger.info("POST request received for Service Registration Charges creation.")
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()  
            self.response_format["data"] = serializer.data
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["error"] = None
            self.response_format["message"] = messages.ADDED.format("Service Registration Charges")

            logger.info(f"Service Registration Charges created with ID: {instance.id}, by user: {instance.created_by}")
            return Response(self.response_format, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating Service Registration Charges: {str(e)}", exc_info=True)
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = str(e)
            self.response_format["message"] = "Failed to add Service Registration Charges"
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

class ServiceVendorRegistrationPayStatusView(CreateAPIView):
    queryset = ServiceVendorRegistrationCharges.objects.all()
    serializer_class = RegPaymentStatusSerializer
    authentication_classes = (JWTAuthentication,) 
    permission_classes = (IsAuthenticated,IsTokenValid)

    def perform_create(self, serializer):
        service_id = self.request.data.get("service_id")
        vendor_id  = self.request.data.get("vendor_id")

        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            logger.error(f"Service not found with id={service_id}")
            raise ValidationError({"service_id": "Service does not exist"})

        try:
            vendor = CustomUser.objects.get(id=vendor_id)
        except CustomUser.DoesNotExist:
            logger.error(f"Vendor not found with id={vendor_id}")
            raise ValidationError({"vendor_id": "Vendor does not exist"})

        email = self.request.user.email

        serializer.save(
            service_id=service,
            vendor_id=vendor,
            created_by=email,
            updated_by=email,
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)  
        return Response(
            {
                "message": "Payment added successfully.",
                "data":    response.data,
            },
            status=status.HTTP_201_CREATED,
        )
    
class GetServiceRegChargesView(ListAPIView):
    serializer_class = ServiceRegistrationChargesSerializer

    def get_queryset(self):
        service_id = self.request.query_params.get('service_id')

        if service_id:
            if not Service.objects.filter(id=service_id).exists():
                logger.warning("Service ID %s does not exist", service_id)
                raise NotFound("No such service exists")
            return ServiceRegistrationChargesDetail.objects.filter(service_id=service_id)

        return ServiceRegistrationChargesDetail.objects.all()
    
class VendorServicePendingPayStatusView(ListAPIView):
    serializer_class = VendorServicePendingPayStatusSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid)

    def get_queryset(self):
        vendor_id = self.request.query_params.get('vendor_id')

        if not vendor_id:
            logger.warning("vendor id is required")
            raise ValidationError({"error": "vendor_id is required"})
        
        try:
            vendor_id = int(vendor_id)
        except ValueError:
            logger.warning("vendor_id must be an integer")
            raise ValidationError({"error" : "vendor_id must be an integer"})
        
        if not CustomUser.objects.filter(id=vendor_id).exists():
            logger.error("vendor id does not exist")
            raise ValidationError({"error": "vendor id does not exist"})
        
        return ServiceVendorRegistrationCharges.objects.filter(vendor_id=vendor_id).distinct('service_id')
    
class serviceRegistrationStatusView(UpdateAPIView):
    serializer_class = ServiceRegistrationStatusSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    http_method_names = ("patch", "put")
    queryset = ServiceVendorRegistrationCharges.objects.all()

    def get_object(self):
        id = self.request.query_params.get("id")
        if id is None:
            raise ValidationError({"error": "id is required"})

        try:
            return self.queryset.get(pk=id)
        except ServiceVendorRegistrationCharges.DoesNotExist:
            logger.error("vendor_id does not exist")
            raise NotFound({"error": f"Record with id={id} not found"})
        
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user.email)

class ServiceRegistrationChargesDeleteAPIView(DestroyAPIView):
    """
    API to delete Service Registration Charges by ID.
    """
    queryset = ServiceRegistrationChargesDetail.objects.all()
    serializer_class = ServiceRegistrationChargesDetailSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsTokenValid]
    http_method_names = ["delete"]

    def __init__(self, **kwargs):
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)

    def destroy(self, request, *args, **kwargs):
        logger.info(f"DELETE request for ServiceRegistrationCharges with ID {kwargs.get('pk')}")
        try:
            instance = self.get_object()
            instance.delete()
            self.response_format.update({
                "data": {"id": kwargs["pk"]},
                "status_code": status.HTTP_200_OK,
                "error": None,
                "message": "Service Registration Charges deleted successfully.",
            })
            return Response(self.response_format, status=status.HTTP_200_OK)
        except ServiceRegistrationChargesDetail.DoesNotExist:
            self.response_format.update({
                "data": None,
                "status_code": status.HTTP_404_NOT_FOUND,
                "error": "Not Found",
                "message": "Service Registration Charges not found.",
            })
            return Response(self.response_format, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error deleting registration charges: {str(e)}", exc_info=True)
            self.response_format.update({
                "data": None,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": str(e),
                "message": "Failed to delete Service Registration Charges.",
            })
            return Response(self.response_format, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetVendorServicePaymentView(ListAPIView):
    serializer_class = GetVendorServicePaymentDetails
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)

    def get_queryset(self):
        queryset = ServiceVendorRegistrationCharges.objects.all()

        vendor_id = self.request.query_params.get('vendor_id')
        service_id = self.request.query_params.get('service_id')
        payment_status = self.request.query_params.get('payment_status')

        if vendor_id and not vendor_id.isdigit():
            logger.warning(f"invalid vendor id: {vendor_id}")
            return queryset.none()
        
        if service_id and not service_id.isdigit():
            logger.warning(f"invalid service id: {service_id}")
            return queryset.none()
        
        if payment_status and payment_status not in ['0', '1', '2', '3']:
            logger.warning(f"invalid payment status: {payment_status}")
            raise queryset.none()

        if vendor_id:
            queryset = ServiceVendorRegistrationCharges.objects.filter(vendor_id=vendor_id)

        if service_id:
            queryset = ServiceVendorRegistrationCharges.objects.filter(service_id=service_id)

        if payment_status:
            queryset = ServiceVendorRegistrationCharges.objects.filter(payment_status=payment_status)
    
        return queryset
