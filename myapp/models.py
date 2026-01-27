import re
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings

class Worker(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

def validate_postal_code(value):
    if not re.match(r'^\d{6}$', value):
        raise ValidationError('Enter a valid SG postal code (6 digits)')

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=6, validators=[validate_postal_code]) # some has leading 0
    street_name = models.CharField(max_length=200)
    unit_number = models.CharField(max_length=10, blank=True)
    frequency = models.CharField(max_length=100)

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
        #self.street_name = 'AAAAA'
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
        seconds = int(self.hours * 3600)
        self.end_time = self.start_time + timedelta(seconds=seconds)
        self.price = self.hours * 20
        super().save(*args, **kwargs)

    