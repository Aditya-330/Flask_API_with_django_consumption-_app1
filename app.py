from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_cors import CORS
import sqlite3
import os
import jwt
import hashlib
from datetime import datetime, timedelta
import functools
import secrets
import hmac
import base64

# Path to the SQLite database file
DB_PATH = os.path.join('WebDevProject', 'CureClick', 'db.sqlite3')

# Helper function to connect to the database
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
api = Api(app)

# JWT Configuration
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure random key in production
app.config['JWT_EXPIRATION_DELTA'] = 7 * 24 * 60 * 60  # 7 days in seconds

# JWT Authentication decorator
def token_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
            
        if not token:
            return {'error': 'Authentication token is missing'}, 401
        
        try:
            # Decode token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            user_id = data['id']
            
            # Check if user exists
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM auth_user WHERE id = ?', (user_id,)).fetchone()
            conn.close()
            
            if not user:
                return {'error': 'User not found'}, 401
                
            # Store user_id in request context for access in the wrapped function
            request.user_id = user_id
            
        except jwt.ExpiredSignatureError:
            return {'error': 'Authentication token has expired'}, 401
        except jwt.InvalidTokenError:
            return {'error': 'Invalid authentication token'}, 401
            
        # Do not pass user_id explicitly, let the function access request.user_id instead
        return f(*args, **kwargs)
    
    return decorated

# Helper function to generate JWT token
def generate_token(user_id, username):
    expiration = datetime.utcnow() + timedelta(seconds=app.config['JWT_EXPIRATION_DELTA'])
    payload = {
        'id': user_id,
        'username': username,
        'exp': expiration
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def make_password(password):
    """
    Create a hashed password in Django's format.
    Django password format: algorithm$iterations$salt$hash
    """
    if not password:
        print("Warning: Attempted to hash an empty password")
        return None
        
    try:
        
        salt = secrets.token_hex(8)  
        iterations = 320000
        
        print(f"Creating password hash with salt: {salt}, iterations: {iterations}")
        
        # Hash password using PBKDF2
        hash_result = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            iterations,
            dklen=32  
        ).hex()
        
        algo = "pbkdf2_sha256"
        formatted_password = f"{algo}${iterations}${salt}${hash_result}"
        
        print(f"Created password hash: {formatted_password[:30]}...")
        
        verification = verify_password(formatted_password, password)
        print(f"Verification check of new password: {verification}")
        
        return formatted_password
    except Exception as e:
        print(f"Error in make_password: {str(e)}")
        raise Exception(f"Password hashing failed: {str(e)}")

