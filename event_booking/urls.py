"""
This file is used as routes for the service app API's.
"""
from django.conf.urls import url
from .views import (DeleteBookingAPIView,
                    AddEventBookingAPIView,
                    GetEventBookingListView,
                    UpdateEventBookingAPIView
                    )

urlpatterns = [
    url('v1/addEventBooking', AddEventBookingAPIView.as_view(), name='add-event'),
    url('addEventBooking', AddEventBookingAPIView.as_view(), name='add-event'),
    
    url('v1/getEventBooking', GetEventBookingListView.as_view(), name='get-booking'),
    url('getEventBooking', GetEventBookingListView.as_view(), name='get-booking'),
    
    url('v1/deleteEventBooking/(?P<pk>.+)', DeleteBookingAPIView.as_view(), name='delete-event'),
    url('deleteEventBooking/(?P<pk>.+)', DeleteBookingAPIView.as_view(), name='delete-event'),
    
    url('v1/updateEventBooking/(?P<pk>.+)', UpdateEventBookingAPIView.as_view(), name='update-event'),
    url('updateEventBooking/(?P<pk>.+)', UpdateEventBookingAPIView.as_view(), name='update-event')
]
