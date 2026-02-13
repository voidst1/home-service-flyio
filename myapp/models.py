from datetime import date, datetime, time, timedelta
import uuid
import zoneinfo
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone

from auditlog.registry import auditlog

from postal_codes.models import PostalCode, TrainStation


class Worker(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class WorkerWeeklySchedule(models.Model):
    worker = models.OneToOneField(
        Worker,
        on_delete=models.CASCADE,
        related_name='weekly_schedule',
    )
    monday_location = models.ForeignKey(
        TrainStation, on_delete=models.SET_NULL,
        related_name='weekly_schedules_monday',
        blank=True, null=True,
        verbose_name='Monday')
    tuesday_location = models.ForeignKey(
        TrainStation, on_delete=models.SET_NULL,
        related_name='weekly_schedules_tuesday',
        blank=True, null=True,
        verbose_name='Tuesday')
    wednesday_location = models.ForeignKey(
        TrainStation, on_delete=models.SET_NULL,
        related_name='weekly_schedules_wednesday',
        blank=True, null=True,
        verbose_name='Wednesday')
    thursday_location = models.ForeignKey(
        TrainStation, on_delete=models.SET_NULL,
        related_name='weekly_schedules_thursday',
        blank=True, null=True,
        verbose_name='Thursday')
    friday_location = models.ForeignKey(
        TrainStation, on_delete=models.SET_NULL,
        related_name='weekly_schedules_friday',
        blank=True, null=True,
        verbose_name='Friday')
    saturday_location = models.ForeignKey(
        TrainStation, on_delete=models.SET_NULL,
        related_name='weekly_schedules_saturday',
        blank=True, null=True,
        verbose_name='Saturday')
    sunday_location = models.ForeignKey(
        TrainStation, on_delete=models.SET_NULL,
        related_name='weekly_schedules_sunday',
        blank=True, null=True,
        verbose_name='Sunday')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.worker.name


class Affiliate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='affiliate',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email_address = models.CharField(max_length=200, unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=100, unique=True)  # TODO: validate better
    postal_code = models.ForeignKey(PostalCode, on_delete=models.PROTECT)
    unit_number = models.CharField(max_length=10, blank=True, null=True)
    frequency = models.CharField(max_length=100)
    affiliate = models.ForeignKey(
        Affiliate,
        on_delete=models.PROTECT,
        related_name='customers',
        blank=True,
        null=True,
    )
    # allow user to be blank for initial version
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        blank=True,
        null=True,
    )
    preferred_worker = models.ForeignKey(
        Worker,
        on_delete=models.PROTECT,
        related_name='customers',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def road_name(self):
        return " ".join([self.postal_code.block_number, self.postal_code.road_name])

    @property
    def address(self):
        return self.postal_code.address

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # https://www.onemap.gov.sg/apidocs/search
        super().save(*args, **kwargs)

auditlog.register(Customer)

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
    ]

    INTERVAL_BREAK_HOUR = 1
    HOURLY_RATE = 20

    HOURS_CHOICES = [
        (3, "Suitable for smaller spaces"),
        (3.5, "Balanced option for medium spaces"),
        (4, "Recommended for up to 2 bedrooms"),
    ]

    # include 0830?
    def get_start_time_choices(date:date):
        #date_obj = date.replace(hour=0, minute=0,second=0,microsecond=0)
        #date_obj = timezone.localtime(date_obj)
        #print(date_obj)
        date_obj = datetime.combine(date, time.min)
        date_obj = timezone.make_aware(date_obj)
        return [
            date_obj.replace(hour=8), # morning
            date_obj.replace(hour=9), # morning
            date_obj.replace(hour=13), # afternoon
            date_obj.replace(hour=14), # afternoon
            date_obj.replace(hour=18), # night
            date_obj.replace(hour=19), # night
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

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    paid = models.BooleanField(default=False)

    price = models.DecimalField(max_digits=1000, decimal_places=2, default=0)
    commission = models.DecimalField(
        max_digits=100, decimal_places=2, default=8)
    hours = models.DecimalField(
        max_digits=10, decimal_places=1, default=3, choices=HOURS_CHOICES)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.customer.affiliate}: {self.worker.name} - {self.customer.name} ({self.start_time})"

    def save(self, hourly_rate=HOURLY_RATE, *args, **kwargs):
        seconds = float(self.hours * 3600)
        self.end_time = self.start_time + timedelta(seconds=seconds)
        self.price = self.hours * hourly_rate

        with transaction.atomic():
            # Lock appointments for this resource in the time window
            Appointment.objects.select_for_update().filter(
                worker_id=self.worker_id,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exists()  # Triggers lock

            # Re-check after lock
            if Appointment.objects.filter(
                worker_id=self.worker_id,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exclude(id=self.pk).exists():
                raise ValidationError("Time slot taken.")

            super().save(*args, **kwargs)

auditlog.register(Appointment)

class AssignedLocation(models.Model):
    worker = models.ForeignKey(
        Worker, on_delete=models.PROTECT, related_name='assigned_locations')
    train_station = models.ForeignKey(
        TrainStation, on_delete=models.PROTECT, related_name='assigned_locations')
    start_time = models.DateTimeField(blank=False, null=False)
    end_time = models.DateTimeField(blank=False, null=False)
    distance_km = models.FloatField(blank=False, null=False, default=1)
    hourly_rate = models.FloatField(blank=False, null=False, default=20)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def start_time_local(self):
        tz = zoneinfo.ZoneInfo(settings.TIME_ZONE)
        return self.start_time.astimezone(tz)

    @property
    def end_time_local(self):
        tz = zoneinfo.ZoneInfo(settings.TIME_ZONE)
        return self.end_time.astimezone(tz)

    def __str__(self):
        tz = zoneinfo.ZoneInfo(settings.TIME_ZONE)
        return f'{self.worker.name}-{self.train_station.name}-{self.distance_km}km {self.start_time_local.strftime("%Y-%m-%d")} ({self.start_time_local.strftime("%I:%M %p")}-{self.end_time_local.strftime("%I:%M %p")})'

    def clean(self):
        cleaned_data = super().clean()

        if AssignedLocation.objects.filter(
            worker_id=self.worker_id,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(id=self.pk).exists():
            raise ValidationError("Date/time taken.")

        return cleaned_data

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # Lock appointments for this resource in the time window
            AssignedLocation.objects.select_for_update().filter(
                worker_id=self.worker_id,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exists()  # Triggers lock

            # Re-check after lock
            if AssignedLocation.objects.filter(
                worker_id=self.worker_id,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exclude(id=self.pk).exists():
                raise ValidationError("Date/time taken.")

            super().save(*args, **kwargs)
    '''
    def get_available_slots(self, hours):
        date_start = self.start_time.replace(
            hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)

        appointments_taken = Appointment.objects.filter(worker=self.worker,
                                                        start_time__range=(self.start_time, self.end_time)).order_by('start_time')
        print(date_start)
        print(date_end)
        print(appointments_taken)
        #taken_slots_start_time = [obj.start_time for obj in appointments_taken]
        #taken_slots_end_time = [obj.end_time for obj in appointments_taken]
        taken_slots_time = [(obj.start_time, obj.end_time)
                            for obj in appointments_taken]

        available_slots = []

        current_time = self.start_time
        while (current_time < self.end_time):
            potential_start_time = current_time
            potential_end_time = potential_start_time + \
                timedelta(minutes=hours*60)

            # update current_time for next iteration, so continue can be used
            # do not reuse this var anymore below
            current_time = current_time + timedelta(minutes=60*0.5)

            # ensure it does not exceed end time of worker
            if potential_end_time > self.end_time:
                current_time = current_time + timedelta(minutes=60*0.5)
                continue

            invalid = False

            for taken_slot_start_time, taken_slot_end_time in taken_slots_time:
                taken_slot_end_time_adjusted = taken_slot_end_time + \
                    timedelta(minutes=60*Appointment.INTERVAL_BREAK_HOUR)  # break in-between appointments

                if potential_start_time >= taken_slot_start_time and potential_start_time < taken_slot_end_time_adjusted:
                    invalid = True
                    break
                if potential_end_time > taken_slot_start_time and potential_end_time <= taken_slot_end_time_adjusted:
                    invalid = True
                    break
            if invalid:
                current_time = current_time + timedelta(minutes=60*0.5)
                continue

            tz = zoneinfo.ZoneInfo(settings.TIME_ZONE)
            # print(potential_start_time, potential_end_time)
            available_slots.append({
                'assigned_location_id': self.id,
                'start_time': potential_start_time.astimezone(tz),
                'end_time': potential_end_time.astimezone(tz),
                'hours': hours,
                'price': hours * self.hourly_rate,
            })

        return available_slots
    '''

    '''
    Version 2

    Start Time
    Morning - 0800, 0900 
    Afternoon - 1300, 1400
    Evening - 1800, 1900


    '''
    def get_available_slots_v2(self, hours):
        appointments_taken = Appointment.objects.filter(worker=self.worker,
                                                        start_time__range=(self.start_time, self.end_time)).order_by('start_time')
        print(f'appointments_taken: {appointments_taken}')

        taken_slots_time = [(obj.start_time, obj.end_time)
                            for obj in appointments_taken]
        available_slots = []

        start_time_choices = Appointment.get_start_time_choices(self.start_time)
        for start_time_choice in start_time_choices:
            potential_start_time = start_time_choice
            potential_end_time = potential_start_time + \
                timedelta(minutes=hours*60)

            # ensure it does not exceed end time of worker
            if potential_end_time > self.end_time:
                continue

            invalid = False

            for taken_slot_start_time, taken_slot_end_time in taken_slots_time:
                taken_slot_end_time_adjusted = taken_slot_end_time + \
                    timedelta(minutes=60*Appointment.INTERVAL_BREAK_HOUR)  # break in-between appointments

                if potential_start_time >= taken_slot_start_time and potential_start_time < taken_slot_end_time_adjusted:
                    invalid = True
                    break
                if potential_end_time > taken_slot_start_time and potential_end_time <= taken_slot_end_time_adjusted:
                    invalid = True
                    break
            if invalid:
                continue

            tz = zoneinfo.ZoneInfo(settings.TIME_ZONE)
            available_slots.append({
                'assigned_location_id': self.id,
                'start_time': potential_start_time.astimezone(tz),
                'end_time': potential_end_time.astimezone(tz),
                'hours': hours,
                'price': hours * self.hourly_rate,
            })

        return available_slots

auditlog.register(AssignedLocation)