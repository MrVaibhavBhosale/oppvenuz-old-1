"""
This file is used as routes for the pinterest app API's.
"""
from django.conf.urls import url
from pinterest.views import GetBoardListAPIView, GetBoardPinListAPIView, GetPinDetailAPIView, GetAllPinsAPIView

urlpatterns = [
    url('v1/get_board_list', GetBoardListAPIView.as_view(), name='get_board_list'),
    url('get_board_list', GetBoardListAPIView.as_view(), name='get_board_list'),
    
    url('v1/get_board_pin_list', GetBoardPinListAPIView.as_view(), name='get_board_pin_list'),
    url('get_board_pin_list', GetBoardPinListAPIView.as_view(), name='get_board_pin_list'),
    
    url('v1/get_pin_detail', GetPinDetailAPIView.as_view(), name='get_pin_detail'),
    url('get_pin_detail', GetPinDetailAPIView.as_view(), name='get_pin_detail'),
    
    url('v1/get_all_pins', GetAllPinsAPIView.as_view(), name='get_all_pins'),
    url('get_all_pins', GetAllPinsAPIView.as_view(), name='get_all_pins')
]