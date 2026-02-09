"""
This file is used for creating a view for the API,
which takes a web request and returns a web response.
"""

import os
import uuid
import time
import hashlib
import base64
import calendar
import datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from apscheduler.schedulers.background import BackgroundScheduler
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    UpdateAPIView,
    CreateAPIView,
    RetrieveAPIView,
)
from django.utils import timezone
from rest_framework.generics import (GenericAPIView,
                                     ListAPIView,
                                     UpdateAPIView,
                                     CreateAPIView,
                                     )

from utilities import messages
from utilities.commonutils import (
    verify_google_play,
    verify_apple_receipt,
    vendor_plan_status_update,
)
from .models import Plan, VendorPlan, SubscriptionPlan
from users.models import CustomUser
from service.models import VendorService
from .serializers import (
    VendorPlanSerializer,
    PricingPlanSerializer,
    UpdateVendorPlanSerializer,
    SubscriptionPlanSerializer,
    UpdatePricingPlanSerializer,
    PlanWaveOffSerializer,
)

from users.permissions import (
    IsTokenValid,
)
from users.utils import ResponseInfo, CustomPagination
from ecdsa import SigningKey
from ecdsa.util import sigencode_der
from decouple import config
import pandas as pd
from service.models import Service, VendorService
from plan.models import Plan, VendorPlan
from utilities.mixins import CSVDownloadMixin
from django.utils import timezone
import datetime
from django.db.models import Count, Q

scheduler = BackgroundScheduler()


@scheduler.scheduled_job("interval", minutes=1, id="job")
def end_subscription():
    current_datetime = datetime.datetime.now()
    now = current_datetime.strftime("%Y-%m-%d %H:%M")
    new_now = datetime.datetime.strptime(now, "%Y-%m-%d %H:%M")

    active_subscriptions = VendorPlan.objects.filter(
        ends_on__lt=new_now, plan_status="ACTIVE"
    ).values("id", "vendor_service_id")
    if active_subscriptions:
        for subscription in active_subscriptions:
            VendorPlan.objects.filter(id=subscription["id"]).update(
                plan_status="INACTIVE", updated_on=current_datetime
            )
            VendorService.objects.filter(id=subscription["vendor_service_id"]).update(
                payment_status="UNPAID"
            )

            active_services_count = VendorPlan.objects.filter(
                vendor_service_id=subscription["vendor_service_id"],
                plan_status="ACTIVE",
            ).count()
            if active_services_count == 0:
                user_id = VendorService.objects.filter(
                    id=subscription["vendor_service_id"]
                ).values("vendor_id")
                CustomUser.objects.filter(id=user_id[0]["vendor_id"]).update(
                    payment_status="PENDING"
                )


scheduler.start()


class RenewAllVendorsSubscriptionPlan(CreateAPIView):
    """
    Class for creating API view for subscription plan creation.
    """
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = SubscriptionPlanSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(RenewAllVendorsSubscriptionPlan, self).__init__(**kwargs)

    def create(self, request, *args, **kwargs):

        vendor_plans = []
        dl = Plan.objects.all().delete()
        vpn = VendorPlan.objects.all().delete()
        try:
            services = Service.objects.all()
            for service in services:
                plan = Plan.objects.create(
                    service_id=service,
                    range_type="HR",
                    subscription_type="SILVER",
                    validity_type="Free",
                )
                vendor_services = VendorService.objects.filter(
                    service_id=service, approval_status="A"
                )
                for vendor_service in vendor_services:
                    vp = VendorPlan(
                        vendor_service_id=vendor_service,
                        plan_id=plan,
                        starts_from=timezone.now(),
                        ends_on=timezone.now() + datetime.timedelta(days=365),
                        plan_status="ACTIVE",
                        duration_in_months=0,
                        subscription_type="SILVER",
                    )
                    vendor_plans.append(vp)
        except Service.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = None
            self.response_format["message"] = messages.SERVICE_NOT_FOUND.format(
                service.slug
            )
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        VendorPlan.objects.bulk_create(vendor_plans)
        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_200_OK)

