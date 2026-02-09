from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import DownlaodAppMobileNumbers, Faq, ContactDetail
from .serializers import SmsRecordSerializer, AllFieldsSmsRecordSerializer, FaqSerializer, ContactDetailSerializer
from users.utils import send_sms
from decouple import config
import json

class SendSmsView(APIView):
    """
    Class for sending SMS and storing the record.
    """
    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = {"status": "", "data": {}, "message": ""}
        super(SendSmsView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        message = "Thanks for your interest! Download App here: https://oppvenuz.com/download-app"
        resp = send_sms(config('TEXT_LOCAL_API_KEY'), phone_number, 'OPPVNZ', message)

        resp_str = resp.decode('utf-8')
        resp_json = json.loads(resp_str)

        if resp_json and resp_json.get('status') == 'success':
            record, created = DownlaodAppMobileNumbers.objects.update_or_create(
                phone_number=phone_number,
                defaults={'message': message}
            )
            serializer = SmsRecordSerializer(record)
            self.response_format["status"] = "success"
            self.response_format["data"] = serializer.data
            self.response_format['message'] = "SMS sent successfully."
            return Response(self.response_format, status=status.HTTP_201_CREATED)
        else:
            self.response_format["status"] = "failed"
            self.response_format['message'] = "Failed to send SMS."
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

class GetAllSmsRecordsView(APIView):
    def get(self, request, *args, **kwargs):
        records = DownlaodAppMobileNumbers.objects.all()
        serializer = AllFieldsSmsRecordSerializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetAllFaqView(APIView):
    def get(self, request, *args, **kwargs):
        faqs = Faq.objects.all()
        serializer = FaqSerializer(faqs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetAllContactDetailsView(APIView):
    def get(self, request, *args, **kwargs):
        contacts = ContactDetail.objects.all()
        serializer = ContactDetailSerializer(contacts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)