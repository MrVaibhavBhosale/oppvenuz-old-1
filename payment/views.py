import os

from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.generics import (GenericAPIView,
                                     ListAPIView,
                                     UpdateAPIView,
                                     )
from utilities import constants

from utilities.commonutils import send_email
from .models import (Payment,
                     PaymentCancellation
                     )
from .serializers import (PayuSerializers,
                          PaymentSerializers,
                          ServicePaymentCancellationSerializers
                          )
from users.permissions import (IsTokenValid,
                               )
# from payu.models import Transaction, CancelRefundCaptureRequests
from users.utils import (ResponseInfo,
                         CustomPagination
                         )
from django.http import HttpResponse
# from payu.gateway import get_hash, check_hash
from hashlib import sha512
from uuid import uuid4
import hashlib
from django.conf import settings
from decouple import config
# load_dotenv()


from oppvenuz.settings.settings import PAYU_MERCHANT_KEY, PAYU_MERCHANT_SALT


class GenerateHashKeyView(GenericAPIView):
    """
    Class for creating API view for Payment gateway homepage.
    """
    permission_classes = ()
    authentication_classes = ()
    serializer_class = PayuSerializers

    def __init__(self, **kwargs):
        """
        Constructor function PaymentSerializers or formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GenerateHashKeyView, self).__init__(**kwargs)

    def post(self, request, *args, **kwags):
        """
        Function for creating a charge.
        """
        key = PAYU_MERCHANT_KEY
        txnid = str(request.data.get('txnid'))
        amount = str(request.data.get('amount'))
        productinfo = str(request.data.get('productinfo'))
        firstname = str(request.data.get('firstname'))
        email = str(request.data.get('email'))
        salt = PAYU_MERCHANT_SALT
        udf1 = ""
        udf2 = ""
        udf3 = ""
        udf4 = ""
        udf5 = ""
        udf6 = ""
        udf7 = ""
        udf8 = ""
        udf9 = ""
        udf10 = ""

        data = {
            'key': key,
            'salt': salt,
            'txnid': txnid,
            'amount': amount,
            'productinfo': productinfo,
            'firstname': firstname,
            'email': email,
        }

        keys = ('txnid', 'amount', 'productinfo', 'firstname', 'email',
                'udf1', 'udf2', 'udf3', 'udf4', 'udf5', 'udf6', 'udf7', 'udf8',
                'udf9', 'udf10')

        hash_string = key + "|" + txnid + "|" + amount + "|" + productinfo + "|" + firstname + "|" + email + "|" + udf1\
                      + "|" + udf2 + "|" + udf3 + "|" + udf4 + "|" + udf5 + "|" + udf6 + "|" + udf7 + "|" + udf8 + "|"\
                      + udf9 + "|" + udf10 + "|" + salt

        def new_get_hash(data, *args, **kwargs):
            hash_value = str(getattr(settings, 'PAYU_MERCHANT_KEY', None))

            for k in keys:
                if data.get(k) is None:
                    hash_value += '|' + str('')
                else:
                    hash_value += '|' + str(data.get(k))

            hash_value += '|' + str(getattr(settings, 'PAYU_MERCHANT_SALT', None))
            hash_value = sha512(hash_value.encode()).hexdigest().lower()
            # Transaction.objects.create(
            #     transaction_id=data.get('txnid'), amount=data.get('amount'))
            return hash_value
        get_hash = new_get_hash

        # hash_key1 = sha512(hash_string.encode())
        generate_hash = get_hash(request.data)

        # hash_key1 = hash_key1.hexdigest().lower()
        data['hash_key'] = generate_hash

        self.response_format["data"] = data
        return Response(self.response_format)


class PayuGenerateHashKey(GenericAPIView):
    serializer_class = PayuSerializers
    def __init__(self, **kwargs):
        """
        Constructor function PaymentSerializers or formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(PayuGenerateHashKey, self).__init__(**kwargs)

    def post(self, request):
        raw_hash = request.data["raw_hash"]
        new_hash_value = raw_hash + str(getattr(settings, 'PAYU_MERCHANT_SALT', None))
        encrypted_hash = sha512(new_hash_value.encode()).hexdigest()
        data = {'hash_data': encrypted_hash}
        self.response_format["data"] = data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = ""
        self.response_format['message'] = "Success."
        return Response(self.response_format)

