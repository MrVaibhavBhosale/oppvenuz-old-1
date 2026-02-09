import json
import os

from django.shortcuts import render

# Create your views here.
import requests
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from requests_oauthlib import OAuth2Session
from rest_framework.generics import ListAPIView
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from utilities import constants
from users.utils import CustomPagination
from rest_framework_simplejwt.authentication import JWTAuthentication
from datetime import datetime, timedelta
from pinterest.models import PinterestToken, PinterestAccessToken
from pinterest.serializers import PinterestTokenSerializer
from users.permissions import IsTokenValid
from users.utils import ResponseInfo
from rest_framework import status
from rest_framework.response import Response
from utilities import messages
from decouple import config

# load_dotenv()


def gen_new_access_token(refresh_token):
    """
    gen access token for pinterest
    """
    raw_data = {"grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": "pins:read,boards:read,user_accounts:read"}
    access_token_data = requests.post(
        "https://api.pinterest.com/v5/oauth/token",
        data=raw_data,
        headers={
            "Authorization": f"Basic {config('BASIC_TOKEN')}"},
    )
    access_token = access_token_data.json().get('access_token')
    return access_token


def get_access_token(refresh_token):
    """
    check access token expire or not and return
    """
    access_token_obj = PinterestAccessToken.objects.first()
    today_date = datetime.now().date()
    if access_token_obj:
        access_token = access_token_obj.access_token
        token_expiry_date = access_token_obj.expiry_date
        if today_date <= token_expiry_date:
            return access_token
        else:
            access_token = gen_new_access_token(refresh_token)
            access_token_obj.access_token = access_token
            access_token_obj.expiry_date = today_date + timedelta(days=20)
            access_token_obj.save()
    else:
        access_token = gen_new_access_token(refresh_token)
        PinterestAccessToken.objects.create(access_token=access_token, expiry_date=today_date + timedelta(days=20))
    return access_token


class GetBoardListAPIView(GenericAPIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = PinterestTokenSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetBoardListAPIView, self).__init__(**kwargs)

    def post(self, request):
        refresh_token_object = PinterestToken.objects.first()
        access_token = get_access_token(refresh_token_object.refresh_token)
        all_boards = requests.get(
            "https://api.pinterest.com/v5/boards",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"},
        )
        data = all_boards.json()
        self.response_format["data"] = data.get('items')
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)


class GetBoardPinListAPIView(GenericAPIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = PinterestTokenSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetBoardPinListAPIView, self).__init__(**kwargs)

    def post(self, request):
        pin_title = self.request.query_params.get('pin_title', None)
        ordering = self.request.query_params.get('ordering', None)
        refresh_token_object = PinterestToken.objects.first()
        access_token = get_access_token(refresh_token_object.refresh_token)
        board_id = request.data.get('board_id')
        all_boards = requests.get(
            f"https://api.pinterest.com/v5/boards/{board_id}/pins",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"},
        )
        data = all_boards.json()
        all_data = data.get('items')
        if pin_title:
            all_data = [data for data in all_data if pin_title.lower() in data['title'].lower()]
        if ordering == "oldest":
            all_data = all_data[::-1]

        paginator = PageNumberPagination()
        paginator.page_size = 20

        result_projects = paginator.paginate_queryset(all_data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects)


class GetPinDetailAPIView(GenericAPIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = PinterestTokenSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetPinDetailAPIView, self).__init__(**kwargs)

    def post(self, request):
        refresh_token_object = PinterestToken.objects.first()
        access_token = get_access_token(refresh_token_object.refresh_token)
        pin_id = request.data.get('pin_id')
        all_boards = requests.get(
            f"https://api.pinterest.com/v5/pins/{pin_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"},
        )
        data = all_boards.json()
        self.response_format["data"] = data
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)


class GetAllPinsAPIView(GenericAPIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = PinterestTokenSerializer
    pagination_class = [PageNumberPagination,]

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetAllPinsAPIView, self).__init__(**kwargs)

    def post(self, request):
        pin_title = self.request.query_params.get('pin_title', None)
        ordering = self.request.query_params.get('ordering', None)
        page_size = self.request.query_params.get('page_size', 250)
        bookmark = request.data.get('bookmark', None)
        refresh_token_object = PinterestToken.objects.first()
        access_token = get_access_token(refresh_token_object.refresh_token)
        all_boards = requests.get(
            constants.PINTEREST_API_URL,
            params=dict(page_size=page_size, bookmark=bookmark),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"},
        )
        data = all_boards.json()
        all_data = data.get('items')

        if pin_title:
            all_data = [data for data in all_data if pin_title.lower() in data['title'].lower()]
        if ordering == "oldest":
            all_data = all_data[::-1]

        paginator = PageNumberPagination()
        paginator.page_size = 20

        result_projects = paginator.paginate_queryset(all_data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects, bookmark=data.get('bookmark', None))
