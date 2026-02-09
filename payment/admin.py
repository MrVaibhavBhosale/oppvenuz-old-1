from django.contrib import admin
from payment.models import Payment,PaymentCancellation
# Register your models here.
admin.site.register(Payment)
admin.site.register(PaymentCancellation)

