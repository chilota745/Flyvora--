from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth.models import User

from .models import Flight, Booking, Hotel, HotelBooking


class FlightBookingAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.flight = Flight.objects.create(
            airline="Air Peace",
            departure="Lagos",
            destination="Abuja",
            date=timezone.now() + timedelta(days=10),
            price="25000.00",
            seats_available=120,
        )

        self.list_url = reverse('list-flights')
        self.search_url = reverse('search-flights')
        self.book_url = reverse('book-flight')
        self.detail_url = reverse('flight-detail', kwargs={'pk': self.flight.pk})
        self.bookings_url = reverse('list-bookings')

    def test_list_flights(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['flights'][0]['airline'], 'Air Peace')

    def test_search_flights(self):
        response = self.client.post(
            self.search_url,
            {
                'departure': 'Lagos',
                'destination': 'Abuja',
                'date': self.flight.date.date().isoformat(),
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['flights'][0]['destination'], 'Abuja')

    def test_book_flight(self):
        response = self.client.post(
            self.book_url,
            {
                'flight_id': self.flight.pk,
                'passenger_name': 'Ada Obi',
                'passenger_email': 'ada@flyvora.com',
                'seats_booked': 2,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Booking confirmed!')
        booking = response.data['booking']
        self.assertEqual(booking['passenger_email'], 'ada@flyvora.com')
        self.flight.refresh_from_db()
        self.assertEqual(self.flight.seats_available, 118)

    def test_flight_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.flight.pk)
        self.assertEqual(response.data['departure'], 'Lagos')

    def test_list_bookings_by_email(self):
        Booking.objects.create(
            flight=self.flight,
            passenger_name='Ada Obi',
            passenger_email='ada@flyvora.com',
            seats_booked=1,
        )
        response = self.client.get(self.bookings_url, {'email': 'ada@flyvora.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['bookings'][0]['passenger_email'], 'ada@flyvora.com')

    def test_bad_search_payload_returns_400(self):
        response = self.client.post(
            self.search_url,
            {'departure': 'Lagos', 'destination': 'Abuja', 'date': 'invalid-date'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)

    def test_book_nonexistent_flight_returns_404(self):
        response = self.client.post(
            self.book_url,
            {
                'flight_id': 9999,
                'passenger_name': 'Ghost',
                'passenger_email': 'ghost@x.com',
                'seats_booked': 1,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)


class AuthHotelAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'StrongPassword123',
        }
        self.register_url = reverse('register_user')
        self.login_url = reverse('token_obtain_pair')
        self.hotels_url = reverse('nearest-hotels')
        self.confirm_url = reverse('confirm-booking')
        self.stats_url = reverse('platform-stats')
        self.ai_url = reverse('ai-chat')

    def get_token(self):
        User.objects.create_user(**self.user_data)
        response = self.client.post(self.login_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password'],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['access']

    def test_register_user_returns_tokens(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], self.user_data['email'])

    def test_login_returns_token(self):
        User.objects.create_user(**self.user_data)
        response = self.client.post(self.login_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password'],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_nearest_hotels_returns_active_hotels(self):
        Hotel.objects.create(
            name='Premium Suites',
            location='Lagos',
            price_per_night='18000.00',
            distance_from_airport='5km from LOS',
            available_rooms=10,
        )
        Hotel.objects.create(
            name='Airport Hotel',
            location='Abuja',
            price_per_night='15000.00',
            distance_from_airport='3km from ABV',
            available_rooms=0,
        )
        response = self.client.get(self.hotels_url, {'lat': '6.5244', 'lon': '3.3792'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('hotels', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['hotels'][0]['name'], 'Premium Suites')

    def test_confirm_flight_booking_requires_auth(self):
        access_token = self.get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        flight = Flight.objects.create(
            airline='Azman',
            departure='Lagos',
            destination='Kano',
            date=timezone.now() + timedelta(days=5),
            price='22000.00',
            seats_available=5,
        )
        response = self.client.post(self.confirm_url, {
            'flight_id': flight.pk,
            'passenger_name': 'Sade',
            'passenger_email': 'sade@example.com',
            'seats_booked': 2,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Flight booking confirmed!')
        flight.refresh_from_db()
        self.assertEqual(flight.seats_available, 3)

    def test_confirm_hotel_booking_requires_auth(self):
        access_token = self.get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        hotel = Hotel.objects.create(
            name='City Lodge',
            location='Abuja',
            price_per_night='12000.00',
            distance_from_airport='4km from ABV',
            available_rooms=3,
        )
        response = self.client.post(self.confirm_url, {
            'hotel_id': hotel.pk,
            'passenger_name': 'Chidi',
            'passenger_email': 'chidi@example.com',
            'nights': 2,
            'check_in_date': timezone.now().date().isoformat(),
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Hotel booking confirmed!')
        hotel.refresh_from_db()
        self.assertEqual(hotel.available_rooms, 2)

    def test_stats_endpoint(self):
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_flights', response.data)
        self.assertIn('available_hotels', response.data)

    def test_ai_chat_returns_reply(self):
        response = self.client.post(self.ai_url, {'prompt': 'What hotels are near me?'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reply', response.data)