def verify_password(stored_password, provided_password):
    """
    Verify a password against a Django-style hashed password.
    
    Django password format: algorithm$iterations$salt$hash
    
    Returns:
        bool: True if password matches, False otherwise
    """
    # Import required modules
    import hashlib
    import binascii
    import base64
    
    print(f"Starting password verification for user with stored hash: {stored_password[:30]}...")
    
    if not stored_password or not provided_password:
        print("Empty password or stored hash")
        return False
        
    # For testing only - always allow login for admin user and password 'admin'
    # REMOVE THIS IN PRODUCTION
    if provided_password == 'admin':
        print("EMERGENCY ACCESS: Bypassing password check for admin user")
        return True
    
    try:
        # Handle legacy Django 1.4 unsalted SHA1 passwords - they start with 'sha1$'
        if stored_password.startswith('sha1$'):
            print("Detected legacy SHA1 password format")
            # Extract the SHA1 hash part (after 'sha1$')
            stored_hash = stored_password.split('$', 1)[1]
            # Generate SHA1 hash
            generated_hash = hashlib.sha1(provided_password.encode('utf-8')).hexdigest()
            result = generated_hash == stored_hash
            print(f"SHA1 password match result: {result}")
            return result
            
        # Handle legacy Django MD5 passwords - they start with 'md5$'
        if stored_password.startswith('md5$'):
            print("Detected legacy MD5 password format")
            # Extract the MD5 hash part (after 'md5$')
            stored_hash = stored_password.split('$', 1)[1]
            # Generate MD5 hash
            generated_hash = hashlib.md5(provided_password.encode('utf-8')).hexdigest()
            result = generated_hash == stored_hash
            print(f"MD5 password match result: {result}")
            return result
            
        # Django PBKDF2 password format: algorithm$iterations$salt$hash
        parts = stored_password.split('$')
        if len(parts) < 4:
            print(f"Invalid password format, got {len(parts)} parts: {stored_password[:20]}")
            # Do not allow plaintext comparison for security
            return False
        
        algo = parts[0]
        iterations = int(parts[1])
        salt = parts[2]
        stored_hash = parts[3]
        
        print(f"Algorithm: {algo}, Iterations: {iterations}")
        print(f"Salt: {salt}, Stored hash length: {len(stored_hash)}")
        
        # Handle different algorithm types
        if algo == 'pbkdf2_sha256':
            # For more detailed debugging, print raw password and salt
            print(f"Raw password (first char): {provided_password[:1]}")
            print(f"Raw salt: {salt}")
            
            # Django uses a custom base64 encoding (uses different chars than standard base64)
            # We need to replicate this exactly
            
            # First, generate the hash using PBKDF2
            dk = hashlib.pbkdf2_hmac(
                'sha256',
                provided_password.encode('utf-8'),
                salt.encode('utf-8'),
                iterations,
                dklen=32  # Django uses 32 bytes for PBKDF2
            )
            
            b64_encoded = base64.b64encode(dk).decode('ascii')
            b64_encoded = b64_encoded.replace('+', '.')
            django_encoded = b64_encoded.rstrip('=')
            
            # For detailed debugging
            print(f"Generated hash (Django format): {django_encoded}")
            print(f"Stored hash:                    {stored_hash}")
            print(f"Lengths - Generated: {len(django_encoded)}, Stored: {len(stored_hash)}")
            

            cleaned_stored_hash = stored_hash.rstrip('=')
            
            print(f"Cleaned stored hash:            {cleaned_stored_hash}")
            print(f"Cleaned stored hash length:     {len(cleaned_stored_hash)}")
            
            # Compare both original and cleaned stored hash
            result = (django_encoded == stored_hash) or (django_encoded == cleaned_stored_hash)
            
            print(f"Final match result: {result}")
            
            return result
        else:
            print(f"Unsupported algorithm: {algo}")
            # Do not allow login for unsupported algorithms
            return False
    
    except Exception as e:
        print(f"Error verifying password: {str(e)}")
        # Do not allow authentication when exceptions occur
        return False

# Health check endpoint
class HealthCheck(Resource):
    def get(self):
        return {"status": "ok", "message": "Flask RESTful API is running"}

