from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from .forms import CustomerForm, BookSlotForm, NewCustomerForm
from .models import Appointment, AssignedLocation, Worker
from .decorators import onboarding_required
from .utils import generate_available_slots, get_user_context, get_workers_by_train_station_day
from django.urls import reverse
from urllib.parse import urlencode
from django.contrib import messages
from django.contrib.auth.decorators import login_required


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

@login_required
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

@login_required
@onboarding_required
def profile_view(request):
    context = get_user_context(request.user)

    if request.method == 'POST':
        form = CustomerForm(
            request.POST, instance=request.user.customer_profile)
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

@login_required
@onboarding_required
def book_slot_view(request):
    context = get_user_context(request.user)
    return render(request, 'book_slot.html', context)

@login_required
@onboarding_required
def bookings_view(request):
    context = get_user_context(request.user)

    appointments = request.user.customer_profile.appointments.all()
    context['appointments'] = appointments

    return render(request, 'bookings.html', context)

@login_required
@onboarding_required
def bookings_new_view(request):
    context = get_user_context(request.user)
    context['postal_code'] = request.user.customer_profile.postal_code
    context['choices_hours'] = Appointment.HOURS_CHOICES

    if request.method == 'POST':
        print('POST')

        start_time = request.POST.get('start_time')
        start_time = datetime.fromtimestamp(int(start_time))
        hours = request.POST.get('hours')
        hours = float(hours)
        w_id = request.POST.get('wid')
        w_id = int(w_id)
        print(f'start_time: {start_time}')
        print(f'hours: {hours}')
        print(f'w_id: {w_id}')

        '''
        al = AssignedLocation.objects.get(id=a_id)
        worker = al.worker
        '''
        new_appointment = Appointment(
            start_time=start_time, hours=hours,
            customer=request.user.customer_profile, worker_id=w_id)
        try:
            new_appointment.save()
            messages.success(request, 'Appointment booked.')
            return redirect('bookings')

        except Exception as e:
            messages.error(request, str(e), 'danger')


    train_station_postal_code_distances = request.user.customer_profile.postal_code.train_station_postal_code_distance.filter(distance_km__lt=1.5).order_by('distance_km')
    nearest_train_stations = [o.train_station for o in train_station_postal_code_distances]

    slots = []

    # Weekly Schedule
    today = date.today()
    for i in range(7):
        current_date = today + timedelta(days=i)
        print(current_date)
        print(current_date.weekday())
        print(current_date.strftime('%A'))

        # get workers available for the day
        workers = []
        for train_station in nearest_train_stations:
            workers += list(get_workers_by_train_station_day(train_station, current_date.weekday()))
        workers = list(set(workers)) # dedup
        print(workers)

        for worker in workers:
            appointments_taken = list(worker.appointments.filter(start_time__date=current_date))
            print(f'appointment-taken: {appointments_taken}')
            # generate free slots
            free_slots = generate_available_slots(current_date, appointments_taken)
            for slot in free_slots:
                date_str = datetime.strftime(slot['start_time'], "%-d %b %Y (%a)")
                slots.append({
                    'wid': worker.pk,#slot['assigned_location_id'],
                    'ts': int(slot['start_time'].timestamp()),
                    'date': datetime.strftime(slot['start_time'], "%d-%m-%Y"),
                    'date_str': date_str,
                    'start_time': datetime.strftime(slot['start_time'], "%-I:%M%P"),
                    'end_time': datetime.strftime(slot['end_time'], "%-I:%M%P"),
                    'hours': slot['hours'],
                    'price': slot['price']
                })

    context['slots'] = slots
    context['choices_dates'] = [('all', 'All')]
    context['dates'] = []

    for slot in slots:
        date_str = slot['date_str']
        exists = any(tup[0] == date_str for tup in context['choices_dates'])
        if not exists:
            context['choices_dates'].append((date_str, date_str))
            context['dates'].append(date_str)


    return render(request, 'bookings_new.html', context)

    '''
    if True:
        now = timezone.now()
        date_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=14)  # default to 14 days first
        #date_end = date_start + timedelta(days=1)  # for testing 1 day

        available_slots = []

        train_station_postal_code_distances = request.user.customer_profile.postal_code.train_station_postal_code_distance.all().order_by('distance_km')
        for obj in train_station_postal_code_distances:
            # print(obj.train_station)
            # print(obj.distance_km)
            assigned_locations = AssignedLocation.objects.filter(
                train_station=obj.train_station,
                distance_km__gte=obj.distance_km,
                start_time__range=(date_start, date_end)
            ).order_by('start_time')
            print(assigned_locations)
            for al in assigned_locations:
                for hours, hours_str in Appointment.HOURS_CHOICES:
                    available_slots.extend(al.get_available_slots_v2(hours))
                #available_slots.extend(al.get_available_slots_v2(3)) # for testing

        # context['slots'] = available_slots

        slots = []
        context['slots'] = slots

        context['choices_dates'] = [('all', 'All')]

        for slot in available_slots:
            date_str = datetime.strftime(slot['start_time'], "%-d %b %Y (%a)")

            exists = any(tup[0] == date_str for tup in context['choices_dates'])
            if not exists:
                context['choices_dates'].append((date_str, date_str))

            slots.append({
                'aid': slot['assigned_location_id'],
                'ts': int(slot['start_time'].timestamp()),
                'date': datetime.strftime(slot['start_time'], "%d-%m-%Y"),
                'date_str': date_str,
                'start_time': datetime.strftime(slot['start_time'], "%-I:%M%P"),
                'end_time': datetime.strftime(slot['end_time'], "%-I:%M%P"),
                'hours': slot['hours'],
                'price': slot['price']
            })

        return render(request, 'bookings_new.html', context)
    '''

