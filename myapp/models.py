import re
from datetime import timedelta
import sys
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Prefetch

from myapp.utils import get_distance_km, get_postal_code_info, validate_postal_code

class Worker(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

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
                'name': 'Server error, please try again.'
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

    def get_train_stations_within_distance_km(self, lat, long, max_distance=3):
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
                    distance=shortest_distance
                )
                new_records.append(train_station_postal_code_distance)
        return new_records


class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=100)
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
    train_station = models.ForeignKey(TrainStation, on_delete=models.PROTECT) 
    latitude = models.DecimalField(max_digits=10, decimal_places=6, blank=False, null=False) # Latitude always falls between -90 and +90 degrees
    longitude = models.DecimalField(max_digits=10, decimal_places=6, blank=False, null=False) # Longitude spans -180 to +180 degrees

    def __str__(self):
        return f'{self.train_station.name}, ({self.latitude}, {self.longitude})'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['train_station', 'latitude', 'longitude'],
                name='unique_train_station_latitude_longitude'
            )
        ]

class AssignedLocation(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.PROTECT)
    train_station = models.ForeignKey(TrainStation, on_delete=models.PROTECT) 
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f'{self.worker.name}-{self.train_station.name} {self.start_time.strftime("%Y-%m-%d")} ({self.start_time.strftime("%I:%M %p")}-{self.end_time.strftime("%I:%M %p")})'

class TrainStationPostalCodeDistance(models.Model):
    train_station = models.ForeignKey(TrainStation, on_delete=models.PROTECT)
    postal_code = models.ForeignKey(PostalCode, on_delete=models.PROTECT)
    distance = models.FloatField(blank=False, null=False)

    def __str__(self):
        return f'{self.postal_code}-{self.train_station}-{self.distance:.2f}km'