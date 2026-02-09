"""
This file is used for creating a view for the API,
which takes a web request and returns a web response.
"""

import os

from rest_framework import status
from fcm_django.models import FCMDevice
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    UpdateAPIView,
    DestroyAPIView,
    CreateAPIView,
)
from utilities import constants

from utilities import messages
from .models import Enquiry, CelebrityEnquiry, ContactDetailView
from users.models import CustomUser
from service.models import VendorService
from .serializers import (
    UserEnquirySerializer,
    CelebrityEnquirySerializer,
    UpdateUserEnquirySerializer,
    UpdateCelebrityEnquiryStatusSerializer,
    ContactDetailViewSerializer,
)
from users.serializers import NotificationSerializer
from users.permissions import (
    IsSuperAdmin,
    IsTokenValid,
)
from users.utils import ResponseInfo, CustomPagination, send_sms
from users.views import ForgotPasswordRequestView
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from users.views import UserLoginAPIView
from utilities.commonutils import send_email
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from utilities.mixins import CSVDownloadMixin
from decouple import config
from service.utils import track_user_action


class CreateContactDetailViewAPI(CreateAPIView):
    serializer_class = ContactDetailViewSerializer
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (IsAuthenticated,)
    http_method_names = ("post",)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(CreateContactDetailViewAPI, self).__init__(**kwargs)

    def get_queryset(self):
        return ContactDetailView.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["error"] = None
        self.response_format["message"] = messages.ADDED.format("ContactDetailView")
        return Response(self.response_format)


