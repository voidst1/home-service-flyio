from django.contrib import admin

from .models import AssignedLocation, Customer, PostalCode, TrainStation, TrainStationExit, TrainStationPostalCodeDistance, Worker, Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Appointment._meta.get_fields()]
    list_filter = ['start_time','worker']

    fields = ['customer', 'worker', 'status', 'hours',
              'price', 'commission', 'start_time', 'end_time']
    readonly_fields = ['end_time', 'price', 'commission']


class AppointmentInline(admin.TabularInline):
    model = Appointment
    fields = ['customer', 'worker', 'status', 'hours',
              'price', 'commission', 'start_time', 'end_time']
    readonly_fields = ['end_time', 'price', 'commission']


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
    list_display = ['id','coordinator','name','phone_number','address','unit_number']
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


@admin.register(PostalCode)
class PostalCodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    readonly_fields = ['block_number', 'road_name',
                       'building', 'address', 'x', 'y', 'latitude', 'longitude']
    # read_only_fields = [field.name for field in PostalCode._meta.fields]
    inlines = [TrainStationPostalCodeDistanceInline]

    # Disable editing of existing entries
    def has_change_permission(self, request, obj=None):
        return False

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
class TrainStationExitAdmin(admin.ModelAdmin):
    list_display = ('train_station', 'latitude', 'longitude')
    readonly_fields = ['latitude', 'longitude']

    # Disable editing of existing entries
    def has_change_permission(self, request, obj=None):
        return False

    # Disable deletion
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TrainStationPostalCodeDistance)
class TrainStationPostalCodeDistanceAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [f.name for f in self.model._meta.fields]
    

    # Disable editing of existing entries
    def has_change_permission(self, request, obj=None):
        return False

    # Disable deletion
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(AssignedLocation)
class AssignedLocationAdmin(admin.ModelAdmin):
    list_display = [field.name for field in AssignedLocation._meta.get_fields()]
    list_filter = ['start_time','worker','train_station']