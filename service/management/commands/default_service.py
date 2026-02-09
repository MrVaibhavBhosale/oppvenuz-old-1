import os
from django.core.management.base import BaseCommand
from service.models import Service
from decouple import config
# load_dotenv()


class Command(BaseCommand):
    def handle(self, *args, **options):
        raw_s3_url = config("RAW_S3_URL", "")
        all_service_data = [
            {
                "service_name": "Honeymoon Packages",
                "service_icons_app": "service_icons/honeymoon+1.png",
                "service_icons_web": "service_icon_web/honeymoon+1_white.svg",
                "service_bg_images_app": "service_bg_images_app/HoneymoonPackages.png",
            },
            {
                "service_name": "Hotel Booking",
                "service_icons_app": "service_icons/booking.png",
                "service_icons_web": "service_icon_web/booking_white.svg",
                "service_bg_images_app": "service_bg_images_app/HotelBooking.png",
            },
            {
                "service_name": "Jewellery",
                "service_icons_app": "service_icons/jewelry+1.png",
                "service_icons_web": "service_icon_web/jewelry+1_white.svg",
                "service_bg_images_app": "service_bg_images_app/Jewellery.png",
            },
            {
                "service_name": "Makeup Artist",
                "service_icons_app": "service_icons/Makeup+Artist.png",
                "service_icons_web": "service_icon_web/Makeup+Artist_white.svg",
                "service_bg_images_app": "service_bg_images_app/MakeupArtist.png",
            },
            {
                "service_name": "Car and Bus Rentals",
                "service_icons_app": "service_icons/car+%26+bus+rentals.png",
                "service_icons_web": "service_icon_web/car+%26+bus+rentals_white.svg",
                "service_bg_images_app": "service_bg_images_app/Car%26BusStand.png",
            },
            {
                "service_name": "Mehendi Artist",
                "service_icons_app": "service_icons/henna-painted-hand.png",
                "service_icons_web": "service_icon_web/Mehendi+Artist_white.svg",
                "service_bg_images_app": "service_bg_images_app/MehendiArtist.png",
            },
            {
                "service_name": "Planner",
                "service_icons_app": "service_icons/celebrity+booking.png",
                "service_icons_web": "service_icon_web/celebrity+booking_white.svg",
                "service_bg_images_app": "service_bg_images_app/Planner.png",
            },
            {
                "service_name": "Choreographer",
                "service_icons_app": "service_icons/Choreographer.png",
                "service_icons_web": "service_icon_web/Choreographer_white.svg",
                "service_bg_images_app": "service_bg_images_app/Choreographer.png",
            },
            {
                "service_name": "Decorators",
                "service_icons_app": "service_icons/Decorator.png",
                "service_icons_web": "service_icon_web/Decorator_white-1.svg",
                "service_bg_images_app": "service_bg_images_app/Decorator.png",
            },
            {
                "service_name": "Doli and Tent Rental",
                "service_icons_app": "service_icons/circus.png",
                "service_icons_web": "service_icon_web/circus_white.svg",
                "service_bg_images_app": "service_bg_images_app/Doli%26Tent.png",
            },
            {
                "service_name": "Event Organiser",
                "service_icons_app": "service_icons/event+1.png",
                "service_icons_web": "service_icon_web/event+1_white.svg",
                "service_bg_images_app": "service_bg_images_app/EventOrganizer.png",
            },
            {
                "service_name": "Fashion Designer and Cloth Store",
                "service_icons_app": "service_icons/dress.png",
                "service_icons_web": "service_icon_web/dress_white.svg",
                "service_bg_images_app": "service_bg_images_app/FashionDesigner.png",
            },
            {
                "service_name": "Fireworks",
                "service_icons_app": "service_icons/fireworks.png",
                "service_icons_web": "service_icon_web/fireworks_white.svg",
                "service_bg_images_app": "service_bg_images_app/Fireworks.png",
            },
            {
                "service_name": "Catering",
                "service_icons_app": "service_icons/Caterer.png",
                "service_icons_web": "service_icon_web/Caterer_white.svg",
                "service_bg_images_app": "service_bg_images_app/Catering.png",
            },
            {
                "service_name": "Cakes",
                "service_icons_app": "service_icons/cake+1.png",
                "service_icons_web": "service_icon_web/cake+1_white.svg",
                "service_bg_images_app": "service_bg_images_app/Cakes.png",
            },
            {
                "service_name": "Flowers and Bouquets",
                "service_icons_app": "service_icons/flower-bouquet.png",
                "service_icons_web": "service_icon_web/flower-bouquet_white.svg",
                "service_bg_images_app": "service_bg_images_app/Flowerist.png",
            },
            {
                "service_name": "Band and DJ Artist",
                "service_icons_app": "service_icons/dj.png",
                "service_icons_web": "service_icon_web/dj_white.svg",
                "service_bg_images_app": "service_bg_images_app/Band%26DJ.png",
            },
            {
                "service_name": "Astrologer and Pandit",
                "service_icons_app": "service_icons/Pandit.png",
                "service_icons_web": "service_icon_web/Pandit_white.svg",
                "service_bg_images_app": "service_bg_images_app/Astrologer%26Pandit.png",
            },
            {
                "service_name": "Accessories and Gift Store",
                "service_icons_app": "service_icons/Gifts.png",
                "service_icons_web": "service_icon_web/Gifts_white.svg",
                "service_bg_images_app": "service_bg_images_app/Gifts.png",
            },
            {
                "service_name": "Photographer",
                "service_icons_app": "service_icons/Photographer.png",
                "service_icons_web": "service_icon_web/Photographer_white.svg",
                "service_bg_images_app": "service_bg_images_app/Photographer.png",
            },
            {
                "service_name": "Security and Bouncer",
                "service_icons_app": "service_icons/verified+1.png",
                "service_icons_web": "service_icon_web/verified+1_white.svg",
                "service_bg_images_app": "service_bg_images_app/SecurityandBouncer.png",
            },
            {
                "service_name": "Venues",
                "service_icons_app": "service_icons/Venue.png",
                "service_icons_web": "service_icon_web/Venue_white.svg",
                "service_bg_images_app": "service_bg_images_app/Venue.png",
            },
            {
                "service_name": "Packers and Movers",
                "service_icons_app": "service_icons/delivery-truck.png",
                "service_icons_web": "service_icon_web/delivery-truck_white.svg",
                "service_bg_images_app": "service_bg_images_app/Packers%26Movers.png",
            },
            {
                "service_name": "Bartenders",
                "service_icons_app": "service_icons/bartender.png",
                "service_icons_web": "service_icon_web/bartender_white.svg",
                "service_bg_images_app": "service_bg_images_app/Bartenders.png",
            },
            {
                "service_name": "Entertainer",
                "service_icons_app": "service_icons/spotlights.png",
                "service_icons_web": "service_icon_web/spotlights_white.svg",
                "service_bg_images_app": "service_bg_images_app/Entertainer.png",
            },
            {
                "service_name": "Videographer",
                "service_icons_app": "service_icons/Videographer.png",
                "service_icons_web": "service_icon_web/Videographer_white.svg",
                "service_bg_images_app": "service_bg_images_app/Videographer.png",
            },
            {
                "service_name": "Flight Bookings",
                "service_icons_app": "service_icons/airplane-ticket+1.png",
                "service_icons_web": "service_icon_web/airplane-ticket+1_white.svg",
                "service_bg_images_app": "service_bg_images_app/FlightBooking.png",
            },
        ]

        for service_data in all_service_data:
            instance, status = Service.objects.update_or_create(
                service_type=service_data["service_name"],
                defaults={
                    "service_icons_app": raw_s3_url + service_data["service_icons_app"],
                    "service_icons_web": raw_s3_url + service_data["service_icons_web"],
                    "service_bg_images_app": raw_s3_url
                    + service_data["service_bg_images_app"],
                },
            )
            self.stdout.write(
                self.style.SUCCESS(f"service - {instance} successfully updated.")
            )
