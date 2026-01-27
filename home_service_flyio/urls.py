"""
URL configuration for home_service_flyio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from myapp.views import (
    home_view,
    profile_view,
    book_slot_view,

    bookings_view,
    bookings_choose_hours_view,
    bookings_choose_slot_view,
)

urlpatterns = [
    path('', home_view, name='home'),  # homepage of this app
    path('profile', profile_view, name='profile'),

    # bookings
    path('bookings', bookings_view, name='bookings'),
    path('bookings/choose-hours', bookings_choose_hours_view,
         name='bookings_choose_hours'),
    path('bookings/choose-slot', bookings_choose_slot_view,
         name='bookings_choose_slot'),

    # to remove
    path('book-slot', book_slot_view, name='book_slot'),

    path("admin/", admin.site.urls),
    path('accounts/', include('allauth.urls')),
]
