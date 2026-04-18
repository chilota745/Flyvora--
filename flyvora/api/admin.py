from django.contrib import admin
from .models import Flight, Booking


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('id', 'airline', 'departure', 'destination', 'date', 'price', 'seats_available')
    list_filter = ('airline', 'departure', 'destination')
    search_fields = ('airline', 'departure', 'destination')
    ordering = ('date',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'passenger_name', 'passenger_email', 'flight', 'seats_booked', 'booking_date')
    list_filter = ('flight__airline',)
    search_fields = ('passenger_name', 'passenger_email')
    ordering = ('-booking_date',)
