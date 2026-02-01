from datetime import datetime, timedelta
import time
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from .forms import CustomerForm, BookSlotForm, NewCustomerForm
from .models import Appointment, AssignedLocation, Worker
from .decorators import onboarding_required
from .utils import does_profile_exist
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib import messages


def default_bookings_choose_date_url():
    base_url = reverse('bookings_choose_date')
    params = urlencode({'hours': Appointment.HOURS_CHOICES[0][1]})
    return f'{base_url}?{params}'

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
def bookings_choose_date_view(request):
    context = {
        'profile_exist': does_profile_exist(request.user),
        'choices': Appointment.HOURS_CHOICES
    }

    hours = request.GET.get('hours')  # validate user input
    if not hours:
        return redirect(default_bookings_choose_date_url())
    hours = float(hours)
    context['hours'] = hours

    # limit get to valid choices
    if not any(hours in tup for tup in Appointment.HOURS_CHOICES):
        return redirect(default_bookings_choose_date_url())

    dates = []
    context['dates'] = dates

    now = timezone.now()
    date_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    date_end = date_start + timedelta(days=14) # default to 14 days first

    train_station_postal_code_distances = request.user.customer_profile.postal_code.train_station_postal_code_distance.all().order_by('distance_km')
    for obj in train_station_postal_code_distances:
        print(obj.train_station)
        print(obj.distance_km)
        assigned_locations = AssignedLocation.objects.filter(
            train_station=obj.train_station,
            distance_km__gte=obj.distance_km,
            start_time__range=(date_start,date_end)
        ).order_by('start_time')
        print(assigned_locations)
        for al in assigned_locations:
            #slots.extend(al.get_available_slots(hours))
            if al.has_available_slot(hours):
                dates.append(al.start_time)

    return render(request, 'bookings_choose_date.html', context)




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
            return redirect(default_bookings_choose_date_url())
        hours = float(hours)
        context['hours'] = hours

        # limit get to valid choices
        if not any(hours in tup for tup in Appointment.HOURS_CHOICES):
            return redirect(default_bookings_choose_slot_url())


        date_str = request.GET.get('date')
        if not date_str:
            return redirect(default_bookings_choose_date_url())
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        context['date'] = date_obj

        date_start = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)

        available_slots = []

        train_station_postal_code_distances = request.user.customer_profile.postal_code.train_station_postal_code_distance.all().order_by('distance_km')
        for obj in train_station_postal_code_distances:
            #print(obj.train_station)
            #print(obj.distance_km)
            assigned_locations = AssignedLocation.objects.filter(
                train_station=obj.train_station,
                distance_km__gte=obj.distance_km,
                start_time__range=(date_start,date_end)
            ).order_by('start_time')
            print(assigned_locations)
            for al in assigned_locations:
                available_slots.extend(al.get_available_slots(hours))




        '''
        # get slots
        train_station_postal_code_distances = request.user.customer_profile.postal_code.train_station_postal_code_distance.all().order_by('distance_km')
        for obj in train_station_postal_code_distances:
            print(obj.train_station)
            train_station = obj.train_station
            assigned_locations = train_station.assigned_locations.filter(end_time__gte=now.date()).order_by('end_time')
            print(assigned_locations)
            for assigned_location in assigned_locations:
                assigned_location.start_time
                assigned_location.end_time
                #assigned_location.distance_km# ensure it's within
                available_dates = assigned_location.worker.get_available_dates(assigned_location.train_station)
                print(f'available_dates: {available_dates}')
            
            # get workers appointment in that day

        # identify the worker(s) first
        '''
        
        # merge and dedup
        #available_slots = worker.get_available_slots(date_start, hours)
        #print(f'available slots: {available_slots}')


        # dummy slots
        '''
        today_8am = now.replace(hour=8, minute=0, second=0, microsecond=0)
        today_10am = now.replace(hour=10, minute=0, second=0, microsecond=0)
        today_3pm = now.replace(hour=15, minute=0, second=0, microsecond=0)
        slots = [
            {
                'start_time': today_8am,
                'end_time': today_8am + timedelta(hours=hours),
                'hours': hours,
                'price': hours * 20,
            },
            {
                'start_time': today_10am,
                'end_time': today_10am + timedelta(hours=hours),
                'hours': hours,
                'price': hours * 20,
            },
            {
                'start_time': today_3pm,
                'end_time': today_3pm + timedelta(hours=hours),
                'hours': hours,
                'price': hours * 20,
            },
        ]
        '''

        forms = []
        context['forms'] = forms

        for slot in available_slots:
            forms.append(BookSlotForm(
                start_time=slot['start_time'], end_time=slot['end_time'], hours=slot['hours'], price=slot['price']))

        return render(request, 'bookings_choose_slot.html', context)


