from django.contrib import admin

from .models import AssignedLocation, Customer, PostalCode, TrainStation, TrainStationExit, TrainStationPostalCodeDistance, Worker, Appointment

class AppointmentInline(admin.TabularInline):
    model = Appointment

class TrainStationPostalCodeDistanceInline(admin.TabularInline):
    model = TrainStationPostalCodeDistance

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False

# Register your models here.
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    inlines = [AppointmentInline]
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
    readonly_fields = ['road_name','address']

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    inlines = [AppointmentInline]

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    fields = ['customer','worker','status','hours','price','commission','start_time','end_time']
    readonly_fields = ['end_time', 'price', 'commission']

@admin.register(PostalCode)
class PostalCodeAdmin(admin.ModelAdmin):
    readonly_fields=('block_number','road_name','building','address','x','y','latitude','longitude')

    inlines = [TrainStationPostalCodeDistanceInline]

    # Disable editing of existing entries
    #def has_change_permission(self, request, obj=None):
    #    return False

    # Disable deletion
    def has_delete_permission(self, request, obj=None):
        return False

class TrainStationExitInline(admin.TabularInline):
    model = TrainStationExit

@admin.register(TrainStation)
class TrainStationAdmin(admin.ModelAdmin):
    readonly_fields = ['name']
    inlines = [TrainStationExitInline]

    # Disable editing of existing entries
    def has_change_permission(self, request, obj=None):
        return False

    # Disable deletion
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(TrainStationExit)
class TrainStationAdmin(admin.ModelAdmin):
    readonly_fields = ['latitude', 'longitude']

    # Disable editing of existing entries
    def has_change_permission(self, request, obj=None):
        return False

    # Disable deletion
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(TrainStationPostalCodeDistance)
class TrainStationPostalCodeDistanceAdmin(admin.ModelAdmin):
    # Disable editing of existing entries
    def has_change_permission(self, request, obj=None):
        return False

    # Disable deletion
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(AssignedLocation)
class AssignedLocationAdmin(admin.ModelAdmin):
    pass