@login_required
@onboarding_required
def bookings_choose_date_view(request):
    context = get_user_context(request.user)
    context['choices'] = Appointment.HOURS_CHOICES

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
    date_end = date_start + timedelta(days=14)  # default to 14 days first

    train_station_postal_code_distances = request.user.customer_profile.postal_code.train_station_postal_code_distance.all().order_by('distance_km')
    for obj in train_station_postal_code_distances:
        print(obj.train_station)
        print(obj.distance_km)
        assigned_locations = AssignedLocation.objects.filter(
            train_station=obj.train_station,
            distance_km__gte=obj.distance_km,
            start_time__range=(date_start, date_end)
        ).order_by('start_time')
        print(assigned_locations)
        for al in assigned_locations:
            # slots.extend(al.get_available_slots_v2(hours))
            if al.has_available_slot(hours):
                dates.append(al.start_time)

    return render(request, 'bookings_choose_date.html', context)

@login_required
@onboarding_required
def bookings_choose_slot_view(request):
    context = get_user_context(request.user)
    context['choices'] = Appointment.HOURS_CHOICES
    
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

        date_start = date_obj.replace(
            hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)

        available_slots = []

        train_station_postal_code_distances = request.user.customer_profile.postal_code.train_station_postal_code_distance.all().order_by('distance_km')
        for obj in train_station_postal_code_distances:
            # print(obj.train_station)
            # print(obj.distance_km)
            assigned_locations = AssignedLocation.objects.filter(
                train_station=obj.train_station,
                distance_km__gte=obj.distance_km,
                start_time__range=(date_start, date_end)
            ).order_by('start_time')
            print(assigned_locations)
            for al in assigned_locations:
                available_slots.extend(al.get_available_slots_v2(hours))

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
        # available_slots = worker.get_available_slots_v2(date_start, hours)
        # print(f'available slots: {available_slots}')

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

@login_required
@onboarding_required
def customers_view(request):
    context = get_user_context(request.user)
    return render(request, 'customers.html', context)