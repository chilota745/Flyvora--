from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from . import views

urlpatterns = [
    # Auth
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', views.register_user, name='register_user'),

    # Flights
    path('flights/', views.list_flights, name='list-flights'), # Kept for general listing
    path('flights/<int:pk>/', views.flight_detail, name='flight-detail'),
    path('search/', views.search_flights, name='search-flights'),
    path('flights/search/', views.search_flights, name='search-flights-alt'),
    path('book/', views.book_flight, name='book-flight'),
    
    # Hotels
    path('hotels/nearest/', views.nearest_hotels, name='nearest-hotels'),
    
    # Bookings
    path('bookings/confirm/', views.confirm_booking, name='confirm-booking'),
    path('bookings/', views.list_bookings, name='list-bookings'), # Kept for user history

    # AI
    path('ai/chat/', views.ai_chat, name='ai-chat'),
    
    # Misc
    path('stats/', views.platform_stats, name='platform-stats'),
]