class CreateSilverPlanForAllAPI(CreateAPIView):
    serializer_class = VendorPlanSerializer
    permission_claases = (IsAuthenticated,)
    authentication_classes = (JWTAuthentication,)

    def create(self, request, *args, **kwargs):
        # Fetch VendorService instances with no associated VendorPlan
        vendor_services_without_plan = VendorService.objects.annotate(num_plans=Count('vendorplan')).filter(num_plans=0)
        now = timezone.now()
        new_plans = [
                VendorPlan(
                    vendor_service_id_id=vendor_service_id.id,
                    starts_from=now,
                    ends_on=now + datetime.timedelta(days=365),
                    plan_status="ACTIVE",
                    subscription_type="SILVER",
                )
                for vendor_service_id in vendor_services_without_plan
            ]
        VendorPlan.objects.bulk_create(new_plans)
        return Response({'message': 'Success'}, status=status.HTTP_200_OK)


class RenewAllVendorSubscriptionPlan(GenericAPIView):
    """
    Class for creating API view for subscription plan creation.
    """
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = SubscriptionPlanSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(RenewAllVendorSubscriptionPlan, self).__init__(**kwargs)

    def create(self, request, *args, **kwargs):

        vendor_plans = []
        dl = Plan.objects.all().delete()
        vpn = VendorPlan.objects.all().delete()
        try:
            services = Service.objects.all()
            for service in services:
                plan = Plan.objects.create(
                    service_id=service,
                    range_type="HR",
                    subscription_type="SILVER",
                    validity_type="Free",
                )
                vendor_services = VendorService.objects.filter(
                    service_id=service, approval_status="A"
                )
                for vendor_service in vendor_services:
                    vp = VendorPlan(
                        vendor_service_id=vendor_service,
                        plan_id=plan,
                        starts_from=timezone.now(),
                        ends_on=timezone.now() + datetime.timedelta(days=365),
                        plan_status="ACTIVE",
                        duration_in_months=0,
                        subscription_type="SILVER",
                    )
                    vendor_plans.append(vp)
        except Service.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = None
            self.response_format["message"] = messages.SERVICE_NOT_FOUND.format(
                service.slug
            )
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        VendorPlan.objects.bulk_create(vendor_plans)
        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_200_OK)


class AddSubscriptionPlanAPIView(GenericAPIView):
    """
    Class for creating API view for subscription plan creation.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = SubscriptionPlanSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddSubscriptionPlanAPIView, self).__init__(**kwargs)

    def post(self, request):
        """
        Function for creating new subscription plan.
        Authorization Header required.
        """

        serialized = self.get_serializer(data=request.data)

        if serialized.is_valid(raise_exception=True):
            serialized.save()

            self.response_format["data"] = serialized.data
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["error"] = None
            self.response_format["message"] = "Subscription Plan created successfully."
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = serialized.errors
            self.response_format["message"] = "Failure."
            return Response(self.response_format)


class UpdateSubscriptionPlanAPIView(UpdateAPIView):
    """
    Class for updating existing subscription plan.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = SubscriptionPlanSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateSubscriptionPlanAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SubscriptionPlan.objects.none()
        subscription_plan_id = self.kwargs["pk"]
        return SubscriptionPlan.objects.filter(id=subscription_plan_id)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.subscription_type = request.data.get("subscription_type")
        instance.features = request.data.get("features")

        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.partial_update(serializer)
            self.response_format["data"] = serializer.data

        return Response(self.response_format)


