"""
Feedbacks views
"""
from django_filters.rest_framework import DjangoFilterBackend
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from rest_framework import filters, generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from users.utils import CustomPagination, ResponseInfo
from django.db.models import Q
from rest_framework.views import APIView
from django.core.cache import cache
from utilities import messages
from .functions import get_vendor_service_detail, get_total_points_by_service_and_city_optimized
from .models import Review
from .serializers import AddReviewSerializer, ReviewSerializer


class GetReviewListView(generics.ListAPIView):
    """
    Get list of reviews for a given vendor service id
    """

    serializer_class = ReviewSerializer
    permission_classes = ()
    authentication_classes = ()
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    pagination_class = CustomPagination
    search_fields = [
        "user__fullname",
        "vendor_service__business_name",
        "comment",
    ]

    def get_queryset(self):
        pk = self.kwargs.get("pk", None)
        queryset = Review.objects.filter(vendor_service_id=pk).order_by("-created_at")
        ratings_param = self.request.query_params.get("rating")
        if ratings_param:
            ratings = list(map(int, ratings_param.split(',')))
            queryset = queryset.filter(Q(rating__in=ratings))
        return queryset

    def list(self, request, *args, **kwargs):
        """
        return users list
        """

        paginator = PageNumberPagination()
        paginator.page_size = 20
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        result_projects = paginator.paginate_queryset(data, request)
        return CustomPagination.get_paginated_response(
            paginator,
            result_projects,
            bookmark=get_vendor_service_detail(self.kwargs.get("pk", None)),
        )


class CreateReviewView(generics.CreateAPIView):
    """
    Add a review to existing vendor service
    """

    serializer_class = AddReviewSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [OAuth2Authentication, JWTAuthentication]

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(CreateReviewView, self).__init__(**kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self.response_format["data"] = serializer.data
        self.response_format["error"] = None
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["message"] = messages.ADDED.format("Review")
        return Response(self.response_format, status=status.HTTP_201_CREATED)


class ServiceCityRelationView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(ServiceCityRelationView, self).__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        total_points_data = get_total_points_by_service_and_city_optimized()
        self.response_format["data"] = total_points_data
        self.response_format["error"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_200_OK)


class NewServiceCityRelationView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def __init__(self, **kwargs):
        """
         Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(NewServiceCityRelationView, self).__init__(**kwargs)

    def format_response(self, data):
        return {
            "data": data,
            "error": None,
            "status_code": status.HTTP_200_OK,
            "message": messages.SUCCESS
        }

    def get(self, request, *args, **kwargs):
        cache_key = 'total_points_data'
        total_points_data = cache.get(cache_key)
        if not total_points_data:
            total_points_data =  get_total_points_by_service_and_city_optimized()
            cache.set(cache_key, total_points_data, timeout=3600)  # Cache for 1 hour
        self.response_format = self.format_response(total_points_data)
        return Response(self.response_format, status=status.HTTP_200_OK)