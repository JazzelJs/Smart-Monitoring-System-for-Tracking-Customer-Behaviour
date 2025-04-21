from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Avg

from datetime import timedelta
import redis, json, subprocess, os, time, cv2

from .utils import generate_otp, send_otp_via_email
from .models import (
    User, EmailOTP, UserCafe, Floor, Camera, Seat, 
    SeatDetection, ActivityLog, Notification, EntryEvent, HourlyEntrySummary
)
from .serializers import (
    UserSerializer, UserListSerializer, UserDetailSerializer,
    LoginSerializer, ResetPasswordSerializer, ValidateOTPSerializer,
    SetNewPasswordSerializer, LogoutSerializer,
    UserCafeSerializer, FloorSerializer, CameraSerializer,
    SeatDetectionSerializer, entry_event_serializer,
)
from .detector import start_detection, stop_detection
import backend_app.shared_video as shared_video

User = get_user_model()
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)


# =====================================================
# === AUTHENTICATION & USER
# =====================================================

class RegisterWithOTPView(generics.GenericAPIView):
    serializer_class = UserSerializer
    def post(self, request):
        email = request.data.get("email")
        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=400)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        otp = generate_otp(user.email)
        send_otp_via_email(user.email, otp)
        return Response({"message": "User created and OTP sent"}, status=201)

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=200)

class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = generate_otp(serializer.validated_data['email'])
        send_otp_via_email(serializer.validated_data['email'], otp)
        return Response({"message": "OTP sent to email"}, status=200)

class ValidateOTPView(generics.GenericAPIView):
    serializer_class = ValidateOTPSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "OTP validated successfully"}, status=200)

class SetNewPasswordView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password reset successful"}, status=200)

class LogoutView(APIView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
            return Response({"message": "Successfully logged out."}, status=205)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer

class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'


# =====================================================
# === CAFE, FLOOR, CAMERA
# =====================================================

class UserCafeCreateView(generics.CreateAPIView):
    queryset = UserCafe.objects.all()
    serializer_class = UserCafeSerializer
    permission_classes = [permissions.IsAuthenticated]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FloorCreateView(generics.CreateAPIView):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    permission_classes = [permissions.IsAuthenticated]
    def perform_create(self, serializer):
        user_cafe = UserCafe.objects.filter(user=self.request.user).first()
        serializer.save(cafe=user_cafe)

class FloorListView(generics.ListAPIView):
    serializer_class = FloorSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Floor.objects.filter(cafe__user=self.request.user)

class CameraListView(generics.ListAPIView):
    serializer_class = CameraSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Camera.objects.filter(floor__cafe__user=self.request.user).order_by('-last_active')

class CameraCreateView(generics.CreateAPIView):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_serializer_context(self):
        return {"request": self.request}

class CameraDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CameraSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Camera.objects.filter(floor__cafe__user=self.request.user)


# =====================================================
# === SEAT DETECTION & ANALYTICS
# =====================================================

class SeatDetectionListCreateView(generics.ListCreateAPIView):
    queryset = SeatDetection.objects.all()
    serializer_class = SeatDetectionSerializer

class SeatDetectionUpdateView(APIView):
    def patch(self, request, pk):
        instance = get_object_or_404(SeatDetection, pk=pk)
        serializer = SeatDetectionSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Updated"}, status=200)
        return Response(serializer.errors, status=400)

class EntryEventListCreateView(generics.ListCreateAPIView):
    queryset = EntryEvent.objects.all()
    serializer_class = entry_event_serializer

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def seat_summary_analytics(request):
    user = request.user
    month_start = now().replace(day=1)
    cafes = UserCafe.objects.filter(user=user)
    seats = Seat.objects.filter(cafe__in=cafes)
    detections = SeatDetection.objects.filter(seat__in=seats, month__gte=month_start)

    popular = detections.values("seat__seat_id").annotate(count=Count("id")).order_by("-count").first()
    avg_duration = detections.aggregate(avg=Avg("duration"))["avg"]
    longest = detections.order_by("-duration").first()

    return Response({
        "most_popular_seat": f"Table {popular['seat__seat_id']}" if popular else None,
        "average_duration": round(avg_duration / 60) if avg_duration else 0,
        "longest_session_table": f"Table {longest.seat.seat_id}" if longest else None,
        "longest_session_duration": round(longest.duration / 60) if longest else 0,
    })


# =====================================================
# === REDIS: ENTRY & CHAIR STATES
# =====================================================

@csrf_exempt
def update_hourly_entry_summary(request):
    end_hour = now().replace(minute=0, second=0, microsecond=0)
    start_hour = end_hour - timedelta(hours=1)
    events = EntryEvent.objects.filter(timestamp__gte=start_hour, timestamp__lt=end_hour)
    entered = events.filter(event_type='enter').count()
    exited = events.filter(event_type='exit').count()

    summary, created = HourlyEntrySummary.objects.update_or_create(
        hour_block=start_hour,
        defaults={'entered': entered, 'exited': exited}
    )
    return JsonResponse({
        "status": "ok",
        "hour": start_hour.strftime('%Y-%m-%d %H:%M'),
        "entered": entered,
        "exited": exited,
        "created": created
    })

@csrf_exempt
def get_entry_state(request):
    try:
        data = redis_client.get("entry_state")
        return JsonResponse(json.loads(data or '{}'))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def chair_occupancy_view(request):
    try:
        data = redis_client.get("chair_occupancy")
        return JsonResponse(json.loads(data or '{}'))
    except redis.exceptions.ConnectionError:
        return JsonResponse({"error": "Redis connection failed"}, status=503)

@csrf_exempt
def reset_chair_cache(request):
    try:
        redis_client.delete("cached_chair_positions")
        return JsonResponse({"status": "cache cleared"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =====================================================
# === VIDEO STREAMING & DETECTION
# =====================================================

@csrf_exempt
def video_feed(request):
    def generate_stream():
        while True:
            with shared_video.video_lock:
                frame = shared_video.latest_frame.copy() if shared_video.latest_frame is not None else None
            if frame is None:
                continue
            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.03)

    return StreamingHttpResponse(generate_stream(), content_type='multipart/x-mixed-replace; boundary=frame')

def get_camera_streams(request):
    user = request.user
    cameras = Camera.objects.filter(cafe__user=user, status='active')

    streams = []
    for cam in cameras:
        streams.append({
            "camera_id": cam.id,
            "floor": cam.floor.name,
            "stream_url": f"rtsp://{cam.admin_name}:{cam.admin_password}@{cam.ip_address}/{cam.channel}"
        })

    return Response({"streams": streams})

@csrf_exempt
def start_detection_view(request):
    try:
        started = start_detection()
        return JsonResponse({"status": "started" if started else "already running"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def stop_detection_view(request):
    stop_detection()
    return JsonResponse({"status": "stopped"})