class GetSubscriptionPlanListAPIView(ListAPIView):
    """
    Class for creating API view for getting subscription plan list.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = SubscriptionPlanSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetSubscriptionPlanListAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SubscriptionPlan.objects.none()

    def get(self, request):
        if request.user.role == "SUPER_ADMIN":
            subscription_plan_list = SubscriptionPlan.objects.all()
            subscription_plan_serialized = self.get_serializer(
                subscription_plan_list, many=True
            )

            self.response_format["data"] = subscription_plan_serialized.data
        return Response(self.response_format)


class AddPricingPlanAPIView(GenericAPIView):
    """
    Class for creating API view for adding pricing plan.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = PricingPlanSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddPricingPlanAPIView, self).__init__(**kwargs)

    def post(self, request):
        """
        Function for creating new pricing plan.
        Authorization Header required.
        """

        serialized = self.get_serializer(data=request.data)

        if serialized.is_valid(raise_exception=True):
            serialized.save()

            self.response_format["data"] = serialized.data
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["error"] = None
            self.response_format["message"] = "Pricing Plan created successfully."
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = serialized.errors
            self.response_format["message"] = "Failure."
            return Response(self.response_format)


class UpdatePricingPlanAPIView(GenericAPIView):
    """
    Class for updating existing pricing plan.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UpdatePricingPlanSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdatePricingPlanAPIView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        pricing_plan_list = request.data.get("pricing_plan_list")

        for instance_plan in pricing_plan_list:
            instance = Plan.objects.filter(id=instance_plan["id"]).first()
            instance.price = instance_plan["price"]

            serializer = self.get_serializer(instance, data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                self.response_format["data"] = serializer.data

        return Response(self.response_format)


class GetPricingPlanListAPIView(ListAPIView):
    """
    Class for creating API view for getting subscription plan list.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = PricingPlanSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetPricingPlanListAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Plan.objects.none()

    def format_plans(self, validity_type, range_type, mr, hr, service_id, dic):
        if len(validity_type) == 0:
            if range_type == "MR":
                mr.append(dic)
            else:
                hr.append(dic)
            validity_type.append({"service_id": service_id, "MR": mr, "HR": hr})
        else:
            for element1 in validity_type:
                found = 0
                if service_id == element1["service_id"]:
                    if range_type == "HR":
                        element1["HR"].append(dic)
                    else:
                        element1["MR"].append(dic)
                    found = 1
                    break
            if found == 0:
                if range_type == "MR":
                    mr.append(dic)
                else:
                    hr.append(dic)
                validity_type.append({"service_id": service_id, "MR": mr, "HR": hr})
        return validity_type

    def get(self, request):
        if request.user.role == "SUPER_ADMIN":
            subscription_plan_list = Plan.objects.filter()
            pricing_plan_serialized = self.get_serializer(
                subscription_plan_list, many=True
            )
            data = list()
            one_month = list()
            three_month = list()
            six_month = list()
            one_year = list()

            for pricing_plan in pricing_plan_serialized.data:
                mr_three_month = list()
                mr_six_month = list()
                mr_one_year = list()
                hr_three_month = list()
                hr_six_month = list()
                hr_one_year = list()
                mr_one_month = list()
                hr_one_month = list()
                dic = {
                    "id": pricing_plan["id"],
                    "service_type": pricing_plan["service_type"],
                    "subscription_type": pricing_plan["subscription_type"],
                    "price": pricing_plan["price"],
                    "range_type": pricing_plan["range_type"],
                    "validity_type": pricing_plan["validity_type"],
                    "service_id": pricing_plan["service_id"],
                }

                if pricing_plan["validity_type"] == "1 Month":
                    one_month = GetPricingPlanListAPIView.format_plans(
                        self,
                        one_month,
                        pricing_plan["range_type"],
                        mr_one_month,
                        hr_one_month,
                        pricing_plan["service_id"],
                        dic,
                    )
                elif pricing_plan["validity_type"] == "3 Month":
                    three_month = GetPricingPlanListAPIView.format_plans(
                        self,
                        three_month,
                        pricing_plan["range_type"],
                        mr_three_month,
                        hr_three_month,
                        pricing_plan["service_id"],
                        dic,
                    )
                elif pricing_plan["validity_type"] == "6 Month":
                    six_month = GetPricingPlanListAPIView.format_plans(
                        self,
                        six_month,
                        pricing_plan["range_type"],
                        mr_six_month,
                        hr_six_month,
                        pricing_plan["service_id"],
                        dic,
                    )
                elif pricing_plan["validity_type"] == "1 Year":
                    one_year = GetPricingPlanListAPIView.format_plans(
                        self,
                        one_year,
                        pricing_plan["range_type"],
                        mr_one_year,
                        hr_one_year,
                        pricing_plan["service_id"],
                        dic,
                    )

            data.append(
                {
                    "1 Month": one_month,
                    "3 Month": three_month,
                    "6 Month": six_month,
                    "1 Year": one_year,
                }
            )
            self.response_format["data"] = data
        return Response(self.response_format)


