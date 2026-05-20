from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Restaurant
from .forms import RestaurantForm
from apps.menus.models import RestaurantSubscription
from apps.qrcodes.models import QRCode


@login_required
def dashboard(request):

    try:
        restaurant = request.user.restaurant
    except Restaurant.DoesNotExist:
        restaurant = None

    subscription = None
    total_qrs = 0
    remaining_qrs = 0

    if restaurant:

        # Active subscription
        subscription = RestaurantSubscription.objects.filter(
            restaurant=restaurant,
            is_active=True
        ).first()

        # Total QR count
        total_qrs = QRCode.objects.filter(
            restaurant=restaurant
        ).count()

        # Remaining QR count
        if subscription:
            remaining_qrs = subscription.plan.qr_limit - total_qrs

    return render(request, 'restaurants/dashboard.html', {
        'restaurant': restaurant,
        'subscription': subscription,
        'total_qrs': total_qrs,
        'remaining_qrs': remaining_qrs,
    })

@login_required
def restaurant_edit(request):
    try:
        restaurant = request.user.restaurant
    except Restaurant.DoesNotExist:
        restaurant = None

    if request.method == 'POST':
        form = RestaurantForm(
            request.POST,
            request.FILES,
            instance=restaurant
        )
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            messages.success(request, '✓ Restaurant settings saved successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = RestaurantForm(instance=restaurant)

    return render(request, 'restaurants/restaurant_form.html', {
        'form': form
    })