class SuccessView(GenericAPIView):
    # permission_classes = (IsAuthenticated, IsTokenValid)
    # authentication_classes = (JWTAuthentication,)
    serializer_class = PayuSerializers

    def __init__(self, **kwargs):
        """
        Constructor function PaymentSerializers or formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(SuccessView, self).__init__(**kwargs)

    def post(self, request):
        # code for check hash and success page
        # payu_serializer = self.get_serializer(data=request.data, many=True)
        # if payu_serializer.is_valid(raise_exception=True):
        #     print("INVALID", payu_serializer.data)
        #     payu_serializer.save()

        status = request.data["status"]
        firstname = request.data["firstname"]
        amount = request.data["amount"]
        txnid = request.data["txnid"]
        posted_hash = request.data["hash"]
        key = request.data["key"]
        productinfo = request.data["productinfo"]
        email = request.data["email"]
        salt = PAYU_MERCHANT_SALT
        try:
            additional_charges = request.data["additionalCharges"]
            ret_hash_seq = additional_charges + '|' + salt + '|' + status + '|||||||||||' + email + '|' + firstname + \
                           '|' + productinfo + '|' + amount + '|' + txnid + '|' + key
        except Exception:
            ret_hash_seq = salt + '|' + status + '|||||||||||' + email + '|' + firstname + '|' + productinfo + '|' \
                           + amount + '|' + txnid + '|' + key
        hashh = hashlib.sha512(ret_hash_seq.encode()).hexdigest().lower()
        if hashh == posted_hash:
            # transaction = Transaction.objects.get(transaction_id=txnid)
            # transaction.payment_gateway_type = request.data.get('PG_TYPE')
            # transaction.transaction_date_time = request.data.get('addedon')
            # transaction.mode = request.data.get('mode')
            # transaction.status = status
            # transaction.amount = amount
            # transaction.mihpayid = request.data.get('mihpayid')
            # transaction.bankcode = request.data.get('bankcode')
            # transaction.bank_ref_num = request.data.get('bank_ref_num')
            # transaction.discount = request.data.get('discount')
            # transaction.additional_charges = request.data.get('additionalCharges', 0)
            # transaction.txn_status_on_payu = request.data.get('unmappedstatus')
            # transaction.hash_status = "Success" if hashh == request.data.get('hash') else "Failed"
            # transaction.save()
            message = ["Thank You. Your order status is " + status,
                       "Your Transaction ID for this transaction is " + txnid,
                       "We have received a payment of Rs. " + amount,
                       "Your order will soon be shipped."]

        else:
            message = ["Invalid Transaction. Please try again."]
        data = {
            "txnid": txnid,
            "status": status,
            "amount": amount
        }
        self.response_format["data"] = data
        self.response_format["message"] = message
        return Response(self.response_format)


class FailureView(GenericAPIView):
    # permission_classes = (IsAuthenticated, IsTokenValid)
    # authentication_classes = (JWTAuthentication,)
    serializer_class = PayuSerializers

    def __init__(self, **kwargs):
        """
        Constructor function PaymentSerializers or formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(FailureView, self).__init__(**kwargs)

    def post(self, request):
        # code for check hash and success page

        status = request.data["status"]
        firstname = request.data["firstname"]
        amount = request.data["amount"]
        txnid = request.data["txnid"]
        posted_hash = request.data["hash"]
        key = request.data["key"]
        productinfo = request.data["productinfo"]
        email = request.data["email"]
        salt = PAYU_MERCHANT_SALT
        try:
            additional_charges = request.POST["additionalCharges"]
            ret_hash_seq = additional_charges + '|' + salt + '|' + status + '|||||||||||' + email + '|' + firstname +\
                           '|' + productinfo + '|' + amount + '|' + txnid + '|' + key
        except Exception:
            ret_hash_seq = salt + '|' + status + '|||||||||||' + email + '|' + firstname + '|' + productinfo + '|'\
                           + amount + '|' + txnid + '|' + key
        hashh = hashlib.sha512(ret_hash_seq.encode()).hexdigest().lower()
        if hashh == posted_hash:
            # transaction = Transaction.objects.get(transaction_id=txnid)
            # transaction.payment_gateway_type = request.data.get('PG_TYPE')
            # transaction.transaction_date_time = request.data.get('addedon')
            # transaction.mode = request.data.get('mode')
            # transaction.status = status
            # transaction.amount = amount
            # transaction.mihpayid = request.data.get('mihpayid')
            # transaction.bankcode = request.data.get('bankcode')
            # transaction.bank_ref_num = request.data.get('bank_ref_num')
            # transaction.discount = request.data.get('discount')
            # transaction.additional_charges = request.data.get('additionalCharges', 0)
            # transaction.txn_status_on_payu = request.data.get('unmappedstatus')
            # transaction.hash_status = "Success" if hashh == request.data.get('hash') else "Failed"
            # transaction.save()
            message = ["Thank You. Your order status is " + status,
                       "Your Transaction ID for this transaction is " + txnid,
                       "We have received a payment of Rs. " + amount,
                       "Your order will soon be shipped."]
        else:
            message = ["Invalid Transaction. Please try again."]

        data = {
            "txnid": txnid,
            "status": status,
            "amount": amount
        }
        self.response_format["data"] = data
        self.response_format["message"] = message
        return Response(self.response_format)


