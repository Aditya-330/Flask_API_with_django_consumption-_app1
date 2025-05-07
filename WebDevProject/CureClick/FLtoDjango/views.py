from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.db.models import Count, Sum, Avg, Q
import calendar, random, json
from .models import Doctor, TimeSlot, ConsultationType, UserBooking, UserProfile
from .api_client import APIClient
from django.db import connection

def api_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('api_token'):
            messages.error(request, 'Please log in to access this page')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def debug_user_in_db(username):
    """Check if user exists in the database using raw SQL query"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, username, email, password FROM auth_user WHERE username = %s", [username])
        row = cursor.fetchone()
        if row:
            return f"User found: ID={row[0]}, username={row[1]}, email={row[2]}, password_hash={row[3][:20]}..."
        return "User not found in database"

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        print(f"Username: {username}")
        
        print(debug_user_in_db(username))
        
        api_client = APIClient()
        response_data, status_code = api_client.login(username, password)
        
        print(f"API login response status: {status_code}")
        
        if status_code == 200:
            print(f"API login successful for user: {username}")
            print(f"API token: {response_data.get('token')[:20]}...")
            
            request.session['api_token'] = response_data.get('token')
            request.session['user_id'] = response_data.get('id')
            
            try:
                user = authenticate(request, username=username, password=password)
                if user:
                    print(f"Django authentication successful for user: {username}")
                    login(request, user)
                else:
                    print(f"Django authentication failed for user: {username}")
                    
                    try:
                        user = User.objects.get(username=username)
                    except User.DoesNotExist:
                        try:
                            user = User.objects.get(email=username)
                        except User.DoesNotExist:
                            print(f"Creating new Django user: {username}")
                            user = User.objects.create_user(
                                username=username,
                                password=password,
                                email=response_data.get('email', '')
                            )
                    
                    print(f"Force logging in user: {username}")
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)
            except Exception as e:
                print(f"Error during Django authentication: {str(e)}")
            
            messages.success(request, 'Login successful')
            return redirect('index')
        else:
            error_message = response_data.get('error', 'Invalid username or password')
            print(f"Login failed: {error_message}")
            messages.error(request, f'Login failed: {error_message}')
            
    return render(request, 'login.html', {'active_form': 'login'})


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')
        full_name = request.POST.get('full_name', '')
        
        print(f"\n==== REGISTRATION ATTEMPT ====")
        print(f"Username: {username}")
        print(f"Email: {email}")
        
        print(debug_user_in_db(username))
        
        if password != cpassword:
            messages.error(request, 'Passwords do not match')
            return render(request, 'login.html', {'active_form': 'register'})
        
        api_client = APIClient()
        response_data, status_code = api_client.signup(username, email, password, full_name)
        
        print(f"API RESPONSE: status={status_code}")
        if status_code == 201:
            print(f"API registration successful for {username}")
            
            print(f"After API call: {debug_user_in_db(username)}")
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM auth_user WHERE username = %s", [username])
                exists = cursor.fetchone()[0] > 0
            
            if exists:
                print(f"User {username} exists in database already, skipping Django user creation")
                messages.success(request, 'Registration successful! You can now login.')
                return redirect('login')
            
            # Django user doesn't exist, create it directly with SQL to bypass ORM issues
            try:
                # First, try the normal ORM method
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email
                )
                print(f"Django user {username} created successfully via ORM")
                messages.success(request, 'Registration successful! You can now login.')
            except Exception as orm_error:
                print(f"ORM error: {str(orm_error)}")
                
                # Fallback: try direct SQL (should be avoided but useful for debugging)
                try:
                    from django.contrib.auth.hashers import make_password as django_make_password
                    hashed_password = django_make_password(password)
                    
                    # Get the highest ID to avoid conflicts
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT MAX(id) FROM auth_user")
                        max_id = cursor.fetchone()[0] or 0
                        new_id = max_id + 1
                        
                        # Current date in proper format
                        import datetime
                        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Insert the user directly
                        cursor.execute("""
                            INSERT INTO auth_user (id, password, is_superuser, username, email, is_staff, is_active, date_joined, last_login, first_name, last_name)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, %s, %s)
                        """, [new_id, hashed_password, False, username, email, False, True, now, '', ''])
                        
                    print(f"Django user {username} created directly via SQL")
                    messages.success(request, 'Registration successful! You can now login.')
                except Exception as sql_error:
                    print(f"SQL insertion error: {str(sql_error)}")
                    messages.warning(request, f'API registration successful, but Django user creation failed. You can still login.')
                
            return redirect('login')
        else:
            # Display the error message from the API
            error_message = response_data.get('error', 'Registration failed')
            print(f"Registration failed: {error_message}")
            messages.error(request, f'Registration failed: {error_message}')
            
    return render(request, 'login.html', {'active_form': 'register'})

def home_view(request):
    if request.method == 'POST' and 'doctor_id' in request.POST:
        doctor_id = request.POST.get('doctor_id')
        password = request.POST.get('password')
        try:
            doctor = Doctor.objects.get(doctor_code=doctor_id)
            if password == 'doctor123':
                user = None
                try:
                    user = User.objects.get(username=doctor_id)
                except User.DoesNotExist:
                    user = User.objects.create_user(
                        username=doctor_id,
                        password='doctor123',
                        first_name=doctor.name
                    )
                login(request, user)
                # Add doctor info to session
                request.session['is_doctor'] = True
                return redirect('docDash')
            else:
                messages.error(request, 'Invalid password')
        except Doctor.DoesNotExist:
            messages.error(request, 'Doctor ID not found')
    # Always render the homepage in all other cases
    return render(request, 'index.html')




def why_view(request):
    return render(request, 'why.html')




@login_required
def doc_dashboard_view(request):
    # Check if the user is a doctor
    try:
        doctor = Doctor.objects.get(doctor_code=request.user.username)
    except Doctor.DoesNotExist:
        # If not a doctor, render the page with a warning
        messages.error(request, "You don't have permission to access the doctor dashboard")
        return redirect('index')
    
    # Handle POST requests for appointment status updates
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')
        
        try:
            # Verify that the booking belongs to this doctor
            booking = UserBooking.objects.get(id=booking_id, doctor=doctor)
            
            # Update the booking status based on the action
            if action == 'check_in':
                booking.status = 'in_progress'
                messages.success(request, f"Patient {booking.full_name} has been checked in")
            elif action == 'confirm':
                booking.status = 'confirmed'
                messages.success(request, f"Appointment for {booking.full_name} has been confirmed")
            elif action == 'complete':
                booking.status = 'completed'
                messages.success(request, f"Appointment for {booking.full_name} has been completed")
            else:
                messages.error(request, "Invalid action")
                
            booking.save()
        except UserBooking.DoesNotExist:
            messages.error(request, "Booking not found or not authorized")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    
    # Current date info
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year
    days_in_month = calendar.monthrange(current_year, current_month)[1]
    
    # Today's appointments
    todays_only_appointments = UserBooking.objects.filter(
        doctor=doctor,
        selected_date=today
    ).order_by('selected_time')
    
    # Count of today's appointments only (not future dates)
    today_count = todays_only_appointments.count()
    
    # Check if there are appointments specifically for today
    today_has_appointments = today_count > 0
    
    # All appointments query (which may include future dates if needed)
    todays_appointments = todays_only_appointments
    
    # If today has no appointments, use all future appointments without slicing yet
    if not today_has_appointments:
        print("No appointments found for today's date. Getting ALL future appointments...")
        todays_appointments = UserBooking.objects.filter(
            doctor=doctor,
            selected_date__gte=today
        ).order_by('selected_date', 'selected_time')  # Remove the slice [:10]
    
    # Debug: Print all appointments for today to check data
    print(f"Today's appointments for doctor {doctor.name}:")
    if not todays_appointments:
        print("WARNING: No appointments found for today. This is likely why nothing is showing in the dashboard.")
    for app in todays_appointments[:10]:  # Only print the first 10 for debugging
        print(f" - {app.id}: {app.full_name} at {app.selected_time}, status: {app.status}")
    
    all_appointments_count = todays_appointments.count()
    
    print(f"Server's current date: {today}")
    print(f"Formatted as: {today.strftime('%Y-%m-%d')}")
    
   
    upcoming_appointments = UserBooking.objects.filter(
        doctor=doctor,
        status__in=['confirmed', 'pending']
    ).filter(
        Q(selected_date__gt=today)
    ).order_by('selected_date', 'selected_time')
    
    upcoming_count = upcoming_appointments.count()
    
    print(f"Upcoming appointments count (future dates only): {upcoming_count}")
    for app in upcoming_appointments[:5]:  # Show first 5 for debugging
        print(f" - Upcoming: {app.id}: {app.full_name} on {app.selected_date} at {app.selected_time}, status: {app.status}")
    
    completed_appointments = todays_appointments.filter(status='completed')
    completed_count = completed_appointments.count()
    
    in_progress_appointments = todays_appointments.filter(status='in_progress')
    in_progress_count = in_progress_appointments.count()

    todays_appointments_display = todays_appointments[:10]  
    
    yesterday = today - timedelta(days=1)
    yesterday_count = UserBooking.objects.filter(doctor=doctor, selected_date=yesterday).count()
    
    # Calculate percentage change from yesterday
    if yesterday_count > 0:
        appointment_change_pct = ((today_count - yesterday_count) / yesterday_count) * 100
    else:
        appointment_change_pct = 0 if today_count == 0 else 100
    
    # Today's earnings - Make sure consultation_fee is a numeric field
    todays_earnings = UserBooking.objects.filter(
        doctor=doctor,
        selected_date=today,
        status__in=['confirmed', 'completed', 'in_progress']
    ).aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0
    
    # Yesterday's earnings for comparison
    yesterday_earnings = UserBooking.objects.filter(
        doctor=doctor,
        selected_date=yesterday,
        status__in=['confirmed', 'completed', 'in_progress']
    ).aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0
    
    # Calculate percentage change in earnings
    if yesterday_earnings > 0:
        earnings_change_pct = ((todays_earnings - yesterday_earnings) / yesterday_earnings) * 100
    else:
        earnings_change_pct = 0 if todays_earnings == 0 else 100
    
    # Monthly earnings
    first_day_of_month = today.replace(day=1)
    monthly_earnings = UserBooking.objects.filter(
        doctor=doctor,
        selected_date__gte=first_day_of_month,
        selected_date__lte=today,
        status__in=['confirmed', 'completed', 'in_progress']
    ).aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0
    
    # Last month's earnings for comparison
    last_month = first_day_of_month - timedelta(days=1)
    first_day_last_month = last_month.replace(day=1)
    last_month_earnings = UserBooking.objects.filter(
        doctor=doctor,
        selected_date__gte=first_day_last_month,
        selected_date__lte=last_month,
        status__in=['confirmed', 'completed', 'in_progress']
    ).aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0
    
    # Calculate percentage change in monthly earnings
    if last_month_earnings > 0:
        monthly_change_pct = ((monthly_earnings - last_month_earnings) / last_month_earnings) * 100
    else:
        monthly_change_pct = 0 if monthly_earnings == 0 else 100
    
    # Current rating from Doctor model
    current_rating = float(doctor.rating) if doctor.rating else 4.5
    
    # For rating change, we'll calculate an estimated change based on recent reviews
    # This is a placeholder; in a real app, you'd have a table tracking rating changes
    rating_change = 0.1  # This would typically come from comparing current rating with previous period
    
    # Count monthly patients
    monthly_patients = UserBooking.objects.filter(
        doctor=doctor,
        selected_date__gte=first_day_of_month,
        selected_date__lte=today
    ).values('user').distinct().count()
    
    # Last month patients for comparison
    last_month_patients = UserBooking.objects.filter(
        doctor=doctor,
        selected_date__gte=first_day_last_month,
        selected_date__lte=last_month
    ).values('user').distinct().count()
    
    # Calculate percentage change in monthly patients
    if last_month_patients > 0:
        patient_change_pct = ((monthly_patients - last_month_patients) / last_month_patients) * 100
    else:
        patient_change_pct = 0 if monthly_patients == 0 else 100
    
    # Patient queue - patients with appointments in the next hour or waiting up to 30 min
    now = timezone.now()
    time_30_min_ago = (now - timedelta(minutes=30)).time()
    time_60_min_ahead = (now + timedelta(minutes=60)).time()
    
    # Handle time edge cases (crossing midnight)
    if time_30_min_ago > time_60_min_ahead:
        # If we're crossing midnight, we need two queries
        queue_patients_before_midnight = UserBooking.objects.filter(
            doctor=doctor,
            selected_date=today,
            status='confirmed',
            selected_time__gte=time_30_min_ago
        )
        queue_patients_after_midnight = UserBooking.objects.filter(
            doctor=doctor,
            selected_date=today + timedelta(days=1),
            status='confirmed',
            selected_time__lte=time_60_min_ahead
        )
        waiting_patients = list(queue_patients_before_midnight) + list(queue_patients_after_midnight)
        waiting_patients.sort(key=lambda x: x.selected_time)
    else:
        waiting_patients = UserBooking.objects.filter(
            doctor=doctor,
            selected_date=today,
            status='confirmed',
            selected_time__gte=time_30_min_ago,
            selected_time__lte=time_60_min_ahead
        ).order_by('selected_time')
    
    # Format queue patients with waiting time
    waiting_patients_data = []
    now = timezone.now()
    for booking in waiting_patients:
        # Create datetime objects for comparison
        appointment_time = datetime.combine(booking.selected_date, booking.selected_time)
        appointment_datetime = timezone.make_aware(appointment_time)
        
        time_diff = now - appointment_datetime if now > appointment_datetime else appointment_datetime - now
        minutes_diff = int(time_diff.total_seconds() / 60)
        
        if now > appointment_datetime:
            wait_time = f"Waiting {minutes_diff} min"
        else:
            wait_time = f"In {minutes_diff} min"
            
        # Check if this is the patient's first booking
        is_new = UserBooking.objects.filter(user=booking.user).count() <= 1
        
        # Format the patient's name
        patient_name = booking.full_name
        if not patient_name and booking.user:
            patient_name = f"{booking.user.first_name} {booking.user.last_name}".strip()
            if not patient_name:
                patient_name = booking.user.username
                
        waiting_patients_data.append({
            'id': booking.id,
            'name': patient_name,
            'wait_time': wait_time,
            'is_new': is_new
        })
    
    # Get current month and year for calendar
    current_month_year = today.strftime('%B %Y')
    
    # Calendar events - real appointments for this month
    month_start = today.replace(day=1)
    if month_start.month == 12:
        month_end = datetime(month_start.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = datetime(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
    
    # Get all appointments for this month
    month_appointments = UserBooking.objects.filter(
        doctor=doctor,
        selected_date__gte=month_start,
        selected_date__lte=month_end
    )
    
    # Debug: Print all month appointments to check data
    print(f"Month appointments for doctor {doctor.name}:")
    if not month_appointments:
        print("WARNING: No appointments found for this month. Calendar will be empty.")
    for app in month_appointments:
        print(f" - {app.id}: {app.full_name} on {app.selected_date}, status: {app.status}")
    
    # Format as calendar events
    calendar_events = []
    for booking in month_appointments:
        # Ensure full_name is never empty
        display_name = booking.full_name
        if not display_name and booking.user:
            display_name = f"{booking.user.first_name} {booking.user.last_name}".strip()
            if not display_name:
                display_name = booking.user.username
        
        calendar_events.append({
            'id': booking.id,
            'title': display_name,
            'date': booking.selected_date.strftime('%Y-%m-%d'),
            'time': booking.selected_time.strftime('%H:%M'),
            'status': booking.status
        })
    
    # ===== CHART DATA =====
    
    # 1. Appointments data for the last 7 days
    appointments_data = []
    days_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = UserBooking.objects.filter(
            doctor=doctor,
            selected_date=date
        ).count()
        appointments_data.append(count)
        days_data.append(date.strftime('%d %b'))
    
    # 2. Earnings data for the last 7 days
    earnings_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        earnings = UserBooking.objects.filter(
            doctor=doctor,
            selected_date=date,
            status__in=['confirmed', 'completed', 'in_progress']
        ).aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0
        earnings_data.append(float(earnings))
    
    # 3. Monthly data for the last 6 months
    monthly_data = []
    month_names = []
    for i in range(5, -1, -1):
        # Calculate month date
        month_date = today.replace(day=1)
        for _ in range(i):
            # Go back one month
            if month_date.month == 1:
                month_date = month_date.replace(year=month_date.year-1, month=12)
            else:
                month_date = month_date.replace(month=month_date.month-1)
            
        # Calculate month end
        if month_date.month == 12:
            month_end = datetime(month_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(month_date.year, month_date.month + 1, 1) - timedelta(days=1)
        
        # Get data for the month
        month_earnings = UserBooking.objects.filter(
            doctor=doctor,
            selected_date__gte=month_date,
            selected_date__lte=month_end,
            status__in=['confirmed', 'completed', 'in_progress']
        ).aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0
        
        monthly_data.append(float(month_earnings))
        month_names.append(month_date.strftime('%b'))
    
    # 4. Rating data - synthetic data based on booking counts
    rating_data = []
    for i in range(5, -1, -1):
        rating = max(3.5, min(5.0, current_rating - (random.uniform(0, 0.5))))
        rating_data.append(round(rating, 1))
    
    # Serialize data for JavaScript
    appointments_data_json = json.dumps(appointments_data)
    days_data_json = json.dumps(days_data)
    earnings_data_json = json.dumps(earnings_data)
    monthly_data_json = json.dumps(monthly_data)
    month_names_json = json.dumps(month_names)
    rating_data_json = json.dumps(rating_data)
    calendar_events_json = json.dumps(calendar_events)
    
    # Debug: Print the JSON data for calendar events
    print(f"Calendar events JSON: {calendar_events_json}")
    
    # All serialized appointments for debug
    all_serialized = json.dumps([{
        'id': a.id,
        'patient_name': a.full_name or (f"{a.user.first_name} {a.user.last_name}".strip() if a.user else "Unknown"),
        'time': a.selected_time.strftime('%H:%M'),
        'status': a.status,
        'type': a.consultation_type.name if a.consultation_type else 'General'
    } for a in todays_appointments_display])
    
    # Debug: Print all serialized appointments
    print(f"All serialized appointments: {all_serialized}")
    
    # Add queue patients to serialized_appointments
    # Convert both to lists before combining them
    all_appointments_with_queue = list(todays_appointments_display) + list(waiting_patients)
    
    # Extended serialized data for all appointments including queue patients
    all_serialized_extended = json.dumps([{
        'id': a.id,
        'patient_name': a.full_name or (f"{a.user.first_name} {a.user.last_name}".strip() if a.user else "Unknown"),
        'time': a.selected_time.strftime('%H:%M'),
        'status': a.status,
        'type': a.consultation_type.name if a.consultation_type else 'General'
    } for a in all_appointments_with_queue])
    
    context = {
        'doctor': doctor,
        'today_date': today.strftime('%A, %B %d, %Y'),
        'today': today,  # Raw date object for template comparisons
        'current_month_year': current_month_year,
        
        # Stats cards data - use today_count for Today's Appointments card
        'today_appointments_count': today_count,  # Changed from all_appointments_count to today_count
        'appointment_change_pct': appointment_change_pct,
        'earnings_today': todays_earnings,
        'earnings_change_pct': earnings_change_pct,
        'monthly_earnings': monthly_earnings,
        'monthly_change_pct': monthly_change_pct,
        'current_rating': current_rating,
        'rating_change': rating_change,
        'monthly_patients': monthly_patients,
        'patient_change_pct': patient_change_pct,
        
        # Appointment data
        'all_appointments': todays_appointments_display,
        'upcoming_appointments': upcoming_appointments[:10],  # Also limit these to 10
        'completed_appointments': completed_appointments[:10],  # Limit to 10
        'in_progress_appointments': in_progress_appointments[:10],  # Limit to 10
        'all_count': all_appointments_count,
        'today_count': today_count,  # Count of only today's appointments
        'upcoming_count': upcoming_count,
        'completed_count': completed_count,
        'in_progress_count': in_progress_count,
        'today_has_appointments': today_has_appointments,  # Flag to indicate if there are appointments specifically for today
        
        # Patient queue
        'waiting_patients': waiting_patients_data,
        
        # Chart data
        'appointments_data': appointments_data_json,
        'days_data': days_data_json,
        'earnings_data': earnings_data_json,
        'monthly_data': monthly_data_json,
        'month_names': month_names_json,
        'rating_data': rating_data_json,
        'calendar_events': calendar_events_json,
        'serialized_appointments': all_serialized_extended
    }
    
    return render(request, 'doc_dashboard.html', context)

@login_required
def book_view(request):
    # Check if user has API token, if not generate warning but allow to continue
    if not request.session.get('api_token'):
        messages.warning(request, 'Your session might have expired. Some features may be limited.')
    
    # Initialize reschedule data variable at the beginning of the function
    reschedule_data = request.session.get('reschedule_booking', {})
    
    # Remove the direct redirect that causes the loop
    # We'll handle reschedule data within the normal form flow instead
    
    # Debug all request parameters
    print("\n" + "=" * 80)
    print("BOOK VIEW DEBUG")
    print(f"Request method: {request.method}")
    print("GET parameters:")
    for key, value in request.GET.items():
        print(f"  {key}: {value}")
    print("POST parameters:")
    for key, value in request.POST.items():
        print(f"  {key}: {value}")
    print("Session data:")
    for key, value in request.session.items():
        print(f"  {key}: {value}")
    print("=" * 80 + "\n")
    
    # Clear any existing service_type error messages to prevent duplicates
    storage = messages.get_messages(request)
    for message in list(storage):
        if "Service type is required" in str(message):
            storage.used = True
    
    # Get the API token from session
    api_token = request.session.get('api_token')
    
    # Initialize API client with token
    api_client = APIClient(token=api_token)
    
    countries = [
        {"name": "India", "code": "+91"},
    ]
    random.shuffle(countries)
    selected_countries = countries[:10]
    
    # Get cities from API (not available in current API, using Django as fallback)
    cities = Doctor.objects.values_list('city', flat=True).distinct()[:10]

    # Get consultation types from API or fallback to Django model
    if api_token:
        try:
            response_data, status_code = api_client.get_consultation_types()
            if status_code == 200:
                services = response_data
            else:
                # Fallback to Django model if API fails
                services = list(ConsultationType.objects.all().values())
        except:
            # Fallback to Django model if API request fails
            services = list(ConsultationType.objects.all().values())
    else:
        # No API token, use Django model
        services = list(ConsultationType.objects.all().values())
    
    if request.method == 'POST':
        # Extra validation for service_id
        service_id = request.POST.get('service_id') or request.GET.get('service_id')
        
        # In reschedule mode, also check the reschedule data
        if not service_id and reschedule_data and 'service_id' in reschedule_data:
            service_id = reschedule_data.get('service_id')
            print(f"Using service_id from reschedule data: {service_id}")
        
        if not service_id:
            messages.error(request, "Please select a service type before proceeding")
            return render(request, 'book.html', {
                'services': services,
                'countries': selected_countries,
                'cities': cities,
                'reschedule_mode': bool(reschedule_data),
                'reschedule_data': reschedule_data,
                'service_name': "Select a service"
            })
            
        # Extract form data
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number','6284664155')
        email = request.POST.get('email')
        
        # Handle age conversion properly
        age_str = request.POST.get('age', '19')
        try:
            age = int(age_str)
        except (ValueError, TypeError):
            age = 19  # Default value if conversion fails
            
        gender = request.POST.get('gender','Male')
        city = request.POST.get('city')
        
        # Required field validation
        if not all([full_name, phone_number, email, city]):
            if not full_name:
                messages.error(request, "Full name is required")
            if not phone_number:
                messages.error(request, "Phone number is required")
            if not email:
                messages.error(request, "Email is required")
            if not city:
                messages.error(request, "City is required")
            return render(request, 'book.html', {
                'services': services,
                'countries': selected_countries,
                'cities': cities,
                'reschedule_mode': bool(reschedule_data),
                'reschedule_data': reschedule_data,
                'service_name': "Select a service"
            })
        
        # Debug the extracted values
        print(f"Extracted values:")
        print(f"  full_name: {full_name}")
        print(f"  phone_number: {phone_number}")
        print(f"  email: {email}")
        print(f"  age: {age} (from {age_str})")
        print(f"  gender: {gender}")
        print(f"  city: {city}")
        print(f"  service_id: {service_id}")
        
        # Store in session
        request.session['patient_details'] = {
            'full_name': full_name,
            'phone_number': phone_number,
            'email': email,
            'age': age,  # Store the integer value
            'gender': gender,
            'city': city,
            'service_id': service_id  # Store service_id in patient_details
        }
        
        # Debug what's stored in session
        print(f"Stored in session: {request.session['patient_details']}")
        
        # Redirect to confirm view with needed parameters
        return redirect(f"/confirm/?service_id={service_id}&city={city}")

    # Prepare pre-filled data for service name if in reschedule mode
    service_name = "Select a service"
    if reschedule_data and 'service_id' in reschedule_data:
        # Try to find the service name in the API response
        service_id = reschedule_data.get('service_id')
        if services and service_id:
            for service in services:
                if str(service.get('id')) == str(service_id):
                    service_name = service.get('name', 'Select a service')
                    break

    return render(request, 'book.html', {
        'services': services,
        'countries': selected_countries,
        'cities': cities,
        'reschedule_mode': bool(reschedule_data),
        'reschedule_data': reschedule_data,
        'service_name': service_name
    })

def calculate_platform_fee(user, consultation):
    user_bookings = UserBooking.objects.filter(user=user)

    if user_bookings.count() < 4:
        return 0  # Platform fee waived for the first 4 bookings

    platform_fee = 50  # Default platform fee
    if consultation.requires_referral:
        platform_fee = 50
    if consultation.emergency_specialty:
        platform_fee = 100
    if consultation.requires_referral and consultation.emergency_specialty:
        platform_fee = 150

    return platform_fee



@login_required
def confirm_view(request):
    # Check if user has API token, if not generate warning but allow to continue
    if not request.session.get('api_token'):
        messages.warning(request, "You don't have an API token. Some features may not work properly. Please try logging out and logging back in.")
    
    # Initialize variables
    confirmation_prompt = False
    final_confirmation = False
    booking_created = False
    booking = None
    all_doctors = []
    doctors = []
    patient_details = request.session.get('patient_details', {})
    
    # Check if we are in reschedule mode
    reschedule_mode = 'reschedule_booking' in request.session
    reschedule_data = request.session.get('reschedule_booking', {})
    
    try:
        # Initialize API client
        api_token = request.session.get('api_token')
        user_id = request.session.get('user_id')
        from .api_client import APIClient
        api_client = APIClient(token=api_token)
        print("API client initialization successful")
    except Exception as e:
        print(f"Error initializing API client: {str(e)}")
        messages.error(request, f"Error initializing API client: {str(e)}")
        api_client = None  # Set to None to handle gracefully later
    
    # Debug reschedule mode
    if reschedule_mode:
        print(f"RESCHEDULE MODE: {reschedule_data}")
    
    # Extract form action if available
    form_action = request.POST.get('form_action', '')
    
    # Handle initial GET request or form reload - this should be processed first
    service_id = request.GET.get("service_id") or request.POST.get("service_id")
    user_city = request.GET.get("city") or request.POST.get("city", "")  # Provide default empty string
    full_name = request.POST.get("full_name", "")
    
    # CASCADING FALLBACKS FOR SERVICE_ID:
    # 1. Try to get from request
    # 2. Try to get from reschedule data
    # 3. Try to get from patient_details (where we stored it in book_view)
    
    # Check if we don't have service_id yet
    if not service_id:
        # Try reschedule data
        if reschedule_mode and 'service_id' in reschedule_data:
            service_id = reschedule_data.get('service_id')
            print(f"Using service_id from reschedule data: {service_id}")
        
        # Try patient_details as last resort
        elif 'reschedule_service_id' in patient_details:
            service_id = patient_details.get('reschedule_service_id')
            print(f"Using service_id from patient_details: {service_id}")
        # Also check for regular service_id in patient_details
        elif 'service_id' in patient_details:
            service_id = patient_details.get('service_id')
            print(f"Using service_id from patient_details: {service_id}")
        
        # NEW FIX: If still no service_id, redirect to book view
        if not service_id:
            messages.error(request, "Service type is required. Please select a service type first.")
            return redirect("book")
    
    # Extra debugging
    print(f"CONFIRM VIEW: Final service_id={service_id}, city={user_city}")
    
    # If reschedule mode, pre-fill form with stored data
    if reschedule_mode:
        service_id = service_id or reschedule_data.get('service_id')
        user_city = user_city or reschedule_data.get('city')
        full_name = full_name or reschedule_data.get('full_name')
    
    try:
        if not service_id:
            messages.error(request, "Service type is required")
            return redirect("book")  # Redirect to a safe page
        
        # Get consultation types from API
        try:
            response_data, status_code = api_client.get_consultation_types()
            
            if status_code != 200:
                messages.error(request, "Unable to fetch service types")
                return redirect("book")
                
            consultation_types = response_data
        except Exception as e:
            print(f"Error fetching consultation types: {str(e)}")
            messages.error(request, "Unable to fetch service types")
            return redirect("book")
        
        # Validate service_id - but be more permissive in reschedule mode
        service_id_valid = False
        for consultation in consultation_types:
            if str(consultation.get('id')) == str(service_id):
                service_id_valid = True
                break
                
        if not service_id_valid and not reschedule_mode:
            messages.error(request, f"Service type with ID {service_id} does not exist.")
            return redirect("book")
        
        # In reschedule mode, if service_id is invalid, try to get a valid one
        if not service_id_valid and reschedule_mode:
            # Try to get a valid service_id
            if consultation_types:
                # Use the first available consultation type
                service_id = str(consultation_types[0].get('id'))
                print(f"Invalid service_id in reschedule mode, using first available: {service_id}")
        
        # Get the selected consultation type
        consultation = None
        for ct in consultation_types:
            if str(ct.get('id')) == str(service_id):
                consultation = ct
                break
                
        # Get doctors from API
        try:
            response_data, status_code = api_client.get_doctors()
            
            if status_code != 200:
                messages.error(request, "Unable to fetch doctors")
                return redirect("book")
            
            all_doctors = response_data
        except Exception as e:
            print(f"Error fetching doctors: {str(e)}")
            messages.error(request, "Unable to fetch doctors")
            return redirect("book")
        
        # Filter doctors by consultation type and city
        doctors = []
        for doctor in all_doctors:
            if str(doctor.get('consultation_type_id')) == str(service_id):
                if not user_city or doctor.get('city', '') == user_city:
                    # Pre-select the previous doctor if in reschedule mode
                    if reschedule_mode and 'doctor_id' in reschedule_data:
                        if str(doctor.get('id')) == str(reschedule_data['doctor_id']):
                            doctor['preselected'] = True
                    doctors.append(doctor)
        
        # If no doctors found, provide a useful message
        if not doctors:
            messages.warning(request, "No doctors found for the selected criteria")
        
        # Time slots (currently not available in API, would need to be added or mocked)
        # For now, we'll use some dummy time slots
        morning_slots = [
            {'start_time': '08:00', 'end_time': '11:00'},
            {'start_time': '08:30', 'end_time': '11:30'},
            {'start_time': '09:00', 'end_time': '12:00'}
        ]
        afternoon_slots = [
            {'start_time': '13:00', 'end_time': '15:00'},
            {'start_time': '13:30', 'end_time': '15:30'},
            {'start_time': '14:00', 'end_time': '16:00'}
        ]
        evening_slots = [
            {'start_time': '17:00', 'end_time': '20:00'},
            {'start_time': '17:30', 'end_time': '20:30'},
            {'start_time': '18:00', 'end_time': '21:00'}
        ]
        
        # Convert time slots to Django format to match template expectations
        formatted_morning_slots = []
        for slot in morning_slots:
            start = datetime.strptime(slot['start_time'], '%H:%M').time()
            end = datetime.strptime(slot['end_time'], '%H:%M').time()
            formatted_morning_slots.append({
                'start_time': start,
                'end_time': end
            })
            
        formatted_afternoon_slots = []
        for slot in afternoon_slots:
            start = datetime.strptime(slot['start_time'], '%H:%M').time()
            end = datetime.strptime(slot['end_time'], '%H:%M').time()
            formatted_afternoon_slots.append({
                'start_time': start,
                'end_time': end
            })
            
        formatted_evening_slots = []
        for slot in evening_slots:
            start = datetime.strptime(slot['start_time'], '%H:%M').time()
            end = datetime.strptime(slot['end_time'], '%H:%M').time()
            formatted_evening_slots.append({
                'start_time': start,
                'end_time': end
            })
        
        # Print debug info for time slots
        print(f"Morning slots: {formatted_morning_slots}")
        print(f"Afternoon slots: {formatted_afternoon_slots}")
        print(f"Evening slots: {formatted_evening_slots}")
        
        # Calculate platform fee (this would normally come from the API)
        platform_fee = 50
        
        # Skip time slot validation on initial GET request
        if request.method == "GET" and not ("selected_time" in request.GET and "selected_date" in request.GET):
            context = {
                "consultation": consultation,
                "doctors": doctors,
                "morning_slots": formatted_morning_slots,
                "afternoon_slots": formatted_afternoon_slots,
                "evening_slots": formatted_evening_slots,
                "city": user_city,
                "full_name": patient_details.get('full_name', ''),
                "platform_fee": platform_fee,
                "reschedule_mode": reschedule_mode,
                # Add gender and age to the context
                "gender": patient_details.get('gender', 'Male'),
                "age": patient_details.get('age', 19),
            }
            return render(request, "confirm.html", context)
    
    except Exception as e:
        # More detailed error
        import traceback
        error_details = traceback.format_exc()
        print(f"Error loading page: {str(e)}\n{error_details}")
        messages.error(request, f"Error loading page: {str(e)}")
        return redirect("book")  # Changed from "myApp" to "book"
    
    # Now handle POST requests
    if request.method == "POST":
        form_action = request.POST.get("form_action")
        print("=" * 50)
        print(f"POST request received in confirm_view")
        print(f"form_action: {form_action}")
        print(f"All POST fields: {list(request.POST.keys())}")
        print(f"POST data: {request.POST}")
        print("=" * 50)
        
        # Defensive check: If form_action is missing but required booking fields are present,
        # default to final_confirm_booking
        if not form_action and all([
            request.POST.get("full_name"),
            request.POST.get("service_id"),
            request.POST.get("doctor_id"),
            request.POST.get("selected_date"),
            request.POST.get("selected_time")
        ]):
            print("NOTICE: form_action was missing but booking fields are present. Defaulting to final_confirm_booking")
            form_action = "final_confirm_booking"

        # Step 1: Handle confirmation prompt
        if form_action == "confirm_booking_prompt":
            print("PROCESSING: confirm_booking_prompt") 
            full_name = request.POST.get("full_name")
            service_id = request.POST.get("service_id")
            doctor_id = request.POST.get("doctor_id")
            selected_date = request.POST.get("selected_date")
            selected_time = request.POST.get("selected_time")
            
            # Debug information
            print(f"Confirmation prompt data: {full_name}, {service_id}, {doctor_id}, {selected_date}, {selected_time}")

            # Validate all required fields
            if not all([full_name, service_id, doctor_id, selected_date, selected_time]):
                messages.error(request, "All booking fields are required.")
                return redirect("confirm")  # Use the correct URL name here

            # Prepare context for confirmation prompt
            try:
                # Get consultation types from API
                response_data, status_code = api_client.get_consultation_types()
                
                if status_code != 200:
                    messages.error(request, "Unable to fetch service types")
                    return redirect("book")
                    
                consultation_types = response_data
                
                # Find the consultation type
                consultation_type = None
                for ct in consultation_types:
                    if str(ct.get('id')) == str(service_id):
                        consultation_type = ct
                        break
                
                if not consultation_type:
                    messages.error(request, f"Service type with ID {service_id} does not exist.")
                    return redirect("book")
                
                # Get doctor details
                response_data, status_code = api_client.get_doctor(doctor_id)
                
                if status_code != 200:
                    messages.error(request, f"Doctor with ID {doctor_id} does not exist.")
                    return redirect("book")
                    
                doctor = response_data
                
                # Calculate fees
                platform_fee = 50  # This would normally come from API or calculation
                consultation_fee = doctor.get('consultation_fee', 0)
                total_amount = float(consultation_fee) + float(platform_fee)

                context = {
                    "confirmation_prompt": True,
                    "full_name": full_name,
                    "consultation_type": consultation_type,
                    "doctor": doctor,
                    "selected_date": selected_date,
                    "selected_time": selected_time,
                    "platform_fee": platform_fee,
                    "consultation_fee": consultation_fee,
                    "total_amount": total_amount,
                    "reschedule_mode": reschedule_mode,
                    # Pass gender and age from patient_details
                    "gender": patient_details.get('gender', 'Male'),
                    "age": patient_details.get('age', 19),
                    # Add the formatted time slots to maintain them in the context
                    "morning_slots": formatted_morning_slots,
                    "afternoon_slots": formatted_afternoon_slots,
                    "evening_slots": formatted_evening_slots,
                }
                return render(request, "confirm.html", context)
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Error preparing confirmation: {str(e)}\n{error_details}")
                messages.error(request, f"Error preparing confirmation: {str(e)}")
                return redirect("confirm")  # Use the correct URL name

        # Handle initial submission from book.html
        elif form_action == "initial_book_submission":
            print("PROCESSING: initial_book_submission")
            # Extract form data from book page
            full_name = request.POST.get("full_name")
            service_id = request.POST.get("service_id")
            email = request.POST.get("email")
            phone_number = request.POST.get("phone_number")
            age = request.POST.get("age", "19")
            gender = request.POST.get("gender", "Male")
            city = request.POST.get("city")
            
            # Validate all required fields
            if not all([service_id, full_name]):
                messages.error(request, "Service type and full name are required.")
                return redirect("book")
                
            # Store in session for later use
            request.session['patient_details'] = {
                'full_name': full_name,
                'phone_number': phone_number,
                'email': email,
                'age': int(age) if age.isdigit() else 19,
                'gender': gender,
                'city': city
            }
            
            # Continue processing like a GET request
            print(f"Continuing with initial book submission, service_id={service_id}, city={city}")
            
            # Return the normal confirm page with doctors list
            try:
                service_id = int(service_id)
                consultation = ConsultationType.objects.get(id=service_id)
                
                doctor_query = Doctor.objects.filter(consultation_type=consultation)
                if city:
                    doctor_query = doctor_query.filter(city=city)
                    
                doctors = doctor_query
                
                # Pre-select the previous doctor if in reschedule mode
                if reschedule_mode:
                    doctor_id = reschedule_data.get('doctor_id')
                    if doctor_id:
                        for doctor in doctors:
                            if doctor.id == int(doctor_id):
                                doctor.preselected = True
                                break
                
                # If no doctors found, provide a useful message
                if not doctors.exists():
                    messages.warning(request, "No doctors found for the selected criteria")
                
                # Time slots with defensive coding
                time_slot_query = TimeSlot.objects.filter(doctor__consultation_type=consultation)
                if city:
                    time_slot_query = time_slot_query.filter(doctor__city=city)
                
                time_slots = time_slot_query
                
                # Handle case where no time slots exist
                if not time_slots.exists():
                    messages.warning(request, "No time slots available for the selected criteria")
                    morning_slots = []
                    afternoon_slots = []
                    evening_slots = []
                else:
                    unique_slots = time_slots.values("start_time", "end_time").distinct()
                    morning_slots = unique_slots.filter(start_time__hour__lt=12)
                    afternoon_slots = unique_slots.filter(start_time__hour__gte=12, start_time__hour__lt=17)
                    evening_slots = unique_slots.filter(start_time__hour__gte=17)
                
                platform_fee = calculate_platform_fee(request.user, consultation)
                
                # Ensure time slots are properly formatted
                formatted_morning_slots = []
                for slot in morning_slots:
                    formatted_morning_slots.append({
                        'start_time': slot['start_time'],
                        'end_time': slot['end_time']
                    })
                    
                formatted_afternoon_slots = []
                for slot in afternoon_slots:
                    formatted_afternoon_slots.append({
                        'start_time': slot['start_time'],
                        'end_time': slot['end_time']
                    })
                    
                formatted_evening_slots = []
                for slot in evening_slots:
                    formatted_evening_slots.append({
                        'start_time': slot['start_time'],
                        'end_time': slot['end_time']
                    })
                
                # Debug slot information
                print(f"Formatted slots - Morning: {len(formatted_morning_slots)}, Afternoon: {len(formatted_afternoon_slots)}, Evening: {len(formatted_evening_slots)}")
                
                context = {
                    "consultation": consultation,
                    "doctors": doctors,
                    "morning_slots": formatted_morning_slots,
                    "afternoon_slots": formatted_afternoon_slots,
                    "evening_slots": formatted_evening_slots,
                    "city": city,
                    "full_name": full_name,
                    "platform_fee": platform_fee,
                    "reschedule_mode": reschedule_mode,
                    "gender": gender,
                    "age": age,
                }
                return render(request, "confirm.html", context)
            except Exception as e:
                messages.error(request, f"Error processing service request: {str(e)}")
                return redirect("book")
                
        # Step 2: Handle final booking submission
        elif form_action == "final_confirm_booking":
            print("=" * 80)
            print("PROCESSING FINAL BOOKING CONFIRMATION")
            print("=" * 80)
            
            full_name = request.POST.get("full_name")
            service_id = request.POST.get("service_id")
            doctor_id = request.POST.get("doctor_id")
            selected_date = request.POST.get("selected_date")
            selected_time = request.POST.get("selected_time")
            
            # Get gender and age directly from the form
            gender = request.POST.get("gender", "Male")
            age_str = request.POST.get("age", "19")
            
            # Debug information
            print(f"Final confirm data: {full_name}, {service_id}, {doctor_id}, {selected_date}, {selected_time}")
            print(f"Gender from form: {gender}")
            print(f"Age from form: {age_str}")
            print(f"Patient details from session: {patient_details}")
            
            try:
                # Ensure age is an integer
                try:
                    age = int(age_str)
                except (ValueError, TypeError):
                    age = 19  # Default to 19 if conversion fails
                
                # Process date and time for API
                # Handle both date formats
                try:
                    if '-' in selected_date:  # YYYY-MM-DD format
                        year, month, day = map(int, selected_date.split('-'))
                    else:  # DD/MM/YYYY format
                        day, month, year = map(int, selected_date.split('/'))
                    
                    selected_date_obj = date(year, month, day)
                    formatted_date = selected_date_obj.strftime('%Y-%m-%d')
                except ValueError as e:
                    messages.error(request, f"Invalid date format: {selected_date}. Error: {str(e)}")
                    return redirect("confirm")
                
                # Handle time format
                try:
                    # Handle time ranges (e.g., "17:00 - 17:30")
                    if " - " in selected_time:
                        start_time = selected_time.split(" - ")[0].strip()
                        selected_time = start_time  # Just use the start time
                    
                    # Try different time formats
                    formats_to_try = ["%H:%M", "%I:%M %p", "%I:%M%p", "%H.%M"]
                    selected_time_obj = None
                    
                    for time_format in formats_to_try:
                        try:
                            selected_time_obj = datetime.strptime(selected_time, time_format).time()
                            break  # Stop if a format works
                        except ValueError:
                            continue
                    
                    if not selected_time_obj:
                        raise ValueError(f"Could not parse time: {selected_time}")
                        
                    formatted_time = selected_time_obj.strftime('%H:%M')
                except Exception as e:
                    messages.error(request, f"Invalid time format: {selected_time}. Error: {str(e)}")
                    return redirect("confirm")

                # Handle reschedule if in reschedule mode
                if reschedule_mode:
                    booking_id = reschedule_data.get('booking_id')
                    if not booking_id:
                        messages.error(request, "No booking ID found for rescheduling")
                        return redirect('myApp')
                    
                    # Prepare booking data for update
                    booking_data = {
                        'selected_date': formatted_date,
                        'selected_time': formatted_time,
                        'doctor_id': doctor_id,
                        'consultation_type_id': service_id,
                        'full_name': full_name,
                        'age': age,
                        'gender': gender,
                        'phone_number': patient_details.get('phone_number', '')
                    }
                    
                    # Update booking through API
                    response_data, status_code = api_client.update_booking(booking_id, booking_data)
                    
                    if status_code == 200:
                        # Clear reschedule data from session
                        if 'reschedule_booking' in request.session:
                            del request.session['reschedule_booking']
                            request.session.modified = True
                        
                        messages.success(request, "Your appointment has been rescheduled successfully.")
                        return redirect('myApp')
                    else:
                        error_message = response_data.get('error', 'Unable to reschedule appointment')
                        messages.error(request, error_message)
                        return redirect('myApp')
                else:
                    # Create new booking through API
                    # Prepare booking data
                    booking_data = {
                        'selected_date': formatted_date,
                        'selected_time': formatted_time,
                        'doctor_id': doctor_id,
                        'consultation_type_id': service_id,
                        'full_name': full_name,
                        'age': age,
                        'gender': gender,
                        'phone_number': patient_details.get('phone_number', '')
                    }
                    
                    # Debug booking data
                    print("\nFINAL VALUES FOR BOOKING:")
                    for key, value in booking_data.items():
                        print(f"  {key}: {value}")
                    
                    # Create booking through API
                    # Make sure we're not passing user_id twice, which causes the backend error
                    # The API will already get user_id from the URL and the token
                    # We must NOT include it in the request body
                    for field in ['user_id', 'user', 'userId', 'userid', 'user-id']:
                        if field in booking_data:
                            del booking_data[field]
                    
                    # Try API booking creation first
                    try:
                        response_data, status_code = api_client.create_booking(user_id, booking_data)
                        
                        if status_code == 201:
                            # Successful creation via API
                            booking = response_data
                            messages.success(request, "Your appointment has been booked successfully.")
                        else:
                            # API returned an error, try using Django model instead
                            raise Exception(f"API Error: {response_data.get('error', 'Unknown error')}")
                            
                    except Exception as api_error:
                        # Log the API error
                        print(f"API booking creation failed: {str(api_error)}")
                        
                        # Fallback to Django model
                        try:
                            # Create booking using Django ORM
                            doctor = Doctor.objects.get(id=doctor_id)
                            consultation_type = ConsultationType.objects.get(id=service_id)
                            
                            # Calculate fees
                            consultation_fee = doctor.consultation_fee
                            platform_fee = calculate_platform_fee(request.user, consultation_type)
                            total_amount = consultation_fee + platform_fee
                            
                            # Create booking
                            booking = UserBooking.objects.create(
                                user=request.user,
                                doctor=doctor,
                                consultation_type=consultation_type,
                                selected_date=formatted_date,
                                selected_time=formatted_time,
                                full_name=full_name,
                                age=age,
                                gender=gender,
                                phone_number=patient_details.get('phone_number', ''),
                                consultation_fee=consultation_fee,
                                platform_fee=platform_fee,
                                total_amount=total_amount,
                                status='confirmed'
                            )
                            
                            # Create booking object for template
                            booking = {
                                'id': booking.id,
                                'selected_date': formatted_date,
                                'selected_time': formatted_time,
                                'full_name': full_name,
                                'age': age,
                                'gender': gender,
                                'total_amount': float(total_amount),
                                'consultation_fee': float(consultation_fee),
                                'platform_fee': float(platform_fee),
                                'doctor': {
                                    'name': doctor.name
                                },
                                'consultation_type': {
                                    'name': consultation_type.name
                                }
                            }
                            
                            messages.success(request, "Your appointment has been booked successfully using our backup system.")
                        except Exception as django_error:
                            # Both API and Django fallback failed
                            error_message = f"Failed to create booking: {str(django_error)}"
                            messages.error(request, error_message)
                            return redirect("confirm")
                    
                    # Format the booking data for the template
                    if isinstance(booking, dict):
                        # Ensure date and time are properly formatted
                        if 'selected_date' in booking and not isinstance(booking['selected_date'], str):
                            booking['selected_date'] = formatted_date
                        
                        if 'selected_time' in booking and not isinstance(booking['selected_time'], str):
                            booking['selected_time'] = formatted_time
                            
                        # Final safety check for date and time
                        if 'selected_date' not in booking or not booking['selected_date']:
                            booking['selected_date'] = formatted_date
                            
                        if 'selected_time' not in booking or not booking['selected_time']:
                            booking['selected_time'] = formatted_time
                            
                        # Get the doctor and consultation type information if needed
                        if 'doctor' not in booking or not isinstance(booking['doctor'], dict):
                            try:
                                doctor_info, _ = api_client.get_doctor(doctor_id)
                                doctor_name = doctor_info.get('name', 'Doctor')
                                booking['doctor'] = {'name': doctor_name}
                            except:
                                booking['doctor'] = {'name': 'Doctor'}

                        if 'consultation_type' not in booking or not isinstance(booking['consultation_type'], dict):
                            try:
                                consultation_types, _ = api_client.get_consultation_types()
                                consultation_name = None
                                for ct in consultation_types:
                                    if str(ct.get('id')) == str(service_id):
                                        consultation_name = ct.get('name')
                                        break
                                if not consultation_name:
                                    consultation_name = 'Consultation'
                                booking['consultation_type'] = {'name': consultation_name}
                            except:
                                booking['consultation_type'] = {'name': 'Consultation'}
                    
                    # Debug the final booking object
                    print("Final booking object for template:")
                    for key, value in booking.items():
                        print(f"  {key}: {value}")
                    
                    context = {
                        "success": True,
                        "booking": booking,
                        # Include time slots to maintain them in the context
                        "morning_slots": formatted_morning_slots,
                        "afternoon_slots": formatted_afternoon_slots,
                        "evening_slots": formatted_evening_slots,
                    }
                    return render(request, "confirm.html", context)

            except Exception as e:
                # Detailed error message
                import traceback
                error_details = traceback.format_exc()
                print(f"Error creating booking: {str(e)}\n{error_details}")
                messages.error(request, f"Error creating booking: {str(e)}")
                return redirect("confirm")

        # Handle the case when a POST request doesn't have a valid form_action
        else:
            print("POST request received without a valid form_action")
            return redirect("confirm")

@login_required
def myApp_view(request):
    """View to display the user's appointments with reschedule and cancel functionality.
    
    NOTE: We're fixing an issue where doctor city information was incorrect. 
    The doctor city should come directly from the doctor record associated with each appointment,
    not from the patient_details in the session.
    """
    # Check if user has API token, if not generate warning but allow to continue
    if not request.session.get('api_token'):
        messages.warning(request, 'Your session might have expired. Some features may be limited.')
    
    # Check if there's reschedule data in the session
    reschedule_data = request.session.get('reschedule_booking', {})
    
    # Get patient details from session
    patient_details = request.session.get('patient_details', {})
    
    # Get the API token from session
    api_token = request.session.get('api_token')
    user_id = request.session.get('user_id')
    
    # Initialize API client with token
    api_client = APIClient(token=api_token)
    
    # Handle GET requests for cancel rescheduling
    if 'cancel_reschedule' in request.GET:
        if 'reschedule_booking' in request.session:
            del request.session['reschedule_booking']
            request.session.modified = True
            messages.info(request, "Rescheduling has been cancelled.")
        return redirect('myApp')
    
    # Handle POST requests for cancellation
    if request.method == 'POST':
        print(f"POST received in myApp_view: {request.POST}")
        
        # Check if cancel_booking is in the request
        if 'cancel_booking' in request.POST:
            booking_id = request.POST.get('booking_id')
            print(f"Attempting to cancel booking with ID: {booking_id}")
            try:
                # Try using API to cancel booking if we have a token
                if api_token:
                    print(f"Using API to cancel booking with token: {api_token[:10]}...")
                    # Make API call to update booking status to 'cancelled' - uses DELETE method
                    response_data, status_code = api_client.cancel_booking(booking_id)
                    print(f"API response: status={status_code}, data={response_data}")
                    
                    if status_code == 200:
                        messages.success(request, "Your appointment has been cancelled successfully.")
                    else:
                        # Fall back to Django if API fails
                        print(f"API cancellation failed with status {status_code}. Trying Django fallback.")
                        try:
                            booking = UserBooking.objects.get(id=booking_id, user=request.user)
                            booking.status = 'cancelled'
                            booking.save()
                            print(f"Successfully cancelled booking using Django fallback")
                            messages.success(request, "Your appointment has been cancelled successfully.")
                        except UserBooking.DoesNotExist:
                            error_message = response_data.get('error', 'Unable to cancel appointment')
                            print(f"Django fallback failed: {error_message}")
                            messages.error(request, error_message)
                else:
                    # No API token, use Django directly
                    print("No API token. Using Django directly.")
                    booking = UserBooking.objects.get(id=booking_id, user=request.user)
                    booking.status = 'cancelled'
                    booking.save()
                    print("Successfully cancelled booking using Django directly")
                    messages.success(request, "Your appointment has been cancelled successfully.")
            except Exception as e:
                print(f"Cancellation error: {str(e)}")
                messages.error(request, f"Error cancelling appointment: {str(e)}")
            return redirect('myApp')
        else:
            print("POST request received but cancel_booking not in request")
    
    # Get appointments data
    if api_token:
        # Try to get appointments through API
        try:
            response_data, status_code = api_client.get_user_bookings(None)
            
            if status_code == 200:
                # Filter out cancelled appointments from API response
                bookings = [booking for booking in response_data if booking.get('status') != 'cancelled']
                upcoming_count = len(bookings)
                
                # Debug raw API response
                print("\n=== RAW API RESPONSE ===")
                for i, booking in enumerate(bookings[:2]):  # Print first 2 bookings for debugging
                    print(f"Booking {i+1} data:")
                    for key, value in booking.items():
                        print(f"  {key}: {value}")
                    print("-" * 30)
            else:
                # Fallback to Django if API returns error
                today = date.today()
                bookings = list(UserBooking.objects.filter(
                    user=request.user,
                    selected_date__gte=today
                ).exclude(status='cancelled').order_by('selected_date', 'selected_time').values())
                upcoming_count = len(bookings)
        except Exception as e:
            # Fallback to Django if API request fails
            print(f"API Error: {str(e)}")
            today = date.today()
            bookings = list(UserBooking.objects.filter(
                user=request.user,
                selected_date__gte=today
            ).exclude(status='cancelled').order_by('selected_date', 'selected_time').values())
            upcoming_count = len(bookings)
    else:
        # No API token, get bookings from Django directly
        today = date.today()
        bookings = list(UserBooking.objects.filter(
            user=request.user,
            selected_date__gte=today
        ).exclude(status='cancelled').order_by('selected_date', 'selected_time').values())
        upcoming_count = len(bookings)
   
    # Format today's date for display
    today_display = datetime.now().strftime("%A, %B %d, %Y")
   
    # Process bookings to match the format expected in the template
    appointments = []
    for booking in bookings:
        # Debug info to see what's stored in the booking
        print(f"Booking {booking.get('id', 'unknown')} details:")
        for key, value in booking.items():
            print(f"  {key}: {value}")
        
        # Check if this booking is currently being rescheduled
        is_being_rescheduled = (reschedule_data and 
                              'booking_id' in reschedule_data and 
                              int(reschedule_data['booking_id']) == booking.get('id', 0))
        
        # Try to get doctor name - check different possible formats from API
        doctor_name = None
        if 'doctor_name' in booking:
            doctor_name = booking['doctor_name']
        elif 'doctor' in booking and isinstance(booking['doctor'], dict) and 'name' in booking['doctor']:
            doctor_name = booking['doctor']['name']
        elif 'doctor' in booking and isinstance(booking['doctor'], str):
            doctor_name = booking['doctor']
        else:
            # Try to get doctor info from Django database
            try:
                if 'doctor_id' in booking:
                    doctor = Doctor.objects.get(id=booking['doctor_id'])
                    doctor_name = doctor.name
            except Exception as e:
                print(f"Error getting doctor name: {e}")
                doctor_name = "Doctor"
                
        # Get doctor clinic
        doctor_clinic = None
        if 'doctor_clinic' in booking:
            doctor_clinic = booking['doctor_clinic']
        elif 'doctor' in booking and isinstance(booking['doctor'], dict) and 'clinic' in booking['doctor']:
            doctor_clinic = booking['doctor']['clinic']
        else:
            # Try to get doctor clinic from Django database
            try:
                if 'doctor_id' in booking:
                    doctor = Doctor.objects.get(id=booking['doctor_id'])
                    doctor_clinic = doctor.clinic
            except Exception as e:
                print(f"Error getting doctor clinic: {e}")
                doctor_clinic = "Hospital"
                
        # Get doctor city
        doctor_city = None
        if 'doctor_city' in booking:
            doctor_city = booking['doctor_city']
        elif 'doctor' in booking and isinstance(booking['doctor'], dict) and 'city' in booking['doctor']:
            doctor_city = booking['doctor']['city']
        else:
            # Try to get doctor city from Django database
            try:
                if 'doctor_id' in booking:
                    doctor = Doctor.objects.get(id=booking['doctor_id'])
                    doctor_city = doctor.city
            except Exception as e:
                print(f"Error getting doctor city: {e}")
                doctor_city = "Unknown Location"
                
        # Get consultation type/specialty name
        consultation_type = None
        if 'consultation_type_name' in booking:
            consultation_type = booking['consultation_type_name']
        elif 'consultation_type' in booking and isinstance(booking['consultation_type'], dict) and 'name' in booking['consultation_type']:
            consultation_type = booking['consultation_type']['name']
        elif 'consultation_type' in booking and isinstance(booking['consultation_type'], str):
            consultation_type = booking['consultation_type']
        else:
            consultation_type = "General"
            
        # Ensure date and time are properly formatted
        booking_date = booking.get('selected_date', '')
        if not booking_date and 'booking_date' in booking:
            booking_date = booking['booking_date']
            
        booking_time = booking.get('selected_time', '')
        if not booking_time and 'booking_time' in booking:
            booking_time = booking['booking_time']
            
        # Get consultation fee
        consultation_fee = booking.get('consultation_fee', 0)
        if isinstance(consultation_fee, str) and consultation_fee.strip():
            try:
                consultation_fee = float(consultation_fee)
            except ValueError:
                consultation_fee = 0
        
        # Format patient name
        patient_name = booking.get('full_name', '')
        if not patient_name and 'patient_name' in booking:
            patient_name = booking['patient_name']
        if not patient_name:
            patient_name = patient_details.get('full_name', '') or request.user.get_full_name() or request.user.username
            
        # Create appointment object with all required data for the template
        appointment = {
            'id': f"APT-{datetime.now().year}-{booking.get('id', 0):03d}",
            'booking_id': booking.get('id', 0),  # Add the actual booking ID for form submission
            'type': consultation_type,
            'fees': consultation_fee,
            'date': booking_date,
            'time': booking_time,
            'doctor': {
                'name': doctor_name,
                'specialty': consultation_type,
                'department': f"{consultation_type} Department",
                'clinic': doctor_clinic,
                'city': doctor_city,
            },
            'patient': {
                'name': patient_name,
                'age': booking.get('age', '') or patient_details.get('age', 19),
                'gender': booking.get('gender', '') or patient_details.get('gender', 'Male'),
                'city': patient_details.get('city', ''),
                'phone': booking.get('phone_number', '') or patient_details.get('phone_number', ''),
            },
            'location': 'Hospital',
            'is_being_rescheduled': is_being_rescheduled,
        }
        
        # Debug output for appointment
        print(f"\n=== APPOINTMENT {appointment['id']} ===")
        print(f"Doctor name: {appointment['doctor']['name']}")
        print(f"Doctor clinic: {appointment['doctor']['clinic']}")
        print(f"Doctor city: {appointment['doctor']['city']}")
        print(f"Doctor specialty: {appointment['doctor']['specialty']}")
        print(f"Patient city: {appointment['patient']['city']}")
        print("=" * 40)
        
        appointments.append(appointment)
   
    context = {
        'appointments': appointments,
        'upcoming_count': upcoming_count,
        'today_date': today_display,
        'reschedule_mode': bool(reschedule_data),
        'reschedule_booking_id': reschedule_data.get('booking_id') if reschedule_data else None,
    }
   
    return render(request, 'myApp.html', context)


@login_required
def reschedule_appointment(request, booking_id):
    """Handle reschedule functionality"""
    # Check if user has API token, if not generate warning but allow to continue
    if not request.session.get('api_token'):
        messages.warning(request, 'Your session might have expired. Some features may be limited.')
    
    # Get the API token from session
    api_token = request.session.get('api_token')
    user_id = request.session.get('user_id')
    
    # Try to get booking details
    booking_details = None
    
    if api_token:
        # Try API first
        api_client = APIClient(token=api_token)
        try:
            response_data, status_code = api_client.get_booking(booking_id)
            if status_code == 200:
                booking_details = response_data
                print(f"Got booking details from API: {booking_details}")
        except Exception as e:
            print(f"API error getting booking details: {e}")
            pass
            
    # Fallback to Django model if API didn't work
    if not booking_details:
        try:
            booking = get_object_or_404(UserBooking, id=booking_id, user=request.user)
            # Convert to dict format similar to API response
            booking_details = {
                'id': booking.id,
                'full_name': booking.full_name,
                'phone_number': booking.phone_number,
                'age': booking.age,
                'gender': booking.gender,
                'doctor_id': booking.doctor.id,
                'service_id': booking.consultation_type.id,
            }
            print(f"Got booking details from Django model: {booking_details}")
        except Exception as e:
            print(f"Django error getting booking details: {e}")
            messages.error(request, "Unable to find booking to reschedule")
            return redirect('myApp')
    
    if not booking_details:
        messages.error(request, "Unable to find booking to reschedule")
        return redirect('myApp')
    
    # Ensure service_id exists
    if 'service_id' not in booking_details or not booking_details['service_id']:
        try:
            # Try to find the service_id from other sources
            if 'consultation_type_id' in booking_details:
                booking_details['service_id'] = booking_details['consultation_type_id']
            elif hasattr(booking, 'consultation_type') and booking.consultation_type:
                booking_details['service_id'] = booking.consultation_type.id
            else:
                # Default to a known service_id as last resort
                # Get first available consultation type
                consultation_type = ConsultationType.objects.first()
                if consultation_type:
                    booking_details['service_id'] = consultation_type.id
        except Exception as e:
            print(f"Error finding service_id: {e}")
    
    print(f"Final booking details before storing in session: {booking_details}")
    
    # Store booking data in session to pre-fill the forms
    request.session['reschedule_booking'] = {
        'booking_id': booking_details.get('id'),
        'full_name': booking_details.get('full_name', ''),
        'phone_number': booking_details.get('phone_number', ''),
        'email': request.user.email,  # User's email from Django user
        'age': booking_details.get('age', ''),
        'gender': booking_details.get('gender', ''),
        'city': booking_details.get('city', ''),  # City may not be available from API
        'service_id': booking_details.get('service_id', ''), 
        'doctor_id': booking_details.get('doctor_id', ''),
    }
    
    # Also populate the patient_details for consistency
    request.session['patient_details'] = {
        'full_name': booking_details.get('full_name', ''),
        'phone_number': booking_details.get('phone_number', ''),
        'email': request.user.email,
        'age': booking_details.get('age', ''),
        'gender': booking_details.get('gender', ''),
        'city': booking_details.get('city', ''),
        'reschedule_service_id': booking_details.get('service_id', ''),
    }
    
    # Instead of redirecting directly to confirm, always redirect to book first
    # This prevents the redirect loop between book and confirm views
    return redirect('book')

@login_required
def profile_view(request):
    
    profile, created = UserProfile.objects.get_or_create(id=request.user)
    
    if request.method == 'POST':
        # Update fields from form data
        profile.full_name = request.POST.get('full_name', '')
        profile.email = request.POST.get('email', '') 
        
        # Handle numeric fields
        age = request.POST.get('age')
        if age:
            try:
                profile.age = int(age)
            except ValueError:
                # Handle invalid age input
                pass
        
        # Handle date of birth - Django needs a date object
        dob = request.POST.get('date_of_birth')
        if dob:
            profile.date_of_birth = dob
        
        # Other personal info
        profile.gender = request.POST.get('gender', '')
        profile.blood_type = request.POST.get('blood_type', '')
        
        # Contact information
        profile.primary_phone = request.POST.get('primary_phone', '')
        profile.address_line1 = request.POST.get('address_line1', '')
        profile.city = request.POST.get('city', '')
        profile.state = request.POST.get('state', '')
        profile.pin_code = request.POST.get('zip_code', '')
        profile.emergency_contact_name = request.POST.get('emergency_contact_name', '')
        profile.emergency_contact_phone = request.POST.get('emergency_contact_phone', '')
        profile.emergency_contact_email = request.POST.get('emergency_contact_email', '')
        profile.emergency_contact_relationship = request.POST.get('emergency_contact_relationship', '')
        
        # Save all changes
        profile.save()
        
        # Update the user's email if it changed
        if request.user.email != profile.email:
            request.user.email = profile.email
            request.user.save()
        
        # Redirect back to profile page
        return redirect('profile')
    
    # For the template to access userprofile through user.userprofile
    # We'll use Django's context processor to extend the user object
    request.user.userprofile = profile
    
    return render(request, 'profile.html')


@login_required
def logout_view(request):
    # Clear any API session variables
    if 'api_token' in request.session:
        del request.session['api_token']
    
    if 'user_id' in request.session:
        del request.session['user_id']
        
    if 'is_doctor' in request.session:
        del request.session['is_doctor']
    
    if 'patient_details' in request.session:
        del request.session['patient_details']
        
    if 'reschedule_booking' in request.session:
        del request.session['reschedule_booking']
    
    # Mark session as modified
    request.session.modified = True
    
    # Log the user out of Django's system
    logout(request)
    
    # Redirect to home page
    return redirect('index')
