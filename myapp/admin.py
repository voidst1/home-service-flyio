from django.contrib import admin

from .models import AssignedLocation, Customer, Worker, Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Appointment._meta.get_fields()]
    list_filter = ['start_time', 'worker']

    fields = ['customer', 'worker', 'status', 'hours',
              'price', 'commission', 'start_time', 'end_time']
    readonly_fields = ['end_time', 'price', 'commission']


class AppointmentInline(admin.TabularInline):
    model = Appointment
    fields = ['customer', 'worker', 'status', 'hours',
              'price', 'commission', 'start_time', 'end_time']
    readonly_fields = ['end_time', 'price', 'commission']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'coordinator', 'name',
                    'phone_number', 'address', 'unit_number']
    fields = [
        'coordinator',
        'user',
        'name',
        'phone_number',
        'road_name',
        'unit_number',
        'postal_code',
        'address',
        'frequency',
    ]
    readonly_fields = ['road_name', 'address']
    inlines = [AppointmentInline]


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    inlines = [AppointmentInline]


@admin.register(AssignedLocation)
class AssignedLocationAdmin(admin.ModelAdmin):
    list_display = [
        field.name for field in AssignedLocation._meta.get_fields()]
    list_filter = ['start_time', 'worker', 'train_station']
