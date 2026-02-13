from datetime import date, timedelta
import re
import zoneinfo
from django.core.exceptions import ValidationError

from home_service_flyio import settings
from myapp.constants import AUTH_GROUP_AFFILIATE
from myapp.models import Appointment, WorkerWeeklySchedule
from postal_codes.models import TrainStation


def does_profile_exists(user) -> bool:
    return hasattr(user, 'customer_profile')

def is_affiliate(user) -> bool:
    return is_in_group(user, AUTH_GROUP_AFFILIATE)

def is_in_group(user, group_name: str) -> bool:
    return user.groups.filter(name=group_name).exists()

def get_user_context(user):
    return {
        'profile_exists': does_profile_exists(user),
        'is_affiliate': is_affiliate(user)
    }

def get_workers_by_train_station_day(train_station:TrainStation, day):
    match day:
        case 0:
          wws = WorkerWeeklySchedule.objects.filter(monday_location=train_station.pk)
          return [w.worker for w in wws]
        case 1:
          wws = WorkerWeeklySchedule.objects.filter(tuesday_location=train_station.pk)
          return [w.worker for w in wws]
        case 2:
          wws = WorkerWeeklySchedule.objects.filter(wednesday_location=train_station.pk)
          return [w.worker for w in wws]
        case 3:
          wws = WorkerWeeklySchedule.objects.filter(thursday_location=train_station.pk)
          return [w.worker for w in wws]
        case 4:
          wws = WorkerWeeklySchedule.objects.filter(friday_location=train_station.pk)
          return [w.worker for w in wws]
        case 5:
          wws = WorkerWeeklySchedule.objects.filter(saturday_location=train_station.pk)
          return [w.worker for w in wws]
        case 6:
          wws = WorkerWeeklySchedule.objects.filter(sunday_location=train_station.pk)
          return [w.worker for w in wws]
        case _:
            return []
       
def generate_available_slots(current_date:date, appointments_taken):
  available_slots = []

  start_time_choices = Appointment.get_start_time_choices(current_date)
  for start_time_choice in start_time_choices:
    potential_start_time = start_time_choice
    for hours, hours_str in Appointment.HOURS_CHOICES:
      potential_end_time = potential_start_time + timedelta(minutes=hours*60)
            
      # check for overlaps with taken slots
      invalid = False
      for taken in appointments_taken:
        taken_slot_end_time_adjusted = taken.end_time + \
          timedelta(minutes=60*Appointment.INTERVAL_BREAK_HOUR)

        if potential_start_time >= taken.start_time and potential_start_time < taken_slot_end_time_adjusted:
          invalid = True
          break
        if potential_end_time > taken.start_time and potential_end_time <= taken_slot_end_time_adjusted:
          invalid = True
          break
      if invalid:
        continue

      tz = zoneinfo.ZoneInfo(settings.TIME_ZONE)
      available_slots.append({
        'start_time': potential_start_time.astimezone(tz),
        'end_time': potential_end_time.astimezone(tz),
        'hours': hours,
        'price': hours * Appointment.HOURLY_RATE,
      })
  return available_slots



