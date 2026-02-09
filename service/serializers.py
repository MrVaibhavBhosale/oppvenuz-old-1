from rest_framework import serializers
from datetime import datetime
import logging
from plan.serializers import VendorPlanSerializer
from utilities.commonutils import (
    verify_google_play,
    verify_apple_receipt,
    vendor_plan_status_update,
)
from .models import (
    Cart,
    Service,
    ServiceSubTypeDetail,
    VendorService,
    VendorPricing,
    VendorServiceOffer,
    ServiceContactDetail,
    VendorServiceViewLike,
    ServiceSuitableFor,
    ServiceEvent,
    CatererServiceMenu,
    VenueType,
    ServiceRegistrationChargesDetail,
    ServiceVendorRegistrationCharges
)
from payment.models import PaymentCancellation
from payment.serializers import ServicePaymentCancellationSerializers
from plan.models import VendorPlan
from users.models import CustomUser, City
from documents.serializers import DocumentListingDetailSerializer, VendorDocument
from .utils import update_service_share_url
from users.serializers import CityListSerializer
from feedbacks.models import (TrackUserAction, TrackUserSession)
import pytz
logger = logging.getLogger(__name__)

class CatererServiceMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatererServiceMenu
        fields = [
            "title",
            "slug",
            "service",
            "min_capacity",
            "max_capacity",
            "is_veg_selected",
            "veg_actual_price",
            "veg_discounted_price",
            "veg_menu",
            "is_non_veg_selected",
            "non_veg_actual_price",
            "non_veg_discounted_price",
            "non_veg_menu",
            "images",
            "menu_name",
            "include_serve_executives",
        ]


class VenueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VenueType
        fields = ["id", "title", "slug", "image", "sequence_number"]


class ServiceEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceEvent
        fields = ["id", "title", "slug"]


class ServiceSuitableForSerializer(serializers.ModelSerializer):
    """
    serializer for ServiceSuitableFor
    """

    class Meta:
        model = ServiceSuitableFor
        fields = ["id", "title"]


class GetServiceSerializers(serializers.ModelSerializer):
    """
    Class for serializing list of all service_types.
    """

    class Meta:
        model = Service
        fields = [
            "id",
            "service_type",
            "service_icons_app",
            "service_icons_web",
            "service_bg_images_app",
            "service_type_code",
            "slug",
            "service_image",
            "is_included",
        ]


class AddVendorServiceSerializers(serializers.ModelSerializer):
    """
    Class for serializing list of all vendor mapped services.
    """

    class Meta:
        model = VendorService
        fields = ["id", "service_id", "vendor_id"]


class GetUserServiceMappingSerializers(serializers.ModelSerializer):
    """
    Class for serializing list of all vendor mapped services.
    """

    service_type = serializers.CharField(
        source="service_id.service_type", read_only=True
    )
    service_icons_app = serializers.CharField(
        source="service_id.service_icons_app", read_only=True
    )
    service_type_code = serializers.CharField(
        source="service_id.service_type_code", read_only=True
    )
    # plan_data = serializers.SerializerMethodField()

    class Meta:
        model = VendorService
        fields = [
            "id",
            "service_id",
            "service_type",
            "approval_status",
            "service_icons_app",
            "service_type_code",
            "is_under_review",
            "reject_reason",
            "is_documents_verified",
        ]

    # Added on July 8 will be remove later after doc verification credit come.
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["is_documents_verified"] = instance.has_required_documents()
        return data

    # def get_plan_data(self, instance):
    #     vendor_id = instance.vendor_id.id
    #     vendor_service_id = instance.id
    #     vendor_plan_data = VendorPlan.objects.filter(vendor_service_id__vendor_id_id=vendor_id,
    #                                                  vendor_service_id=vendor_service_id)
    #     data = {}
    #     if vendor_plan_data.exists():
    #         vendor_plan = vendor_plan_data.order_by("-created_on")
    #         vendor_plan_serialized = VendorPlanSerializer(vendor_plan.first())
    #         Product_Id = vendor_plan.first().subscription_response[
    #             'productId'] if vendor_plan.first().subscription_response else ""
    #         Purchase_Token = vendor_plan.first().subscription_response[
    #             'purchaseToken'] if vendor_plan.first().subscription_response else ""
    #         receipt_response = verify_google_play(Purchase_Token, Product_Id)
    #         is_expired = receipt_response.is_expired
    #         data.update({"plan_purchased": True, "expires_at": vendor_plan_serialized.data.get('ends_on'), "expired": False})
    #         if is_expired:
    #             vendor_service = vendor_plan.first().vendor_service_id
    #             vendor_service.payment_status = "UNPAID"
    #             vendor_service.save()
    #             data.update({"expired": True})
    #     else:
    #         data = {"plan_purchased": False, "expires_at": None, "expired": None}
    #     return data


class GetApprovedServiceSerializers(serializers.ModelSerializer):
    """
    Class for serializing list of all vendor approved services.
    """

    service_type = serializers.CharField(
        source="service_id.service_type", read_only=True
    )

    class Meta:
        model = VendorService
        fields = [
            "id",
            "service_id",
            "service_type",
            "business_name",
            "payment_status",
            "user_group_service_type",
            "is_waved_off",
            "is_under_review",
        ]


class GetVendorBusinessSerializers(serializers.ModelSerializer):
    """
    Class for serializing list of all vendor business.
    """

    class Meta:
        model = VendorService
        fields = ["id", "business_name"]


class ServiceSubtypeDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServiceSubTypeDetail
        fields = [
            "id",
            "title",
            "service_subtype",
            "service",
            "actual_price",
            "discounted_price",
            "images",
            "min_order_qty",
            "selected_services",
            "cake_available_in_shapes_and_sizes",
            "purchase_type",
            "actual_price_per_hour",
            "discounted_price_per_hour",
            "min_duration",
            "pandit_pooja_samagree_included",
            "sitting_capacity",
            "floating_capacity",
            "outfit_name",
            "gender",
            "card_type",
            "package_details",
            "max_order_qty",
            "time",
            "city",
            "local_price",
            "city_price",
            "delivery_charge",
        ]


# class ServiceByTypeSerializer(serializers.ModelSerializer):
#     service_type = serializers.CharField(source='service_id.service_type', read_only=True)
#     # vendor_id = serializers.IntegerField(source='vendor_id.id', read_only=True)
#     vendor_name = serializers.CharField(source='vendor_id.fullname', read_only=True)
#     service_pricing = ServicePricingSerializers(many=True, read_only=True)

#     class Meta:
#         model = VendorService
#         fields = ['service_pricing',
#             'id', 'business_name', 'business_image', 'area', 'city', 'state', 'vendor_id', 'vendor_name',
#             'pin_code', 'additional_information', 'venue_discounted_price_per_event', 'service_type',
#         ]

#     def to_representation(self, instance):
#         response = super().to_representation(instance)
#         response['service_likes'] = VendorServiceViewLike.objects.prefetch_related('vendor_service_id').filter(vendor_service_id=instance, is_liked=True).count()
#         # service_pricing = VendorPricing.objects.prefetch_related('vendor_service_id').filter(vendor_service_id=instance.id)
#         # response['service_pricing'] = ServicePricingSerializers(service_pricing, many=True).data
#         return response


class ServiceDetailsSerializers(serializers.ModelSerializer):
    """
    Class for serializing vendor service details.
    """

    venue_type = VenueTypeSerializer(many=True, read_only=True)
    service_type = serializers.CharField(
        source="service_id.service_type", read_only=True
    )
    service_type_code = serializers.CharField(
        source="service_id.service_type_code", read_only=True
    )
    vendor_contact = serializers.CharField(
        source="vendor_id.contact_number", read_only=True
    )
    vendor_name = serializers.CharField(source="vendor_id.fullname", read_only=True)
    service_views = serializers.SerializerMethodField()
    service_likes = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    plan_data = serializers.SerializerMethodField()
    plan_info = serializers.SerializerMethodField()
    service_pricing = serializers.SerializerMethodField()
    best_suitable_for_detail = serializers.SerializerMethodField(
        "get_best_suitable_for_detail"
    )
    subtype_services = serializers.SerializerMethodField("get_subtype_services")
    contact_details = serializers.SerializerMethodField("get_contact_details")
    payment_cancellation_policy = serializers.SerializerMethodField(
        "get_payment_cancellation_policy"
    )
    caterer_services = serializers.SerializerMethodField("get_caterer_services")
    is_favorited = serializers.SerializerMethodField("get_is_favorited")
    document_list = serializers.SerializerMethodField()

    class Meta:
        model = VendorService
        fields = [
            "id",
            "vendor_id",
            "vendor_name",
            "service_id",
            "service_type_code",
            "business_name",
            "business_image",
            "working_since",
            "number_of_events_done",
            "user_group_service_type",
            "website_url",
            "facebook_url",
            "instagram_url",
            "additional_information",
            "area",
            "city",
            "state",
            "pin_code",
            "service_attachments",
            "service_pricing",
            "approval_status",
            "payment_status",
            "share_url",
            "created_at",
            "service_type",
            "vendor_contact",
            "reject_reason",
            "is_waved_off",
            "service_views",
            "service_likes",
            "is_liked",
            "plan_data",
            "plan_info",
            "updated_at",
            "about_us",
            "venue_type",
            "share_count",
            "venue_area",
            "delivery_charges",
            "min_capacity",
            "max_capacity",
            "is_under_review",
            "venue_capacity",
            "is_venue_only",
            "is_veg_selected",
            "fix_charges_for_veg",
            "discounted_price_per_plate_veg",
            "menu_for_plate_veg",
            "is_nonveg_selected",
            "fix_charges_for_nonveg",
            "venue_actual_price_per_event",
            "venue_discounted_price_per_event",
            "discounted_price_per_plate_nonveg",
            "fix_charges_for_travel_to_other_city",
            "menu_for_plate_nonveg",
            "is_decoration_available",
            "is_outdoor_decoration_selected",
            "outdoor_decoration_fix_charges",
            "outdoor_decor_image_urls",
            "is_indoor_decoration_selected",
            "indoor_decoration_fix_charges",
            "indoor_decor_image_urls",
            "best_suitable_for",
            "best_suitable_for_detail",
            "additional_facilities",
            "travel_to_venue",
            "fix_charges_for_travel_to_venue",
            "makeup_bridal_actual_price",
            "makeup_bridal_discounted_price",
            "makeup_family_guest_actual_price",
            "makeup_family_guest_discounted_price",
            "is_trial_makeup_provided",
            "fix_charges_for_trial_makeup",
            "is_makeup_extensions_provided",
            "fix_charges_for_makeup_extensions",
            "mehendi_bridal_actual_price_per_hand",
            "mehendi_bridal_discounted_price_per_hand",
            "mehendi_guest_actual_price_per_hand",
            "mehendi_guest_discounted_price_per_hand",
            "subtype_services",
            "contact_details",
            "payment_cancellation_policy",
            "caterer_services",
            "is_favorited",
            "is_documents_verified",
            "document_list",
            "is_share_url_updated",
            "sitting_capacity",
            "floating_capacity",
            "city_wise_prices"
        ]


    def get_document_list(self, instance):
        docs = instance.vendordocument_set.filter(is_verified=True)
        return DocumentListingDetailSerializer(docs, many=True).data

    def get_payment_cancellation_policy(self, instance):
        payment_cancellation = PaymentCancellation.objects.filter(
            vendor_service_id=instance.id
        )
        payment_cancellation_serialized = ServicePaymentCancellationSerializers(
            payment_cancellation, many=True
        )
        return payment_cancellation_serialized.data

    def get_contact_details(self, instance):
        contact_details = ServiceContactDetail.objects.filter(
            vendor_service_id=instance.id
        )
        contact_detail_serialized = ServiceContactDetailsSerializers(
            contact_details, many=True
        )
        return contact_detail_serialized.data

    def get_subtype_services(self, instance):
        service_subtypes = instance.subtypes.all()
        return ServiceSubtypeDetailSerializer(service_subtypes, many=True).data

    def get_service_pricing(self, instance):
        service_pricing = VendorPricing.objects.filter(vendor_service_id=instance.id)
        return ServicePricingSerializers(service_pricing, many=True).data

    def get_is_favorited(self, instance):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.favorites.filter(id=instance.id).exists()
        return False

    def get_is_liked(self, instance):
        user = self.context["request"].user
        if user.is_authenticated:
            return instance.vendorserviceviewlike_set.filter(
                user_id=user, is_liked=True
            ).exists()
        return False

    def get_service_views(self, instance):
        vendor_service_id = instance.id
        vendor_service_view_count = (
            VendorServiceViewLike.objects.filter(vendor_service_id=vendor_service_id)
            .filter(is_viewed=True)
            .count()
        )
        return vendor_service_view_count

    def get_service_likes(self, instance):
        return instance.vendorserviceviewlike_set.filter(is_liked=True).count()

    def get_plan_info(self, instance):
        today = datetime.now().date()
        plans = VendorPlan.objects.filter(
            vendor_service_id=instance,
            plan_status="ACTIVE",
            ends_on__date__gte=today,
        ).order_by("-created_on")
        if plans.exists():
            return VendorPlanSerializer(plans.first(), many=False).data
        return None


    def get_plan_data(self, instance):
        data = {}
        vendor_id = instance.vendor_id.id
        vendor_service_id = instance.id
        vendor_plan_data = VendorPlan.objects.filter(
            vendor_service_id__vendor_id_id=vendor_id,
            vendor_service_id=vendor_service_id,
        )
        try:
            if vendor_plan_data.exists():
                vendor_plan = vendor_plan_data.order_by("-created_on")
                vendor_plan_serialized = VendorPlanSerializer(vendor_plan.first())
                vendor_plan_data = vendor_plan.first()
                if not vendor_plan_data.subscription_response:
                    data = {
                        "plan_purchased": False,
                        "expires_at": vendor_plan_data.ends_on,
                        "expired": datetime.now() > vendor_plan_data.ends_on,
                        "type": vendor_plan_data.subscription_type,
                    }

                elif "ios_device" in vendor_plan_data.subscription_response:
                    verify_apple_receipt_data = verify_apple_receipt(
                        vendor_plan_data.subscription_response["transactionReceipt"],
                        vendor_plan_data.subscription_id,
                    )
                    data.update(
                        {
                            "plan_purchased": True,
                            "expires_at": vendor_plan_serialized.data.get("ends_on"),
                            "expired": False,
                        }
                    )
                    if verify_apple_receipt_data["is_expire"]:
                        vendor_plan_status_update(vendor_plan_data)
                        data.update({"expired": True})
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
                    receipt_response = verify_google_play(Purchase_Token, Product_Id)
                    is_expired = receipt_response.is_expired
                    data.update(
                        {
                            "plan_purchased": True,
                            "expires_at": vendor_plan_serialized.data.get("ends_on"),
                            "expired": False,
                        }
                    )
                    if is_expired:
                        vendor_plan_status_update(vendor_plan_data)
                        data.update({"expired": True})
            else:
                data = {
                    "plan_purchased": False,
                    "expires_at": vendor_plan_data.ends_on,
                    "expired": datetime.now() < vendor_plan_data.ends_on,
                }
        except Exception as e:
            pass
        return data

    def get_best_suitable_for_detail(self, instance):
        suitables = instance.best_suitable_for.all()
        return ServiceSuitableForSerializer(suitables, many=True).data

    def get_caterer_services(self, instance):
        cater_services = instance.cater_menu.all()
        return CatererServiceMenuSerializer(cater_services, many=True).data


