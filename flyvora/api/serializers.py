from rest_framework import serializers
from .models import Flight, Booking, Hotel, HotelBooking


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    flight_info = FlightSerializer(source='flight', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'flight', 'flight_info', 'passenger_name', 'passenger_email',
                  'seats_booked', 'booking_date']
        read_only_fields = ['booking_date']


class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = '__all__'


class HotelBookingSerializer(serializers.ModelSerializer):
    hotel_info = HotelSerializer(source='hotel', read_only=True)

    class Meta:
        model = HotelBooking
        fields = ['id', 'hotel', 'hotel_info', 'passenger_name', 'passenger_email',
                  'nights', 'check_in_date', 'booking_date']
        read_only_fields = ['booking_date']


class SearchSerializer(serializers.Serializer):
    """Validates the payload for the flight search endpoint."""
    departure = serializers.CharField(max_length=100, required=False, allow_blank=True)
    destination = serializers.CharField(max_length=100, required=False, allow_blank=True)
    date = serializers.DateField(required=False, allow_null=True)

