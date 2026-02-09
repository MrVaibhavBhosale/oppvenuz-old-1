from django.forms import ValidationError
import django_filters
from .models import Category, VendorService
from django_filters import rest_framework as filters
from django.db.models import Q, Subquery, OuterRef
from plan.models import VendorPlan


class VendorServiceFitlter(filters.FilterSet):
    """
    Custom Fitlterset for vendor services
    """

    city = filters.CharFilter()
    user_group = filters.CharFilter()

    class Meta:
        """
        Meta information
        """

        fields = ("user_group", "city")

    def filter_queryset(self, queryset):
        """
        Filter queryset w.r.t. the given params
        """
        data = self.request.GET
        query = Q()
        if data.get("city"):
            query &= Q(city=data.get("city"))
        if data.get("user_group"):
            query &= Q(user_group_service_type=data.get("user_group"))
        return queryset.filter(query)


class CustomRecordFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(field_name="city", method="get_city")
    service_type = django_filters.CharFilter(
        field_name="slug", method="get_service_type"
    )
    start_date = django_filters.DateFilter(
        field_name="created_at", method="get_start_date"
    )
    end_date = django_filters.DateFilter(field_name="created_at", method="get_end_date")
    user_group = django_filters.CharFilter(
        field_name="user_group_service_type", method="get_user_group"
    )

    def get_city(self, queryset, field_name, value):
        if not value:
            return queryset
        values = "".join(value.split(" ")).split(",")
        queryset = queryset.filter(city__in=values)
        return queryset

    def get_user_group(self, queryset, field_name, value):
        if not value:
            return queryset
        queryset = queryset.filter(user_group_service_type=value)
        return queryset

    def get_service_type(self, queryset, field_name, value):
        print(value)
        if not value:
            return queryset
        values = value.split(",")
        print(values)
        queryset = queryset.filter(service_id_id__slug__in=values)
        return queryset

    def get_start_date(self, queryset, field_name, value):
        if not value:
            return queryset
        queryset = queryset.filter(created_at__date__gte=value)
        return queryset

    def get_end_date(self, queryset, field_name, value):
        if not value:
            return queryset
        queryset = queryset.filter(created_at__date__lte=value)
        return queryset

    class Meta:
        model = VendorService
        fields = ("city", "service_id_id__service_type", "created_at")


class ReportFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name="created_at", method="get_start_date"
    )
    end_date = django_filters.DateFilter(field_name="created_at", method="get_end_date")

    def get_start_date(self, queryset, field_name, value):
        if not value:
            return queryset
        queryset = queryset.filter(created_at__date__gte=value)
        return queryset

    def get_end_date(self, queryset, field_name, value):
        if not value:
            return queryset
        queryset = queryset.filter(created_at__date__lte=value)
        return queryset

    class Meta:
        model = VendorService
        fields = ("created_at",)


class ServiceFilter(filters.FilterSet):
    service_type = filters.CharFilter(
        field_name="service_id__service_type", lookup_expr="icontains"
    )
    city = filters.CharFilter(field_name="city", lookup_expr="iexact")
    price = filters.RangeFilter(field_name="vendorpricing__discounted_price")
    # subscription = filters.CharFilter(field_name="vendorplan__subscription_type", lookup_expr='iexact')
    subscription = filters.CharFilter(
        method="filter_subscription", lookup_expr="iexact"
    )
    venue_type = filters.CharFilter(method="filter_venue_type")
    service_slug = filters.CharFilter(
        field_name="service_id__slug", lookup_expr="icontains"
    )
    approval_status = filters.CharFilter(
        field_name="approval_status", lookup_expr="iexact"
    )
    star_rating = filters.CharFilter(
        field_name="vendorpricing__hotel_stars", lookup_expr="iexact"
    )
    title = filters.CharFilter(
        field_name="subtypes__title", lookup_expr="iexact"
    )

    subcategory = filters.CharFilter(method="filter_by_subcategory")

    def __init__(self, *args, **kwargs):
        super(ServiceFilter, self).__init__(*args, **kwargs)
        # Dynamically add the price range filter based on the service_type
        service_type = self.data.get("service_type", None)
        if service_type == "Venues":
            self.filters["price"] = filters.RangeFilter(
                field_name="venue_discounted_price_per_event"
            )
        else:
            self.filters["price"] = filters.RangeFilter(
                field_name="vendorpricing__discounted_price"
            )

    def filter_subscription(self, queryset, name, value):
        # Subquery to get the latest active plan for each vendor
        latest_active_plan = (
            VendorPlan.objects.filter(
                vendor_service_id=OuterRef("pk"), plan_status="ACTIVE"
            )
            .order_by("-created_on")
            .values("subscription_type")[:1]
        )

        # Filter the queryset based on the latest active plan's subscription type
        return queryset.annotate(
            latest_subscription=Subquery(latest_active_plan)
        ).filter(latest_subscription__iexact=value)
    
    def filter_venue_type(self, queryset, name, value):
        # Filter using either `vendorpricing__venue_type` or `venue_type__slug`
        return queryset.filter(
            Q(vendorpricing__venue_type__iexact=value) |
            Q(subtypes__title__icontains=value)
        )
    def filter_by_subcategory(self, queryset, name, value):        
        if not value:
            return queryset          
        subcategory_obj = Category.objects.filter(id=value).first()
        if not subcategory_obj:
            raise ValidationError({"error": "Invalid subcategory"})
        subcategory = subcategory_obj.service_name.strip().lower()
        if subcategory == "all vendor":           
            return queryset.exclude(service_id__service_type__iexact="venue")
        
        if subcategory == "all venue":
            return queryset.filter(service_id__service_type__iexact="venue")
           
        return queryset.filter(         
            Q(subtypes__title__iexact=subcategory)|
            Q(service_id__service_type__iexact=subcategory)
        )   

    class Meta:
        model = VendorService
        fields = [
            "service_id__service_type",
            "service_id__slug",
            "city",
            "vendorpricing__discounted_price",
            "venue_discounted_price_per_event",
            "venue_type",
            "approval_status",
            "vendorpricing__hotel_stars",
            "vendorpricing__venue_type",
            "subtypes__title",
        ]
