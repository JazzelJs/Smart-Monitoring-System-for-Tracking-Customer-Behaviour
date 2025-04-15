# backend_app/urls.py

from django.urls import path
from .views import (
    # 🔐 Auth
    RegisterWithOTPView, LoginView, ResetPasswordView, ValidateOTPView,
    SetNewPasswordView, LogoutView,

    # 👤 User
    UserListView, UserDetailView,

    # 🪑 Example Other APIs (you can add your own)
    UserCafeCreateView, FloorCreateView, CameraCreateView, CameraListView, get_seat_occupancy, record_seat_detection, seat_summary_analytics, current_occupied_seats 
    , get_camera_streams  
    #DashboardDataView, CameraListView, SeatStatusView, ReportGenerationView,
)

urlpatterns = [
    # Auth
    path('auth/register/', RegisterWithOTPView.as_view(), name='register-with-otp'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('auth/verify-otp/', ValidateOTPView.as_view(), name='verify-otp'),
    path('auth/set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # User
    path('users/', UserListView.as_view(), name='user-list'),
    path('user/<int:pk>/', UserDetailView.as_view(), name='user-detail'),

     path('cafes/', UserCafeCreateView.as_view(), name='create-cafe'),
    path('floors/', FloorCreateView.as_view(), name='create-floor'),
    path('cameras/', CameraCreateView.as_view(), name='create-camera'),
    path('cameras/list/', CameraListView.as_view(), name='list-camera'),
    #path("api/live-seats/", live_seat_occupancy, name="live_seat_occupancy"),

    path('api/seat-occupancy/', get_seat_occupancy),  # Redis-based
    path('api/record-detection/', record_seat_detection),  # DB tracking
    path("analytics/seats/summary/", seat_summary_analytics),      #  React summary card
    path("analytics/seats/current/", current_occupied_seats),      #  React table data
    path('analytics/get-streams/', get_camera_streams),



    # Example non-auth APIs
    #path('dashboard/', DashboardDataView.as_view(), name='dashboard-data'),
    #path('seats/', SeatStatusView.as_view(), name='seat-status'),
    #path('cameras/', CameraListView.as_view(), name='camera-list'),
    #path('reports/generate/', ReportGenerationView.as_view(), name='generate-report'),
]
