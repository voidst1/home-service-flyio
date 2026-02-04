from django.core.exceptions import ValidationError
from django.db import models

from postal_codes.utils import get_distance_km, get_postal_code_info, validate_postal_code

class PostalCode(models.Model):
    name = models.CharField(max_length=6, primary_key=True,
                            validators=[validate_postal_code])
    block_number = models.CharField(max_length=10)  # BLK_NO
    road_name = models.CharField(
        max_length=100, blank=False, null=False)  # ROAD_NAME
    building = models.CharField(max_length=100)  # BUILDING
    address = models.CharField(
        max_length=200, blank=False, null=False)  # ADDRESS
    x = models.DecimalField(
        max_digits=15, decimal_places=10, blank=False, null=False)  # X
    y = models.DecimalField(
        max_digits=15, decimal_places=10, blank=False, null=False)  # Y
    latitude = models.DecimalField(
        max_digits=10, decimal_places=6, blank=False, null=False)  # LATITUDE
    longitude = models.DecimalField(
        max_digits=10, decimal_places=6, blank=False, null=False)  # LONGITUDE

    def __str__(self):
        return self.name

    def clean(self):
        all_fields = [f.name for f in self._meta.fields]
        self.clean_fields(exclude=[f for f in all_fields if f not in ['name']])

        postal_code_result = get_postal_code_info(self.name)
        # print(postal_code_result)

        if isinstance(postal_code_result, str):  # if error message string returned
            raise ValidationError({
                'name': f'OneMap API error: {postal_code_result}'
            })
        elif postal_code_result['found'] == 0:
            raise ValidationError({
                'name': 'Invalid postal code'
            })
        else:
            result = postal_code_result['results'][0]
            self.block_number = result['BLK_NO']
            self.road_name = result['ROAD_NAME']
            self.building = result['BUILDING']
            self.address = result['ADDRESS']
            self.x = result['X']
            self.y = result['Y']
            self.latitude = result['LATITUDE']
            self.longitude = result['LONGITUDE']

    def save(self, *args, **kwargs):
        is_new_state = self._state.adding
        super().save(*args, **kwargs)

        if is_new_state:
            # if True:
            new_records = self.get_train_stations_within_distance_km(
                float(self.latitude), float(self.longitude))
            TrainStationPostalCodeDistance.objects.bulk_create(new_records)

    # possibly 1 to 3km
    def get_train_stations_within_distance_km(self, lat, long, max_distance=3):
        train_stations = TrainStation.objects.prefetch_related(
            'train_station_exits').all()
        new_records = []
        for train_station in train_stations:
            # print(f"Processing {train_station.name}")
            shortest_distance = sys.float_info.max
            for train_station_exit in train_station.train_station_exits.all():
                # print(f"Processing {train_station_exit}")
                distance = get_distance_km(
                    lat, long, train_station_exit.latitude, train_station_exit.longitude)
                if distance < shortest_distance:
                    shortest_distance = distance
                # print(f"Distance: {distance}")
            # print(f"Shortest Distance: {shortest_distance}")

            # add if within threshold
            if shortest_distance <= max_distance:
                train_station_postal_code_distance = TrainStationPostalCodeDistance(
                    train_station=train_station,
                    postal_code=self,
                    distance_km=shortest_distance
                )
                new_records.append(train_station_postal_code_distance)
        return new_records


class TrainStation(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class TrainStationExit(models.Model):
    train_station = models.ForeignKey(
        TrainStation, on_delete=models.PROTECT, related_name='train_station_exits')
    # Latitude always falls between -90 and +90 degrees
    latitude = models.DecimalField(
        max_digits=10, decimal_places=6, blank=False, null=False)
    # Longitude spans -180 to +180 degrees
    longitude = models.DecimalField(
        max_digits=10, decimal_places=6, blank=False, null=False)

    def __str__(self):
        return self.train_station.name
        # return f'{self.train_station.name}, ({self.latitude}, {self.longitude})'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['train_station', 'latitude', 'longitude'],
                name='unique_train_station_latitude_longitude'
            )
        ]


class TrainStationPostalCodeDistance(models.Model):
    train_station = models.ForeignKey(
        TrainStation, on_delete=models.PROTECT, related_name='train_station_postal_code_distance')
    postal_code = models.ForeignKey(
        PostalCode, on_delete=models.PROTECT, related_name='train_station_postal_code_distance')
    distance_km = models.FloatField(blank=False, null=False)

    def __str__(self):
        return f'{self.postal_code}-{self.train_station}-{self.distance_km:.2f}km'
