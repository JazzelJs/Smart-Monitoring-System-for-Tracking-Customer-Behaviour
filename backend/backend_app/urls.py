from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    # --- Auth ---
    RegisterWithOTPView, LoginView, ResetPasswordView, ValidateOTPView,
    SetNewPasswordView, LogoutView,

    # --- User ---
    UserListView, UserDetailView,

    # --- Cafe & Camera & Floor ---
    UserCafeCreateView, FloorCreateView, FloorListView,
    CameraCreateView, CameraListView, CameraDetailView,

    # --- Detection & Analytics ---
    start_detection_view, stop_detection_view,
    reset_chair_cache, chair_occupancy_view,
    update_hourly_entry_summary, SeatDetectionListCreateView, SeatDetectionUpdateView,
    EntryEventListCreateView, GenerateReportView, ReportListView, get_entry_state, video_feed,
    seat_summary_analytics,rtsp_stream, user_cafe_view, peak_hour_analytics, visitor_traffic, customer_analytics, detection_status, activity_log, monthly_report_summary, historical_reports, detected_customers, 
)

urlpatterns = [
    # === Auth ===
    path('auth/register/', RegisterWithOTPView.as_view(), name='register-with-otp'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('auth/verify-otp/', ValidateOTPView.as_view(), name='verify-otp'),
    path('auth/set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # === User ===
    path('users/', UserListView.as_view(), name='user-list'),
    path('user/<int:pk>/', UserDetailView.as_view(), name='user-detail'),

    # === Cafe, Floor, Camera ===
    path('cafes/', UserCafeCreateView.as_view(), name='create-cafe'),
    path('floors/', FloorCreateView.as_view(), name='create-floor'),
    path('floors/list/', FloorListView.as_view(), name='list-floor'),
    path('cameras/', CameraCreateView.as_view(), name='create-camera'),
    path('cameras/list/', CameraListView.as_view(), name='list-camera'),
    path('cameras/<int:pk>/', CameraDetailView.as_view(), name='camera-detail'),
    path('stream/<int:camera_id>/', rtsp_stream, name='rtsp_stream'),
    

    # === Detection Control ===
    path('analytics/start-detection/', start_detection_view, name='start-detection'),
    path('analytics/stop-detection/', stop_detection_view, name='stop-detection'),
    #path('analytics/detection-status/', get_detection_status, name='detection-status'),
    path('analytics/customers/list/', detected_customers),
    path("cafes/user/", user_cafe_view), 


    # === Seat Analytics ===
    path('analytics/seats/summary/', seat_summary_analytics, name='seat-summary'),
    path('analytics/peak-hours/', peak_hour_analytics),
    path('analytics/customers/', customer_analytics, name='customer-analytics'),
    #path("snapshot/", snapshot, name="snapshot"),



    # === Real-time Chair Status ===
    path('chair-occupancy/', chair_occupancy_view, name='chair-occupancy'),
    path('detection/reset-chairs/', reset_chair_cache, name='reset-chairs'),

    # === Entry Events and Live State ===
    path('entry-events/', EntryEventListCreateView.as_view(), name='entry-events'),
    path('entry-state/', get_entry_state, name='entry-state'),
    path('aggregate-hourly/', update_hourly_entry_summary, name='hourly-entry-summary'),
    path('analytics/visitor-traffic/', visitor_traffic, name='visitor-traffic'),
    path('analytics/detection-status/', detection_status, name='detection-status'),
    path('analytics/activity-log/', activity_log, name ='activity-log'),
    #path("analytics/popular-zones/", zone_popularity_view),
    # === Seat Detection DB ===
    path('seats/', SeatDetectionListCreateView.as_view(), name='seat-detections'),
    path('seats/<int:pk>/', SeatDetectionUpdateView.as_view(), name='update-seat'),

    # === Live Video Feed ===
    path('video_feed/', video_feed, name='video_feed'),

    # Reports
     path('analytics/monthly-report/<int:year>/<int:month>/', monthly_report_summary),
     path('historical-data/reports/', historical_reports),
     path('reports/generate/', GenerateReportView.as_view(), name='generate_report'),
    path('reports/', ReportListView.as_view(), name='report_list'),  # For listing reports
]

# Serve media files if in DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', video_feed),
    ]
