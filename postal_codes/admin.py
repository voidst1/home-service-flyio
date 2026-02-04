from django.contrib import admin

from postal_codes.models import PostalCode, TrainStation, TrainStationExit, TrainStationPostalCodeDistance


class TrainStationPostalCodeDistanceInline(admin.TabularInline):
    model = TrainStationPostalCodeDistance

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
