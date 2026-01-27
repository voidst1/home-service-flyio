from django.contrib import admin

from .models import Customer, Worker, Appointment

class AppointmentInline(admin.TabularInline):
    model = Appointment

# Register your models here.
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    inlines = [AppointmentInline]
    fields = [
        'coordinator',
        'user',
        'name',
        'phone_number',
        'postal_code',
        'street_name',
        'unit_number',
        'frequency',
    ]
    readonly_fields = ['street_name']

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    inlines = [AppointmentInline]

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    fields = ['customer','worker','status','hours','price','commission','start_time','end_time']
    readonly_fields = ['end_time', 'price', 'commission']

