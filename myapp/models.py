import re
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

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Best practice
        on_delete=models.PROTECT,
        related_name='customers'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('texted', 'Texted'),
        ('soft', 'Soft Booking'),
        ('confirmed', 'Confirmed Slot'),
        ('no_match', 'No available matches'),
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
    hours = models.DecimalField(max_digits=10, decimal_places=1, default=3)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.worker.name} - {self.customer.name} ({self.start_time})"  


    