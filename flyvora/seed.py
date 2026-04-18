"""
Seed script – run with:
    python seed.py
Populates the database with sample flights for testing.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from datetime import datetime
from api.models import Flight, Hotel

# Clear existing data
Flight.objects.all().delete()
Hotel.objects.all().delete()

# Seed Flights
sample_flights = [
    {
        'airline': 'Air Peace',
        'departure': 'Lagos',
        'destination': 'Abuja',
        'date': timezone.make_aware(datetime(2026, 5, 1, 6, 30)),
        'price': 45000.00,
        'seats_available': 120,
    },
    {
        'airline': 'Air Peace',
        'departure': 'Abuja',
        'destination': 'Lagos',
        'date': timezone.make_aware(datetime(2026, 5, 1, 14, 0)),
        'price': 47000.00,
        'seats_available': 80,
    },
    {
        'airline': 'Ibom Air',
        'departure': 'Lagos',
        'destination': 'Port Harcourt',
        'date': timezone.make_aware(datetime(2026, 5, 2, 8, 0)),
        'price': 38000.00,
        'seats_available': 60,
    },
    {
        'airline': 'Ibom Air',
        'departure': 'Port Harcourt',
        'destination': 'Abuja',
        'date': timezone.make_aware(datetime(2026, 5, 3, 10, 15)),
        'price': 52000.00,
        'seats_available': 90,
    },
    {
        'airline': 'United Nigeria Airlines',
        'departure': 'Enugu',
        'destination': 'Lagos',
        'date': timezone.make_aware(datetime(2026, 5, 4, 7, 45)),
        'price': 41000.00,
        'seats_available': 50,
    },
    {
        'airline': 'United Nigeria Airlines',
        'departure': 'Lagos',
        'destination': 'Kano',
        'date': timezone.make_aware(datetime(2026, 5, 5, 9, 0)),
        'price': 55000.00,
        'seats_available': 110,
    },
    {
        'airline': 'Green Africa',
        'departure': 'Abuja',
        'destination': 'Enugu',
        'date': timezone.make_aware(datetime(2026, 5, 6, 12, 30)),
        'price': 33000.00,
        'seats_available': 75,
    },
    {
        'airline': 'Green Africa',
        'departure': 'Kano',
        'destination': 'Lagos',
        'date': timezone.make_aware(datetime(2026, 5, 7, 16, 0)),
        'price': 53000.00,
        'seats_available': 40,
    },
]

created_flights = Flight.objects.bulk_create([Flight(**f) for f in sample_flights])
print(f"[OK] Seeded {len(created_flights)} flights.")

# Seed Hotels
sample_hotels = [
    {
        'name': 'Legend Hotel (Curio Collection)',
        'location': 'Ikeja Airport, Lagos',
        'price_per_night': 180000.00,
        'distance_from_airport': '0.5km from LOS Terminal',
        'image_url': 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&q=80&w=800',
        'description': 'Luxury stay right at the heart of Ikeja Airport.',
        'available_rooms': 25
    },
    {
        'name': 'Transcorp Hilton',
        'location': 'Maitama, Abuja',
        'price_per_night': 150000.00,
        'distance_from_airport': '40km from ABV International',
        'image_url': 'https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&q=80&w=800',
        'description': 'The premier destination for luxury in the capital city.',
        'available_rooms': 45
    },
    {
        'name': 'Eko Hotels & Suites',
        'location': 'Victoria Island, Lagos',
        'price_per_night': 120000.00,
        'distance_from_airport': '22km from LOS International',
        'image_url': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&q=80&w=800',
        'description': 'Iconic lagoon views and world-class amenities.',
        'available_rooms': 30
    },
    {
        'name': 'Radisson Blu Anchorage',
        'location': 'VI Waterfront, Lagos',
        'price_per_night': 95000.00,
        'distance_from_airport': '25km from LOS International',
        'image_url': 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&q=80&w=800',
        'description': 'Modern luxury on the shores of the Lagos lagoon.',
        'available_rooms': 20
    },
    {
        'name': 'Sheraton Hotel',
        'location': 'Ikeja, Lagos',
        'price_per_night': 85000.00,
        'distance_from_airport': '5km from LOS International',
        'image_url': 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&q=80&w=800',
        'description': 'Reliable comfort near the bustling Ikeja business district.',
        'available_rooms': 40
    }
]

created_hotels = Hotel.objects.bulk_create([Hotel(**h) for h in sample_hotels])
print(f"[OK] Seeded {len(created_hotels)} hotels.")

