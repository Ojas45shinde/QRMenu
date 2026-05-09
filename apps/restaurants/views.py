from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Restaurant
from .forms import RestaurantForm


@login_required
def dashboard(request):
    try:
        restaurant = request.user.restaurant
    except Restaurant.DoesNotExist:
        restaurant = None
    return render(request, 'restaurants/dashboard.html', {
        'restaurant': restaurant
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