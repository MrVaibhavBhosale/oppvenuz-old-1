"""
Utility functions
"""

import string
import random
import os
from decouple import config
import json
import requests
from utilities import constants

# load_dotenv()
# SIGNDESK_API_KEY = "83b879c5f8ff7b02a9f6b678c0340dcb"
# SIGNDESK_APPLICATION_ID = "oppvenuzpvtltd_user_uat"

SIGNDESK_API_KEY = "950cd7e09483deecc152f1f02a6db864"
SIGNDESK_APPLICATION_ID = "oppvenuzpvtltd_user_1"


def get_signdesk_headers():
    return {
        "Content-Type": "application/json",
        "x-parse-application-id": SIGNDESK_APPLICATION_ID,
        "x-parse-rest-api-key": SIGNDESK_API_KEY,
    }



def generate_unique_code(model, field_name, length=50):
    characters = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(characters, k=length))
        if not model.objects.filter(**{field_name: code}).exists():
            return code


def mask_document_number(doc_number, visible_digits=4, mask_char="X"):
    masked_section_length = len(doc_number) - visible_digits
    masked_section = mask_char * masked_section_length
    visible_section = doc_number[-visible_digits:]
    return masked_section + visible_section


def verify_adhar_otp(ref_id, txn_id, otp):
    data = json.dumps(
        {
            "reference_id": ref_id,
            "transaction_id": txn_id,
            "otp": otp,
        }
    )
    headers = get_signdesk_headers()
    response = requests.post(
        constants.ADHAR_OTP_VERIFY_URL, data=data, headers=headers
    )
    return response