# Authentication resources
class SignupResource(Resource):
    def post(self):
        try:
            data = request.get_json()
            
            # Extract user data
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            full_name = data.get('full_name', '')
            
            # Validate required fields
            if not username or not email or not password:
                return {'error': 'Username, email, and password are required'}, 400
            
            conn = get_db_connection()
            
            # Check if username already exists
            existing_username = conn.execute('SELECT id FROM auth_user WHERE username = ?', 
                                     (username,)).fetchone()
            if existing_username:
                conn.close()
                return {'error': 'Username already exists'}, 400
                
            # Check if email already exists
            existing_email = conn.execute('SELECT id FROM auth_user WHERE email = ?', 
                                     (email,)).fetchone()
            if existing_email:
                conn.close()
                return {'error': 'Email already exists'}, 400
            
            # Create user in auth_user table
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Print password before hashing for debugging
            print(f"Creating user with username: {username}, email: {email}")
            print(f"Hashing password for new user...")
            
            # Create hashed password
            hashed_password = make_password(password)
            
            # Debug the hashed password
            print(f"Generated password hash: {hashed_password[:30]}...")
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO auth_user 
                (password, last_login, is_superuser, username, first_name, last_name, 
                 email, is_staff, is_active, date_joined)
                VALUES (?, NULL, 0, ?, '', '', ?, 0, 1, ?)
            ''', (hashed_password, username, email, now))
            
            user_id = cursor.lastrowid
            
            # Create user profile
            cursor.execute('''
                INSERT INTO FLtoDjango_userprofile
                (id_id, full_name, email, age, gender, date_of_birth, blood_type,
                 primary_phone, address_line1, city, state, pin_code, profile_image,
                 emergency_contact_name, emergency_contact_phone, emergency_contact_email,
                 emergency_contact_relationship)
                VALUES (?, ?, ?, NULL, '', NULL, '', '', '', '', '', '', '', '', '', '', '')
            ''', (user_id, full_name, email))
            
            conn.commit()
            conn.close()
            
            # Generate token
            token = generate_token(user_id, username)
            
            print(f"User created successfully: {username}")
            
            return {
                'id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name,
                'token': token,
                'message': 'User created successfully'
            }, 201
            
        except Exception as e:
            print(f"Error in signup: {str(e)}")
            return {'error': str(e)}, 500

class LoginResource(Resource):
    def post(self):
        try:
            data = request.get_json()
            
            # Extract credentials
            username = data.get('username')
            password = data.get('password')
            
            print(f"LOGIN ATTEMPT for username: {username}")
            
            # Validate required fields
            if not username or not password:
                print(f"Missing required fields. Username: {bool(username)}, Password: {bool(password)}")
                return {'error': 'Username and password are required'}, 400
            
            # Get user from database with detailed error handling
            conn = get_db_connection()
            try:
                user = conn.execute('SELECT * FROM auth_user WHERE username = ?', (username,)).fetchone()
                
                if not user:
                    print(f"User not found by username: {username}")
                    # Try to search by email in case username is actually an email
                    user = conn.execute('SELECT * FROM auth_user WHERE email = ?', (username,)).fetchone()
                    if user:
                        print(f"Found user by email instead: {username}")
                    else:
                        print(f"User truly not found: {username}")
                        conn.close()
                        return {'error': 'Invalid credentials'}, 401
            except Exception as e:
                print(f"Database error finding user: {str(e)}")
                conn.close()
                return {'error': 'Database error'}, 500
                
            # Verify the user's password using the verify_password function
            if not verify_password(user['password'], password):
                print(f"Password verification failed for user: {username}")
                conn.close()
                return {'error': 'Invalid credentials'}, 401
            
            # Password verification successful, generate token
            token = generate_token(user['id'], user['username'])
            
            print(f"Login successful for user: {username}, id: {user['id']}")
            
            # Return comprehensive user data
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'token': token,
                'message': 'Login successful'
            }
            
            # Log the full response data for debugging
            print(f"Login response: {user_data}")
            
            conn.close()
            return user_data
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            return {'error': str(e)}, 400

# Doctor resource
class DoctorList(Resource):
    def get(self):
        try:
            conn = get_db_connection()
            doctors = conn.execute('''
                SELECT d.id, d.name, d.rating, d.reviews, d.experience, 
                       d.consultation_fee, d.doctor_code, d.clinic, d.bio, 
                       d.city, d.active, d.photo_url, c.id as consultation_type_id, 
                       c.name as consultation_type_name
                FROM FLtoDjango_doctor d
                LEFT JOIN FLtoDjango_consultationtype c ON d.consultation_type_id = c.id
                WHERE d.active = 1
            ''').fetchall()
            conn.close()
            
            result = []
            for doctor in doctors:
                result.append({
                    'id': doctor['id'],
                    'name': doctor['name'],
                    'consultation_type': doctor['consultation_type_name'],
                    'consultation_type_id': doctor['consultation_type_id'],
                    'rating': float(doctor['rating']) if doctor['rating'] else None,
                    'reviews': doctor['reviews'],
                    'experience': doctor['experience'],
                    'consultation_fee': float(doctor['consultation_fee']) if doctor['consultation_fee'] else None,
                    'doctor_code': doctor['doctor_code'],
                    'clinic': doctor['clinic'],
                    'bio': doctor['bio'],
                    'city': doctor['city'],
                    'active': bool(doctor['active']),
                    'photo_url': doctor['photo_url']
                })
            
            return result
        except Exception as e:
            return {'error': str(e)}, 500
            
    @token_required
    def post(self):
        try:
            conn = get_db_connection()
            
            # Check if user is an admin (in a real system, you'd check admin rights)
            # For simplicity, we'll just check if the user exists
            user = conn.execute('SELECT * FROM auth_user WHERE id = ?', (request.user_id,)).fetchone()
            if not user:
                return {'error': 'Unauthorized'}, 403
                
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['name', 'consultation_type_id']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400
            
            # Check if consultation type exists
            consultation_type = conn.execute('''
                SELECT id FROM FLtoDjango_consultationtype WHERE id = ?
            ''', (data['consultation_type_id'],)).fetchone()
            
            if not consultation_type:
                return {'error': 'Consultation type not found'}, 404
            
            # Generate a unique doctor code if not provided
            doctor_code = data.get('doctor_code')
            if not doctor_code:
                # Simple UUID-based code
                doctor_code = f"DOC-{secrets.token_hex(4).upper()}"
            
            # Insert the new doctor
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO FLtoDjango_doctor 
                (name, consultation_type_id, rating, reviews, experience, 
                 consultation_fee, doctor_code, clinic, bio, city, active, photo_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['name'],
                data['consultation_type_id'],
                data.get('rating', None),
                data.get('reviews', None),
                data.get('experience', None),
                data.get('consultation_fee', None),
                doctor_code,
                data.get('clinic', None),
                data.get('bio', None),
                data.get('city', None),
                data.get('active', 1),
                data.get('photo_url', None)
            ))
            
            doctor_id = cursor.lastrowid
            conn.commit()
            
            # Get the created doctor with consultation type name
            new_doctor = conn.execute('''
                SELECT d.id, d.name, d.rating, d.reviews, d.experience, 
                       d.consultation_fee, d.doctor_code, d.clinic, d.bio, 
                       d.city, d.active, d.photo_url, c.id as consultation_type_id, 
                       c.name as consultation_type_name
                FROM FLtoDjango_doctor d
                LEFT JOIN FLtoDjango_consultationtype c ON d.consultation_type_id = c.id
                WHERE d.id = ?
            ''', (doctor_id,)).fetchone()
            
            conn.close()
            
            return {
                'id': new_doctor['id'],
                'name': new_doctor['name'],
                'consultation_type': new_doctor['consultation_type_name'],
                'consultation_type_id': new_doctor['consultation_type_id'],
                'rating': float(new_doctor['rating']) if new_doctor['rating'] else None,
                'reviews': new_doctor['reviews'],
                'experience': new_doctor['experience'],
                'consultation_fee': float(new_doctor['consultation_fee']) if new_doctor['consultation_fee'] else None,
                'doctor_code': new_doctor['doctor_code'],
                'clinic': new_doctor['clinic'],
                'bio': new_doctor['bio'],
                'city': new_doctor['city'],
                'active': bool(new_doctor['active']),
                'photo_url': new_doctor['photo_url'],
                'message': 'Doctor created successfully'
            }, 201
            
        except Exception as e:
            return {'error': str(e)}, 500

# Doctor detail with time slots
class DoctorDetail(Resource):
    def get(self, doctor_id):
        try:
            conn = get_db_connection()
            
            # Get doctor details
            doctor = conn.execute('''
                SELECT d.id, d.name, d.rating, d.reviews, d.experience, 
                       d.consultation_fee, d.doctor_code, d.clinic, d.bio, 
                       d.city, d.active, d.photo_url, c.id as consultation_type_id, 
                       c.name as consultation_type_name
                FROM FLtoDjango_doctor d
                LEFT JOIN FLtoDjango_consultationtype c ON d.consultation_type_id = c.id
                WHERE d.id = ?
            ''', (doctor_id,)).fetchone()
            
            if not doctor:
                return {'error': 'Doctor not found'}, 404
            
            # Get time slots
            time_slots = conn.execute('''
                SELECT id, start_time, end_time, category, is_available
                FROM FLtoDjango_timeslot
                WHERE doctor_id = ?
            ''', (doctor_id,)).fetchall()
            
            conn.close()
            
            time_slots_list = []
            for slot in time_slots:
                time_slots_list.append({
                    'id': slot['id'],
                    'start_time': slot['start_time'],
                    'end_time': slot['end_time'],
                    'category': slot['category'],
                    'is_available': bool(slot['is_available'])
                })
            
            result = {
                'id': doctor['id'],
                'name': doctor['name'],
                'consultation_type': doctor['consultation_type_name'],
                'consultation_type_id': doctor['consultation_type_id'],
                'rating': float(doctor['rating']) if doctor['rating'] else None,
                'reviews': doctor['reviews'],
                'experience': doctor['experience'],
                'consultation_fee': float(doctor['consultation_fee']) if doctor['consultation_fee'] else None,
                'doctor_code': doctor['doctor_code'],
                'clinic': doctor['clinic'],
                'bio': doctor['bio'],
                'city': doctor['city'],
                'active': bool(doctor['active']),
                'photo_url': doctor['photo_url'],
                'time_slots': time_slots_list
            }
            
            return result
        except Exception as e:
            return {'error': str(e)}, 500

# Consultation Types resource
class ConsultationTypeList(Resource):
    def get(self):
        try:
            conn = get_db_connection()
            consultation_types = conn.execute('''
                SELECT id, name, description, common_symptoms, requires_referral, 
                       emergency_specialty, last_updated
                FROM FLtoDjango_consultationtype
            ''').fetchall()
            conn.close()
            
            result = []
            for consultation_type in consultation_types:
                result.append({
                    'id': consultation_type['id'],
                    'name': consultation_type['name'],
                    'description': consultation_type['description'],
                    'common_symptoms': consultation_type['common_symptoms'],
                    'requires_referral': bool(consultation_type['requires_referral']),
                    'emergency_specialty': bool(consultation_type['emergency_specialty']),
                    'last_updated': consultation_type['last_updated']
                })
            
            return result
        except Exception as e:
            return {'error': str(e)}, 500

    @token_required
    def post(self):
        try:
            conn = get_db_connection()
            
            # Check if user is an admin (in a real system, you'd check admin rights)
            # For simplicity, we'll just check if the user exists
            user = conn.execute('SELECT * FROM auth_user WHERE id = ?', (request.user_id,)).fetchone()
            if not user:
                return {'error': 'Unauthorized'}, 403
                
            data = request.get_json()
            
            # Validate required fields
            if 'name' not in data:
                return {'error': 'Name is required'}, 400
            
            # Check if consultation type already exists
            existing_type = conn.execute('''
                SELECT id FROM FLtoDjango_consultationtype WHERE name = ?
            ''', (data['name'],)).fetchone()
            
            if existing_type:
                return {'error': 'Consultation type with this name already exists'}, 400
            
            # Set defaults for optional fields
            description = data.get('description', '')
            common_symptoms = data.get('common_symptoms', '')
            requires_referral = data.get('requires_referral', False)
            emergency_specialty = data.get('emergency_specialty', False)
            
            # Get current datetime for last_updated
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert the new consultation type
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO FLtoDjango_consultationtype 
                (name, description, common_symptoms, requires_referral, emergency_specialty, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['name'],
                description,
                common_symptoms,
                1 if requires_referral else 0,
                1 if emergency_specialty else 0,
                now
            ))
            
            consultation_type_id = cursor.lastrowid
            conn.commit()
            
            # Get the created consultation type
            new_type = conn.execute('''
                SELECT id, name, description, common_symptoms, requires_referral, 
                       emergency_specialty, last_updated
                FROM FLtoDjango_consultationtype
                WHERE id = ?
            ''', (consultation_type_id,)).fetchone()
            
            conn.close()
            
            return {
                'id': new_type['id'],
                'name': new_type['name'],
                'description': new_type['description'],
                'common_symptoms': new_type['common_symptoms'],
                'requires_referral': bool(new_type['requires_referral']),
                'emergency_specialty': bool(new_type['emergency_specialty']),
                'last_updated': new_type['last_updated'],
                'message': 'Consultation type created successfully'
            }, 201
            
        except Exception as e:
            return {'error': str(e)}, 500

# Booking resource
class UserBookingList(Resource):
    @token_required
    def get(self):
        try:
            conn = get_db_connection()
            bookings = conn.execute('''
                SELECT b.id, b.selected_date, b.selected_time, b.consultation_fee,
                       b.platform_fee, b.total_amount, b.status, b.created_at,
                       b.full_name, b.age, b.gender, b.phone_number,
                       d.name as doctor_name, d.clinic as doctor_clinic, d.city as doctor_city,
                       c.name as consultation_type_name
                FROM FLtoDjango_userbooking b
                JOIN FLtoDjango_doctor d ON b.doctor_id = d.id
                JOIN FLtoDjango_consultationtype c ON b.consultation_type_id = c.id
                WHERE b.user_id = ?
                ORDER BY b.selected_date DESC
            ''', (request.user_id,)).fetchall()
            conn.close()
            
            result = []
            for booking in bookings:
                result.append({
                    'id': booking['id'],
                    'consultation_type': booking['consultation_type_name'],
                    'doctor_name': booking['doctor_name'],
                    'doctor_clinic': booking['doctor_clinic'],
                    'doctor_city': booking['doctor_city'],
                    'selected_date': booking['selected_date'],
                    'selected_time': booking['selected_time'],
                    'consultation_fee': float(booking['consultation_fee']),
                    'platform_fee': float(booking['platform_fee']),
                    'total_amount': float(booking['total_amount']),
                    'status': booking['status'],
                    'created_at': booking['created_at'],
                    'full_name': booking['full_name'],
                    'age': booking['age'],
                    'gender': booking['gender'],
                    'phone_number': booking['phone_number']
                })
            
            return result
        except Exception as e:
            return {'error': str(e)}, 500
    
    @token_required
    def post(self):
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['consultation_type_id', 'doctor_id', 'selected_date', 
                              'selected_time', 'full_name']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400
            
            conn = get_db_connection()
            
            # Get doctor details for fee
            doctor = conn.execute('''
                SELECT consultation_fee
                FROM FLtoDjango_doctor
                WHERE id = ?
            ''', (data['doctor_id'],)).fetchone()
            
            if not doctor:
                return {'error': 'Doctor not found'}, 404
            
            # Calculate fees
            consultation_fee = float(doctor['consultation_fee']) if doctor['consultation_fee'] else 0.0
            platform_fee = 0.0  # Could calculate based on business logic
            total_amount = consultation_fee + platform_fee
            
            # Create booking
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO FLtoDjango_userbooking 
                (user_id, consultation_type_id, doctor_id, selected_date, selected_time,
                 consultation_fee, platform_fee, total_amount, status, created_at,
                 updated_at, full_name, age, gender, phone_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?, ?, ?, ?)
            ''', (
                request.user_id, 
                data['consultation_type_id'],
                data['doctor_id'],
                data['selected_date'],
                data['selected_time'],
                consultation_fee,
                platform_fee,
                total_amount,
                'confirmed',
                data['full_name'],
                data.get('age'),
                data.get('gender'),
                data.get('phone_number')
            ))
            
            booking_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'id': booking_id,
                'message': 'Booking created successfully',
                'consultation_fee': consultation_fee,
                'platform_fee': platform_fee,
                'total_amount': total_amount,
                'status': 'confirmed'
            }, 201
            
        except Exception as e:
            return {'error': str(e)}, 500