class AddVendorSubscriptionPlanAPIView(GenericAPIView):
    """
    Class for creating API view for adding pricing plan.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = VendorPlanSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddVendorSubscriptionPlanAPIView, self).__init__(**kwargs)

    def vendor_plan_save(self, serialized, obj=None):
        vendor_service_id = serialized.data["vendor_service_id"]
        VendorService.objects.filter(id=vendor_service_id).update(payment_status="PAID")
        CustomUser.objects.filter(id=self.request.user.id).update(payment_status="DONE")
        VendorPlan.objects.filter(
            vendor_service_id_id=vendor_service_id
        ).exclude(id=obj.id).update(plan_status="INACTIVE")
        return None

    def post(self, request):
        """
        Function for creating new vendor subscription pricing plan.
        Authorization Header required.
        """

        serialized = self.get_serializer(data=request.data)
        receipt_data = request.data.get("subscription_response")
        if "ios_device" in receipt_data:
            verify_apple_receipt_data = verify_apple_receipt(
                receipt_data["transactionReceipt"], request.data["subscription_id"]
            )
            if verify_apple_receipt_data["status"]:
                if serialized.is_valid(raise_exception=True):
                    obj = serialized.save()

                    self.vendor_plan_save(serialized, obj)
                    self.response_format["data"] = serialized.data
                    self.response_format["status_code"] = status.HTTP_201_CREATED
                    self.response_format["error"] = None
                    self.response_format["message"] = messages.ADDED.format(
                        "Vendor subscription plan"
                    )
                    return Response(self.response_format)
                else:
                    self.response_format["data"] = None
                    self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                    self.response_format["error"] = serialized.errors
                    self.response_format["message"] = "Failure."
                    return Response(self.response_format)
            else:
                self.response_format["data"] = None
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                self.response_format["error"] = messages.RECEIPT_NOT_VALID
                self.response_format["message"] = "Failure."
                return Response(self.response_format)
        else:
            try:
                receipt_response = verify_google_play(
                    receipt_data["purchaseToken"], receipt_data["productId"]
                )
                if not receipt_response.is_expired:
                    if serialized.is_valid(raise_exception=True):
                        obj = serialized.save()
                        self.vendor_plan_save(serialized, obj)
                        self.response_format["data"] = serialized.data
                        self.response_format["status_code"] = status.HTTP_201_CREATED
                        self.response_format["error"] = None
                        self.response_format["message"] = messages.ADDED.format(
                            "Vendor subscription plan"
                        )
                        return Response(self.response_format)
                self.response_format["data"] = None
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                self.response_format["error"] = serialized.errors
                self.response_format["message"] = "Failure."
                return Response(self.response_format)

            except Exception as e:
                print(e, str(e))
                self.response_format["data"] = str(e)
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                self.response_format["error"] = serialized.errors
                self.response_format["message"] = "Failure."
                return Response(self.response_format)


class GetVendorPlanAPIView(ListAPIView):
    """
    Class for getting current plan for a vendor if any.
    """

    permission_classes = (IsTokenValid, IsAuthenticated)
    authentication_classes = (JWTAuthentication,)
    serializer_class = VendorPlanSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetVendorPlanAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorPlan.objects.none()

    def get(self, request, *args, **kwargs):
        vendor_plan = (
            VendorPlan.objects.filter(
                vendor_service_id__vendor_id_id=self.kwargs["vendor_id"]
            )
            .order_by("-created_on")
            .first()
        )
        if vendor_plan:
            vendor_plan_serialized = self.get_serializer(vendor_plan)
            self.response_format["data"] = vendor_plan_serialized.data
        return Response(self.response_format)


class GetVendorCurrentPlanAPIView(ListAPIView):
    permission_classes = (IsTokenValid, IsAuthenticated)
    authentication_classes = (JWTAuthentication,)
    serializer_class = VendorPlanSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetVendorCurrentPlanAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorPlan.objects.none()

    def post(self, request, *args, **kwargs):
        vendor_service_id = self.request.data.get("vendor_service_id")
        vendor_id = self.request.data.get("vendor_id")
        if vendor_id and vendor_service_id:
            vendor_plan_data = VendorPlan.objects.filter(
                vendor_service_id__vendor_id_id=vendor_id,
                vendor_service_id=vendor_service_id,
            )
            if vendor_plan_data.exists():
                vendor_plan = vendor_plan_data.order_by("-created_on")
                vendor_plan_serialized = self.get_serializer(vendor_plan.first())
                vendor_plan_data = vendor_plan.first()
                if not vendor_plan_data.subscription_response:
                    data = VendorPlanSerializer(vendor_plan_data, many=False).data
                    data["is_expired"] = (
                        vendor_plan_data.ends_on < datetime.datetime.now()
                    )
                    data["is_subscribed"] = False
                    self.response_format["data"] = data
                    print(data)
                    return Response(self.response_format)

                elif (
                    vendor_plan_data.subscription_response
                    and "ios_device" in vendor_plan_data.subscription_response
                ):
                    verify_apple_receipt_data = verify_apple_receipt(
                        vendor_plan_data.subscription_response["transactionReceipt"],
                        vendor_plan_data.subscription_id,
                    )
                    if verify_apple_receipt_data["is_expire"]:
                        vendor_plan_status_update(vendor_plan_data)
                    receipt_data = {
                        "is_expired": verify_apple_receipt_data["is_expire"]
                    }
                    data = {
                        **vendor_plan_serialized.data,
                        **receipt_data,
                        "is_subscribed": True,
                    }
                    self.response_format["data"] = data
                    return Response(self.response_format)

                else:
                    Product_Id = (
                        vendor_plan_data.subscription_response["productId"]
                        if vendor_plan_data.subscription_response
                        else ""
                    )
                    Purchase_Token = (
                        vendor_plan_data.subscription_response["purchaseToken"]
                        if vendor_plan_data.subscription_response
                        else ""
                    )
                    try:
                        receipt_response = verify_google_play(
                            Purchase_Token, Product_Id
                        )
                    except Exception as e:
                        self.response_format["data"] = None
                        self.response_format["status_code"] = status.HTTP_200_OK
                        self.response_format["error"] = None
                        self.response_format["message"] = messages.PLAN_EXPIRED
                        return Response(self.response_format)
                    is_expired = receipt_response.is_expired
                    if is_expired:
                        vendor_plan_status_update(vendor_plan_data)
                    receipt_data = {
                        "raw_response": receipt_response.raw_response,
                        "is_expired": is_expired,
                    }
                    data = {
                        **vendor_plan_serialized.data,
                        **receipt_data,
                        "is_subscribed": True,
                    }
                    self.response_format["data"] = data
                    return Response(self.response_format)
            else:
                data = {"is_subscribed": False}
                self.response_format["data"] = data
                self.response_format["status_code"] = status.HTTP_200_OK
                self.response_format["error"] = None
                self.response_format["message"] = (
                    "This service is not subscribed any plan yet."
                )
                return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = None
            self.response_format["message"] = (
                "Please enter vendor id and vendor service id."
            )
            return Response(self.response_format)


class UpdateVendorPlanValidityAPIView(UpdateAPIView):
    """
    Class for updating existing vendor plan.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UpdateVendorPlanSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateVendorPlanValidityAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return VendorPlan.objects.none()
        vendor_plan_id = self.kwargs["pk"]
        return VendorPlan.objects.filter(id=vendor_plan_id)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.ends_on = request.data.get("ends_on")

        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.partial_update(serializer)
            self.response_format["data"] = serializer.data

        return Response(self.response_format)


