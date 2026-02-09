import json
import os
from django.core.management.base import BaseCommand
from service.models import Service
from decouple import config
import urllib.parse
# load_dotenv()
import requests
from requests_oauthlib import OAuth2Session


class Command(BaseCommand):
    def handle(self, *args, **options):
        client_id = config("CLIENT_ID")
        redirect_uri = "https://www.oppvenuz.com/home"
        authorization_base_url = "https://www.pinterest.com/oauth/"
        token_url = "https://api.pinterest.com/v5/oauth/token"

        pinterest = OAuth2Session(client_id, redirect_uri=redirect_uri, scope="pins:read,boards:read,user_accounts:read")
        authorization_url, _ = pinterest.authorization_url(authorization_base_url)
        print("Please go to the following URL and authorize your application:", authorization_url)

        code = input("Enter the authorization code:")
        data = {"grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri}
        bmi_new_response = requests.post(
            token_url,
            data=data,
            headers={
                     "Authorization": f"Basic {config('BASIC_TOKEN')}"},
        )
        print(bmi_new_response.json(), "****")
