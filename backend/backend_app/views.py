from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone 
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate, TruncWeek, ExtractHour
from collections import defaultdict
from datetime import timedelta, datetime
from .models import Report, UserCafe
from .serializers import ReportSerializer
from django.utils.dateparse import parse_date
from .report_generator import generate_pdf_for_month

import calendar



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
    month_start = timezone.now().replace(day=1)

    cafes = UserCafe.objects.filter(user=user)
    cameras = Camera.objects.filter(cafe__in=cafes)

    detections = SeatDetection.objects.filter(
        camera__in=cameras,
        time_start__gte=month_start
    )

    # Most popular seat
    popular = detections.values("chair_id").annotate(
        count=Count("id")
    ).order_by("-count").first()

    # Average duration
    avg_duration = detections.exclude(time_end__isnull=True).aggregate(
        avg=Avg(F("time_end") - F("time_start"))
    )["avg"]

    # Longest completed session
    annotated = detections.exclude(time_end__isnull=True).annotate(
        duration=ExpressionWrapper(F("time_end") - F("time_start"), output_field=DurationField())
    )
    longest = annotated.order_by("-duration").first()

    # Longest ongoing session
    ongoing = detections.filter(time_end__isnull=True).annotate(
        current_duration=ExpressionWrapper(timezone.now() - F("time_start"), output_field=DurationField())
    ).order_by("-current_duration").first()

    return Response({
        "most_popular_seat": f"Chair {popular['chair_id']}" if popular else None,
        "average_duration": round(avg_duration.total_seconds() / 60) if avg_duration else 0,
        "longest_session_table": f"Chair {longest.chair_id}" if longest else None,
        "longest_session_duration": round(longest.duration.total_seconds() / 60) if longest else 0,
        "longest_current_stay": f"Chair {ongoing.chair_id}" if ongoing else None

    })