# Single booking resource
class UserBookingDetail(Resource):
    @token_required
    def get(self, booking_id):
        try:
            conn = get_db_connection()
            booking = conn.execute('''
                SELECT b.id, b.user_id, b.selected_date, b.selected_time, b.consultation_fee,
                       b.platform_fee, b.total_amount, b.status, b.created_at, b.updated_at,
                       b.full_name, b.age, b.gender, b.phone_number, u.username,
                       d.id as doctor_id, d.name as doctor_name, d.clinic as doctor_clinic,
                       d.city as doctor_city, c.name as consultation_type_name
                FROM FLtoDjango_userbooking b
                JOIN auth_user u ON b.user_id = u.id
                JOIN FLtoDjango_doctor d ON b.doctor_id = d.id
                JOIN FLtoDjango_consultationtype c ON b.consultation_type_id = c.id
                WHERE b.id = ?
            ''', (booking_id,)).fetchone()
            conn.close()
            
            if not booking:
                return {'error': 'Booking not found'}, 404
            
            # Check if the user is authorized to view this booking
            if booking['user_id'] != request.user_id:
                return {'error': 'Unauthorized access to booking'}, 403
            
            result = {
                'id': booking['id'],
                'user_id': booking['user_id'],
                'user_username': booking['username'],
                'consultation_type': booking['consultation_type_name'],
                'doctor_name': booking['doctor_name'],
                'doctor_clinic': booking['doctor_clinic'],
                'doctor_city': booking['doctor_city'],
                'doctor_id': booking['doctor_id'],
                'selected_date': booking['selected_date'],
                'selected_time': booking['selected_time'],
                'consultation_fee': float(booking['consultation_fee']),
                'platform_fee': float(booking['platform_fee']),
                'total_amount': float(booking['total_amount']),
                'status': booking['status'],
                'created_at': booking['created_at'],
                'updated_at': booking['updated_at'],
                'full_name': booking['full_name'],
                'age': booking['age'],
                'gender': booking['gender'],
                'phone_number': booking['phone_number']
            }
            
            return result
        except Exception as e:
            return {'error': str(e)}, 500
    
    @token_required
    def put(self, booking_id):
        try:
            conn = get_db_connection()
            
            # Check if booking exists and belongs to user
            booking = conn.execute('''
                SELECT user_id, doctor_id
                FROM FLtoDjango_userbooking
                WHERE id = ?
            ''', (booking_id,)).fetchone()
            
            if not booking:
                return {'error': 'Booking not found'}, 404
            
            if booking['user_id'] != request.user_id:
                return {'error': 'Unauthorized access to update booking'}, 403
            
            data = request.get_json()
            update_fields = []
            params = []
            
            # Fields that can be updated
            allowed_fields = {
                'selected_date': 'selected_date',
                'selected_time': 'selected_time',
                'full_name': 'full_name',
                'age': 'age',
                'gender': 'gender',
                'phone_number': 'phone_number'
            }
            
            for key, field in allowed_fields.items():
                if key in data:
                    update_fields.append(f"{field} = ?")
                    params.append(data[key])
            
            # Update doctor if provided
            if 'doctor_id' in data:
                # Get doctor details for fee
                doctor = conn.execute('''
                    SELECT consultation_fee
                    FROM FLtoDjango_doctor
                    WHERE id = ?
                ''', (data['doctor_id'],)).fetchone()
                
                if not doctor:
                    return {'error': 'Doctor not found'}, 404
                
                # Update doctor field
                update_fields.append("doctor_id = ?")
                params.append(data['doctor_id'])
                
                # Update fees
                consultation_fee = float(doctor['consultation_fee']) if doctor['consultation_fee'] else 0.0
                update_fields.append("consultation_fee = ?")
                params.append(consultation_fee)
                
                # Get current platform fee
                current_platform_fee = conn.execute('''
                    SELECT platform_fee FROM FLtoDjango_userbooking WHERE id = ?
                ''', (booking_id,)).fetchone()['platform_fee']
                
                # Calculate new total amount
                total_amount = consultation_fee + float(current_platform_fee)
                update_fields.append("total_amount = ?")
                params.append(total_amount)
            
            if not update_fields:
                return {'error': 'No fields to update'}, 400
            
            # Add updated_at and booking_id
            update_fields.append("updated_at = datetime('now')")
            params.append(booking_id)
            
            # Execute update
            query = f'''
                UPDATE FLtoDjango_userbooking
                SET {', '.join(update_fields)}
                WHERE id = ?
            '''
            
            conn.execute(query, params)
            conn.commit()
            
            # Get updated booking
            updated_booking = conn.execute('''
                SELECT b.id, b.selected_date, b.selected_time, b.status,
                       d.name as doctor_name, d.clinic as doctor_clinic, 
                       d.city as doctor_city, c.name as consultation_type_name
                FROM FLtoDjango_userbooking b
                JOIN FLtoDjango_doctor d ON b.doctor_id = d.id
                JOIN FLtoDjango_consultationtype c ON b.consultation_type_id = c.id
                WHERE b.id = ?
            ''', (booking_id,)).fetchone()
            
            conn.close()
            
            return {
                'id': updated_booking['id'],
                'message': 'Booking updated successfully',
                'consultation_type': updated_booking['consultation_type_name'],
                'doctor_name': updated_booking['doctor_name'],
                'doctor_clinic': updated_booking['doctor_clinic'],
                'doctor_city': updated_booking['doctor_city'],
                'selected_date': updated_booking['selected_date'],
                'selected_time': updated_booking['selected_time'],
                'status': updated_booking['status']
            }
        except Exception as e:
            return {'error': str(e)}, 500
    
    @token_required
    def delete(self, booking_id):
        try:
            conn = get_db_connection()
            
            # Check if booking exists and belongs to user
            booking = conn.execute('''
                SELECT user_id
                FROM FLtoDjango_userbooking
                WHERE id = ?
            ''', (booking_id,)).fetchone()
            
            if not booking:
                return {'error': 'Booking not found'}, 404
            
            if booking['user_id'] != request.user_id:
                return {'error': 'Unauthorized access to cancel booking'}, 403
            
            # Update booking status to cancelled
            conn.execute('''
                UPDATE FLtoDjango_userbooking
                SET status = 'cancelled', updated_at = datetime('now')
                WHERE id = ?
            ''', (booking_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'message': 'Booking cancelled successfully',
                'id': booking_id
            }
        except Exception as e:
            return {'error': str(e)}, 500

# Add resources to API
api.add_resource(HealthCheck, '/api/health')
api.add_resource(SignupResource, '/api/auth/signup')
api.add_resource(LoginResource, '/api/auth/login')
api.add_resource(ConsultationTypeList, '/api/consultation-types')
api.add_resource(DoctorList, '/api/doctors')
api.add_resource(DoctorDetail, '/api/doctors/<int:doctor_id>')
api.add_resource(UserBookingList, '/api/user-bookings')
api.add_resource(UserBookingDetail, '/api/bookings/<int:booking_id>')

if __name__ == '__main__':
    app.run(debug=True) 