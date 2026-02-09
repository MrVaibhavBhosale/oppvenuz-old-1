from django.conf.urls import url

from .views import CreateReviewView, GetReviewListView, ServiceCityRelationView, NewServiceCityRelationView

urlpatterns = [
    url('v1/serviceCityRelation', ServiceCityRelationView.as_view(), name='service-city-relation'),
    url('v1/newserviceCityRelation', NewServiceCityRelationView.as_view(), name='new-service-city-relation'),
    url("v1/listReview/(?P<pk>.+)", GetReviewListView.as_view(), name="list-reviews"),
    url("v1/createReview", CreateReviewView.as_view(), name="create-review"),
]
