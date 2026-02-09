"""
This file is used as routes for the service app API's.
"""
from django.conf.urls import url
from .views import (SuccessView,
                    FailureView,
                    GenerateHashKeyView,
                    AddVendorServicePaymentAPIView,
                    UpdatePaymentCancellationAPIView,
                    GetVendorServiceBillingInfoListView,
                    PayuGenerateHashKey,
                    PaymentEmailSend, GetAwsCredAPIView
                    )

urlpatterns = [
    url('v1/updatePaymentCancellation/(?P<pk>.+)', UpdatePaymentCancellationAPIView.as_view(), name='update-service-price'),
    url('updatePaymentCancellation/(?P<pk>.+)', UpdatePaymentCancellationAPIView.as_view(), name='update-service-price'),
    
    url('v1/getBillingInfo/(?P<vendor_service_id>.+)', GetVendorServiceBillingInfoListView.as_view(), name='get-billing-info'),
    url('getBillingInfo/(?P<vendor_service_id>.+)', GetVendorServiceBillingInfoListView.as_view(), name='get-billing-info'),
    
    url('v1/addVendorServicePayment', AddVendorServicePaymentAPIView.as_view(), name='add-vendor-payment'),
    url('addVendorServicePayment', AddVendorServicePaymentAPIView.as_view(), name='add-vendor-payment'),
    
    url('v1/generateHashKey', GenerateHashKeyView.as_view(), name="generate-hash"),
    url('generateHashKey', GenerateHashKeyView.as_view(), name="generate-hash"),
    
    url('v1/payu_generate_hash_key', PayuGenerateHashKey.as_view(), name='payu_generate_hash_key'),
    url('payu_generate_hash_key', PayuGenerateHashKey.as_view(), name='payu_generate_hash_key'),
    
    url('v1/success', SuccessView.as_view(), name="success"),
    url('success', SuccessView.as_view(), name="success"),
    
    url('v1/failure', FailureView.as_view(), name="failure"),
    url('failure', FailureView.as_view(), name="failure"),
    
    url('v1/payment_email_send', PaymentEmailSend.as_view(), name='payment_email_send'),
    url('payment_email_send', PaymentEmailSend.as_view(), name='payment_email_send'),
    
    url('v1/getAwsCred', GetAwsCredAPIView.as_view(), name='getAwsCred'),
    url('getAwsCred', GetAwsCredAPIView.as_view(), name='getAwsCred')
]
