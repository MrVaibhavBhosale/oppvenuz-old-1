"""
This file is used for creating a view for the API,
which takes a web request and returns a web response.
"""

from rest_framework import status
from rest_framework.response import Response
from fcm_django.models import FCMDevice
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.authentication import JWTAuthentication
import boto3
import uuid
from decouple import config
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    ListAPIView,
    UpdateAPIView,
    DestroyAPIView,
    GenericAPIView,
    CreateAPIView,
    RetrieveAPIView,
)
from article.functions import update_article_slugs
from bs4 import BeautifulSoup
from utilities import messages
from .models import (
    Article,
    ArticleLike,
    Banner,
    Testimonial,
    CelebrityCategory,
    Celebrity,
    Blog,
)
from rest_framework.filters import SearchFilter
from .serializers import (
    ArticleSerializer,
    ArticleSlugSerializer,
    LikeArticleSerializers,
    DeleteArticleSerializer,
    DisLikeArticleSerializers,
    BannerSerializer,
    TestimonialSerializer,
    CelebritySerializer,
    CelebrityCategorySerializer,
    BlogSerializer,
)
from users.permissions import (
    IsSuperAdmin,
    IsTokenValid,
)
from users.utils import ResponseInfo, CustomPagination
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.db.models import Count
from utilities.mixins import CSVDownloadMixin
from users.serializers import NotificationSerializer
from users.views import UserLoginAPIView
from users.models import CustomUser
from utilities.constants import DELETED
from django.utils import timezone

class UpdateArticleSlug(ListAPIView):
    serializer_class = ArticleSerializer
    authentication_classes = [JWTAuthentication, OAuth2Authentication]
    permission_classes = [
        AllowAny,
    ]
    queryset = Article.objects.all()

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateArticleSlug, self).__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        update_article_slugs()
        serializer = self.get_serializer(self.get_queryset(), many=True)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)


class GetArticleDetailAPI(RetrieveAPIView):
    serializer_class = ArticleSerializer
    authentication_classes = [OAuth2Authentication, JWTAuthentication]
    permission_classes = [
        AllowAny,
    ]
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Article.objects.select_related("user_id")
            .prefetch_related("cities", "service_types")
            .filter(status="PUBLISHED")
        )

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetArticleDetailAPI, self).__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={"request": request})
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)


