'''
utility functions
'''
import os
import branchio
from random import shuffle
from feedbacks.models import ServiceTracker, TrackingAction, TrackUserAction
from oppvenuz.settings.settings import PROD_API_URL, DEV_API_URL, STAGING_API_URL, LOCAL_API_URL
from utilities import constants
from django.db.models import Q, Count, OuterRef
from .models import VendorService, Cart
from users.models import CustomUser
from decouple import config
import requests
from rest_framework import pagination

dev_client = branchio.Client(config("DEVELOP_BRANCH_API_KEY"))
staging_client = branchio.Client(config("STAGING_BRANCH_API_KEY"))


def generate_service_share_url(service, env=None):
    if env == 'stage':
        share_url = constants.BRANCHIO_SERVICE_SHARE_PATH_STAGE.format(service.service_id.slug, service.id)
        branch_key = config('DEVELOP_BRANCH_API_KEY')
    elif env == 'dev':
        share_url = constants.BRANCHIO_SERVICE_SHARE_PATH_DEV.format(service.service_id.slug, service.id)
        branch_key = config('DEVELOP_BRANCH_API_KEY')
    else:
        share_url = constants.BRANCHIO_SERVICE_SHARE_PATH.format(service.service_id.slug, service.id)
        branch_key = config('STAGING_BRANCH_API_KEY')
    url = constants.BRANCH_CART_URL
    payload = {
        "data": {
            "$fallback_url": share_url,
            "$desktop_url": share_url
        },
        "branch_key": branch_key
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)

    url = response.json().get('url') or None
    return url


def update_service_share_url(service, host):
    if service.is_share_url_updated:
        return service.share_url
    if host == DEV_API_URL:
        env = 'dev'
    elif host == STAGING_API_URL:
        env = 'stage'
    else:
        env = None

    url = generate_service_share_url(service=service, env=env) if env else generate_service_share_url(service=service)

    service.share_url = url
    service.is_share_url_updated = True
    service.save()
    print(env, service.share_url)
    return service.share_url



def generate_cart_url(env=None):
    url = constants.BRANCH_CART_URL

    if env == 'stage':
        cart_url = constants.BRANCHIO_REDIRECT_PATH_STAGE
        branch_key = config('DEVELOP_BRANCH_API_KEY')
    elif env == 'dev':
        cart_url = constants.BRANCHIO_REDIRECT_PATH_DEV
        branch_key = config('DEVELOP_BRANCH_API_KEY')
    else:
        cart_url = constants.BRANCHIO_REDIRECT_PATH
        branch_key = config('STAGING_BRANCH_API_KEY')


    payload = {
        "data": {
            "$fallback_url": cart_url,
            "$desktop_url": cart_url
        },
        "branch_key": branch_key
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)

    url = response.json().get('url') or None
    return url


def update_user_cart_url(user, host):
    if user.is_cart_url_updated:
        return user.cart_url
    if host == DEV_API_URL:
        env = 'dev'
    elif host == STAGING_API_URL:
        env = 'stage'
    else:
        env = None

    url = generate_cart_url(env=env) if env else generate_cart_url()

    user.cart_url = url
    user.is_cart_url_updated = True
    user.save()
    print(env, user.cart_url)
    return user.cart_url


def get_recommended_services(user: CustomUser):
    """
    This function recommends vendor services based on the user's cart items.

    Args:
        user: A queryset of Cart objects representing the user's cart.

    Returns:
        A queryset of recommended VendorService objects.
    """
    if not Cart.objects.filter(user_id=user).exists():
        print('random generated ................')
        return VendorService.objects.filter(approval_status='A').order_by('?')[:10]

    cart_items = Cart.objects.filter(user_id=user)
    service_ids = set(v.vendor_service_id.service_id.id for v in cart_items)
    cities = set(v.vendor_service_id.city for v in cart_items if v.vendor_service_id.city)
    recommended_services = VendorService.objects.filter(
        service_id__in=service_ids,
        approval_status='A',
        city__in=cities
    ).annotate(
        service_count=Count('id')
    ).filter(service_count__gt=0).order_by('?')[:10]
    return recommended_services

def get_or_create_users_cart_url(user, request=None):
    '''
    get or create users cart url
    '''
    if user.cart_url:
        return user.cart_url
    else:
        host = request.META["HTTP_HOST"]

        if host == PROD_API_URL:
            client = staging_client
        else:
            client = dev_client
        response = client.create_deep_link_url(
                data={
                    "link_type": "user_cart",
                    "redirect_url_path": constants.BRANCHIO_REDIRECT_PATH,
                    "user_id": user.id,
                }
            )
        url = response[branchio.RETURN_URL]
        user.cart_url = url
        user.save()
        return url


def get_user_ip(request):
    '''
    get user ip from request
    '''
    user_ip = request.META.get('HTTP_X_FORWARDED_FOR', None) or request.META.get('REMOTE_ADDR', None)
    return user_ip


def track_action(request, vendor, action):
    ServiceTracker.objects.create(
        user=request.user if request.user.is_authenticated else None,
        vendor=vendor,
        service=vendor.service_id,
        city=vendor.city,
        ip_address=get_user_ip(request),
        action=action,
        points=action
    )

def track_user_action(request, vendor, action):
    TrackUserAction.objects.create(
        user=request.user if request.user.is_authenticated else None,
        vendor=vendor,
        action=action
    )

def is_all_services_verified(user):
    services = VendorService.objects.filter(vendor_id=user.id)
    for service in services:
        if not service.has_required_documents():
            return False
    return True
class CustomPerCategoryPagination(pagination.PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def paginate_category(self, request, queryset, view, category, category_id, bookmark=None):
        page = self.paginate_queryset(queryset, request, view=view)
        serializer_class = view.get_serializer_for_category(category)

        if not serializer_class:
            raise Exception(f"No serializer defined for category: {category}")

        grouped_data = {}
        if page is not None:
            for item in page:
                subcategory = item.service_id.service_type
                grouped_data.setdefault(subcategory, []).append(item)
        else:
            for item in queryset:
                subcategory = item.service_id.service_type
                grouped_data.setdefault(subcategory, []).append(item)

        category_items = []
        for subcategory, item_list in grouped_data.items():
            serializer = serializer_class(item_list, many=True, context={'request': request})
            category_items.append({
                "subcategory": subcategory,
                "items": serializer.data
            })
        if page is not None:
             response_data = {
                "pagination": {
                    "count": self.page.paginator.count,
                    "total_pages": self.page.paginator.num_pages,
                    "page": self.page.number,
                    "page_size": self.page.paginator.per_page,
                    "next_page": self.get_next_link(),
                    "previous_page": self.get_previous_link(),
                    "bookmark": bookmark,
                },
                "category": category,
                "category_id": category_id,
                "items": category_items,
            }
        else:
            response_data = {
                "pagination": {
                    "count": len(queryset),
                    "total_pages": 1,
                    "page": 1,
                    "page_size": len(queryset),
                    "next_page": None,
                    "previous_page": None,
                    "bookmark": bookmark,
                },
                "category": category,
                "category_id": category_id,
                "items": category_items,
            }

        return response_data