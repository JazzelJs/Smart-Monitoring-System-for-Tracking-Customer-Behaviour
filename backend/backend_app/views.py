from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils.timezone import now
from django.http import JsonResponse
from datetime import timedelta
from django.db.models import Count, Avg
import redis, json, subprocess, os
from .utils import generate_otp, send_otp_via_email

from .models import (
    User, EmailOTP, UserCafe, Floor, Camera, Seat, 
    SeatDetection, ActivityLog, Notification
)

from .serializers import (
    UserSerializer, UserListSerializer, UserDetailSerializer,
    LoginSerializer, ResetPasswordSerializer, ValidateOTPSerializer,
    SetNewPasswordSerializer, LogoutSerializer,
    UserCafeSerializer, FloorSerializer, CameraSerializer,
    SeatDetectionSerializer
)

User = get_user_model()

# =====================================================
# === AUTHENTICATION & USER MANAGEMENT
# =====================================================

class RegisterWithOTPView(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request):
        email = request.data.get("email")
        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        otp = generate_otp(user.email)
        send_otp_via_email(user.email, otp)

        return Response({"message": "User created and OTP sent"}, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = generate_otp(serializer.validated_data['email'])
        send_otp_via_email(serializer.validated_data['email'], otp)
        return Response({"message": "OTP sent to email"}, status=status.HTTP_200_OK)

class ValidateOTPView(generics.GenericAPIView):
    serializer_class = ValidateOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "OTP validated successfully"}, status=status.HTTP_200_OK)

class SetNewPasswordView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)

class LogoutView(APIView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
            return Response({"message": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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

class CameraDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CameraSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Camera.objects.filter(floor__cafe__user=self.request.user)

# =====================================================
# === SEAT DETECTION & ANALYTICS
# =====================================================

@api_view(['POST'])
def record_seat_detection(request):
    serializer = SeatDetectionSerializer(data=request.data)

    if serializer.is_valid():
        detection = serializer.save()

        ActivityLog.objects.create(
            cafe=detection.camera.cafe,
            seat_detection=detection,
            customer=None,
            action="Seated"
        )

        total = Seat.objects.filter(cafe=detection.camera.cafe).count()
        occupied = Seat.objects.filter(cafe=detection.camera.cafe, is_occupied=True).count()
        if total > 0 and occupied / total >= 0.8:
            Notification.objects.create(
                cafe=detection.camera.cafe,
                seat_detection=detection,
                message="Nearly all seats are currently occupied!",
                category="alert"
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

    response = {
        "most_popular_seat": f"Table {popular['seat__seat_id']}" if popular else None,
        "average_duration": round(avg_duration / 60) if avg_duration else 0,
        "longest_session_table": f"Table {longest.seat.seat_id}" if longest else None,
        "longest_session_duration": round(longest.duration / 60) if longest else 0,
    }

    return Response(response)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_occupied_seats(request):
    user = request.user
    cafes = UserCafe.objects.filter(user=user)
    floors = Floor.objects.filter(cafe__in=cafes)
    allowed_camera_ids = Camera.objects.filter(floor__in=floors).values_list('id', flat=True)

    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    data = r.get("current_occupied_seats")

    if data:
        all_seats = json.loads(data).get("seats", [])
        user_seats = [seat for seat in all_seats if int(seat.get("camera_id", 0)) in allowed_camera_ids]
        return JsonResponse({"seats": user_seats})

    return JsonResponse({"seats": []})

# =====================================================
# === YOLO CONTROL
# =====================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_yolo_detection(request):
    r = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
    if r.get("yolo_pid"):
        return Response({"status": "already running"}, status=400)

    try:
        process = subprocess.Popen(["python", "yolo_realtime_detection.py"])
        r.set("yolo_pid", str(process.pid))
        r.set("yolo_status", "Running")
        return Response({"status": "YOLO started"})
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def stop_yolo_detection(request):
    r = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
    pid = r.get("yolo_pid")
    if not pid:
        return Response({"status": "not running"}, status=400)

    try:
        os.kill(int(pid), 9)
        r.delete("yolo_pid")
        r.set("yolo_status", "Stopped")
        return Response({"status": "YOLO stopped"})
    except Exception as e:
        return Response({"error": str(e)}, status=500)

# =====================================================
# === STREAMS & REDIS VIEW
# =====================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
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

@api_view(['GET'])
def get_seat_occupancy(request):
    try:
        r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        data = r.get("seat_occupancy")
        return JsonResponse(json.loads(data)) if data else JsonResponse({"occupied": 0, "available": 0})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_detection_status(request):
    r = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
    status = r.get("yolo_status") or "Stopped"
    return Response({"status": status})
