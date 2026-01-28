from datetime import datetime, timedelta
import time
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from .forms import CustomerForm, BookSlotForm, NewCustomerForm
from .models import Appointment, Worker
from .decorators import onboarding_required
from .utils import does_profile_exist
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib import messages


def default_bookings_choose_slot_url():
    base_url = reverse('bookings_choose_slot')
    params = urlencode({'hours': Appointment.HOURS_CHOICES[0][1]})
    return f'{base_url}?{params}'


def home_view(request):
    if request.user.is_authenticated:
        return redirect('bookings')

        # if does_profile_exist(request.user):
        #    print(request.user.customer_profile.name)
        #    return redirect('bookings')
        # else:
        #    return redirect('profile')

    return render(request, 'home.html')

    # return HttpResponse("<h1>Home page</h1>")

    # context = {'title': 'Welcome'}
    # if request.user.is_authenticated:
    #    context['username'] = request.user.username
    # return render(request, 'home.html', context)


def onboarding_view(request):
    return redirect('onboarding_profile')

def onboarding_profile_view(request):
    if request.method == 'POST':
        form = NewCustomerForm(request.POST)
        if form.is_valid():
            form.save(user=request.user)
            # messages.info(request, "You may now start booking")
            return redirect('home')
    else:
        form = NewCustomerForm()

    return render(request, 'onboarding_profile.html', {'form': form})

@onboarding_required
def profile_view(request):
    context = { # see if this can be removed
        'profile_exist': does_profile_exist(request.user)
    }

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=request.user.customer_profile)
        print(form.data)
        if form.is_valid():
            form.save()
            messages.info(request, "Profile Updated")
    else:
        form = CustomerForm(instance=request.user.customer_profile)

    context['form'] = form
    return render(request, 'profile.html', context)

# <a class="nav-link active" aria-current="page" href="#">Bookings</a>

# views below require onboarding


@onboarding_required
def book_slot_view(request):
    context = {
        'profile_exist': does_profile_exist(request.user)
    }
    return render(request, 'book_slot.html', context)


@onboarding_required
def bookings_view(request):
    context = {
        'profile_exist': does_profile_exist(request.user)
    }

    appointments = request.user.customer_profile.appointments.all()
    context['appointments'] = appointments

    return render(request, 'bookings.html', context)


@onboarding_required
def bookings_choose_hours_view(request):
    context = {
        'profile_exist': does_profile_exist(request.user)
    }
    print(Appointment.HOURS_CHOICES)
    return render(request, 'bookings_choose_hours.html', context)


@onboarding_required
def bookings_choose_slot_view(request):
    context = {
        'profile_exist': does_profile_exist(request.user),
        'choices': Appointment.HOURS_CHOICES
    }
    if request.method == 'POST':
        customer = request.user.customer_profile
        worker = Worker.objects.all().first()  # temp

        start_time = request.POST.get('start_time')
        print(start_time)
        start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S%z")
        # start_time = timezone.now()
        # start_time = datetime.fromtimestamp(ts)
        hours = request.POST.get('hours')
        hours = float(hours)

        new_appointment = Appointment(
            start_time=start_time, hours=hours, customer=customer, worker=worker)
        new_appointment.save()

        print(start_time)
        print(hours)

        messages.success(request, 'Appointment booked.')
        return redirect('bookings')

    else:
        hours = request.GET.get('hours')  # validate user input
        if not hours:
            return redirect(default_bookings_choose_slot_url())
        hours = float(hours)
        context['hours'] = hours

        # limit get to valid choices
        if not any(hours in tup for tup in Appointment.HOURS_CHOICES):
            return redirect(default_bookings_choose_slot_url())

        print(Appointment.HOURS_CHOICES)

        now = timezone.now()
        today_8am = now.replace(hour=8, minute=0, second=0, microsecond=0)
        today_10am = now.replace(hour=10, minute=0, second=0, microsecond=0)
        today_3pm = now.replace(hour=15, minute=0, second=0, microsecond=0)

        slots = [
            {
                'start_time': today_8am,
                'end_time': today_8am + timedelta(hours=hours),
                'hours': 3,
                'price': 60,
            },
            {
                'start_time': today_10am,
                'end_time': today_10am + timedelta(hours=hours),
                'hours': 3,
                'price': 60,
            },
            {
                'start_time': today_3pm,
                'end_time': today_3pm + timedelta(hours=hours),
                'hours': 3,
                'price': 60,
            },
        ]

        forms = []
        context['forms'] = forms

        for slot in slots:
            forms.append(BookSlotForm(
                start_time=slot['start_time'], end_time=slot['end_time'], hours=slot['hours'], price=slot['price']))

        return render(request, 'bookings_choose_slot.html', context)