class GetPlanByServiceTypeAPIView(ListAPIView):
    """
    Class for getting current plan for a vendor if any.
    """

    permission_classes = (IsTokenValid, IsAuthenticated)
    authentication_classes = (JWTAuthentication,)
    serializer_class = PricingPlanSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetPlanByServiceTypeAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Plan.objects.none()

    def post(self, request, *args, **kwargs):
        service_plan = Plan.objects.filter(
            service_id=request.data["service_id"], range_type=request.data["range_type"]
        )

        service_plan_serialized = self.get_serializer(service_plan, many=True)
        self.response_format["data"] = service_plan_serialized.data
        return Response(self.response_format)


class GenerateSignatureAPIView(GenericAPIView):
    """
    Class for generating apple signature
    """

    permission_classes = (IsTokenValid, IsAuthenticated)
    authentication_classes = (JWTAuthentication,)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GenerateSignatureAPIView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        """
        @see https://developer.apple.com/documentation/storekit/in-app_purchase/generating_a_signature_for_subscription_offers
        @param app_bundle_id: application bundle ID
        @param product_identifier: product identifier (subscription ID)
        @param offer_identifier: offer identifier
        @param application_username: user identification in our system
        @return: base64 encoded signature of the request
        """

        nonce = str(uuid.uuid4())
        # timestamp multiplied by 1000 since Apple want this to be in milliseconds
        timestamp = 1000 * calendar.timegm(datetime.datetime.now().timetuple())
        key_id = config("SUBSCRIPTION_OFFERS_KEY_ID")
        payload = "\u2063".join(
            [
                request.data.get("app_bundle_id"),
                key_id,
                request.data.get("product_identifier"),
                request.data.get("subscription_offer_id"),
                request.data.get("application_username"),
                nonce,
                str(timestamp),
            ]
        )
        signing_key = SigningKey.from_pem(open(config("APPLE_SIGNIN_KEY_PATH")).read())

        # pem = APPLE_PRIVATE_KEY
        # signing_key = SigningKey.from_pem(pem)
        signature = signing_key.sign(
            payload.encode("utf-8"), hashfunc=hashlib.sha256, sigencode=sigencode_der
        )
        encoded_signature = base64.b64encode(signature)
        data = {
            "keyID": key_id,
            "nonce": nonce,
            "timestamp": str(timestamp),
            "signature": str(encoded_signature, "utf-8"),
        }
        self.response_format["data"] = data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)



