import re
from datetime import datetime, timedelta
import sys
import time
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.utils import timezone

from myapp.utils import get_distance_km, get_postal_code_info, validate_postal_code

class Worker(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def is_invalid_slot(self):
        pass

    '''
    # extract this to change
    # next 2 weeks, or within one month
    def get_available_dates(self, train_station):
        available_dates = []

        now = timezone.now()
        date_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=14) # default to 14 days first

        assigned_locations = self.assigned_locations.filter(train_station=train_station, start_time__range=(date_start, date_end))
        #print(assigned_locations)
        for al in assigned_locations:
            available_dates.append(al.start_time)

        # todo, further filtering of slots

        return available_dates

    # interval is in hours
    # return a list of start_time
    def get_available_slots(self, date, duration, interval=0.5, hourly_rate=20):
        # Current day start: today at 00:00:00
        #today_start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        # Current day end: tomorrow at 00:00:00 (exclusive upper bound)
        #today_end = today_start + timedelta(days=1)

        date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)

        available_slots = []

        assigned_locations = self.assigned_locations.filter(start_time__range=(date_start, date_end))
        if len(assigned_locations) == 0:
            return available_slots
        
        #print(f'assigned_locations: {assigned_locations}')

        appointments_taken = self.appointments.filter(start_time__range=(date_start, date_end)).order_by('start_time')
        #print(self.name)
        #print(f'appointments_taken: {appointments_taken}')

        # usually shouldn't need to iterate, one location per day, but added in just in case.
        for al in assigned_locations:
            available_period = [al.start_time, al.end_time]
            taken_slots_start_time = [obj.start_time for obj in appointments_taken]
            taken_slots_end_time = [obj.end_time for obj in appointments_taken]
            #print(available_period)
            #print(taken_slots_start_time)
            #print(taken_slots_end_time)

            current_time = al.start_time
            while(current_time < al.end_time):
                potential_start_time = current_time
                potential_end_time = potential_start_time + timedelta(minutes=duration*60)
                
                # update current_time for next iteration, so continue can be used
                # do not reuse this var anymore below
                current_time = current_time + timedelta(minutes=60*interval)

                # ensure it does not exceed end time of worker
                if potential_end_time > al.end_time:
                    continue

                invalid = False
                for taken_slot_start_time in taken_slots_start_time:
                    # ensure the start time of taken slot is not in between potential slot
                    if taken_slot_start_time >= potential_start_time and taken_slot_start_time < potential_end_time:
                        invalid = True
                        break
                if invalid:
                    continue
                for taken_slot_end_time in taken_slots_end_time:
                    # ensure the end time of taken slot is not in between potential slot
                    if taken_slot_end_time > potential_start_time and taken_slot_end_time <= potential_end_time:
                        invalid = True
                        break
                if invalid:
                    continue

                #print(potential_start_time, potential_end_time)
                available_slots.append({
                    'start_time': potential_start_time,
                    'end_time': potential_end_time,
                    'hours': duration,
                    'price': duration * hourly_rate,
                })

        return available_slots

    '''


class PostalCode(models.Model):
    name = models.CharField(max_length=6, primary_key=True, validators=[validate_postal_code])
    block_number = models.CharField(max_length=10) # BLK_NO
    road_name = models.CharField(max_length=100, blank=False, null=False) # ROAD_NAME
    building = models.CharField(max_length=100) # BUILDING
    address = models.CharField(max_length=200, blank=False, null=False) # ADDRESS
    x = models.DecimalField(max_digits=15, decimal_places=10,blank=False, null=False) # X
    y = models.DecimalField(max_digits=15, decimal_places=10,blank=False, null=False) # Y
    latitude = models.DecimalField(max_digits=10, decimal_places=6, blank=False, null=False) # LATITUDE
    longitude = models.DecimalField(max_digits=10, decimal_places=6, blank=False, null=False) # LONGITUDE

    def __str__(self):
        return self.name
    
    def clean(self):
        all_fields = [f.name for f in self._meta.fields]
        self.clean_fields(exclude=[f for f in all_fields if f not in ['name']])

        postal_code_result = get_postal_code_info(self.name)
        # print(postal_code_result)

        if isinstance(postal_code_result, str): # if error message string returned
            raise ValidationError({
                'name': f'OneMap API error: {postal_code_result}'
            })
        elif postal_code_result['found'] == 0:
            raise ValidationError({
                'name': 'Invalid postal code'
            })
        else:
            result = postal_code_result['results'][0]
            self.block_number = result['BLK_NO']
            self.road_name = result['ROAD_NAME']
            self.building = result['BUILDING']
            self.address = result['ADDRESS']
            self.x = result['X']
            self.y = result['Y']
            self.latitude = result['LATITUDE']
            self.longitude = result['LONGITUDE']


    def save(self, *args, **kwargs):
        is_new_state = self._state.adding
        super().save(*args, **kwargs)
            
        if is_new_state:
        #if True:
            new_records = self.get_train_stations_within_distance_km(float(self.latitude), float(self.longitude))
            TrainStationPostalCodeDistance.objects.bulk_create(new_records)

    def get_train_stations_within_distance_km(self, lat, long, max_distance=3): # possibly 1 to 3km
        train_stations = TrainStation.objects.prefetch_related('train_station_exits').all()
        new_records = []
        for train_station in train_stations:
            #print(f"Processing {train_station.name}")
            shortest_distance = sys.float_info.max
            for train_station_exit in train_station.train_station_exits.all():
                #print(f"Processing {train_station_exit}")
                distance = get_distance_km(lat, long, train_station_exit.latitude, train_station_exit.longitude)
                if distance < shortest_distance:
                    shortest_distance = distance
                #print(f"Distance: {distance}")
            #print(f"Shortest Distance: {shortest_distance}")

            # add if within threshold
            if shortest_distance <= max_distance:
                train_station_postal_code_distance = TrainStationPostalCodeDistance(
                    train_station=train_station,
                    postal_code=self,
                    distance_km=shortest_distance
                )
                new_records.append(train_station_postal_code_distance)
        return new_records


class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=100) # TODO: validate better
    postal_code = models.ForeignKey(PostalCode, on_delete=models.PROTECT) 
    unit_number = models.CharField(max_length=10, blank=True)
    frequency = models.CharField(max_length=100)

    @property
    def road_name(self):
        return " ".join([self.postal_code.block_number, self.postal_code.road_name])

    @property
    def address(self):
        return self.postal_code.address

    # rename to account_manager
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Best practice
        on_delete=models.PROTECT,
        related_name='customers',
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # https://www.onemap.gov.sg/apidocs/search
        super().save(*args, **kwargs)

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('texted', 'Texted'),
        ('soft', 'Soft Booking'),
        ('confirmed', 'Confirmed Slot'),
        ('no_match', 'No available matches'),
    ]

    HOURS_CHOICES = [
        (3, str(3)),
        (3.5, str(3.5)),
        (4, str(4)),
        (4.5, str(4.5)),
        (5, str(5)),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='appointments'
    )
    worker = models.ForeignKey(
        Worker,
        on_delete=models.PROTECT,
        related_name='appointments'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])

    price = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=100, decimal_places=2, default=8)
    hours = models.DecimalField(max_digits=10, decimal_places=1, default=3, choices=HOURS_CHOICES)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.customer.coordinator}: {self.worker.name} - {self.customer.name} ({self.start_time})"  

    def save(self, *args, **kwargs):
        seconds = float(self.hours * 3600)
        self.end_time = self.start_time + timedelta(seconds=seconds)
        self.price = self.hours * 20
        super().save(*args, **kwargs)

    
