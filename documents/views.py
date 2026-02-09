import requests
import json
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from .serializers import (
    VendorDocumentSerializer,
    AadhaarRequestOtpSerializer,
    AdharVerifyOtpSerializer,
    VendorDocumentUpdateSerializer,
)
from utilities import constants, messages
from .utils import generate_unique_code, get_signdesk_headers, verify_adhar_otp
from users.utils import ResponseInfo
from .models import VendorDocument
from service.models import VendorService


class VendorDocumentUpdateAPI(generics.UpdateAPIView):
    serializer_class = VendorDocumentUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    lookup_field = "id"

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(VendorDocumentUpdateAPI, self).__init__(**kwargs)

    def get_queryset(self):
        if self.request.user.is_staff:
            return VendorDocument.objects.all()
        return VendorDocument.objects.filter(
            vendor_service__vendor_id=self.request.user
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        serializer = VendorDocumentSerializer(instance, many=False)

        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_205_RESET_CONTENT
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_205_RESET_CONTENT)


class SetVendorDocumentVerificationAPI(generics.ListAPIView):
    serializer_class = VendorDocumentSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        for vendor in VendorService.objects.all():
            vendor.has_required_documents()
            print(vendor)
        return Response(
            {"message": "Completed successfully"}, status=status.HTTP_200_OK
        )


class AadhaarRequestOTPAPI(generics.CreateAPIView):
    """
    request otp from adhar card
    """

    serializer_class = AadhaarRequestOtpSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AadhaarRequestOTPAPI, self).__init__(**kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document_id = serializer.validated_data.get("document_id")
        ref_id = generate_unique_code(model=VendorDocument, field_name="reference_id")
        data = json.dumps({"reference_id": ref_id, "source": document_id})
        headers = get_signdesk_headers()
        response = requests.post(
            url=constants.ADHAR_OTP_REQUEST_URL, data=data, headers=headers
        )
        resp_status = response.json().get("status")
        if resp_status == "success":
            obj = serializer.save()
            obj.user = request.user
            obj.reference_id = ref_id
            obj.save()
        self.response_format["data"] = response.json()
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_200_OK)


class AadhaarVerifyOTPAPI(generics.CreateAPIView):
    """
    verify otp from adhar card
    """

    serializer_class = AdharVerifyOtpSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AadhaarVerifyOTPAPI, self).__init__(**kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction_id = serializer.validated_data.get("transaction_id")
        ref_id = serializer.validated_data.get("reference_id")
        otp = serializer.validated_data.get("otp")
        headers = get_signdesk_headers()
        print(ref_id, transaction_id, otp)
        data = json.dumps(
            {
                "reference_id": ref_id,
                "transaction_id": transaction_id,
                "otp": str(otp),
            }
        )
        response = requests.post(
            constants.ADHAR_OTP_VERIFY_URL, data=data, headers=headers
        )
        resp_status = response.json().get("status")
        if resp_status == "success":
            doc = VendorDocument.objects.get(reference_id=ref_id)
            print(doc, "-----------")
            doc.is_verified = True
            doc.save()

            # check if has all required docs
            doc.vendor_service.has_required_documents()
            self.response_format["data"] = VendorDocumentSerializer(
                doc, many=False
            ).data
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = messages.SUCCESS
            return Response(self.response_format, status=status.HTTP_200_OK)
        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
        self.response_format["error"] = None
        self.response_format["message"] = messages.ERROR
        return Response(response.json(), status=status.HTTP_400_BAD_REQUEST)


class PANCardOrGSTVerificationAPI(generics.CreateAPIView):
    """
    Pan card verification view
    """

    serializer_class = AadhaarRequestOtpSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(PANCardOrGSTVerificationAPI, self).__init__(**kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document_id = serializer.validated_data.get("document_id", None)
        document_base64 = serializer.validated_data.get("document_base64", None)
        ref_id = generate_unique_code(model=VendorDocument, field_name="reference_id")
        document_type = serializer.validated_data.get("document_type", None)
        if document_type == "PAN":
            url = constants.PAN_VERIFY_URL
        if document_type == "GST":
            url = constants.GST_VERIFY_URL
        if document_type == "MSME":
            url = constants.MSME_VERIFY_URL

        headers = get_signdesk_headers()
        if document_id and document_type == "MSME":
            data = json.dumps({"reference_id": ref_id, "source": document_id})
        elif document_id:
            data = json.dumps(
                {"reference_id": ref_id, "source_type": "id", "source": document_id}
            )
        else:
            data = json.dumps(
                {
                    "reference_id": ref_id,
                    "source_type": "base64",
                    "source": document_base64,
                }
            )

        response = requests.post(url, data=data, headers=headers)
        resp_status = response.json().get("status")
        if resp_status == "success":
            doc = serializer.save()
            doc.user = request.user
            doc.reference_id = ref_id
            doc.is_verified = True
            doc.save()
            doc.vendor_service.has_required_documents()
            self.response_format["data"] = VendorDocumentSerializer(
                doc, many=False
            ).data
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = messages.SUCCESS
            return Response(self.response_format, status=status.HTTP_200_OK)
        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
        self.response_format["error"] = None
        self.response_format["message"] = messages.ERROR
        return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)


class DummyPANCardOrGSTVerificationAPI(generics.CreateAPIView):
    """
    Pan card verification view
    """

    serializer_class = AadhaarRequestOtpSerializer
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(DummyPANCardOrGSTVerificationAPI, self).__init__(**kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document_id = serializer.validated_data.get("document_id", None)
        document_base64 = serializer.validated_data.get("document_base64", None)
        ref_id = generate_unique_code(model=VendorDocument, field_name="reference_id")
        document_type = serializer.validated_data.get("document_type", None)
        doc = serializer.save()
        doc.user = request.user
        doc.reference_id = ref_id
        doc.is_verified = True
        doc.save()
        doc.vendor_service.has_required_documents()
        self.response_format["data"] = VendorDocumentSerializer(
            doc, many=False
        ).data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_200_OK)
