"""
Util function
"""
from django.db.models import Avg, Count, Sum, Max
from .models import Review, ServiceTracker
from collections import defaultdict


def get_total_points_by_service_and_city_optimized():
    # Step 1: Aggregate points by service type and city
    aggregated_data = (
        ServiceTracker.objects.filter(service__is_included=True)
        .values("service__service_type", "city")
        .annotate(total_points=Sum("points"))
        .order_by("service__service_type", "-total_points")
    )

    # Step 2: Determine the city with the highest points for each service type
    highest_points_data = {}
    for entry in aggregated_data:
        service_type = entry["service__service_type"]
        city = entry["city"]
        total_points = entry["total_points"]

        # Only keep the city with the maximum points for each service type
        if service_type not in highest_points_data or total_points > highest_points_data[service_type]["total_points"]:
            highest_points_data[service_type] = {"city": city, "total_points": total_points}

        sorted_services = dict(sorted(highest_points_data.items(), key=lambda item: item[1]['total_points'], reverse=True))

    return sorted_services

def get_total_points_by_service_and_city_new():
    data = ServiceTracker.objects.values("service", "points", "city", "service__service_type").order_by("service__service_type").exclude(service__is_included=False)
    #  Initialize defaultdict to store aggregated results
    aggregated_data = defaultdict(lambda: defaultdict(int))

    # Aggregate data
    for entry in data:
        service_type = entry['service__service_type']
        city = entry['city']
        points = entry['points']
        aggregated_data[service_type][city] += points

    # Find the city with the highest points for each service type
    highest_points_data = {}
    for service_type, cities in aggregated_data.items():
        max_city = max(cities, key=cities.get)
        highest_points_data[service_type] = {max_city: {'total_points': cities[max_city]}}

    return highest_points_data

def calculate_average_rating(vendor_service_id):
    try:
        average_rating = Review.objects.filter(
            vendor_service_id=vendor_service_id
        ).aggregate(Avg("rating"))["rating__avg"]
        if average_rating is not None:
            return round(average_rating, 2)
        return 0  # Return 0 if there are no reviews yet
    except Exception as e:
        # Handle exceptions, log errors, or return an appropriate value based on your use case
        return 0


def calculate_total_reviews(vendor_service_id):
    try:
        total_reviews = Review.objects.filter(
            vendor_service_id=vendor_service_id
        ).count()
        return total_reviews
    except Exception as e:
        # Handle exceptions, log errors, or return an appropriate value based on your use case
        return 0


def get_ratings_counts(vendor_service_id):
    rating_counts = (
        Review.objects.filter(vendor_service_id=vendor_service_id)
        .values("rating")
        .annotate(count=Count("rating"))
        .order_by("rating")
    )
    rating_dict = {i: 0 for i in range(1, 6)}
    for rating_count in rating_counts:
        rating_dict[rating_count["rating"]] = rating_count["count"]
    return rating_dict


def get_vendor_service_detail(vendor_service_id):
    average_ratings = calculate_average_rating(vendor_service_id)
    total_reviews = calculate_total_reviews(vendor_service_id)
    ratings_counts = get_ratings_counts(vendor_service_id)
    return {
        "average_ratings": average_ratings,
        "total_reviews": total_reviews,
        "ratings_counts": ratings_counts,
    }
