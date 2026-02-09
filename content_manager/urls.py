from django.conf.urls import url, re_path
from .views import SendSmsView, GetAllSmsRecordsView, GetAllFaqView, GetAllContactDetailsView

urlpatterns = [
    url('send-sms', SendSmsView.as_view(), name='send_sms'),
    url('getDownloadAppSmsRecords', GetAllSmsRecordsView.as_view(), name='get_sms_records'),
    url('getFaq', GetAllFaqView.as_view(), name='get_faq'),
    url('getContactDetails', GetAllContactDetailsView.as_view(), name='get_contact_details'),
]