class TrainStation(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class TrainStationExit(models.Model):
    train_station = models.ForeignKey(TrainStation, on_delete=models.PROTECT, related_name='train_station_exits')
    latitude = models.DecimalField(max_digits=10, decimal_places=6, blank=False, null=False) # Latitude always falls between -90 and +90 degrees
    longitude = models.DecimalField(max_digits=10, decimal_places=6, blank=False, null=False) # Longitude spans -180 to +180 degrees

    def __str__(self):
        return self.train_station.name
        #return f'{self.train_station.name}, ({self.latitude}, {self.longitude})'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['train_station', 'latitude', 'longitude'],
                name='unique_train_station_latitude_longitude'
            )
        ]

class AssignedLocation(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.PROTECT,related_name='assigned_locations')
    train_station = models.ForeignKey(TrainStation, on_delete=models.PROTECT,related_name='assigned_locations') 
    start_time = models.DateTimeField(blank=False,null=False)
    end_time = models.DateTimeField(blank=False,null=False)
    distance_km = models.FloatField(blank=False,null=False,default=1)
    hourly_rate = models.FloatField(blank=False,null=False,default=20)

    def __str__(self):
        return f'{self.worker.name}-{self.train_station.name}-{self.distance_km}km {self.start_time.strftime("%Y-%m-%d")} ({self.start_time.strftime("%I:%M %p")}-{self.end_time.strftime("%I:%M %p")})'
    
    def has_available_slot(self, hours):
        date_start = self.start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)

        appointments_taken = Appointment.objects.filter(worker=self.worker,
                                                        start_time__range=(date_start,date_end)).order_by('start_time')
        taken_slots_start_time = [obj.start_time for obj in appointments_taken]
        taken_slots_end_time = [obj.end_time for obj in appointments_taken]

        current_time = self.start_time
        while(current_time < self.end_time):
            potential_start_time = current_time
            potential_end_time = potential_start_time + timedelta(minutes=hours*60)

            # update current_time for next iteration, so continue can be used
            # do not reuse this var anymore below
            current_time = current_time + timedelta(minutes=60*hours)

            # ensure it does not exceed end time of worker
            if potential_end_time > self.end_time:
                continue

            invalid = False
            for taken_slot_start_time in taken_slots_start_time:
                # ensure the start time of taken slot is not in between potential slot
                if taken_slot_start_time >= potential_start_time and taken_slot_start_time < potential_end_time:
                    invalid = True
                    break
            if invalid:
                continue
            for taken_slot_end_time in taken_slots_end_time:
                # ensure the end time of taken slot is not in between potential slot
                taken_slot_end_time_adjusted = taken_slot_end_time + timedelta(minutes=60*1.5) # 1.5 hours break in-between
                if taken_slot_end_time > potential_start_time and taken_slot_end_time <= potential_end_time:
                    invalid = True
                    break
            if invalid:
                continue

            return True

        return False

    def get_available_slots(self, hours):
        date_start = self.start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)

        appointments_taken = Appointment.objects.filter(worker=self.worker,
                                                        start_time__range=(date_start,date_end)).order_by('start_time')
        taken_slots_start_time = [obj.start_time for obj in appointments_taken]
        taken_slots_end_time = [obj.end_time for obj in appointments_taken]

        available_slots = []

        current_time = self.start_time
        while(current_time < self.end_time):
            potential_start_time = current_time
            potential_end_time = potential_start_time + timedelta(minutes=hours*60)

            # update current_time for next iteration, so continue can be used
            # do not reuse this var anymore below
            current_time = current_time + timedelta(minutes=60*0.5)

            # ensure it does not exceed end time of worker
            if potential_end_time > self.end_time:
                current_time = current_time + timedelta(minutes=60*0.5)
                continue

            invalid = False
            for taken_slot_start_time in taken_slots_start_time:
                # ensure the start time of taken slot is not in between potential slot
                if taken_slot_start_time >= potential_start_time and taken_slot_start_time < potential_end_time:
                    invalid = True
                    break
            if invalid:
                current_time = current_time + timedelta(minutes=60*0.5)
                continue
            for taken_slot_end_time in taken_slots_end_time:
                # ensure the end time of taken slot is not in between potential slot
                taken_slot_end_time_adjusted = taken_slot_end_time + timedelta(minutes=60*1.5) # 1.5 hours break in-between
                if taken_slot_end_time_adjusted > potential_start_time and taken_slot_end_time_adjusted <= potential_end_time:
                    invalid = True
                    break
            if invalid:
                current_time = current_time + timedelta(minutes=60*0.5)
                continue

            #print(potential_start_time, potential_end_time)
            available_slots.append({
                'start_time': potential_start_time,
                'end_time': potential_end_time,
                'hours': hours,
                'price': hours * self.hourly_rate,
            })

        return available_slots

class TrainStationPostalCodeDistance(models.Model):
    train_station = models.ForeignKey(TrainStation, on_delete=models.PROTECT,related_name='train_station_postal_code_distance')
    postal_code = models.ForeignKey(PostalCode, on_delete=models.PROTECT,related_name='train_station_postal_code_distance')
    distance_km = models.FloatField(blank=False, null=False)

    def __str__(self):
        return f'{self.postal_code}-{self.train_station}-{self.distance_km:.2f}km'