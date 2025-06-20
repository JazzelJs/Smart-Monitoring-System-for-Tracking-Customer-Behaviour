# Generated by Django 5.0.6 on 2025-05-01 09:50

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Camera',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive')], max_length=50)),
                ('location', models.CharField(blank=True, max_length=255, null=True)),
                ('last_active', models.DateTimeField(blank=True, null=True)),
                ('channel', models.CharField(max_length=50)),
                ('ip_address', models.GenericIPAddressField()),
                ('admin_name', models.CharField(blank=True, max_length=100)),
                ('admin_password', models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('customer_id', models.AutoField(primary_key=True, serialize=False)),
                ('face_id', models.CharField(max_length=100, unique=True)),
                ('first_visit', models.DateTimeField()),
                ('visit_count', models.IntegerField(default=0)),
                ('last_visit', models.DateTimeField(blank=True, null=True)),
                ('average_stay', models.FloatField()),
                ('status', models.CharField(choices=[('new', 'New'), ('returning', 'Returning')], max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='EmailOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('code', models.CharField(max_length=6)),
                ('purpose', models.CharField(choices=[('signup', 'Signup'), ('reset', 'Reset')], default='signup', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Floor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('floor_number', models.IntegerField()),
                ('name', models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='HourlyEntrySummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hour_block', models.DateTimeField(unique=True)),
                ('entered', models.PositiveIntegerField(default=0)),
                ('exited', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Seat',
            fields=[
                ('seat_id', models.AutoField(primary_key=True, serialize=False)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('is_occupied', models.BooleanField(default=False)),
                ('x1', models.IntegerField()),
                ('y1', models.IntegerField()),
                ('x2', models.IntegerField()),
                ('y2', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('name', models.CharField(max_length=150)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EntryEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('enter', 'Enter'), ('exit', 'Exit')], max_length=5)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('track_id', models.IntegerField(blank=True, null=True)),
                ('camera', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend_app.camera')),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend_app.customer')),
            ],
        ),
        migrations.AddField(
            model_name='camera',
            name='floor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cameras', to='backend_app.floor'),
        ),
        migrations.CreateModel(
            name='SeatDetection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_start', models.DateTimeField()),
                ('time_end', models.DateTimeField(blank=True, null=True)),
                ('camera', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detections', to='backend_app.camera')),
                ('seat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detections', to='backend_app.seat')),
            ],
        ),
        migrations.CreateModel(
            name='UserCafe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('location', models.CharField(max_length=255)),
                ('capacity', models.IntegerField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cafes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='seat',
            name='cafe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seats', to='backend_app.usercafe'),
        ),
        migrations.CreateModel(
            name='PopularSeat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usage_count', models.IntegerField(default=0)),
                ('avg_duration', models.FloatField()),
                ('seat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='popularity', to='backend_app.seat')),
                ('cafe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='popular_seats', to='backend_app.usercafe')),
            ],
        ),
        migrations.CreateModel(
            name='PeakHour',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('current_occupancy', models.FloatField()),
                ('avg_daily_visitors', models.FloatField()),
                ('detector', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='peak_hours', to='backend_app.seatdetection')),
                ('cafe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='peak_hours', to='backend_app.usercafe')),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('category', models.CharField(choices=[('info', 'Info'), ('alert', 'Alert')], max_length=50)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
                ('peak_hour', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='backend_app.peakhour')),
                ('seat_detection', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='backend_app.seatdetection')),
                ('cafe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='backend_app.usercafe')),
            ],
        ),
        migrations.AddField(
            model_name='floor',
            name='cafe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='floors', to='backend_app.usercafe'),
        ),
        migrations.AddField(
            model_name='customer',
            name='cafe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customers', to='backend_app.usercafe'),
        ),
        migrations.AddField(
            model_name='camera',
            name='cafe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cameras', to='backend_app.usercafe'),
        ),
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_type', models.CharField(choices=[('seating', 'Seating'), ('entry', 'Entry'), ('exit', 'Exit')], default='seating', max_length=20)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='backend_app.customer')),
                ('seat_detection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_logs', to='backend_app.seatdetection')),
                ('cafe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_logs', to='backend_app.usercafe')),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('month', models.IntegerField()),
                ('file_url', models.URLField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cafe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='backend_app.usercafe')),
            ],
            options={
                'unique_together': {('cafe', 'year', 'month')},
            },
        ),
    ]