class ContactDetailViewList(ListAPIView, CSVDownloadMixin):
    """
    Class for creating API view for getting celebrity enquiry list.
    """

    permission_classes = (IsAuthenticated,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = ContactDetailViewSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    pagination_class = CustomPagination
    filterset_fields = ("is_deleted",)
    search_fields = ["user__fullname", "user__contact_number", "service__business_name"]

    def get_queryset(self):
        return ContactDetailView.objects.all().order_by("-created_at")

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


class AddCelebrityEnquiryAPIView(GenericAPIView):
    """
    Class for creating API view for celebrity enquiry creation.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = CelebrityEnquirySerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddCelebrityEnquiryAPIView, self).__init__(**kwargs)

    def post(self, request):
        """
        Function for creating new celebrity enquiry.
        """
        request.data["user_id"] = request.user.id
        role = request.user.role.lower()
        fullname = request.user.fullname
        super_admin = CustomUser.objects.filter(role="SUPER_ADMIN").values("id").first()
        serialized = self.get_serializer(data=request.data)

        if serialized.is_valid(raise_exception=True):
            celebrity_enquiry_id = serialized.save()

            message = "New celebrity enquiry from {} {}.".format(role, fullname)
            params = (
                "{" + '"celebrity_enquiry_id": {}'.format(celebrity_enquiry_id.id) + "}"
            )

            notification_data = {
                "message": message,
                "status": "UR",
                "user_id": super_admin["id"],
                "notification_type": "CELEBRITY_ENQUIRY",
                "params": params,
            }

            req = NotificationSerializer(data=notification_data)
            if req.is_valid(raise_exception=True):
                req.save()

            # is_device = FCMDevice.objects.filter(user_id=user_id)
            # if is_device:
            #     UserLoginAPIView.generate_fcm_token(self, user_id, data)

            user = CustomUser.objects.filter(role="SUPER_ADMIN").values(
                "email", "fullname"
            )
            email = user[0]["email"]
            event_date = serialized.data["event_date"].split("T")[0]
            # template_id = "d-12f76f780a354dab991366dd3caf0c62"
            # sender = DEFAULT_FROM_EMAIL
            # data_dict = {"user_name1": user[0]['fullname'], "user_name2": fullname,
            #              "user_email": serialized.data['email'], "user_phone": serialized.data['contact_number'],
            #              "event_date": event_date, "event_city": serialized.data['location'],
            #              "celebrity_preferences": serialized.data['celebrity_type'],
            #              "celebrity_name": serialized.data['celebrity_name'],
            #              "celebrity_budget": serialized.data['budget'],
            #              "user_message": serialized.data['message']}
            #
            # ForgotPasswordRequestView.send_mail(self, template_id, sender, email, data_dict)

            template_id = constants.CELEBRITY_ENQUIRY_TEMPLATE
            data_dict = {}
            send_email(template_id, email, data_dict)

            template_id = constants.ADMIN_REC_ON_CELEB_ENQ_BY_USER
            data_dict = {
                "user": serialized.data["fullname"],
                "email": serialized.data["email"],
                "contact_number": serialized.data["contact_number"],
                "message": serialized.data["message"],
            }
            send_email(template_id, constants.TEST_EMAIL, data_dict, bcc=True)
            contact_number = request.data.get("contact_number", None)
            if contact_number:
                send_sms_contact_number = contact_number
            else:
                send_sms_contact_number = request.user.contact_number

            if send_sms_contact_number:
                # send sms
                send_sms_contact_number = [contact_number, constants.CLIENT_NUMBER]
                try:
                    message = messages.SMS_USER_SEND_CELEB_ENQUIRY.format(
                        request.user.fullname
                    )
                    resp = send_sms(
                        config("TEXT_LOCAL_API_KEY"),
                        send_sms_contact_number,
                        "OPPVNZ",
                        message,
                    )
                except Exception as e:
                    print("Error", e)
            self.response_format["data"] = serialized.data
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["error"] = None
            self.response_format["message"] = "Celebrity enquiry created successfully."
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = serialized.errors
            self.response_format["message"] = "Failure."
            return Response(self.response_format)


class UpdateCelebrityEnquiryAPIView(GenericAPIView):
    """
    Class for updating celebrity enquiry status,
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UpdateCelebrityEnquiryStatusSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateCelebrityEnquiryAPIView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        celebrity_enquiry_ids = request.data.get("enquiry_ids")
        enq_status = request.data.get("enquiry_status")
        reason = request.data.get("reason", None)

        if enq_status in ["P", "D", "S", "C"] and not reason:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = None
            self.response_format["message"] = messages.ENQ_REASON
            return Response(self.response_format)

        CelebrityEnquiry.objects.filter(id__in=celebrity_enquiry_ids).update(
            enquiry_status=enq_status, reason=reason
        )
        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.UPDATE.format("Enquiry")
        return Response(self.response_format)


class GetCelebrityEnquiryListAPIView(ListAPIView, CSVDownloadMixin):
    """
    Class for creating API view for getting celebrity enquiry list.
    """

    permission_classes = (IsAuthenticated,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = CelebrityEnquirySerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    pagination_class = CustomPagination
    filterset_fields = ("enquiry_status",)
    search_fields = ["fullname", "contact_number"]

    def get_queryset(self):
        return CelebrityEnquiry.objects.all().order_by("-created_at")

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


class GetCelebrityEnquiryAPIView(ListAPIView):
    """
    Class for creating API view for getting celebrity enquiry list.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = CelebrityEnquirySerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetCelebrityEnquiryAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CelebrityEnquiry.objects.none()

    def get(self, request, *args, **kwargs):
        if request.user.role == "SUPER_ADMIN":
            celebrity_enquiry_list = CelebrityEnquiry.objects.filter(
                id=self.kwargs["pk"]
            )
            celebrity_enquiry_serialized = self.get_serializer(
                celebrity_enquiry_list, many=True
            )
            data = celebrity_enquiry_serialized.data

            self.response_format["data"] = data
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = "Success."
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = None
            self.response_format["message"] = "Failure."
        return Response(self.response_format)


class AddUserEnquiryAPIView(GenericAPIView):
    """
    Class for creating API view for user enquiry creation.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = UserEnquirySerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddUserEnquiryAPIView, self).__init__(**kwargs)

    def post(self, request):
        """
        Function for creating new user enquiry.
        """
        request.data["user_id"] = request.user.id
        vendor_service = VendorService.objects.filter(
            id=request.data["vendor_service_id"]
        ).values("business_name", "vendor_id")
        business_name = vendor_service[0]["business_name"]
        vendor_id = vendor_service[0]["vendor_id"]
        serialized = self.get_serializer(data=request.data)
        vendor_service_id = request.data.get("vendor_service_id")

        if serialized.is_valid(raise_exception=True):
            user_enquiry = serialized.save()

            vendor_service = VendorService.objects.get(id=vendor_service_id)
            track_user_action(request, vendor_service, "send_enquiry")

            message = "You have a new enquiry for {} from {}.".format(
                business_name, request.user.fullname
            )
            params = "{" + '"user_enquiry_id": {}'.format(user_enquiry.id) + "}"

            notification_data = {
                "message": message,
                "status": "UR",
                "user_id": vendor_id,
                "notification_type": "SERVICE_ENQUIRY",
                "params": params,
            }

            req = NotificationSerializer(data=notification_data)
            if req.is_valid(raise_exception=True):
                req.save()
            is_device = FCMDevice.objects.filter(user_id=vendor_id)
            if is_device:
                UserLoginAPIView.generate_fcm_token(self, vendor_id, notification_data)

            user = CustomUser.objects.filter(id=vendor_id).values(
                "email", "fullname", "contact_number"
            )
            email = user[0]["email"]
            # template_id = "d-3cda16b311674163b0a950b48b97f3bc"
            # sender = DEFAULT_FROM_EMAIL
            # data_dict = {"vendor_name": user[0]['fullname'], "user_name": request.user.fullname, "service_name": business_name}
            # ForgotPasswordRequestView.send_mail(self, template_id, sender, email, data_dict)

            template_id = constants.USER_ENQUIRY_TEMPLATE
            data_dict = {"user": business_name}
            send_email(template_id, email, data_dict)

            sender = request.user

            if sender.email:
                template = constants.USER_SEND_SERVICE_ENQUIRY_TEMPLATE
                mail_data = {"user": sender.fullname, "service": business_name}
                send_email(template, sender.email, mail_data)

            if user[0]["contact_number"]:
                # send sms
                try:
                    message = messages.VEND_REC_ON_USER_ENQ_SERVICE.format(
                        business_name
                    )
                    print(user[0]["contact_number"], message)
                    resp = send_sms(
                        config("TEXT_LOCAL_API_KEY"),
                        user[0]["contact_number"],
                        "OPPVNZ",
                        message,
                    )
                except Exception as e:
                    print("Error", e)

            number = request.user.contact_number
            if number:
                print("--------------------")
                # send sms
                try:
                    message = messages.SMS_USER_SEND_SERVICE_ENQUIRY.format(
                        request.user.fullname
                    )
                    print(number, message)
                    print(
                        send_sms(
                            config("TEXT_LOCAL_API_KEY"), number, "OPPVNZ", message
                        )
                    )
                except Exception as e:
                    print("Error", e)

            self.response_format["data"] = serialized.data
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["error"] = None
            self.response_format["message"] = "User enquiry created successfully."
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = serialized.errors
            self.response_format["message"] = "Failure."
            return Response(self.response_format)


class UpdateUserEnquiryAPIView(UpdateAPIView):
    """
    Class for updating celebrity enquiry status,
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UpdateUserEnquirySerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateUserEnquiryAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Enquiry.objects.none()
        user_enquiry_id = self.kwargs["pk"]
        return Enquiry.objects.filter(id=user_enquiry_id)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.enquiry_status = request.data.get("enquiry_status")

        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.partial_update(serializer)
            self.response_format["data"] = serializer.data
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = messages.UPDATE.format("Enquiry status")

        return Response(self.response_format)


class GetUserEnquiryListView(ListAPIView):
    """
    Class for creating API view for getting user enquiry list.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UserEnquirySerializer
    filter_backends = (SearchFilter,)
    search_fields = ("fullname", "email")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Enquiry.objects.none()

    def post(self, request):
        paginator = PageNumberPagination()
        paginator.page_size = 20
        data = []
        enquiry_status = request.data.get("enquiry_status")
        vendor_id = request.user
        if request.user.role == "VENDOR":
            user_enquiry_list = Enquiry.objects.filter(
                enquiry_status=enquiry_status, vendor_service_id__vendor_id=vendor_id
            ).order_by("-id")
            user_enquiry_serialized = self.get_serializer(
                self.filter_queryset(user_enquiry_list), many=True
            )
            data = user_enquiry_serialized.data

        result_projects = paginator.paginate_queryset(data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects)


class GetUserEnquiryAPIView(ListAPIView):
    """
    Class for creating API view for getting celebrity enquiry list.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UserEnquirySerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetUserEnquiryAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the enquiries by user.
        """
        if getattr(self, "swagger_fake_view", False):
            return Enquiry.objects.none()

    def get(self, request, *args, **kwargs):
        if request.user.role == "VENDOR":
            user_enquiry_list = Enquiry.objects.filter(id=self.kwargs["pk"])
            user_enquiry_serialized = self.get_serializer(user_enquiry_list, many=True)
            data = user_enquiry_serialized.data

            self.response_format["data"] = data
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = "Success."
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = None
            self.response_format["message"] = "Failure."
        return Response(self.response_format)


class DeleteCelebEnquiryAPIView(DestroyAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = CelebrityEnquirySerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(DeleteCelebEnquiryAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CelebrityEnquiry.objects.all()

    def delete(self, request, *args, **kwargs):

        try:
            instance = CelebrityEnquiry.objects.get(id=self.kwargs["pk"])
            reason = request.data.get("reason", None)
            if not reason:
                self.response_format["data"] = None
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                self.response_format["error"] = None
                self.response_format["message"] = messages.ENQ_REASON
                return Response(self.response_format)
            instance.enquiry_status = "D"
            instance.reason = reason
            instance.save()
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_204_NO_CONTENT
            self.response_format["error"] = None
            self.response_format["message"] = messages.DELETE.format("Item")
            return Response(self.response_format)
        except CelebrityEnquiry.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = True
            self.response_format["message"] = messages.NOT_FOUND.format("Celeb Enqiry")
            return Response(self.response_format)
