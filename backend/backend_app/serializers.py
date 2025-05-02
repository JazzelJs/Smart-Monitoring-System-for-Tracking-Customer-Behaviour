from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    EmailOTP, UserCafe, Floor, Camera, SeatDetection, EntryEvent
)
from datetime import datetime

import calendar

User = get_user_model()

# =====================================================
# === AUTHENTICATION & USER SERIALIZERS
# =====================================================

class UserSerializer(serializers.ModelSerializer):
    passwordConfirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'passwordConfirm', 'name', 'phone_number']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if data['password'] != data['passwordConfirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('passwordConfirm')
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name']


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'phone_number']


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = authenticate(request=self.context.get('request'), email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
            }
        }


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
class UserCafeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCafe
        fields = ['id', 'name', 'location', 'capacity']


# =====================================================
# === OTP & PASSWORD RESET
# =====================================================

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email not found")
        return value


class ValidateOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()

    def validate(self, data):
        email = data['email']
        otp = data['otp']
        try:
            record = EmailOTP.objects.filter(
                email=email,
                code=otp,
                purpose='signup'
            ).latest("created_at")

            if record.is_expired():
                raise serializers.ValidationError("OTP has expired")

        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP")

        return data


class SetNewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email not registered")
        return value

    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

# =====================================================
# === CAFE, FLOOR, CAMERA, SEAT DETECTION
# =====================================================

class UserCafeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCafe
        fields = ["id", "name", "location", "capacity", "user"]
        extra_kwargs = {'user': {'read_only': True}}


class FloorSerializer(serializers.ModelSerializer):
    camera_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, allow_empty=True, default=list
    )

    class Meta:
        model = Floor
        fields = ['id', 'cafe', 'floor_number', 'name', 'camera_ids']
        extra_kwargs = {'cafe': {'read_only': True}}

    def create(self, validated_data):
        camera_ids = validated_data.pop('camera_ids', [])
        floor = Floor.objects.create(**validated_data)

        if camera_ids:
            Camera.objects.filter(id__in=camera_ids).update(floor=floor)

        return floor


class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = [
            "id",
            "cafe",
            "floor",
            "status",
            "ip_address",
            "channel",
            "location",
            "admin_name",
            "admin_password",
            "last_active",
        ]
        extra_kwargs = {
            "cafe": {"read_only": True},
            "admin_password": {"write_only": True}
        }

    def create(self, validated_data):
        floor = validated_data.get("floor")

        if not floor:
            raise serializers.ValidationError({"floor": "Floor is required."})

        validated_data["cafe"] = floor.cafe  # ✅ assign cafe from floor
        return super().create(validated_data)



class SeatDetectionSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()

    class Meta:
        model = SeatDetection
        fields = ['id', 'chair_id', 'time_start', 'time_end', 'duration']
        read_only_fields = ['id', 'duration']

    def get_duration(self, obj):
        return obj.duration()


class entry_event_serializer(serializers.ModelSerializer):
    class Meta:
        model = EntryEvent
        fields = ['event_type', 'timestamp', 'track_id']



#Reports

# serializers.py
from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    date_range = serializers.SerializerMethodField()
    url_view = serializers.SerializerMethodField()
    url_download = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = ['id', 'name', 'date_range', 'file_url', 'url_view', 'url_download']

    def get_name(self, obj):
        month_name = obj.created_at.strftime('%B')
        return f"{month_name} {obj.year}"

    def get_date_range(self, obj):
        month = obj.month
        year = obj.year
        _, last_day = calendar.monthrange(year, month)
        start = datetime(year, month, 1).strftime("%B 1, %Y")
        end = datetime(year, month, last_day).strftime("%B %d, %Y")
        return f"{start} - {end}"

    def get_url_view(self, obj):
        return obj.file_url  # You can customize if there's a separate view URL

    def get_url_download(self, obj):
        return obj.file_url  # Or different download link

