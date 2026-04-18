from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Flight, Booking, Hotel, HotelBooking
from .serializers import FlightSerializer, BookingSerializer, SearchSerializer, HotelSerializer, HotelBookingSerializer
from .cache import set_cache, get_cache
import os


@api_view(['GET'])
def list_flights(request):
    """
    GET /api/flights/
    Returns a list of all available flights.
    Supports optional query params: ?departure=&destination=&airline=
    """
    flights = Flight.objects.filter(seats_available__gt=0)
    departure = request.query_params.get('departure')
    destination = request.query_params.get('destination')
    airline = request.query_params.get('airline')

    if departure:
        flights = flights.filter(departure__icontains=departure)
    if destination:
        flights = flights.filter(destination__icontains=destination)
    if airline:
        flights = flights.filter(airline__icontains=airline)

    serializer = FlightSerializer(flights, many=True)
    return Response({'count': flights.count(), 'flights': serializer.data})


@api_view(['POST'])
def search_flights(request):
    """
    POST /api/search/
    Body: { "departure": "Lagos", "destination": "Abuja", "date": "2026-05-01" }
    """
    serializer = SearchSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    flights = Flight.objects.filter(seats_available__gt=0)
    
    if data.get('departure'):
        flights = flights.filter(departure__icontains=data['departure'])
    if data.get('destination'):
        flights = flights.filter(destination__icontains=data['destination'])
    if data.get('date'):
        flights = flights.filter(date__date=data['date'])

    result_serializer = FlightSerializer(flights, many=True)
    return Response({
        'count': flights.count(),
        'query': data,
        'flights': result_serializer.data,
    })