class ListVendorPlanAPIView(ListAPIView, RetrieveAPIView, CSVDownloadMixin):
    serializer_class = VendorPlanSerializer
    permission_classes = (IsTokenValid, IsAuthenticated, IsAdminUser)
    authentication_classes = (JWTAuthentication,)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = ("subscription_type", "plan_status", "plan_id__validity_type")
    search_fields = ("vendor_service_id__business_name", "duration_in_months",)
    http_method_names = ("get",)
    pagination_class = CustomPagination

    def get_queryset(self):
        if self.request.query_params.get('purchased', False):
            return VendorPlan.objects.filter(subscription_response__isnull=False, plan_status='ACTIVE', vendor_service_id__approval_status='A').distinct()
        return VendorPlan.objects.filter(vendor_service_id__approval_status='A', plan_status='ACTIVE').order_by('-updated_on').distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if request.GET.get("download") == "csv":
            return self.download_csv(request, queryset, self.serializer_class)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    

class VendorPlanDetailAPIView(RetrieveAPIView):
    serializer_class = VendorPlanSerializer
    permission_classes = (IsTokenValid, IsAuthenticated, IsAdminUser)
    authentication_classes = (JWTAuthentication,)
    http_method_names = ("get",)
    pagination_class = CustomPagination

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(VendorPlanDetailAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        return VendorPlan.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)


