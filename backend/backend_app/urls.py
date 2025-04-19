from django.urls import path
from .views import (
    # 🔐 Auth
    RegisterWithOTPView, LoginView, ResetPasswordView, ValidateOTPView,
    SetNewPasswordView, LogoutView,

    # 👤 User
    UserListView, UserDetailView,

    # 📹 Cameras & Cafe
    UserCafeCreateView, FloorCreateView, FloorListView, CameraCreateView, CameraListView, CameraDetailView,

    # 🪑 Seat & Analytics
    get_seat_occupancy, record_seat_detection, seat_summary_analytics, current_occupied_seats,
    
    # 🔁 YOLO & Streams
    get_camera_streams, get_detection_status, start_yolo_detection, stop_yolo_detection
)


urlpatterns = [
    # --- Auth ---
    path('auth/register/', RegisterWithOTPView.as_view(), name='register-with-otp'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('auth/verify-otp/', ValidateOTPView.as_view(), name='verify-otp'),
    path('auth/set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # --- User ---
    path('users/', UserListView.as_view(), name='user-list'),
    path('user/<int:pk>/', UserDetailView.as_view(), name='user-detail'),

    # --- Cafe & Floor ---
    path('cafes/', UserCafeCreateView.as_view(), name='create-cafe'),
    path('floors/', FloorCreateView.as_view(), name='create-floor'),
    path('floors/list/', FloorListView.as_view(), name='create-floor'),

    # --- Camera Management ---
    path('cameras/', CameraCreateView.as_view(), name='create-camera'),
    path('cameras/list/', CameraListView.as_view(), name='list-camera'),
    path('cameras/<int:pk>/', CameraDetailView.as_view(), name='camera-detail'),

    # --- Seat Detection & Analytics ---
    path('api/seat-occupancy/', get_seat_occupancy),
    path('api/record-detection/', record_seat_detection),
    path("analytics/seats/summary/", seat_summary_analytics),
    path("analytics/seats/current/", current_occupied_seats),
    path('analytics/get-streams/', get_camera_streams),
    path('analytics/detection-status/', get_detection_status, name='detection-status'),

    # --- YOLO Control ---
    path('yolo/start/', start_yolo_detection, name='start-yolo'),
    path('yolo/stop/', stop_yolo_detection, name='stop-yolo'),
]
