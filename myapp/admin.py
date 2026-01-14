from django.contrib import admin

from .models import Customer, Worker, Appointment

class AppointmentInline(admin.TabularInline):
    model = Appointment

# Register your models here.
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    inlines = [AppointmentInline]

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    inlines = [AppointmentInline]

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    pass