class PopularBlogList(ListAPIView):
    serializer_class = ArticleSerializer
    permission_classes = (AllowAny,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = (
        "title",
        "content",
    )
    filterset_fields = ("status",)
    pagination_class = CustomPagination

    def get_queryset(self):
        return (
            Article.objects.filter(status=Article.Status_Choice.PUBLISHED)
            .annotate(like_count=Count("articlelike"))
            .order_by("-like_count")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BannerCreateAPIView(CreateAPIView):
    serializer_class = BannerSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    http_method_names = ("post",)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(BannerCreateAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        return Banner.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["error"] = None
        self.response_format["message"] = messages.ADDED.format("Banner")
        return Response(self.response_format)


class TestimonialCreateAPIView(CreateAPIView):
    serializer_class = TestimonialSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    http_method_names = ("post",)

    def __init__(self, **kwargs):
        self.response_format = ResponseInfo().response
        super(TestimonialCreateAPIView, self).__init__(**kwargs)

    def upload_to_s3(self, file_obj, filename):
        try:
            bucket = config("S3_BUCKET_NAME")
            s3 = boto3.client(
                "s3",
                aws_access_key_id=config("s3AccessKey"),
                aws_secret_access_key=config("s3Secret"),
            )
            unique_filename = f"{uuid.uuid4()}_{filename}"
            key = f"testimonials/{unique_filename}"
            s3.upload_fileobj(
                file_obj,
                bucket,
                key,
                ExtraArgs={
                    "ACL": "public-read",
                    "ContentType": file_obj.content_type
                }
            )
            return f"https://{bucket}.s3.amazonaws.com/{key}"
        except Exception as e:
            raise ValidationError({"media": f"Failed to upload media to S3: {str(e)}"})

    def create(self, request, *args, **kwargs):
        data = request.data
        media = {}

        image = request.FILES.get('image')
        video = request.FILES.get('video')

        if image and video:
            raise ValidationError({"media": "Cannot upload both image and video."})

        if image:
            if image.size > 1 * 1024 * 1024:
                raise ValidationError({"media": "Image size must not exceed 1MB."})
            if image.content_type not in ["image/png", "image/jpeg"]:
                raise ValidationError({"media": "Only PNG and JPEG images are allowed."})
            media['image'] = self.upload_to_s3(image, image.name)

        if video:
            if video.size > 1 * 1024 * 1024:
                raise ValidationError({"media": "Video size must not exceed 1MB."})
            if video.content_type != "video/mp4":
                raise ValidationError({"media": "Only MP4 videos are allowed."})
            media['video'] = self.upload_to_s3(video, video.name)

        if not (image or video):
            raise ValidationError({"media": "Please upload either an image or a video."})

        data_dict = {
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "state": data.get("state"),
            "city": data.get("city"),
            "description": data.get("description"),
            "media": media,
        }

        serializer = self.get_serializer(data=data_dict)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        self.response_format['data'] = serializer.data
        self.response_format['status_code'] = status.HTTP_201_CREATED
        self.response_format['message'] = 'Testimonial added successfully.'
        return Response(self.response_format, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.email)
        
        
class CelebrityCategoryCreateAPIView(CreateAPIView):
    serializer_class = CelebrityCategorySerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    http_method_names = ("post",)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(CelebrityCategoryCreateAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        return CelebrityCategory.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["error"] = None
        self.response_format["message"] = messages.ADDED.format("Celebrity Category")
        return Response(self.response_format)


class CelebrityCreateAPIView(CreateAPIView):
    serializer_class = CelebritySerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    http_method_names = ("post",)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(CelebrityCreateAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        return Celebrity.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        message = "🚨 New Celebrity Alert! 🌟 Be the first to know about the latest addition. Tap to find out more! "
        params = "{" + '"celebrity_id": {}'.format(instance.id) + "}"
        all_users = CustomUser.objects.filter(role="USER", status="ACTIVE").values_list(
            "id", flat=True
        )
        for user in all_users:
            notification_data = {
                "message": message,
                "status": "UR",
                "user_id": user,
                "notification_type": "CELEBRITY_ADDED",
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

        headers = self.get_success_headers(serializer.data)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["error"] = None
        self.response_format["message"] = messages.ADDED.format("Celebrity")
        return Response(self.response_format)


class ListBannersAPIView(ListAPIView, CSVDownloadMixin):
    serializer_class = BannerSerializer
    authentication_classes = ()
    permission_classes = ()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("is_featured",)
    http_method_names = ("get",)
    pagination_class = CustomPagination

    def get_queryset(self):
        return Banner.objects.all().order_by("?")

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


class ListTestimonialsAPIView(ListAPIView, CSVDownloadMixin):
    serializer_class = TestimonialSerializer
    authentication_classes = ()
    permission_classes = ()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("status_type",)
    http_method_names = ("get",)
    pagination_class = None

    def get_queryset(self):
        return Testimonial.objects.all().order_by("?")

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

class ListApprovedTestimonialsAPIView(ListAPIView, RetrieveAPIView):
    serializer_class = TestimonialSerializer
    authentication_classes = ()
    permission_classes = ()
    filter_backends = (DjangoFilterBackend,)
    http_method_names = ("get",)
    lookup_field = 'id'
    pagination_class = None

    def get_queryset(self):
        return Testimonial.objects.filter(status_type=2).order_by("?")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ListCelebrityCategoriesAPIView(ListAPIView):
    serializer_class = CelebrityCategorySerializer
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = ("title",)
    http_method_names = ("get",)
    search_fields = ("title",)
    pagination_class = CustomPagination

    def get_queryset(self):
        return CelebrityCategory.objects.all()

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


class ListCelebrityAPIView(ListAPIView, CSVDownloadMixin):
    serializer_class = CelebritySerializer
    authentication_classes = ()
    permission_classes = ()
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_fields = ("profession", "category")
    http_method_names = ("get",)
    search_fields = (
        "profession",
        "name",
        "description",
        "category__title",
    )
    pagination_class = CustomPagination

    def get_queryset(self):
        return Celebrity.objects.all().order_by("-updated_at")

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


class BannerUpdateAPIView(UpdateAPIView):
    serializer_class = BannerSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    http_method_names = ("patch", "put")

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(BannerUpdateAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        return Banner.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_205_RESET_CONTENT
        self.response_format["error"] = None
        self.response_format["message"] = messages.UPDATE.format("Banner")
        return Response(self.response_format)


class TestimonialUpdateAPIView(UpdateAPIView):
    serializer_class = TestimonialSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["patch", "put"]

    def __init__(self, **kwargs):
        self.response_format = {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "error": None,
            "data": None,
            "message": None
        }
        super().__init__(**kwargs)

    def get_queryset(self):
        return Testimonial.objects.all()

    def perform_update(self, serializer):
        if serializer.validated_data.get("status_type") == 2:
           serializer.instance.approved_at = timezone.now()
           serializer.instance.approved_by = self.request.user.email
        serializer.save()

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            self.response_format.update({
                "success": True,
                "status_code": status.HTTP_200_OK,
                "data": serializer.data,
                "message": "Testimonial updated successfully."
            })
            return Response(self.response_format)
        except Exception as e:
            self.response_format.update({
                "status_code": status.HTTP_400_BAD_REQUEST,
                "error": str(e),
                "message": "Failed to update testimonial"
            })
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)


class CelebrityUpdateAPIView(UpdateAPIView, RetrieveAPIView):
    serializer_class = CelebritySerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    http_method_names = ("patch", "put", "get")

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(CelebrityUpdateAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        return Celebrity.objects.filter(id=self.kwargs["pk"])

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


class BannerDeleteAPIView(DestroyAPIView):
    serializer_class = BannerSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    http_method_names = ("delete",)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(BannerDeleteAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        return Banner.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_204_NO_CONTENT
        self.response_format["error"] = None
        self.response_format["message"] = messages.DELETE.format("Banner")
        return Response(self.response_format)


class TestimonialDeleteAPIView(DestroyAPIView):
    serializer_class = TestimonialSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid)
    http_method_names = ("delete",)

    def __init__(self, **kwargs):
        self.response_format = {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "error": None,
            "data": None,
            "message": None
        }
        super().__init__(**kwargs)

    def get_queryset(self):
        return Testimonial.objects.all()

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            instance.status_type = 3
            instance.comment = request.data.get('comment', '')
            instance.save()
            
            self.response_format.update({
                "message": messages.DELETE.format("Testimonial"),
                "data": {
                    "id": instance.id,
                    "status_type": 3,
                    "comment": instance.comment
                }
            })
            
            return Response(self.response_format)
            
        except Exception as e:
            self.response_format.update({
                "success": False,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "error": str(e),
                "message": "Deletion failed"
            })
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

class CelebrityDeleteAPIView(DestroyAPIView):
    serializer_class = CelebritySerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    http_method_names = ("delete",)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(CelebrityDeleteAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        return Celebrity.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_204_NO_CONTENT
        self.response_format["error"] = None
        self.response_format["message"] = messages.DELETE.format("Celebrity")
        return Response(self.response_format)


class AddArticleAPIView(GenericAPIView):
    """
    Class for creating API view for article creation.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ArticleSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddArticleAPIView, self).__init__(**kwargs)

    def post(self, request):
        """
        Function for creating new articles.
        """
        request.data["user_id"] = request.user.id
        cities = request.data.get("cities")
        service_types = request.data.get("service_types")

        serialized = self.get_serializer(data=request.data)

        if serialized.is_valid(raise_exception=True):
            instance = serialized.save()
            message = "New blog post available! Dive into the latest tech insights now."
            params = "{" + '"article_id": {}'.format(instance.id) + "}"
            all_users = CustomUser.objects.filter(
                role="USER", status="ACTIVE"
            ).values_list("id", flat=True)
            for user in all_users:
                notification_data = {
                    "message": message,
                    "status": "UR",
                    "user_id": user,
                    "notification_type": "ARTICLE_PUBLISHED",
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
            instance.cities.add(*cities)
            instance.service_types.add(*service_types)
            self.response_format["data"] = serialized.data
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["error"] = None
            self.response_format["message"] = "Article created successfully."
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = serialized.errors
            self.response_format["message"] = "Failure."
            return Response(self.response_format)


class UpdateArticleAPIView(UpdateAPIView):
    """
    Class for updating existing article
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ArticleSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateArticleAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the purchases for
        the user as determined by the username portion of the URL.
        """
        if getattr(self, "swagger_fake_view", False):
            return Article.objects.none()
        article_id = self.kwargs["pk"]
        return Article.objects.filter(id=article_id)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.title = request.data.get("title")
        instance.content = request.data.get("content")
        instance.likes = request.data.get("likes")
        instance.status = request.data.get("status")
        instance.image_header = request.data.get("image_header")

        cities = request.data.get("cities", None)
        service_types = request.data.get("service_types", None)
        if cities:
            instance.cities.set(cities)
        if service_types:
            instance.service_types.set(service_types)

        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.partial_update(serializer)
            self.response_format["data"] = serializer.data

        return Response(self.response_format)


class DeleteArticleAPIView(UpdateAPIView):
    """
    Class for updating existing article
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = DeleteArticleSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(DeleteArticleAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the purchases for
        the user as determined by the username portion of the URL.
        """
        if getattr(self, "swagger_fake_view", False):
            return Article.objects.none()
        article_id = self.kwargs["pk"]
        return Article.objects.filter(id=article_id)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = request.data.get("status")

        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.partial_update(serializer)
            self.response_format["data"] = serializer.data

        return Response(self.response_format)


def truncate_html_soup(content, max_length):
    soup = BeautifulSoup(content, "html.parser")
    if len(soup.get_text()) <= max_length:
        return content

    truncated_text = soup.get_text()[:max_length] + "..."
    truncated_soup = BeautifulSoup(truncated_text, "html.parser")
    return str(truncated_soup)


class GetArticleListAPIView(ListAPIView, CSVDownloadMixin):
    """
    Class for creating API view for getting article list.
    """

    permission_classes = (AllowAny,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = ArticleSerializer
    pagination_class = CustomPagination
    filter_backends = (SearchFilter, DjangoFilterBackend)
    filterset_fields = ["status", "service_types__slug", "cities__city_name"]
    search_fields = [
        "title",
    ]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Article.objects.none()

        if (
            self.request.user.is_authenticated
            and self.request.user.role == "SUPER_ADMIN"
        ):
            return Article.objects.exclude(status="DELETED").order_by("-created_at")
        return Article.objects.filter(status="PUBLISHED").order_by("-created_at")

    def truncate_content(self, data):
        max_length = 150  # Set your desired max length here
        for item in data:
            if "content" in item:
                item["short_content"] = truncate_html_soup(item["content"], max_length)
        return data

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if request.GET.get("download") == "csv":
            return self.download_csv(request, queryset, self.serializer_class)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.truncate_content(serializer.data)
            return self.get_paginated_response(paginated_data)

        serializer = self.get_serializer(queryset, many=True)
        truncated_data = self.truncate_content(serializer.data)
        return Response(truncated_data)


# class GetArticleListAPIView(ListAPIView):
#     """
#     Class for creating API view for getting article list.
#     """
#     permission_classes = (AllowAny,)
#     authentication_classes = (OAuth2Authentication, JWTAuthentication)
#     serializer_class = ArticleSerializer

#     def get_queryset(self):
#         if getattr(self, 'swagger_fake_view', False):
#             return Article.objects.none()

#     def post(self, request):
#         paginator = PageNumberPagination()
#         paginator.page_size = 20
#         data = []
#         user_role = request.data['user_role']
#         if user_role == 'SUPER_ADMIN':
#             article_list = Article.objects.exclude(status="DELETED").order_by("-created_at")
#             article_serialized = self.get_serializer(article_list, many=True)
#             article_data = article_serialized.data
#         elif user_role == 'USER':
#             article_list = Article.objects.filter(status="PUBLISHED").order_by("-created_at")
#             article_serialized = self.get_serializer(article_list, many=True)
#             article_data = article_serialized.data

#         for article in article_data:
#             article["likes"] = ArticleLike.objects.filter(article_id=article["id"]).count()
#             data.append(article)

#         result_projects = paginator.paginate_queryset(data, request)
#         return CustomPagination.get_paginated_response(paginator, result_projects)


class SearchArticleAPIView(ListAPIView):
    """
    Class for searching existing article.
    """

    queryset = Article.objects.filter(status="PUBLISHED")
    permission_classes = ()
    authentication_classes = ()
    serializer_class = ArticleSerializer
    filter_backends = (SearchFilter,)

    search_fields = ("title",)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(SearchArticleAPIView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        paginator = PageNumberPagination()
        paginator.page_size = 20
        data = []

        artist_serialized = super().list(request, *args, **kwargs)

        for article in artist_serialized.data:
            article["likes"] = ArticleLike.objects.filter(
                article_id=article["id"]
            ).count()
            data.append(article)

        result_projects = paginator.paginate_queryset(artist_serialized.data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects)


class GetArticleSlugsAPI(ListAPIView):
    serializer_class = ArticleSlugSerializer
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (AllowAny,)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetArticleSlugsAPI, self).__init__(**kwargs)

    def get_queryset(self):
        return Article.objects.filter(status="PUBLISHED")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class LikeDislikeArticleAPIView(CreateAPIView):
    serializer_class = LikeArticleSerializers
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (IsAuthenticated, IsTokenValid)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(LikeDislikeArticleAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        user = self.request.user
        return user.favorites.all()

    def create(self, request, *args, **kwargs):
        user = self.request.user
        article_id = self.kwargs["pk"]
        r = user.like_dislike_article(article_id)
        message = (
            messages.ARTICLE_LIKED_DISLIKED.format("liked")
            if r == 1
            else messages.ARTICLE_LIKED_DISLIKED.format("disliked")
        )
        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["error"] = None
        self.response_format["message"] = message
        return Response(self.response_format)


class LikeArticleAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = LikeArticleSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(LikeArticleAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ArticleLike.objects.none()

    def post(self, request, *args, **kwargs):
        request.data["user_id"] = request.user.id
        request.data["article_id"] = self.kwargs["pk"]
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        self.response_format["data"] = None
        self.response_format["error"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = ["Success."]
        return Response(self.response_format)


class DisLikeArticleAPIView(DestroyAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = DisLikeArticleSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(DisLikeArticleAPIView, self).__init__(**kwargs)

    def delete(self, request, *args, **kwargs):
        article_id = request.data["article_id"]
        user_id = request.user.id
        instance = ArticleLike.objects.filter(article_id=article_id).filter(
            user_id=user_id
        )
        self.perform_destroy(instance)

        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_204_NO_CONTENT
        self.response_format["error"] = None
        self.response_format["message"] = ["Success."]
        return Response(self.response_format)


class BlogCreateAPIView(CreateAPIView):
    queryset = Blog.objects.all()
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = BlogSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["topic"] = data.get("blog_topic", "")
        data["published_date"] = data.get("published_date", None)
        data["category"] = data.get("category", "")
        data["blog_description"] = data.get("blog_description", "")
        data["created_by"] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)