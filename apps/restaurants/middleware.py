from django.http import Http404
from .models import Restaurant


class TenantMiddleware:
    """
    Middleware to attach the current restaurant (tenant)
    to the request based on URL slug.

    Example:
    /m/pizza-palace/        → restaurant_slug = pizza-palace
    /m/pizza-palace/table-1 → restaurant_slug = pizza-palace
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Default: no restaurant attached
        request.restaurant = None

        # Try extracting restaurant_slug from URL
        slug = None
        if hasattr(request, "resolver_match") and request.resolver_match:
            slug = request.resolver_match.kwargs.get("restaurant_slug")

        # If slug exists → fetch restaurant
        if slug:
            try:
                request.restaurant = Restaurant.objects.get(
                    slug=slug,
                    is_active=True
                )
            except Restaurant.DoesNotExist:
                raise Http404("Restaurant not found")

        # Continue request processing
        response = self.get_response(request)
        return response