# class ServicePlanWaveOffAPI(CreateAPIView):
#     serializer_class = PlanWaveOffSerializer
#     permission_classes = (IsTokenValid, IsAuthenticated, IsAdminUser)
#     authentication_classes = (JWTAuthentication,)

#     def __init__(self, **kwargs):
#         """
#         Constructor function for formatting the web response to return.
#         """
#         self.response_format = ResponseInfo().response
#         super(ServicePlanWaveOffAPI, self).__init__(**kwargs)


#     def create(self, request, *args, **kwargs):
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         vender_id = serializer.validated_data.get('vendor_service_id')
#         sub_type = serializer.validated_data.get('subscription_type')
#         duration = serializer.validated_data.get('duration')

#         try:
#             plan = VendorPlan.objects.filter(vendor_service_id=vender_id).latest('created_on')
#         except VendorPlan.DoesNotExist:
#             self.response_format["data"] = None
#             self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
#             self.response_format["error"] = True
#             self.response_format["message"] = messages.NO_PLAN
#             return Response(self.response_format)

#         if plan.subscription_type == 'SILVER':
#             days = 180 if duration == 6 else 365
#             new_plan = VendorPlan.objects.create(
#                 vendor_service_id=vender_id,
#                 subscription_type=sub_type,
#                 duration_in_months=duration,
#                 plan_status='ACTIVE',
#                 starts_from=timezone.now(),
#                 ends_on=timezone.now() + datetime.timedelta(days=days)
#             )
#             plan.plan_status = 'INACTIVE'
#             plan.save()
#             data = VendorPlanSerializer(new_plan, many=False).data
#             self.response_format["data"] = data
#             self.response_format["status_code"] = status.HTTP_200_OK
#             self.response_format["error"] = None
#             self.response_format["message"] = messages.SUCCESS
#             return Response(self.response_format)
#         self.response_format["data"] = None
#         self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
#         self.response_format["error"] = True
#         self.response_format["message"] = messages.NO_FREE_PLAN
#         return Response(self.response_format)


class ServicePlanWaveOffAPI(CreateAPIView):
    serializer_class = PlanWaveOffSerializer
    permission_classes = (IsTokenValid, IsAuthenticated, IsAdminUser)
    authentication_classes = (JWTAuthentication,)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(ServicePlanWaveOffAPI, self).__init__(**kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        vender_id = serializer.validated_data.get('vendor_service_id')
        sub_type = serializer.validated_data.get('subscription_type')
        duration = serializer.validated_data.get('duration')

        try:
            # Fetch the latest plan for the vendor
            plan = VendorPlan.objects.filter(vendor_service_id=vender_id).latest('created_on')
            current_subscription = plan.subscription_type
            if current_subscription == sub_type:         
                self.response_format["data"] = None
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                self.response_format["error"] = True
                self.response_format["message"] = messages.INVALID_PLAN_TRANSITION
                return Response(self.response_format)

        except VendorPlan.DoesNotExist:
            plan = None
            current_subscription = None
        
        # Upgrade logic
        days = 180 if duration == 6 else 365
        new_plan = VendorPlan.objects.create(
            vendor_service_id=vender_id,
            subscription_type=sub_type,
            duration_in_months=12 if sub_type == 'SILVER' else duration,
            plan_status='ACTIVE',
            starts_from=timezone.now(),
            ends_on=timezone.now() + datetime.timedelta(days=days)
        )
        if plan:
            plan.plan_status = 'INACTIVE'
            plan.save()

        data = VendorPlanSerializer(new_plan, many=False).data
        self.response_format["data"] = data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)
