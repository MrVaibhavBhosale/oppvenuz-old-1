from rest_framework import serializers
from .models import (Payment,
                     PayuTemp,
                     PaymentCancellation
                     )


class ServicePaymentCancellationSerializers(serializers.ModelSerializer):
    """
    Class for serializing payment cancellation policy of a service.
    """
    class Meta:
        model = PaymentCancellation
        fields = ["id", "vendor_service_id", "advance_for_booking", "payment_on_event_date", "payment_on_delivery",
                  "cancellation_policy"]


class PaymentSerializers(serializers.ModelSerializer):
    """
    Class for serializing payment of a service.
    """
    plan_id = serializers.IntegerField(source="vendor_plan_id.plan_id_id", read_only=True)
    plan_name = serializers.CharField(source="plan_id.subscription_type", read_only=True)
    start_date = serializers.DateTimeField(source="vendor_plan_id.starts_from", read_only=True)
    end_date = serializers.DateTimeField(source="vendor_plan_id.ends_on", read_only=True)
    vendor_id = serializers.IntegerField(source="vendor_plan_id.vendor_id_id", read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "vendor_id", "plan_id", "plan_name", "start_date", "end_date", "vendor_plan_id",
                  "amount_received", "transaction_id", "created_at"]


class PayuSerializers(serializers.ModelSerializer):
    """
    Class for serializing payment cancellation policy of a service.
    """
    class Meta:
        model = PayuTemp
        fields = ["id", "amount", "paymentMode"]
