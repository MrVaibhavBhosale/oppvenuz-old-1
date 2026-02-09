from rest_framework import serializers
from .models import VendorEventBooking
from service.serializers import GetServiceSerializers


class VendorEventBookingSerializers(serializers.ModelSerializer):
    """
    Class for serializing list of all events.
    """
    class Meta:
        model = VendorEventBooking
        fields = ["id", "vendor_id", "booking_title", "event_date", "start_time", "end_time", "is_all_day", "notes",
                  "customer_name", "customer_email", "customer_contact", "tags", "service_type"]


    def to_representation(self, instance):
        response =  super().to_representation(instance)
        response["service_type"] = GetServiceSerializers(instance.service_type, many=False).data
        return response

class UpdateEventBookingSerializers(serializers.ModelSerializer):
    """
    Class for serializing deleting event.
    """
    class Meta:
        model = VendorEventBooking
        fields = ["id", "is_deleted"]