@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def peak_hour_analytics(request):

    user = request.user
    cafes = UserCafe.objects.filter(user=user)
    cameras = Camera.objects.filter(cafe__in=cafes)
    end_time = timezone.now().astimezone(timezone.get_current_timezone())
    start_time = end_time - timedelta(days=7)
    entries = EntryEvent.objects.filter(camera__in=cameras,event_type="enter", timestamp__range=(start_time, end_time))

    # Peak hour
    hour_counts = defaultdict(int)
    day_counts = defaultdict(int)
    days = set()

    for e in entries:
        hour = e.timestamp.replace(minute=0, second=0, microsecond=0)
        hour_counts[hour] += 1

        day_name = calendar.day_name[e.timestamp.weekday()]
        day_counts[day_name] += 1

        days.add(e.timestamp.date())

    peak_hour, hour_visitors = max(hour_counts.items(), key=lambda x: x[1], default=(None, 0))
    peak_day, day_visitors = max(day_counts.items(), key=lambda x: x[1], default=("None", 0))
    avg_visitors = entries.count() // len(days) if days else 0

    # 🔸 CURRENT OCCUPANCY
    try:
        redis_data = redis_client.get("chair_occupancy")
        data = json.loads(redis_data or '{}')
        chairs = data.get("chairs", {})
        occupied = sum(1 for c in chairs.values() if c["status"] == "occupied")
        total = len(chairs)
        occupancy_percent = round((occupied / total) * 100) if total else 0
    except:
        occupied, total, occupancy_percent = 0, 0, 0

    return Response({
        "peak_hour": f"{peak_hour.hour:02d}:00 - {peak_hour.hour+1:02d}:00" if peak_hour else "-",
        "peak_hour_visitors": hour_visitors,
        "peak_day": peak_day,
        "peak_day_visitors": day_visitors,
        "avg_daily_visitors": avg_visitors,
        "occupancy_percent": occupancy_percent,
        "occupied_seats": occupied,
        "total_seats": total,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def visitor_traffic(request):

    user = request.user
    cafes = UserCafe.objects.filter(user=user)
    cameras = Camera.objects.filter(cafe__in=cafes)
    mode = request.GET.get('mode', 'daily')
    now_time = timezone.now()

    if mode == 'daily':
        # Past 1 day, group by hour
        start_time = now_time.replace(hour=0, minute=0, second=0, microsecond=0)
        entries = EntryEvent.objects.filter(event_type='enter', timestamp__gte=start_time)
        data = entries.annotate(hour=ExtractHour('timestamp')).values('hour').annotate(count=Count('id')).order_by('hour')
        result = [{"label": f"{d['hour']:02d}:00", "count": d['count']} for d in data]

    elif mode == 'weekly':
        # Past 7 days, group by day
        start_time = now_time - timedelta(days=6)
        entries = EntryEvent.objects.filter(event_type='enter', timestamp__date__gte=start_time.date())
        data = entries.annotate(day=TruncDate('timestamp'),  tzinfo=timezone.get_current_timezone_name()).values('day').annotate(count=Count('id')).order_by('day'),  
        result = [{"label": d['day'].strftime('%A'), "count": d['count']} for d in data]

    elif mode == 'monthly':
        # Last 4 weeks, group by week
        start_time = now_time - timedelta(weeks=4)
        entries = EntryEvent.objects.filter(event_type='enter', timestamp__gte=start_time)
        data = entries.annotate(week=TruncWeek('timestamp'),  tzinfo=timezone.get_current_timezone_name()).values('week').annotate(count=Count('id')).order_by('week')
        result = [{"label": d['week'].strftime('Week %W'), "count": d['count']} for d in data]

    else:
        result = []

    if not result:
        result = [{"label": "No Data", "count": 0}]

    return Response(result)



@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def customer_analytics(request):
    user = request.user
    cafes = UserCafe.objects.filter(user=user)
    now = timezone.now()
    month_start = now.replace(day=1)

    # Query customers for user's cafes
    customers = Customer.objects.filter(cafe__in=cafes)

    # Filter this month
    current_month_customers = customers.filter(first_visit__gte=month_start)

    # Metrics
    first_time_count = current_month_customers.filter(status='new').count()
    returning_count = current_month_customers.filter(status='returning').count()
    total_customers = current_month_customers.count()

    retention_rate = (returning_count / total_customers * 100) if total_customers else 0
    avg_visits = customers.aggregate(avg_visits=Avg('visit_count'))['avg_visits'] or 0

    return Response({
        "first_time_customers": first_time_count,
        "returning_customers": returning_count,
        "retention_rate": round(retention_rate, 2),
        "average_visits": round(avg_visits, 1)
    })

# views.py
from django.http import JsonResponse
from backend_app.models import EntryEvent, SeatDetection

def activity_log(request):
    event_filter = request.GET.get('event_type')
    location_filter = request.GET.get('location')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Entry Events
    entry_logs = EntryEvent.objects.select_related('camera__floor').values(
        'id', 'timestamp', 'event_type', 'camera__floor__name'
    )

    # Seat Detection Events
    seat_logs = SeatDetection.objects.select_related('camera__floor').values(
        'id', 'time_start', 'time_end', 'camera__floor__name'
    )

    logs = []

    for e in entry_logs:
        logs.append({
            'id': f"entry_{e['id']}",
            'timestamp': e['timestamp'],
            'event': 'Customer Arrives' if e['event_type'] == 'enter' else 'Customer Exits',
            'location': e.get('camera__floor__name', 'Unknown'),
        })

    for s in seat_logs:
        logs.append({
            'id': f"seat_{s['id']}",
            'timestamp': s['time_start'],
            'event': 'Customer Sitting Down',
            'location': s.get('camera__floor__name', 'Unknown'),
        })

    # Apply filters
    if event_filter:
        logs = [log for log in logs if log['event'] == event_filter]

    if location_filter:
        logs = [log for log in logs if log['location'] == location_filter]

    if start_date:
        logs = [log for log in logs if log['timestamp'].date() >= datetime.strptime(start_date, "%Y-%m-%d").date()]

    if end_date:
        logs = [log for log in logs if log['timestamp'].date() <= datetime.strptime(end_date, "%Y-%m-%d").date()]

    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    return JsonResponse(logs[:5], safe=False)





# =====================================================
# === REDIS: ENTRY & CHAIR STATES
# =====================================================

@csrf_exempt
def update_hourly_entry_summary(request):
    end_hour = timezone.now().replace(minute=0, second=0, microsecond=0)
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


# === CUSTOMER TRACKING UTILS ===
from .models import Customer

def get_or_create_customer(face_id):
    customer, created = Customer.objects.get_or_create(
        face_id=face_id,
        defaults={
            'first_visit': timezone.now(),
            'visit_count': 1,
            'last_visit': timezone.now(),
            'average_stay': 0.0,
            'status': 'new'
        }
    )
    if not created:
        customer.visit_count += 1
        customer.last_visit = timezone.now()
        customer.status = 'returning'
        customer.save()
    return customer

def log_entry_event(track_id, face_id=None):
    customer = None
    if face_id:
        customer = get_or_create_customer(face_id)
    
    EntryEvent.objects.create(
        event_type='enter',
        track_id=track_id,
        customer=customer  # 🔥 Link customer here!
    )

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
        # Check Redis flag first
        status = redis_client.get("detection_status")
        if status == "running":
            return JsonResponse({"status": "already running"})

        # Start detection process
        started = start_detection()

        if started:
            redis_client.set("detection_status", "running")
            return JsonResponse({"status": "started"})
        else:
            return JsonResponse({"status": "failed to start"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def stop_detection_view(request):
    try:
        stop_detection()
        redis_client.set("detection_status", "stopped")
        return JsonResponse({"status": "stopped"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def detection_status(request):
    # Example: use Redis flag or global variable
    status = redis_client.get("detection_status") or "stopped"
    return Response({"is_detecting": status == "running"})






# Reports Generation

from django.db.models.functions import TruncDay, TruncHour, TruncMonth
from dateutil.relativedelta import relativedelta
from django.utils.timezone import make_aware



@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def monthly_report_summary(request, year, month):
    user = request.user
    year, month = int(year), int(month)

    cafes = UserCafe.objects.filter(user=user)
    cameras = Camera.objects.filter(cafe__in=cafes)
    now = timezone.now()

    start = make_aware(datetime(year, month, 1))
    end = make_aware((datetime(year, month, 1) + relativedelta(months=1)) - timedelta(seconds=1))
    prev_start = make_aware(datetime(year, month, 1) - relativedelta(months=1))
    prev_end = make_aware(datetime(year, month, 1) - timedelta(seconds=1))


    # === TOTAL VISITORS ===
    total_visitors = EntryEvent.objects.filter(camera__in=cameras, event_type="enter", timestamp__range=(start, end)).count()

    # === PEAK HOUR ===
    hourly_data = EntryEvent.objects.filter(camera__in=cameras, event_type="enter", timestamp__range=(start, end)) \
        .annotate(hour=TruncHour('timestamp'),  tzinfo=timezone.get_current_timezone_name()) \
        .values('hour').annotate(count=Count('id')).order_by('-count')
    peak = hourly_data.first()
    peak_hour = f"{peak['hour'].hour:02d}:00 - {peak['hour'].hour+1:02d}:00" if peak else "-"

    # === RETURNING CUSTOMERS ===
    customer_ids = EntryEvent.objects.filter(camera__in=cameras, timestamp__range=(start, end)) \
        .values_list('customer_id', flat=True).distinct()

    returning_customers = Customer.objects.filter(customer_id__in=customer_ids, status='returning').count()
    returning_percentage = (returning_customers / customer_ids.count()) * 100 if customer_ids else 0

    # === CUSTOMER BREAKDOWN ===
    first_time = Customer.objects.filter(customer_id__in=customer_ids, status='new').count()
    breakdown = {
        "first_time": first_time,
        "returning": returning_customers
    }

    # === AVERAGE DURATION ===
    detections = SeatDetection.objects.filter(camera__in=cameras, time_start__range=(start, end)).exclude(time_end__isnull=True)
    durations = detections.annotate(duration=ExpressionWrapper(F('time_end') - F('time_start'), output_field=DurationField()))
    avg_duration = durations.aggregate(avg=Avg('duration'))['avg']
    avg_duration_str = f"{avg_duration.seconds // 3600} H {((avg_duration.seconds // 60) % 60)} M" if avg_duration else "0 H 0 M"

    # === DAILY TRAFFIC (THIS vs LAST MONTH) ===
    def get_daily_traffic(start, end):
        return EntryEvent.objects.filter(camera__in=cameras, event_type="enter", timestamp__range=(start, end)) \
            .annotate(day=TruncDay('timestamp'),  tzinfo=timezone.get_current_timezone_name()) \
            .values('day').annotate(count=Count('id')).order_by('day')

    daily_this = list(get_daily_traffic(start, end))
    daily_last = list(get_daily_traffic(prev_start, prev_end))

    # === HOURLY TRAFFIC (THIS vs LAST MONTH) ===
    def get_hourly_traffic(start, end):
        return EntryEvent.objects.filter(camera__in=cameras, event_type="enter", timestamp__range=(start, end)) \
            .annotate(hour=ExtractHour('timestamp')) \
            .values('hour').annotate(count=Count('id')).order_by('hour')

    hourly_this = list(get_hourly_traffic(start, end))
    hourly_last = list(get_hourly_traffic(prev_start, prev_end))

    # === MONTHLY TRENDS (LAST 6 MONTHS) ===
    trends_start = now - relativedelta(months=6)
    monthly_trends = EntryEvent.objects.filter(camera__in=cameras, event_type="enter", timestamp__gte=trends_start) \
        .annotate(month=TruncMonth('timestamp'),  tzinfo=timezone.get_current_timezone_name()) \
        .values('month').annotate(count=Count('id')).order_by('month')

    # === MOST POPULAR SEAT (THIS vs LAST MONTH) ===
    def get_popular_seat(start, end):
        result = SeatDetection.objects.filter(camera__in=cameras, time_start__range=(start, end)) \
            .values('chair_id').annotate(count=Count('id')).order_by('-count').first()
        return result['chair_id'] if result else None

    popular_this = get_popular_seat(start, end)
    popular_last = get_popular_seat(prev_start, prev_end)

    return Response({
        "total_visitors": total_visitors,
        "peak_hour": peak_hour,
        "returning_customers_percentage": round(returning_percentage, 1),
        "average_visit_duration": avg_duration_str,
        "daily_visitor_traffic": {
            "this_month": daily_this,
            "last_month": daily_last
        },
        "hourly_visitor_traffic": {
            "this_month": hourly_this,
            "last_month": hourly_last
        },
        "monthly_visitor_trends": monthly_trends,
        "popular_seat": {
            "this_month": f"Chair {popular_this}" if popular_this else "-",
            "last_month": f"Chair {popular_last}" if popular_last else "-"
        },
        "customer_breakdown": breakdown
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def historical_reports(request):
    user = request.user
    year = request.GET.get('year')
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')

    cafes = UserCafe.objects.filter(user=user)
    reports = Report.objects.filter(cafe__in=cafes)

    if year:
        reports = reports.filter(year=year)

    if start_date:
        start = parse_date(start_date)
        reports = reports.filter(created_at__date__gte=start)

    if end_date:
        end = parse_date(end_date)
        reports = reports.filter(created_at__date__lte=end)

    reports = reports.order_by('-created_at')
    serializer = ReportSerializer(reports, many=True)
    return Response(serializer.data)



class GenerateReportView(APIView):
    def post(self, request):
        user = request.user
        cafe = UserCafe.objects.get(user=user)

        year = int(request.data.get("year"))
        month = int(request.data.get("month"))

        if Report.objects.filter(cafe=cafe, year=year, month=month).exists():
            return Response({"error": "Report already exists."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate PDF (return file URL)
        file_url = generate_pdf_for_month(cafe, year, month)

        # Save Report
        report = Report.objects.create(cafe=cafe, year=year, month=month, file_url=file_url)
        return Response({"status": "success", "report_id": report.id}, status=status.HTTP_201_CREATED)


class ReportListView(APIView):
    def get(self, request):
        user = request.user
        cafe = UserCafe.objects.get(user=user)
        reports = Report.objects.filter(cafe=cafe).order_by('-year', '-month')

        data = [
            {
                "id": report.id,
                "year": report.year,
                "month": report.month,
                "file_url": report.file_url,
                "created_at": report.created_at
            }
            for report in reports
        ]
        return Response(data)