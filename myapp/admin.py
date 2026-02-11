from django.contrib import admin

from .models import AssignedLocation, Customer, Affiliate, Worker, Appointment, WorkerWeeklySchedule


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
    list_display = ['id', 'affiliate', 'name',
                    'phone_number', 'road_name', 'unit_number', 'postal_code']
    fields = [
        'affiliate',
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

class CustomerInline(admin.TabularInline):
    model = Customer

@admin.register(Affiliate)
class AffiliateAdmin(admin.ModelAdmin):
    inlines = [CustomerInline]

'''
@admin.register(WorkerWeeklySchedule)
class WorkerWeeklyScheduleAdmin(admin.ModelAdmin):
    list_display = [
        field.name for field in WorkerWeeklySchedule._meta.get_fields()]
    readonly_fields = ['worker']
    fields = [
        'worker',
        'monday_location',
        'tuesday_location',
        'wednesday_location',
        'thursday_location',
        'friday_location',
    ]
'''

class WorkerWeeklyScheduleTabularInline(admin.TabularInline):
    model = WorkerWeeklySchedule

class WorkerWeeklyScheduleStackedInline(admin.StackedInline):
    model = WorkerWeeklySchedule

'''
@admin.register(AssignedLocation)
class AssignedLocationAdmin(admin.ModelAdmin):
    list_display = [
        field.name for field in AssignedLocation._meta.get_fields()]
    list_filter = ['start_time', 'worker', 'train_station']
'''

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'monday',
        'tuesday',
        'wednesday',
        'thursday',
        'friday',
    ]

    @admin.display(description='Monday')
    def monday(self, obj):
        return f"{obj.weekly_schedule.monday_location}"

    @admin.display(description='Tuesday')
    def tuesday(self, obj):
        return f"{obj.weekly_schedule.tuesday_location}"
    
    @admin.display(description='Wednesday')
    def wednesday(self, obj):
        return f"{obj.weekly_schedule.wednesday_location}"
    
    @admin.display(description='Thursday')
    def thursday(self, obj):
        return f"{obj.weekly_schedule.thursday_location}"
    
    @admin.display(description='Friday')
    def friday(self, obj):
        return f"{obj.weekly_schedule.friday_location}"
    
    inlines = [
        WorkerWeeklyScheduleStackedInline,
        #AppointmentInline
    ]

