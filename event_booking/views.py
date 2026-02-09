"""
This file is used for creating a view for the API,
which takes a web request and returns a web response.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.generics import (GenericAPIView,
                                     UpdateAPIView,
                                     ListAPIView
                                     )

from utilities import messages
from .models import VendorEventBooking
from .serializers import (VendorEventBookingSerializers,
                          UpdateEventBookingSerializers
                          )

from users.permissions import (IsTokenValid,
                               )
from users.utils import (ResponseInfo,
                         CustomPagination
                         )


class AddEventBookingAPIView(GenericAPIView):
    """
    Class for creating API view for adding items to user cart.
    """
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = VendorEventBookingSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddEventBookingAPIView, self).__init__(**kwargs)

    def post(self, request):
        """
        Function for creating new event booking.
        Authorization Header required.
        """
        request.data['vendor_id'] = request.user.id
        serialized = self.get_serializer(data=request.data)

        if serialized.is_valid(raise_exception=True):
            serialized.save()

            self.response_format["data"] = serialized.data
            self.response_format["message"] = messages.BOOKING_SUCCESS.format("Event booked")
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = serialized.errors
            self.response_format['message'] = "Failure."
            return Response(self.response_format)


class GetEventBookingListView(ListAPIView):
    """
    Class for creating API view for getting event booking.
    """
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = VendorEventBookingSerializers

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return VendorEventBooking.objects.none()
        start_date = self.request.data["start_date"]
        end_date = self.request.data["end_date"]
        return VendorEventBooking.objects.filter(vendor_id=self.request.user.id).filter(
            event_date__gte=start_date).filter(event_date__lte=end_date).filter(is_deleted=False)

    def post(self, request, *args, **kwargs):
        """
        Function for getting vendor event booking.
        """
        paginator = PageNumberPagination()
        paginator.page_size = 50

        vendor_event_serialized = super().list(request, *args, **kwargs)

        result_projects = paginator.paginate_queryset(vendor_event_serialized.data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects)


class UpdateEventBookingAPIView(GenericAPIView):
    """
    Class for updating event booking details.
    """
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = VendorEventBookingSerializers

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateEventBookingAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return VendorEventBooking.objects.none()
        vendor_event_booking_id = self.kwargs['pk']
        return VendorEventBooking.objects.filter(id=vendor_event_booking_id)

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        request.data['vendor_id'] = request.user.id
        instance.vendor_id_id = request.data.get('vendor_id')
        instance.booking_title = request.data.get("booking_title")
        instance.event_date = request.data.get("event_date")
        instance.start_time = request.data.get("start_time")
        instance.end_time = request.data.get("end_time")
        instance.is_all_day = request.data.get("is_all_day")
        instance.notes = request.data.get("notes")
        instance.customer_name = request.data.get("customer_name")
        instance.customer_email = request.data.get("customer_email")
        instance.customer_contact = request.data.get("customer_contact")
        instance.tags = request.data.get("tags")

        event_booking_serializer = self.get_serializer(instance, data=request.data)
        if event_booking_serializer.is_valid(raise_exception=True):
            event_booking_serializer.save()
            self.response_format["data"] = event_booking_serializer.data
            self.response_format["message"] = messages.UPDATE.format("Booking")
        return Response(self.response_format)


class DeleteBookingAPIView(UpdateAPIView):
    """
    Class for creating API view for getting event booking.
    """
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UpdateEventBookingSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(DeleteBookingAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return VendorEventBooking.objects.none()
        return VendorEventBooking.objects.filter(id=self.kwargs['pk'])

    def post(self, request, *args, **kwargs):
        """
        Function for getting vendor event booking.
        """
        instance = self.get_object()
        instance.is_deleted = True

        vendor_event_serializer = self.get_serializer(instance, data=request.data)
        if vendor_event_serializer.is_valid(raise_exception=True):
            vendor_event_serializer.save()
            self.response_format["data"] = vendor_event_serializer.data
            self.response_format["message"] = messages.DELETE.format("Booking")
        return Response(self.response_format)
