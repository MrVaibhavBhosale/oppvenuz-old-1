"""
This file is used as routes for the plan app API's.
"""
from django.conf.urls import url
from .views import (GetVendorPlanAPIView,
                    AddPricingPlanAPIView,
                    UpdatePricingPlanAPIView,
                    GetPricingPlanListAPIView,
                    AddSubscriptionPlanAPIView,
                    GetPlanByServiceTypeAPIView,
                    UpdateSubscriptionPlanAPIView,
                    GetSubscriptionPlanListAPIView,
                    UpdateVendorPlanValidityAPIView,
                    AddVendorSubscriptionPlanAPIView,
                    GetVendorCurrentPlanAPIView, GenerateSignatureAPIView,
                    RenewAllVendorSubscriptionPlan, ListVendorPlanAPIView,
                    VendorPlanDetailAPIView, ServicePlanWaveOffAPI,
                    CreateSilverPlanForAllAPI, RenewAllVendorsSubscriptionPlan
                    )


urlpatterns = [
    url('v1/renewAllVendorPlans', RenewAllVendorsSubscriptionPlan.as_view(), name='renewAllVendorPlans'),
    url('v1/waveOffVendorFee', ServicePlanWaveOffAPI.as_view(), name='waveOffVendorFee'),
    url('v1/listVendorPlans', ListVendorPlanAPIView.as_view(), name='listVendorPlans'),
    url('v1/vendorPlansDetail/(?P<pk>.+)', VendorPlanDetailAPIView.as_view(), name='vendorPlansDetails'),
    url('v1/renewAllVendorPlan', RenewAllVendorSubscriptionPlan.as_view(), name='renewAllVendorPlan'),
    url('v1/updatePlanforAll', CreateSilverPlanForAllAPI.as_view(), name='update-plan-for-all'),
    url('v1/addSubscriptionPlan', AddSubscriptionPlanAPIView.as_view(), name='add-subscription-plan'),
    url('addSubscriptionPlan', AddSubscriptionPlanAPIView.as_view(), name='add-subscription-plan'),

    url('v1/updateSubscriptionPlan/(?P<pk>.+)', UpdateSubscriptionPlanAPIView.as_view(), name='update-subscription-plan'),
    url('updateSubscriptionPlan/(?P<pk>.+)', UpdateSubscriptionPlanAPIView.as_view(), name='update-subscription-plan'),

    url('v1/getSubscriptionPlanList', GetSubscriptionPlanListAPIView.as_view(), name='get-subscription-plan'),
    url('getSubscriptionPlanList', GetSubscriptionPlanListAPIView.as_view(), name='get-subscription-plan'),

    url('v1/addPricingPlan', AddPricingPlanAPIView.as_view(), name='add-pricing-plan'),
    url('addPricingPlan', AddPricingPlanAPIView.as_view(), name='add-pricing-plan'),

    url('v1/updatePricingPlan', UpdatePricingPlanAPIView.as_view(), name='update-pricing-plan'),
    url('updatePricingPlan', UpdatePricingPlanAPIView.as_view(), name='update-pricing-plan'),

    url('v1/getPricingPlanList', GetPricingPlanListAPIView.as_view(), name='get-pricing-plan'),
    url('getPricingPlanList', GetPricingPlanListAPIView.as_view(), name='get-pricing-plan'),

    url('v1/addVendorSubscriptionPlan', AddVendorSubscriptionPlanAPIView.as_view(), name='add-vendor-subscription'),
    url('addVendorSubscriptionPlan', AddVendorSubscriptionPlanAPIView.as_view(), name='add-vendor-subscription'),

    url('v1/getCurrentVendorPlan/(?P<vendor_id>.+)', GetVendorPlanAPIView.as_view(), name='get-vendor-plan'),
    url('getCurrentVendorPlan/(?P<vendor_id>.+)', GetVendorPlanAPIView.as_view(), name='get-vendor-plan'),

    url('v1/getVendorCurrentPlan', GetVendorCurrentPlanAPIView.as_view(), name='get-vendor-current-plan'),
    url('getVendorCurrentPlan', GetVendorCurrentPlanAPIView.as_view(), name='get-vendor-current-plan'),

    url('v1/extendVendorPlanValidity/(?P<pk>.+)', UpdateVendorPlanValidityAPIView.as_view(), name='update-vendor-plan'),
    url('extendVendorPlanValidity/(?P<pk>.+)', UpdateVendorPlanValidityAPIView.as_view(), name='update-vendor-plan'),

    url('v1/getPlanByServiceType', GetPlanByServiceTypeAPIView.as_view(), name='get-plan-by-service-type'),
    url('getPlanByServiceType', GetPlanByServiceTypeAPIView.as_view(), name='get-plan-by-service-type'),

    url('v1/generate_signature', GenerateSignatureAPIView.as_view(), name='generate_signature'),
    url('generate_signature', GenerateSignatureAPIView.as_view(), name='generate_signature')
]
