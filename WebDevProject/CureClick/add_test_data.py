from FLtoDjango.models import ConsultationType, Doctor, TimeSlot
from django.utils import timezone
from datetime import time, timedelta
import random

print("Script started")

def create_consultation_types():
    """Create sample consultation types"""
    print("Creating consultation types...")
    consultation_types = [
        {
            'name': 'General Medicine',
            'description': 'General medical consultation for common illnesses and health issues',
            'requires_referral': False,
            'emergency_specialty': False
        },
        {
            'name': 'Cardiology',
            'description': 'Specialized consultation for heart-related issues',
            'requires_referral': True,
            'emergency_specialty': True
        },
        {
            'name': 'Dermatology',
            'description': 'Treatment for skin, hair, and nail conditions',
            'requires_referral': False,
            'emergency_specialty': False
        },
        {
            'name': 'Orthopedics',
            'description': 'Treatment for bone and joint issues',
            'requires_referral': False,
            'emergency_specialty': True
        },
        {
            'name': 'Pediatrics',
            'description': 'Medical care for children and adolescents',
            'requires_referral': False,
            'emergency_specialty': False
        },
        {
            'name': 'Neurology',
            'description': 'Diagnosis and treatment of nervous system disorders',
            'requires_referral': True,
            'emergency_specialty': True
        },
    ]
    
    count = 0
    existing = 0
    for ct_data in consultation_types:
        ct, created = ConsultationType.objects.get_or_create(
            name=ct_data['name'],
            defaults={
                'description': ct_data['description'],
                'requires_referral': ct_data['requires_referral'],
                'emergency_specialty': ct_data['emergency_specialty']
            }
        )
        
        if created:
            count += 1
            print(f'Created consultation type: {ct.name}')
        else:
            existing += 1
            print(f'Consultation type already exists: {ct.name}')
    
    print(f'Created {count} new consultation types, {existing} already existed')

def create_doctors():
    """Create sample doctors for each consultation type"""
    print("Creating doctors...")
    # List of cities
    cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Kolkata', 'Pune', 'Jaipur']
    
    # Get all consultation types
    consultation_types = ConsultationType.objects.all()
    print(f"Found {consultation_types.count()} consultation types")
    
    count = 0
    existing = 0
    for ct in consultation_types:
        print(f"Creating doctors for {ct.name}...")
        # Create 2 doctors for each consultation type
        for i in range(2):
            doctor_code = f'DOC{ct.id}{i+1}'
            name = f'Dr. {random.choice(["Sharma", "Patel", "Kumar", "Singh", "Gupta", "Joshi"])} {random.choice(["A", "B", "C", "D", "E"])}'
            city = random.choice(cities)
            experience = random.randint(2, 20)
            rating = round(random.uniform(3.5, 5.0), 1)
            reviews = random.randint(10, 200)
            consultation_fee = random.choice([500, 600, 700, 800, 900, 1000, 1200, 1500])
            
            doctor, created = Doctor.objects.get_or_create(
                doctor_code=doctor_code,
                defaults={
                    'name': name,
                    'consultation_type': ct,
                    'rating': rating,
                    'reviews': reviews,
                    'experience': experience,
                    'consultation_fee': consultation_fee,
                    'clinic': f'{name} Clinic, {city}',
                    'bio': f'Experienced {ct.name} specialist with {experience} years of practice',
                    'city': city,
                    'active': True,
                    'photo_url': ''
                }
            )
            
            if created:
                count += 1
                print(f'Created doctor: {doctor.name} ({ct.name})')
            else:
                existing += 1
                print(f'Doctor already exists: {doctor.name} ({ct.name})')
    
    print(f'Created {count} new doctors, {existing} already existed')

def create_time_slots():
    """Create time slots for all doctors"""
    print("Creating time slots...")
    doctors = Doctor.objects.all()
    print(f"Found {doctors.count()} doctors")
    
    # Define time slots
    morning_slots = [time(9, 0), time(9, 30), time(10, 0), time(10, 30), time(11, 0), time(11, 30)]
    afternoon_slots = [time(13, 0), time(13, 30), time(14, 0), time(14, 30), time(15, 0), time(15, 30)]
    evening_slots = [time(17, 0), time(17, 30), time(18, 0), time(18, 30), time(19, 0), time(19, 30)]
    
    all_slots = morning_slots + afternoon_slots + evening_slots
    
    count = 0
    for doctor in doctors:
        print(f"Creating time slots for {doctor.name}...")
        # Delete existing time slots for this doctor
        deleted = TimeSlot.objects.filter(doctor=doctor).delete()
        print(f"Deleted {deleted[0]} existing time slots")
        
        # Create new time slots
        for slot_time in all_slots:
            end_time = (timezone.datetime.combine(timezone.datetime.today(), slot_time) + timedelta(minutes=30)).time()
            
            time_slot = TimeSlot.objects.create(
                doctor=doctor,
                start_time=slot_time,
                end_time=end_time,
                is_available=True
            )
            count += 1
    
    print(f'Created {count} time slots')

print('Starting to populate test data...')

# Create consultation types
create_consultation_types()

# Create doctors
create_doctors()

# Create time slots
create_time_slots()

print('Successfully populated test data!') 