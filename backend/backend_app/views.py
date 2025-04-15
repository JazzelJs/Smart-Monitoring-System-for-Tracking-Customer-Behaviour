from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import generics, status
from rest_framework.response import Response
from .models import User, EmailOTP
from .serializers import UserSerializer
from .utils import generate_otp, send_otp_via_email
import redis
import json
from rest_framework import generics, permissions
from .models import UserCafe, Floor, Camera, Seat, SeatDetection
from django.shortcuts import render
from django.utils.timezone import now
from django.db.models import Count, Avg
from datetime import timedelta
from .serializers import UserCafeSerializer, FloorSerializer, CameraSerializer, SeatDetectionSerializer
from .models import SeatDetection, ActivityLog, Notification, Seat, Camera
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

from .serializers import (
    UserSerializer, UserListSerializer, UserDetailSerializer,
    LoginSerializer, ResetPasswordSerializer, ValidateOTPSerializer,
    SetNewPasswordSerializer, LogoutSerializer
)
from .utils import generate_otp, send_otp_via_email

User = get_user_model()


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'


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
        email = serializer.validated_data['email']
        otp = generate_otp(email)
        send_otp_via_email(email, otp)
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


class UserCafeCreateView(generics.CreateAPIView):
    queryset = UserCafe.objects.all()
    serializer_class = UserCafeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if not serializer.is_valid():
            print(serializer.errors)
        serializer.save(user=self.request.user)

class FloorCreateView(generics.CreateAPIView):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    permission_classes = [permissions.IsAuthenticated]

class CameraCreateView(generics.CreateAPIView):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    permission_classes = [permissions.IsAuthenticated]

class CameraListView(generics.ListAPIView):
    serializer_class = CameraSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Camera.objects.filter(floor__cafe__user=self.request.user)
    
# === Redis Live View ===
@api_view(['GET'])
def get_seat_occupancy(request):
    try:
        r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        data = r.get("seat_occupancy")
        if data:
            return JsonResponse(json.loads(data))
        return JsonResponse({"occupied": 0, "available": 0})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# === Seat Detection + Logging + Notification ===
@api_view(['POST'])
def record_seat_detection(request):
    serializer = SeatDetectionSerializer(data=request.data)

    if serializer.is_valid():
        detection = serializer.save()

        # Auto-log activity
        ActivityLog.objects.create(
            cafe=detection.camera.cafe,
            seat_detection=detection,
            customer=None,  # you can link later with face recog
            action="Seated"
        )

        # Alert: 80%+ occupancy
        cafe = detection.camera.cafe
        total_seats = Seat.objects.filter(cafe=cafe).count()
        occupied_seats = Seat.objects.filter(cafe=cafe, is_occupied=True).count()

        if total_seats > 0 and occupied_seats / total_seats >= 0.8:
            Notification.objects.create(
                cafe=cafe,
                seat_detection=detection,
                message="Nearly all seats are currently occupied!",
                category="alert"
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seat_summary_analytics(request):
    user = request.user
    month_start = now().replace(day=1)

    cafes = UserCafe.objects.filter(user=user)
    seats = Seat.objects.filter(cafe__in=cafes)
    detections = SeatDetection.objects.filter(seat__in=seats, month__gte=month_start)

    # Most popular seat
    popular = detections.values("seat__seat_id").annotate(count=Count("id")).order_by("-count").first()

    # Average duration
    avg_duration = detections.aggregate(avg=Avg("duration"))["avg"]

    # Longest session
    longest = detections.order_by("-duration").first()

    response = {
        "most_popular_seat": f"Table {popular['seat__seat_id']}" if popular else None,
        "average_duration": round(avg_duration / 60) if avg_duration else 0,
        "longest_session_table": f"Table {longest.seat.seat_id}" if longest else None,
        "longest_session_duration": round(longest.duration / 60) if longest else 0,
    }

    return Response(response)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_occupied_seats(request):
    user = request.user
    cafes = UserCafe.objects.filter(user=user)
    floors = Floor.objects.filter(cafe__in=cafes)
    allowed_camera_ids = Camera.objects.filter(floor__in=floors).values_list('id', flat=True)

    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    data = r.get("current_occupied_seats")  # your YOLO script should store this

    if data:
        all_seats = json.loads(data).get("seats", [])

        # Filter seats from user's cameras only
        user_seats = [
            seat for seat in all_seats
            if int(seat.get("camera_id", 0)) in allowed_camera_ids
        ]

        return JsonResponse({"seats": user_seats})

    return JsonResponse({"seats": []})

import subprocess

@api_view(['POST'])
@permission_classes([IsAuthenticated])
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

import os   
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_yolo_detection(request):
    r = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

    pid = r.get("yolo_pid")
    if not pid:
        return Response({"status": "not running"}, status=400)

    try:
        os.kill(int(pid), 9)  # SIGKILL
        r.delete("yolo_pid")
        r.set("yolo_status", "Stopped")
        return Response({"status": "YOLO stopped"})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Camera

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_camera_streams(request):
    user = request.user
    cameras = Camera.objects.filter(cafe__user=user, status='active')

    streams = []
    for cam in cameras:
        stream_url = f"rtsp://{cam.admin_name}:{cam.admin_password}@{cam.ip_address}/{cam.channel}"
        streams.append({
            "camera_id": cam.id,
            "floor": cam.floor.name,
            "stream_url": stream_url
        })

    return Response({"streams": streams})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_detection_status(request):
    r = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
    status = r.get("yolo_status") or "Stopped"
    return Response({"status": status})
