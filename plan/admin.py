from django.contrib import admin
from plan.models import Plan, SubscriptionPlan, VendorPlan
# Register your models here.

admin.site.register(Plan)
admin.site.register(SubscriptionPlan)
admin.site.register(VendorPlan)