class ServiceContactDetailsSerializers(serializers.ModelSerializer):
    """
    class for serializing service contact details.
    """

    class Meta:
        model = ServiceContactDetail
        fields = [
            "id",
            "vendor_service_id",
            "contact_person",
            "contact_email",
            "contact_number",
        ]


class ServiceShareUrlSerializers(serializers.ModelSerializer):
    """
    class for serializing service contact details.
    """

    class Meta:
        model = VendorService
        fields = ["id", "share_url", "share_count"]


class UserCartUrlSerializers(serializers.ModelSerializer):
    """
    class for serializing service contact details.
    """

    class Meta:
        model = CustomUser
        fields = ["id", "cart_url"]


class UpdateContactDetailsSerializers(serializers.ModelSerializer):
    """
    class for serializing service contact details.
    """

    class Meta:
        model = ServiceContactDetail
        fields = [
            "id",
            "vendor_service_id_id",
            "contact_person",
            "contact_email",
            "contact_number",
        ]


class ServiceBusinessSerializers(serializers.ModelSerializer):
    """
    class for serializing service contact details.
    """

    class Meta:
        model = VendorService
        fields = ["id", "business_name"]


class ServicePricingSerializers(serializers.ModelSerializer):
    """
    class for serializing service pricing.
    """

    class Meta:
        model = VendorPricing
        fields = [
            "id",
            "vendor_service_id",
            "package_name",
            "package_details",
            "actual_price",
            "discounted_price",
            "attachments",
            "events",
            "hotel_stars",
            "additional_rooms_available",
            "available_rooms_qty",
            "per_room_rate",
            "venue_type",
            "include_serve_executives",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["venue_type"] = (
            str(instance.venue_type) if instance.venue_type else None
        )
        return response


class UpdateServiceStatusSerializers(serializers.ModelSerializer):
    """
    Class for serializing vendor service status.
    """

    class Meta:
        model = VendorService
        fields = ["id", "approval_status"]


class UpdateServiceWaveOffSerializers(serializers.ModelSerializer):
    """
    Class for serializing vendor service wave off fee.
    """

    class Meta:
        model = VendorService
        fields = ["id", "is_waved_off"]


class ServiceViewLikeSerializers(serializers.ModelSerializer):
    """
    Class for serializing vendor service views and likes.
    """

    class Meta:
        model = VendorServiceViewLike
        fields = [
            "id",
            "vendor_service_id",
            "user_id",
            "is_liked",
            "is_viewed",
            "viewed_at",
            "liked_at",
        ]


class UpdateServiceViewLikeSerializers(serializers.ModelSerializer):
    """
    Class for serializing vendor service updating views and likes.
    """

    class Meta:
        model = VendorServiceViewLike
        fields = [
            "id",
            "vendor_service_id",
            "user_id",
            "is_liked",
            "is_viewed",
            "viewed_at",
            "liked_at",
        ]
        validators = []

    def create(self, validated_data):
        like_service, created = VendorServiceViewLike.objects.update_or_create(
            vendor_service_id=validated_data.get("vendor_service_id"),
            user_id=validated_data.get("user_id"),
            defaults={
                "is_liked": validated_data.get("is_liked"),
                "is_viewed": validated_data.get("is_viewed"),
                "viewed_at": validated_data.get("viewed_at"),
                "liked_at": validated_data.get("liked_at"),
            },
        )

        return like_service


class VendorServiceOfferSerializers(serializers.ModelSerializer):
    """
    Class for serializing vendor service offers.
    """

    class Meta:
        model = VendorServiceOffer
        fields = ["vendor_service_id", "image_url", "percentage","start_date", "end_date"]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['business_name'] = instance.vendor_service_id.business_name
        response['service_detail'] = GetServiceSerializers(instance.vendor_service_id.service_id).data
        response['additional_information'] = instance.vendor_service_id.additional_information
        return response

class PlatinumServiceOfferSerializers(serializers.ModelSerializer):
    """
    Class for serializing vendor service offers.
    """

    service_type = serializers.CharField(
        source="service_id.service_type", read_only=True
    )

    class Meta:
        model = VendorService
        fields = [
            "id",
            "business_name",
            "service_type",
            "service_id",
            "is_under_review",
        ]


class CartItemSerializers(serializers.ModelSerializer):
    """
    Class for serializing user cart.
    """

    business_name = serializers.CharField(
        source="vendor_service_id.business_name", read_only=True
    )
    business_image = serializers.CharField(
        source="vendor_service_id.business_image", read_only=True
    )
    area = serializers.CharField(source="vendor_service_id.area")
    city = serializers.CharField(source="vendor_service_id.city")
    state = serializers.CharField(source="vendor_service_id.state")
    pin_code = serializers.CharField(source="vendor_service_id.pin_code")
    cart_url = serializers.SerializerMethodField()
    is_cart_url_updated = serializers.SerializerMethodField()
    package_name = serializers.SerializerMethodField()
    package_details = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "user_id",
            "vendor_service_id",
            "guest_quantity",
            "actual_price",
            "discounted_price",
            "text_to_represent",
            "business_name",
            "business_image",
            "area",
            "city",
            "state",
            "pin_code",
            "package_id",
            "package_name",
            "package_details",
            "is_cart_url_updated",
            "cart_url",
            "created_at",
            "updated_at",
            "is_manual_package",
            "is_with_decoration",
            "is_pre_defined_package",
            "venue_no_of_days",
            "venue_is_rental_only",
            "venue_is_non_veg",
            "is_bridal_selected",
            "is_family_guest_selected",
            "is_makeup_extensions",
            "is_trial_makeup",
            "is_travel",
            "is_other_city",
            "total_cart_value",
            "service_type",
            "cart_details",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if instance.service_type:
            response["service_type"] = GetServiceSerializers(
                instance.service_type, many=False
            ).data
        else:
            response["service_type"] = GetServiceSerializers(
                instance.vendor_service_id.service_id, many=False
            ).data

        return response

    def get_package_name(self, instance):
        if instance.package_id:
            package = VendorPricing.objects.filter(id=instance.package_id.id).values(
                "package_name"
            )
            package_name = package[0]["package_name"]
        else:
            package_name = None
        return package_name

    def get_package_details(self, instance):
        if instance.package_id:
            package = VendorPricing.objects.filter(id=instance.package_id.id).values(
                "package_details"
            )
            package_details = package[0]["package_details"]
        else:
            package_details = None
        return package_details

    def get_cart_url(self, instance):
        url = CustomUser.objects.filter(id=instance.user_id.id).values("cart_url")
        cart_url = url[0]["cart_url"]

        return cart_url

    def get_is_cart_url_updated(self, instance):
        return instance.user_id.is_cart_url_updated if instance.user_id else False


class UpdateServiceOfferSerializers(serializers.ModelSerializer):
    """
    Class for serializing vendor service offers.
    """

    class Meta:
        model = VendorServiceOffer
        fields = ["image_url", "start_date", "percentage", "end_date"]


class AddCartItemSerializers(serializers.ModelSerializer):
    """
    Class for serializing user cart.
    """

    class Meta:
        model = Cart
        fields = [
            "id",
            "user_id",
            "vendor_service_id",
            "guest_quantity",
            "actual_price",
            "discounted_price",
            "text_to_represent",
            "package_id",
            "created_at",
            "updated_at",
            "is_manual_package",
            "is_pre_defined_package",
            "venue_no_of_days",
            "venue_is_rental_only",
            "venue_is_non_veg",
            "is_bridal_selected",
            "is_family_guest_selected",
            "is_makeup_extensions",
            "is_trial_makeup",
            "is_travel",
            "is_other_city",
            "total_cart_value",
            "service_type",
            "is_with_decoration",
            "cart_details",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["service_type"] = GetServiceSerializers(
            instance.service_type, many=False
        ).data
        return response


class ServiceReportDetailsSerializers(serializers.ModelSerializer):
    """
    Class for serializing vendor service details.
    """

    service_type = serializers.CharField(
        source="service_id.service_type", read_only=True
    )
    contact = serializers.CharField(source="vendor_id.contact_number", read_only=True)
    vendor_name = serializers.CharField(source="vendor_id.fullname", read_only=True)
    email = serializers.CharField(source="vendor_id.email", read_only=True)
    # plan_type = serializers.SerializerMethodField()
    subscription_type = serializers.SerializerMethodField()
    service_status = serializers.SerializerMethodField()

    class Meta:
        model = VendorService
        fields = [
            "id",
            "vendor_id",
            "vendor_name",
            "service_id",
            "business_name",
            "user_group_service_type",
            "area",
            "city",
            "state",
            "pin_code",
            "created_at",
            "service_type",
            "email",
            "contact",
            "share_count",
            "subscription_type",
            "service_status",
            "is_under_review",
            "min_capacity",
            "max_capacity",
            "reject_reason",
        ]

    # def get_plan_type(self, instance):
    #     vendor_service_id = instance.id
    #     plan = VendorPlan.objects.filter(vendor_service_id=vendor_service_id).values("plan_id__range_type")
    #     plan_type = plan[0]["plan_id__range_type"]
    #     return plan_type

    def get_subscription_type(self, instance):
        vendor_service_id = instance.id
        # plan = VendorPlan.objects.filter(vendor_service_id=vendor_service_id).values("plan_id__subscription_type")
        # subscription_type = plan[0]["plan_id__subscription_type"]
        plan = VendorPlan.objects.filter(vendor_service_id=vendor_service_id).first()
        subscription_type = plan.subscription_type if plan else ""
        return subscription_type

    def get_service_status(self, instance):
        return (
            instance.get_approval_status_display()
            if instance.get_approval_status_display()
            else ""
        )


class VendorServiceLikeReportSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor_id.fullname", read_only=True)
    email = serializers.CharField(source="vendor_id.email", read_only=True)
    contact = serializers.CharField(source="vendor_id.contact_number", read_only=True)
    service_type = serializers.CharField(source="service_id.service_type", read_only=True)
    subscription_type = serializers.SerializerMethodField()
    service_status = serializers.SerializerMethodField()
    like_count = serializers.IntegerField(read_only=True)
    favorite_count = serializers.IntegerField(read_only=True)
    added_to_cart_count = serializers.IntegerField(read_only=True)
    send_enquiry_count = serializers.IntegerField(read_only=True)
    view_contact_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = VendorService
        fields = [
            "vendor_name", "business_name", "email", "contact", "area", "city",
            "state", "pin_code", "service_type", "subscription_type",
            "service_status", "like_count", "favorite_count",
            'added_to_cart_count', 'send_enquiry_count', 'view_contact_count'
        ]

    def get_subscription_type(self, instance):
        plan = VendorPlan.objects.filter(vendor_service_id=instance.id).first()
        return plan.subscription_type if plan else ""

    def get_service_status(self, instance):
        return instance.get_approval_status_display() or ""


class UserActivityReportSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.fullname", read_only=True)
    mobile = serializers.CharField(source="user.contact_number", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    vendor_name = serializers.CharField(source="vendor.business_name", read_only=True)
    vendor_city = serializers.CharField(source="vendor.city", read_only=True)
    action_date = serializers.SerializerMethodField()

    class Meta:
        model = TrackUserAction
        fields = ["username", "mobile", "email", "vendor_name", "vendor_city", "action", "action_date"]

    def get_action_date(self, obj):
        india_tz = pytz.timezone("Asia/Kolkata")
        return obj.created_at.astimezone(india_tz).strftime("%Y-%m-%d %H:%M:%S")


class UserSessionReportSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.fullname", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    mobile = serializers.CharField(source="user.contact_number", read_only=True)
    address = serializers.CharField(source="user.address", read_only=True)
    session_time = serializers.SerializerMethodField()

    class Meta:
        model = TrackUserSession
        fields = [
            "username", "email", "mobile", "address",
            "action", "city", "session_time"
        ]

    def get_session_time(self, obj):
        india_tz = pytz.timezone("Asia/Kolkata")
        return obj.time.astimezone(india_tz).strftime("%Y-%m-%d %H:%M:%S")


class SuperaAdminListVendorServiceListSerializer(serializers.ModelSerializer):
    service_type = serializers.CharField(
        source="service_id.service_type", read_only=True
    )

    class Meta:
        model = VendorService
        fields = [
            "id",
            "vendor_id",
            "service_id",
            "business_name",
            "is_under_review",
            "reject_reason",
            "area",
            "city",
            "state",
            "pin_code",
            "service_attachments",
            "share_count",
            "approval_status",
            "payment_status",
            "created_at",
            "service_type",
            "updated_at",
        ]


class SuperAdminVendorSerializer(serializers.ModelSerializer):
    vendor_service = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "fullname",
            "email",
            "role",
            "contact_number",
            "status",
            "address_state",
            "address",
            "date_joined",
            "vendor_service",
        ]

    def get_vendor_service(self, instance):
        service_data = SuperaAdminListVendorServiceListSerializer(
            instance.vendorservice_set.all(), many=True
        ).data
        return service_data


class SuperAdminServiceDetailsSerializers(serializers.ModelSerializer):
    """
    Class for serializing vendor service details.
    """

    venue_type = VenueTypeSerializer(many=True, read_only=True)
    service_type = serializers.CharField(
        source="service_id.service_type", read_only=True
    )
    service_type_code = serializers.CharField(
        source="service_id.service_type_code", read_only=True
    )
    vendor_contact = serializers.CharField(
        source="vendor_id.contact_number", read_only=True
    )
    vendor_name = serializers.CharField(source="vendor_id.fullname", read_only=True)
    vendor_email = serializers.CharField(source="vendor_id.email", read_only=True)
    service_views = serializers.IntegerField(
        source="vendor_service_views", read_only=True
    )
    service_likes = serializers.IntegerField(
        source="vendor_service_likes", read_only=True
    )
    is_liked = serializers.SerializerMethodField()
    contact_details = serializers.SerializerMethodField()
    service_pricing = serializers.SerializerMethodField()
    payment_cancellation_policy = serializers.SerializerMethodField()
    plan_data = serializers.SerializerMethodField()
    document_list = serializers.SerializerMethodField()
    subtype_services = serializers.SerializerMethodField("get_subtype_services")

    class Meta:
        model = VendorService
        fields = [
            "id",
            "vendor_id",
            "vendor_name",
            "service_id",
            "vendor_email",
            "service_type_code",
            "business_name",
            "business_image",
            "working_since",
            "number_of_events_done",
            "user_group_service_type",
            "website_url",
            "facebook_url",
            "instagram_url",
            "venue_type",
            "share_count",
            "additional_information",
            "area",
            "city",
            "state",
            "pin_code",
            "service_attachments",
            "subtype_services",
            "delivery_charges",
            "is_under_review",
            "approval_status",
            "payment_status",
            "share_url",
            "created_at",
            "service_type",
            "vendor_contact",
            "min_capacity",
            "max_capacity",
            "reject_reason",
            "is_waved_off",
            "contact_details",
            "service_pricing",
            "service_views",
            "payment_cancellation_policy",
            "service_likes",
            "is_liked",
            "plan_data",
            "updated_at",
            "is_documents_verified",
            "document_list",
            "sitting_capacity",
            "floating_capacity",
            "city_wise_prices",
        ]


    def get_subtype_services(self, instance):
        service_subtypes = instance.subtypes.all()
        return ServiceSubtypeDetailSerializer(service_subtypes, many=True).data

    def get_document_list(self, instance):
        docs = instance.vendordocument_set.filter(is_verified=True)
        return DocumentListingDetailSerializer(docs, many=True).data

    def get_is_liked(self, instance):
        user_id = self.context["request"].data.get("user_id")
        vendor_service_id = instance.id
        return VendorServiceViewLike.objects.filter(
            vendor_service_id=vendor_service_id, user_id=user_id, is_liked=True
        ).exists()

    def get_contact_details(self, instance):
        contact_details = ServiceContactDetail.objects.filter(
            vendor_service_id=instance.id
        )
        return ServiceContactDetailsSerializers(contact_details, many=True).data

    def get_service_pricing(self, instance):
        service_pricing = VendorPricing.objects.filter(vendor_service_id=instance.id)
        return ServicePricingSerializers(service_pricing, many=True).data

    def get_payment_cancellation_policy(self, instance):
        payment_cancellation_policy = PaymentCancellation.objects.filter(
            vendor_service_id=instance.id
        )
        return ServicePaymentCancellationSerializers(
            payment_cancellation_policy, many=True
        ).data

    def get_plan_data(self, instance):
        data = {}
        vendor_id = instance.vendor_id.id
        vendor_service_id = instance.id
        vendor_plan_data = VendorPlan.objects.filter(
            vendor_service_id__vendor_id_id=vendor_id,
            vendor_service_id=vendor_service_id,
        )
        try:
            if vendor_plan_data.exists():
                vendor_plan = vendor_plan_data.order_by("-created_on")
                vendor_plan_serialized = VendorPlanSerializer(vendor_plan.first())
                vendor_plan_data = vendor_plan.first()
                if "ios_device" in vendor_plan_data.subscription_response:
                    verify_apple_receipt_data = verify_apple_receipt(
                        vendor_plan_data.subscription_response["transactionReceipt"],
                        vendor_plan_data.subscription_id,
                    )
                    data.update(
                        {
                            "plan_purchased": True,
                            "expires_at": vendor_plan_serialized.data.get("ends_on"),
                            "expired": False,
                        }
                    )
                    if verify_apple_receipt_data["is_expire"]:
                        vendor_plan_status_update(vendor_plan_data)
                        data.update({"expired": True})
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
                    receipt_response = verify_google_play(Purchase_Token, Product_Id)
                    is_expired = receipt_response.is_expired
                    data.update(
                        {
                            "plan_purchased": True,
                            "expires_at": vendor_plan_serialized.data.get("ends_on"),
                            "expired": False,
                        }
                    )
                    if is_expired:
                        vendor_plan_status_update(vendor_plan_data)
                        data.update({"expired": True})
            else:
                data = {"plan_purchased": False, "expires_at": None, "expired": None}
        except Exception as e:
            pass
        return data


class ServiceByTypeSerializer(serializers.ModelSerializer):
    service_type = serializers.CharField(
        source="service_id.service_type", read_only=True
    )
    service_type_code = serializers.CharField(
        source="service_id.service_type_code", read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    vendor_name = serializers.CharField(source="vendor_id.fullname", read_only=True)
    subscription_plan = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    plan_data = serializers.SerializerMethodField()
    service_likes = serializers.SerializerMethodField()
    subtype_services = serializers.SerializerMethodField("get_subtype_services")
    caterer_services = serializers.SerializerMethodField("get_caterer_services")
    share_url = serializers.SerializerMethodField("get_share_url")

    class Meta:
        model = VendorService
        fields = [
            "id",
            "business_name",
            "business_image",
            "area",
            "city",
            "state",
            "vendor_id",
            "vendor_name",
            "service_type_code",
            "pin_code",
            "additional_information",
            "venue_discounted_price_per_event",
            "makeup_bridal_discounted_price",
            "mehendi_bridal_discounted_price_per_hand",
            "service_type",
            "is_favorited",
            "subscription_plan",
            "plan_data",
            "is_liked",
            "share_url",
            "service_likes",
            "share_count",
            "subtype_services",
            "reject_reason",
            "caterer_services",
            "is_share_url_updated",
            "city_wise_prices",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["service_likes"] = instance.vendorserviceviewlike_set.filter(
            is_liked=True
        ).count()
        service_pricing = instance.vendorpricing_set.all()
        response["service_pricing"] = ServicePricingSerializers(
            service_pricing, many=True
        ).data
        return response

    def get_is_favorited(self, instance):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.favorites.filter(id=instance.id).exists()
        return False

    def get_subscription_plan(self, instance):
        today = datetime.now().date()
        plans = (
            VendorPlan.objects.filter(
                vendor_service_id=instance,
                plan_status="ACTIVE",
                ends_on__date__gte=today,
            )
            .order_by("-created_on")
            .values_list("subscription_type", flat=True)[:1]
        )
        if plans:
            return plans[0]
        return None

    def get_plan_data(self, instance):
        today = datetime.now().date()
        plans = VendorPlan.objects.filter(
            vendor_service_id=instance,
            plan_status="ACTIVE",
            ends_on__date__gte=today,
        ).order_by("-created_on")
        if plans.exists():
            return VendorPlanSerializer(plans.first(), many=False).data
        return None

    def get_is_liked(self, instance):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.vendorserviceviewlike_set.filter(
                vendor_service_id_id=instance.id, is_liked=True
            ).exists()
        return False

    def get_service_likes(self, instance):
        return instance.vendorserviceviewlike_set.filter(is_liked=True).count()

    def get_subtype_services(self, instance):
        service_subtypes = instance.subtypes.all()
        return ServiceSubtypeDetailSerializer(service_subtypes, many=True).data

    def get_caterer_services(self, instance):
        cater_menu = instance.cater_menu.all()
        return CatererServiceMenuSerializer(cater_menu, many=True).data

    def get_share_url(self, instance):
        if instance.is_share_url_updated:
            return instance.share_url
        host = self.context["request"].get_host()
        return update_service_share_url(instance, host)


class ListVendorServicesSerializer(serializers.ModelSerializer):
    venue_type = VenueTypeSerializer(many=True, read_only=True)
    service_type = serializers.CharField(
        source="service_id.service_type", read_only=True
    )
    service_type_code = serializers.CharField(
        source="service_id.service_type_code", read_only=True
    )
    vendor_contact = serializers.CharField(
        source="vendor_id.contact_number", read_only=True
    )
    vendor_name = serializers.CharField(source="vendor_id.fullname", read_only=True)
    service_views = serializers.SerializerMethodField()
    service_likes = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    plan_data = serializers.SerializerMethodField()
    service_pricing = serializers.SerializerMethodField()
    best_suitable_for_detail = serializers.SerializerMethodField(
        "get_best_suitable_for_detail"
    )
    subtype_services = serializers.SerializerMethodField("get_subtype_services")
    contact_details = serializers.SerializerMethodField("get_contact_details")
    payment_cancellation_policy = serializers.SerializerMethodField(
        "get_payment_cancellation_policy"
    )
    caterer_services = serializers.SerializerMethodField("get_caterer_services")
    is_favorited = serializers.SerializerMethodField("get_is_favorited")
    document_list = serializers.SerializerMethodField()

    class Meta:
        model = VendorService
        fields = [
            "id",
            "vendor_id",
            "vendor_name",
            "service_id",
            "service_type_code",
            "business_name",
            "business_image",
            "working_since",
            "number_of_events_done",
            "user_group_service_type",
            "website_url",
            "facebook_url",
            "instagram_url",
            "additional_information",
            "area",
            "city",
            "state",
            "pin_code",
            "service_attachments",
            "service_pricing",
            "approval_status",
            "payment_status",
            "share_url",
            "created_at",
            "service_type",
            "vendor_contact",
            "reject_reason",
            "is_waved_off",
            "service_views",
            "service_likes",
            "is_liked",
            "plan_data",
            "updated_at",
            "about_us",
            "venue_type",
            "share_count",
            "venue_area",
            "delivery_charges",
            "min_capacity",
            "max_capacity",
            "is_under_review",
            "venue_capacity",
            "is_venue_only",
            "is_veg_selected",
            "fix_charges_for_veg",
            "discounted_price_per_plate_veg",
            "menu_for_plate_veg",
            "is_nonveg_selected",
            "fix_charges_for_nonveg",
            "venue_actual_price_per_event",
            "venue_discounted_price_per_event",
            "discounted_price_per_plate_nonveg",
            "fix_charges_for_travel_to_other_city",
            "menu_for_plate_nonveg",
            "is_decoration_available",
            "is_outdoor_decoration_selected",
            "outdoor_decoration_fix_charges",
            "outdoor_decor_image_urls",
            "is_indoor_decoration_selected",
            "indoor_decoration_fix_charges",
            "indoor_decor_image_urls",
            "best_suitable_for",
            "best_suitable_for_detail",
            "additional_facilities",
            "travel_to_venue",
            "fix_charges_for_travel_to_venue",
            "makeup_bridal_actual_price",
            "makeup_bridal_discounted_price",
            "makeup_family_guest_actual_price",
            "makeup_family_guest_discounted_price",
            "is_trial_makeup_provided",
            "fix_charges_for_trial_makeup",
            "is_makeup_extensions_provided",
            "fix_charges_for_makeup_extensions",
            "mehendi_bridal_actual_price_per_hand",
            "mehendi_bridal_discounted_price_per_hand",
            "mehendi_guest_actual_price_per_hand",
            "mehendi_guest_discounted_price_per_hand",
            "subtype_services",
            "contact_details",
            "payment_cancellation_policy",
            "caterer_services",
            "is_favorited",
            "is_documents_verified",
            "document_list",
            "is_share_url_updated",
            "sitting_capacity",
            "floating_capacity",
            "city_wise_prices",
        ]

    def get_document_list(self, instance):
        docs = instance.vendordocument_set.filter(is_verified=True)
        return DocumentListingDetailSerializer(docs, many=True).data

    def get_payment_cancellation_policy(self, instance):
        payment_cancellation = PaymentCancellation.objects.filter(
            vendor_service_id=instance.id
        )
        payment_cancellation_serialized = ServicePaymentCancellationSerializers(
            payment_cancellation, many=True
        )
        return payment_cancellation_serialized.data

    def get_contact_details(self, instance):
        contact_details = ServiceContactDetail.objects.filter(
            vendor_service_id=instance.id
        )
        contact_detail_serialized = ServiceContactDetailsSerializers(
            contact_details, many=True
        )
        return contact_detail_serialized.data

    def get_subtype_services(self, instance):
        service_subtypes = instance.subtypes.all()
        return ServiceSubtypeDetailSerializer(service_subtypes, many=True).data

    def get_service_pricing(self, instance):
        service_pricing = VendorPricing.objects.filter(vendor_service_id=instance.id)
        return ServicePricingSerializers(service_pricing, many=True).data

    def get_is_favorited(self, instance):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.favorites.filter(id=instance.id).exists()
        return False

    def get_is_liked(self, instance):
        user = self.context["request"].user
        if user.is_authenticated:
            return instance.vendorserviceviewlike_set.filter(
                user_id=user, is_liked=True
            ).exists()
        return False

    def get_service_views(self, instance):
        vendor_service_id = instance.id
        vendor_service_view_count = (
            VendorServiceViewLike.objects.filter(vendor_service_id=vendor_service_id)
            .filter(is_viewed=True)
            .count()
        )
        return vendor_service_view_count

    def get_service_likes(self, instance):
        return instance.vendorserviceviewlike_set.filter(is_liked=True).count()

    def get_plan_data(self, instance):
        today = datetime.now().date()
        plans = VendorPlan.objects.filter(
            vendor_service_id=instance,
            plan_status="ACTIVE",
            ends_on__date__gte=today,
        ).order_by("-created_on")
        if plans.exists():
            return VendorPlanSerializer(plans.first(), many=False).data
        return None

    def get_best_suitable_for_detail(self, instance):
        suitables = instance.best_suitable_for.all()
        return ServiceSuitableForSerializer(suitables, many=True).data

    def get_caterer_services(self, instance):
        cater_services = instance.cater_menu.all()
        return CatererServiceMenuSerializer(cater_services, many=True).data


class ServiceRegistrationChargesDetailSerializer(serializers.ModelSerializer):
    serviceID = serializers.IntegerField(write_only=True)
    registrationCharges = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)

    class Meta:
        model = ServiceRegistrationChargesDetail
        fields = ['serviceID', 'registrationCharges']

    def validate_serviceID(self, value):
        if not Service.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid serviceID. No such Service exists.")
        return value

    def validate_registrationCharges(self, value):
        if value <= 0:
            raise serializers.ValidationError("Registration charge must be a positive number.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')

        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError("User is not authenticated.")

        service = Service.objects.get(id=validated_data['serviceID'])
        registration_charges = validated_data['registrationCharges']
        user_email = request.user.email

        return ServiceRegistrationChargesDetail.objects.create(
            service_id=service,
            registration_charges=registration_charges,
            created_by=user_email,
            updated_by=user_email
        )
    
class RegPaymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceVendorRegistrationCharges
        fields = [
            'service_id',
            'vendor_id',
            'registration_charges',
            'payment_status',
            'registration_remark',
            'transaction_id',
            'transaction_remark'
            ]
        extra_kwargs = {
            'created_by': {'read_only': True},
            'updated_by': {'read_only': True},
        }
        
    def validate(self, data):
        if data.get('payment_status') == 1 and not data.get('transaction_id'):
            raise serializers.ValidationError("Transaction ID is required when payment status is completed.")
        return data
    
    def create(self, validated_data):
        instance = super().create(validated_data)
        return instance
    
class ServiceRegistrationChargesSerializer(serializers.ModelSerializer):
    service_type = serializers.CharField(source = 'service_id.service_type', read_only=True)
    class Meta:
        model = ServiceRegistrationChargesDetail
        fields = ['service_id','service_type', 'registration_charges']

class VendorServicePendingPayStatusSerializer(serializers.ModelSerializer):
    pending_status = serializers.SerializerMethodField()
    class Meta:
        model = ServiceVendorRegistrationCharges
        fields = ['service_id', 'registration_charges', 'pending_status']

    def get_pending_status(self, obj):
        return obj.payment_status != 1
    
class ServiceRegistrationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceVendorRegistrationCharges
        fields = ['payment_status', 'registration_remark', 'transaction_remark']

class GetVendorServicePaymentDetails(serializers.ModelSerializer):
    service_type = serializers.CharField(source = 'service_id.service_type', read_only=True)
    vendor_name = serializers.CharField(source = 'vendor_id.fullname', read_only=True)

    class Meta:
        model = ServiceVendorRegistrationCharges
        fields = '__all__'