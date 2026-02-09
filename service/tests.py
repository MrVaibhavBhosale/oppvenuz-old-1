"""
Tests for Login View
"""
from rest_framework import status
from rest_framework.test import APITestCase
from service.serializers import Service, GetServiceSerializers
from utilities import routes
from .models import VendorService  # Adjust the import according to your project structure
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


class GetServiceListViewTests(APITestCase):
    """
    test cases for GetServiceListViewTests
    """

    def setUp(self):
        Service.objects.create(service_type="Type1", is_included=True)
        Service.objects.create(service_type="Type2", is_included=False)
        Service.objects.create(service_type="Type3", is_included=True)

    def test_get_service_list(self):
        """Test retrieving the list of services"""
        url = routes.GETSERVICES  # Replace with your URL name for GetServiceListView
        response = self.client.get(url)
        
        # Ensure the response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response data structure
        self.assertIn("data", response.data)
        self.assertIsInstance(response.data["data"], list)

        # Verify returned data matches what is in the database
        services = Service.objects.all().order_by("service_type")
        serializer = GetServiceSerializers(services, many=True)
        self.assertEqual(response.data["data"], serializer.data)

    def test_filter_services(self):
        """Test filtering the service list by 'is_included' field"""
        url = routes.GETSERVICES  # Replace with your URL name for GetServiceListView
        response = self.client.get(url, {"is_included": True})

        # Ensure the response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the filter returns only services where is_included=True
        filtered_services = Service.objects.filter(is_included=True).order_by("service_type")
        serializer = GetServiceSerializers(filtered_services, many=True)
        self.assertEqual(response.data["data"], serializer.data)