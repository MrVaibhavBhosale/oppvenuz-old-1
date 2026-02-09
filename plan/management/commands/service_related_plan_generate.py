from django.core.management.base import BaseCommand
from plan.models import Plan
from service.models import Service

# Create your commands here.


class Command(BaseCommand):
    """
    this command execute on initial db setup initial service plan will generate in database.
    """
    help = "Add plan in plan model"

    def handle(self, *args, **options):
        all_service = Service.objects.all()
        for service_obj in all_service:
            for plan_validity_choice in Plan.Validity_Choices:
                for plan_range_choice in Plan.Range_Choice:
                    for plan_subscription_type_choice in Plan.Subscription_type_Choices:
                        if Plan.objects.filter(
                            service_id__id=service_obj.id,
                            range_type=plan_range_choice[0],
                            subscription_type=plan_subscription_type_choice[0],
                            validity_type=plan_validity_choice[0],
                        ).exists():
                            self.stdout.write(self.style.ERROR(f"Plan all ready exists."))
                        else:
                            plan_obj = Plan.objects.create(
                                service_id=service_obj,
                                range_type=plan_range_choice[0],
                                subscription_type=plan_subscription_type_choice[0],
                                price=100,
                                validity_type=plan_validity_choice[0],
                            )
                            self.stdout.write(self.style.SUCCESS(f"Plan - {plan_obj} successfully created."))