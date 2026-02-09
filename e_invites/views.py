from django.core.management import call_command
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from e_invites.filters import CustomInviteTemplateFilter, TemplateFilter
from e_invites.functions import toggle_favorite
from e_invites.models import InviteTemplate, SavedTemplate, Template
from e_invites.serializers import (
    InviteTemplateSerializer,
    SavedTemplateSerializer,
    TemplateSerializer,
    InviteTemplateDataSerializer,
)
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
    ListAPIView,
    UpdateAPIView,
    RetrieveAPIView,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from users.permissions import IsTokenValid
from users.utils import CustomPagination, ResponseInfo
from utilities import messages, constants
from utilities.scheduler import scheduler, start_scheduler, update_placid_templates
# 
# start_scheduler()


class StartSchedulerAPI(CreateAPIView):
    serializer_class = TemplateSerializer
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return Template.objects.all()

    def create(self, request, *args, **kwargs):
        try:
            # Call your management command
            call_command(
                "run_scheduler"
            )  # Replace 'my_management_command' with the name of your management command

            return Response({"message": constants.SCHEDULER_STARTED}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class UserSavedTemplateAPI(ListAPIView):
    serializer_class = TemplateSerializer
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (IsAuthenticated,)
    http_method_names = ("get", "post")
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ("title",)
    pagination_class = CustomPagination

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UserSavedTemplateAPI, self).__init__(**kwargs)

    def get_queryset(self):
        user = self.request.user
        return Template.objects.filter(template_users__user=user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class SaveOrUnsaveTemplateAPI(ListAPIView, CreateAPIView):
    serializer_class = SavedTemplateSerializer
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (IsAuthenticated,)
    http_method_names = ("get", "post")
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ("template__title",)
    pagination_class = CustomPagination

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(SaveOrUnsaveTemplateAPI, self).__init__(**kwargs)

    def get_queryset(self):
        user = self.request.user
        return SavedTemplate.objects.select_related("user", "template").filter(
            user=user
        )

    def post(self, request, *args, **kwargs):
        template_uuid = request.data.get("template_uuid")
        try:
            template = Template.objects.get(uuid=template_uuid)
            if toggle_favorite(request.user, template):
                self.response_format["data"] = []
                self.response_format["status_code"] = status.HTTP_201_CREATED
                self.response_format["error"] = None
                self.response_format["message"] = messages.TEMPLATED_SAVED
                return Response(self.response_format)
            else:
                self.response_format["data"] = []
                self.response_format["status_code"] = status.HTTP_200_OK
                self.response_format["error"] = None
                self.response_format["message"] = messages.TEMPLATE_REMOVED
                return Response(self.response_format)
        except Template.DoesNotExist:
            self.response_format["data"] = []
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = None
            self.response_format["message"] = messages.TEMPLATE_NOT_FOUND
            return Response(self.response_format)



class TemplateListAPI(ListAPIView):
    serializer_class = TemplateSerializer
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    http_method_names = ("get",)
    search_fields = ("title",)
    pagination_class = CustomPagination
    filterset_class = TemplateFilter

    def get_queryset(self):
        slugify = self.request.query_params.get("slugify", False)
        if slugify:
            for template in Template.objects.all():
                template.save()
            return Template.objects.filter(is_active=True)
        return Template.objects.filter(is_active=True)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
class TemplateDetailAPI(RetrieveAPIView):
    serializer_class = TemplateSerializer
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (AllowAny,)
    http_method_names = ("get",)
    lookup_field = 'uuid'

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(TemplateDetailAPI, self).__init__(**kwargs)


    def get_queryset(self):
        return Template.objects.all()

    def get_object(self):
        queryset = self.get_queryset()
        lookup_value = self.kwargs.get(self.lookup_field)
        
        try:
            # Try using the 'uuid' field first
            return get_object_or_404(queryset, uuid=lookup_value)
        except:
            # If that fails, try using the 'uid' field
            return get_object_or_404(queryset, uid=lookup_value)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)


class AddInviteTemplateAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = InviteTemplateSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddInviteTemplateAPIView, self).__init__(**kwargs)

    def post(self, request):
        """
        Function for creating new Invite Template.
        """
        serialized = self.get_serializer(data=request.data)
        if serialized.is_valid(raise_exception=True):
            serialized.save()
            self.response_format["data"] = serialized.data
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["error"] = None
            self.response_format["message"] = messages.ADDED.format("Invite Template")
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = serialized.errors
            self.response_format["message"] = messages.ERROR.format("Invite Template")
            return Response(self.response_format)


class UpdateInviteTemplateAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = InviteTemplateSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateInviteTemplateAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return InviteTemplate.objects.none()
        invite_template_id = self.kwargs["pk"]
        return InviteTemplate.objects.filter(id=invite_template_id)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            self.response_format["data"] = serializer.data
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = messages.UPDATE.format("Invite template")
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = None
            self.response_format["message"] = messages.ERROR.format("Invite Template")
        return Response(self.response_format)


class InviteTemplateListAPIView(ListAPIView):
    """
    Class for creating API view for getting invite template list.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = InviteTemplateSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = CustomInviteTemplateFilter
    search_fields = ("template_data__title",)
    pagination_class = CustomPagination

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(InviteTemplateListAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return InviteTemplate.objects.none()
        user_id = self.request.query_params.get("user_id", None)
        if user_id:
            return InviteTemplate.objects.exclude(template_url=None).filter(user=user_id)
        else:
            return InviteTemplate.objects.exclude(template_url=None).all()

    def post(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    

class InviteTemplateRetrieveAPIView(RetrieveAPIView):
    """
    Class for creating API view for getting invite template list.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = InviteTemplateSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(InviteTemplateRetrieveAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return InviteTemplate.objects.none()
        user_id = self.request.query_params.get("user_id", None)
        if user_id:
            return InviteTemplate.objects.exclude(template_url=None).filter(user=user_id)
        else:
            return InviteTemplate.objects.exclude(template_url=None).all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)


class GetInviteTemplateAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = InviteTemplateSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetInviteTemplateAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return InviteTemplate.objects.none()
        invite_template_id = self.kwargs["pk"]
        return InviteTemplate.objects.filter(id=invite_template_id)

    def get(self, request, *args, **kwargs):
        invite_template_serialized_data = self.get_serializer(
            self.get_queryset(), many=True
        ).data
        self.response_format["data"] = invite_template_serialized_data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)


class UpdatePlacidTemplateView(GenericAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = TemplateSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdatePlacidTemplateView, self).__init__(**kwargs)

    def post(self, request):
        """
        Function for creating new Invite Template.
        """
        update_placid_templates()
        self.response_format["data"] = {}
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.TEMPLATE_UPDATE
        return Response(self.response_format)


class DistinctTagsAPIView(ListAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)

    def get(self, request, *args, **kwargs):
        # Get all tags and tag_slugs
        templates = Template.objects.values_list('tags', 'tag_slugs')

        distinct_tags = {
            tag: tag_slug
            for tags, tag_slugs in templates
            if tags and tag_slugs
            for tag, tag_slug in zip(tags, tag_slugs)
        }
        
        # Format the response
        response_data = [{"tag": tag, "tag_slug": tag_slug} for tag, tag_slug in distinct_tags.items()]
        return Response(response_data, status=status.HTTP_200_OK)