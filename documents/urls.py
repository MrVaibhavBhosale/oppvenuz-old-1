"""
Urls config
"""

from django.urls import path
from .views import (
    AadhaarRequestOTPAPI,
    AadhaarVerifyOTPAPI,
    PANCardOrGSTVerificationAPI,
    SetVendorDocumentVerificationAPI,
    VendorDocumentUpdateAPI,
    DummyPANCardOrGSTVerificationAPI,
)

urlpatterns = [
    path("v1/aadhaar-otp", AadhaarRequestOTPAPI.as_view(), name="aadhaar-otp"),
    path("v1/aadhaar-verify", AadhaarVerifyOTPAPI.as_view(), name="aadhaar-verify"),
    path("v1/pan-gst-verify", PANCardOrGSTVerificationAPI.as_view(), name="pan-verify"),
    path(
        "v1/set-doc-verification",
        SetVendorDocumentVerificationAPI.as_view(),
        name="set-doc-verification",
    ),
    path('v1/update-doc-url/<int:id>/', VendorDocumentUpdateAPI.as_view(), name="v1/update-doc-url"),
    path('v1/dummy-doc-verify', DummyPANCardOrGSTVerificationAPI.as_view(), name="dummy-doc-verify"),
]
