from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import EmailOTP, UserCafe, Floor, Camera

User = get_user_model()


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
        user.set_password(validated_data['password'])  # ✅ This hashes it!
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



class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email not found")
        return value



from rest_framework import serializers
from .models import EmailOTP
from django.contrib.auth import get_user_model

User = get_user_model()

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
                purpose='signup'  # <-- make sure it's for signup
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


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class UserCafeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCafe
        fields = ["id", "name", "location", "capacity", "user"]
        extra_kwargs = {'user': {'read_only': True}}  # 🔒 this line makes it safe


class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'cafe', 'floor_number', 'name']


# serializers.py
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
            "admin_password"
        ]

from rest_framework import serializers
from .models import SeatDetection
from datetime import datetime

class SeatDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatDetection
        fields = '__all__'

    def validate(self, data):
        # Auto-calculate the month from time_start
        if data.get("time_start"):
            data["month"] = data["time_start"].date().replace(day=1)
        return data
