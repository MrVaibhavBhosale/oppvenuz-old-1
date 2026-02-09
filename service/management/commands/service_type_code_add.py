import os
from django.core.management.base import BaseCommand
from service.models import Service
from decouple import config
# load_dotenv()


class Command(BaseCommand):
    def handle(self, *args, **options):
        counter = 1
        all_service = Service.objects.all().order_by("service_type")
        for service_obj in all_service:
            service_obj.service_type_code = f"s_{counter}"
            service_obj.save()
            counter = counter + 1
            self.stdout.write(
                self.style.SUCCESS(f"service type code - {service_obj} successfully updated.")
            )