@api_view(['POST'])
def book_flight(request):
    """
    POST /api/book/
    """
    flight_id = request.data.get('flight_id')
    if not flight_id:
        return Response({'error': 'flight_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        flight = Flight.objects.get(pk=flight_id)
    except Flight.DoesNotExist:
        return Response({'error': f'Flight with id={flight_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

    seats_requested = int(request.data.get('seats_booked', 1))
    if flight.seats_available < seats_requested:
        return Response(
            {'error': f'Not enough seats. Only {flight.seats_available} seat(s) left.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    booking_data = {
        'flight': flight.pk,
        'passenger_name': request.data.get('passenger_name', ''),
        'passenger_email': request.data.get('passenger_email', ''),
        'seats_booked': seats_requested,
    }

    booking_serializer = BookingSerializer(data=booking_data)
    if not booking_serializer.is_valid():
        return Response({'errors': booking_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        booking = booking_serializer.save()
        flight.seats_available -= seats_requested
        flight.save()

    return Response(
        {
            'message': 'Booking confirmed!',
            'booking': BookingSerializer(booking).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
def list_bookings(request):
    bookings = Booking.objects.select_related('flight').all()
    email = request.query_params.get('email')
    if email:
        bookings = bookings.filter(passenger_email__iexact=email)

    serializer = BookingSerializer(bookings, many=True)
    return Response({'count': bookings.count(), 'bookings': serializer.data})


@api_view(['GET'])
def flight_detail(request, pk):
    try:
        flight = Flight.objects.get(pk=pk)
    except Flight.DoesNotExist:
        return Response({'error': 'Flight not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = FlightSerializer(flight)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    from django.contrib.auth.models import User
    
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not username or not email or not password:
        return Response({'error': 'Username, email, and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.create_user(username=username, email=email, password=password)
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'User created successfully!',
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# --- New Hotel Views ---

@api_view(['GET'])
@permission_classes([AllowAny])
def nearest_hotels(request):
    """
    GET /api/hotels/nearest/
    Simulates Foursquare Location API & Duffel Flights/Stays API
    Expects ?lat= & ?lon=
    """
    lat = request.query_params.get('lat')
    lon = request.query_params.get('lon')
    
    # 1. Check local cache to prevent redundant "Foursquare/Duffel" API hits
    cache_key = f"hotels_nearest_{lat}_{lon}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return Response(cached_data)

    # 2. Simulate external API handshake
    # _simulate_duffel_api_delay() 
    
    # 3. Fallback to our seeded DB hotels if no real coords provided or just to return data
    hotels = Hotel.objects.filter(available_rooms__gt=0)
    serializer = HotelSerializer(hotels, many=True)
    
    response_data = {
        'count': hotels.count(), 
        'source': 'Duffel/Foursquare Simulated', 
        'hotels': serializer.data
    }
    
    # Cache the structured JSON format
    set_cache(cache_key, response_data, timeout_seconds=600)
    
    return Response(response_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_booking(request):
    """
    POST /api/bookings/confirm/
    Finalizes booking with the external provider and logs heavily in PostgreSQL (simulated via SQLite).
    """
    flight_id = request.data.get('flight_id')
    hotel_id = request.data.get('hotel_id')

    if flight_id:
        try:
            flight = Flight.objects.get(pk=flight_id)
        except Flight.DoesNotExist:
            return Response({'error': 'Flight not found.'}, status=status.HTTP_404_NOT_FOUND)

        seats = int(request.data.get('seats_booked', 1))
        if flight.seats_available < seats:
            return Response({'error': 'Not enough seats.'}, status=status.HTTP_400_BAD_REQUEST)

        b_data = {
            'flight': flight.pk,
            'passenger_name': request.data.get('passenger_name', ''),
            'passenger_email': request.data.get('passenger_email', ''),
            'seats_booked': seats,
        }
        b_serializer = BookingSerializer(data=b_data)
        if b_serializer.is_valid():
            with transaction.atomic():
                b = b_serializer.save()
                flight.seats_available -= seats
                flight.save()
            return Response({'message': 'Flight booking confirmed!', 'booking': b_serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'errors': b_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    elif hotel_id:
        try:
            hotel = Hotel.objects.get(pk=hotel_id)
        except Hotel.DoesNotExist:
            return Response({'error': 'Hotel not found.'}, status=status.HTTP_404_NOT_FOUND)

        nights = int(request.data.get('nights', 1))
        if hotel.available_rooms < 1:
            return Response({'error': 'No rooms available.'}, status=status.HTTP_400_BAD_REQUEST)

        b_data = {
            'hotel': hotel.pk,
            'passenger_name': request.data.get('passenger_name', ''),
            'passenger_email': request.data.get('passenger_email', ''),
            'nights': nights,
            'check_in_date': request.data.get('check_in_date', timezone.now().date())
        }
        b_serializer = HotelBookingSerializer(data=b_data)
        if b_serializer.is_valid():
            with transaction.atomic():
                b = b_serializer.save()
                hotel.available_rooms -= 1
                hotel.save()
            return Response({'message': 'Hotel booking confirmed!', 'booking': b_serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'errors': b_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'error': 'Require either flight_id or hotel_id.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def platform_stats(request):
    """
    GET /api/stats/
    Returns lightweight stats for the AI Chatbot.
    """
    return Response({
        'total_flights': Flight.objects.count(),
        'available_hotels': Hotel.objects.filter(available_rooms__gt=0).count(),
        'destinations': Flight.objects.values_list('destination', flat=True).distinct().count(),
        'message': "Flyvora is currently serving major Nigerian hubs with premium travel options."
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def ai_chat(request):
    """
    POST /api/ai/chat/
    Sends user prompt and search context to the LLM (Simulated).
    Body: {"prompt": "Find cheapest hotel", "context": {...}}
    """
    prompt = request.data.get("prompt", "").lower()
    
    # 1. API Handshake Authentication check simulation
    # if not os.environ.get('OPENAI_API_KEY'): raise APIError
    
    # 2. Logic simulation based on text matching
    prompt_str = str(prompt).lower()
    response_text = ""
    
    if any(k in prompt_str for k in ["price", "cheap", "cost", "deal", "discount"]):
        response_text = "[AI Agent]: I've analyzed our live Duffel API feed. The best value flights are currently tagged with 'Price Update' indicators on the platform!"
    elif any(k in prompt_str for k in ["where am i", "location", "near me", "my location", "map"]):
        context_city = request.data.get("context", {}).get("detectedCity", "Unknown")
        response_text = f"[AI Agent]: Based on your secure Foursquare Geolocation ping, you are currently near {context_city}. I can find hotels closest to this hub if you'd like."
    elif any(k in prompt_str for k in ["how many", "stats", "available"]):
        fc = Flight.objects.count()
        hc = Hotel.objects.filter(available_rooms__gt=0).count()
        response_text = f"[AI Agent]: Connecting to our Postgres cluster... I see {fc} live flights and {hc} premium hotels ready for booking."
    elif any(k in prompt_str for k in ["airport", "terminal", "flight"]):
        response_text = "[AI Agent]: We connect you to major Nigerian hubs like Murtala Muhammed (LOS), Nnamdi Azikiwe (ABV), and more. Check the search grid to explore!"
    elif any(k in prompt_str for k in ["hotel", "stay", "room", "accommodation"]):
        response_text = "[AI Agent]: We've got you covered. Foursquare tells me there are excellent premium hotels right near the airport. Scroll to the hotels section to book."
    elif any(k in prompt_str for k in ["book", "reserve", "ticket", "buy"]):
        response_text = "[AI Agent]: To book, simply click the 'Book' button on any flight or hotel card. I will handle the final confirmation via our secure API."
    else:
        response_text = "[AI Agent]: I am the Flyvora AI Assistant. I can process your constraints against our live travel APIs. How can I help you book today?"
        
    return Response({
        "reply": response_text,
        "smart_labels": ["Best Value", "Fastest Server"]
    })
