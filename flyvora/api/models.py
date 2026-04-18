from django.db import models


class Flight(models.Model):
    """Represents an available flight."""
    airline = models.CharField(max_length=100)
    departure = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    date = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    previous_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    seats_available = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['date']

    def save(self, *args, **kwargs):
        if self.pk:
            old_flight = Flight.objects.get(pk=self.pk)
            if old_flight.price != self.price:
                self.previous_price = old_flight.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.airline}: {self.departure} -> {self.destination} on {self.date.strftime('%Y-%m-%d %H:%M')}"


class Booking(models.Model):
    """Represents a passenger's flight booking."""
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='bookings')
    passenger_name = models.CharField(max_length=200)
    passenger_email = models.EmailField()
    seats_booked = models.PositiveIntegerField(default=1)
    booking_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-booking_date']

    def __str__(self):
        return f"Booking by {self.passenger_name} on {self.flight}"
class Hotel(models.Model):
    """Represents an available hotel."""
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    distance_from_airport = models.CharField(max_length=100, help_text="e.g. 5km from LOS")
    image_url = models.URLField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True)
    total_rooms = models.PositiveIntegerField(default=50)
    available_rooms = models.PositiveIntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.location}"

class HotelBooking(models.Model):
    """Represents a guest's hotel booking."""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='bookings')
    passenger_name = models.CharField(max_length=200)
    passenger_email = models.EmailField()
    nights = models.PositiveIntegerField(default=1)
    check_in_date = models.DateField()
    booking_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Hotel Booking: {self.passenger_name} at {self.hotel.name}"