class UpdatePaymentCancellationAPIView(UpdateAPIView):
    """
    Class for updating service vendor contact details.
    """
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ServicePaymentCancellationSerializers

    def __init__(self, **kwargs):
        """
        Constructor function PaymentSerializers or formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdatePaymentCancellationAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PaymentCancellation.objects.none()
        payment_cancellation_id = self.kwargs['pk']
        return PaymentCancellation.objects.filter(id=payment_cancellation_id)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()

        instance.vendor_service_id_id = request.data.get("vendor_service_id")
        instance.advance_for_booking = request.data.get("advance_for_booking")
        instance.payment_on_delivery = request.data.get("payment_on_delivery")
        instance.cancellation_policy = request.data.get("cancellation_policy")
        instance.payment_on_event_date = request.data.get("payment_on_event_date")

        payment_cancellation_serializer = self.get_serializer(instance, data=request.data)
        if payment_cancellation_serializer.is_valid(raise_exception=True):
            self.partial_update(payment_cancellation_serializer)
            self.response_format["data"] = payment_cancellation_serializer.data

        return Response(self.response_format)


class GetVendorServiceBillingInfoListView(ListAPIView):
    """
    Class for creating API view for getting vendor service billing details.
    """
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = PaymentSerializers

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Payment.objects.none()

    def get(self, request, *args, **kwargs):
        """
        Function for getting vendor service billing details.
        """
        paginator = PageNumberPagination()
        paginator.page_size = 10
        vendor_service_id = self.kwargs['vendor_service_id']
        vendor_service_billing_list = Payment.objects.filter(vendor_plan_id__vendor_service_id=vendor_service_id)

        vendor_service_billing_serialized = self.get_serializer(vendor_service_billing_list, many=True)
        data = vendor_service_billing_serialized.data

        result_projects = paginator.paginate_queryset(data, request)
        return CustomPagination.get_paginated_response(paginator, result_projects)


class AddVendorServicePaymentAPIView(GenericAPIView):
    """
    Class for creating API view for adding vendor service payment.
    """
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = PaymentSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddVendorServicePaymentAPIView, self).__init__(**kwargs)

    def post(self, request):
        """
        Function for creating new vendor service payment.
        Authorization Header required.
        """
        serialized = self.get_serializer(data=request.data)

        if serialized.is_valid(raise_exception=True):
            serialized.save()

            self.response_format["data"] = serialized.data
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["error"] = None
            self.response_format["message"] = "Vendor service payment created successfully."
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = serialized.errors
            self.response_format['message'] = "Failure."
            return Response(self.response_format)


class PaymentEmailSend(GenericAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = PayuSerializers

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(PaymentEmailSend, self).__init__(**kwargs)

    def post(self, request):
        # code for check hash and success page

        payment_status = request.data.get("status", None)
        if payment_status:
            if payment_status == "SUCCESS":
                # Payment success mail
                template_id = constants.VENDOR_PAYMENT_DONE_TEMPLATE
                data_dict = {"vendor_name": request.user.fullname}
                send_email(template_id, request.user.email, data_dict)
            else:
                # Payment Fail mail
                template_id = constants.VENDOR_PAYMENT_PENDING_TEMPLATE
                data_dict = {"vendor_name": request.user.fullname}
                send_email(template_id, request.user.email, data_dict)

            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["error"] = None
            self.response_format["message"] = "Email send successfully."
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = None
            self.response_format["message"] = "Failure."
            return Response(self.response_format)


class GetAwsCredAPIView(GenericAPIView):
    """
    API for return AWS creditional
    """
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication,)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetAwsCredAPIView, self).__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        data = {
            "S3_BUCKET_NAME": config("S3_BUCKET_NAME", ""),
            "s3AccessKey": config("s3AccessKey", ""),
            "s3Secret": config("s3Secret", "")
        }
        self.response_format["data"] = data
        return Response(self.response_format)

# posted = {}
        # Merchant Key and Salt provided y the PayU.
        # for i in request.data:
        #     posted[i] = request.data[i]
        #     print(i, request.data[i])
        # hash_object = hashlib.sha256(b'randint(0,20)')
        # txnid = hash_object.hexdigest()[0:20]
        # hashh1 = ''
        # posted['txnid'] = txnid
        # hashSequence = "key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5|udf6|udf7|udf8|udf9|udf10"
        # posted['key'] = KEY
        # hash_string = ''
        # hashVarsSeq = hashSequence.split('|')
        # for i in hashVarsSeq:
        #     try:
        #         hash_string += str(posted[i])
        #     except Exception:
        #         hash_string += ''
        #     hash_string += '|'
        # hash_string += SALT
        # hashh1 = hashlib.sha512(hash_string.encode()).hexdigest().lower()

        # hashh = hashlib.sha512(hash_string.encode()).hexdigest().lower()
        # print(hashh)
        # print(data['hash_key'])