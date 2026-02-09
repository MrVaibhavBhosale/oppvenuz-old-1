from .models import VendorPlan
from .serializers import VendorPlanSerializer
from datetime import datetime
from utilities.commonutils import verify_google_play, verify_apple_receipt


def get_vendor_current_plan(vendor_id, service_id):

    plans = VendorPlan.objects.filter(
        vendor_service_id__vendor_id_id=vendor_id,
        vendor_service_id=service_id,
    ).order_by("-created_on")

    if plans.exists():
        plan = plans.first()

    if not plan.subscription_response:
        data = VendorPlanSerializer(plan, many=False).data
        data["is_expired"] = plan.ends_on < datetime.datetime.now()
        return data

    if plan.subscription_response and "ios_device" in plan.subscription_response:
        receipt = verify_apple_receipt(
            plan.subscription_response["transactionReceipt"],
            plan.subscription_id,
        )
        