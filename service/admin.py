from django.contrib import admin

# Register your models here.
from service.models import (Service, VendorService, VendorPricing, VendorServiceOffer, ServiceContactDetail, VendorServiceViewLike, Cart,
                            ServiceSuitableFor, ServiceSubTypeDetail, ServiceEvent
                            )

admin.site.register(Service)
admin.site.register(VendorService)
admin.site.register(ServiceContactDetail)
admin.site.register(VendorPricing)
admin.site.register(VendorServiceOffer)
admin.site.register(VendorServiceViewLike)
admin.site.register(Cart)
admin.site.register(ServiceSuitableFor)
admin.site.register(ServiceSubTypeDetail)
admin.site.register(ServiceEvent)