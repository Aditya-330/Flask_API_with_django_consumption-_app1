from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from FLtoDjango.models import ConsultationType, Doctor, TimeSlot
from django.utils import timezone
from datetime import time, timedelta
import random

class Command(BaseCommand):
    help = 'Populates the database with test data for consultation types and doctors'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to populate test data...')
        
        # Create consultation types
        self.create_consultation_types()
        
        # Create doctors
        self.create_doctors()
        
        # Create time slots
        self.create_time_slots()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated test data!'))
    
    def create_consultation_types(self):
        """Create sample consultation types"""
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
                self.stdout.write(f'Created consultation type: {ct.name}')
        
        self.stdout.write(self.style.SUCCESS(f'Created {count} new consultation types'))
    
    def create_doctors(self):
        """Create sample doctors for each consultation type"""
        # List of cities
        cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Kolkata', 'Pune', 'Jaipur']
        
        # Get all consultation types
        consultation_types = ConsultationType.objects.all()
        
        count = 0
        for ct in consultation_types:
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
                    self.stdout.write(f'Created doctor: {doctor.name} ({ct.name})')
        
        self.stdout.write(self.style.SUCCESS(f'Created {count} new doctors'))
    
    def create_time_slots(self):
        """Create time slots for all doctors"""
        doctors = Doctor.objects.all()
        
        # Define time slots
        morning_slots = [time(9, 0), time(9, 30), time(10, 0), time(10, 30), time(11, 0), time(11, 30)]
        afternoon_slots = [time(13, 0), time(13, 30), time(14, 0), time(14, 30), time(15, 0), time(15, 30)]
        evening_slots = [time(17, 0), time(17, 30), time(18, 0), time(18, 30), time(19, 0), time(19, 30)]
        
        all_slots = morning_slots + afternoon_slots + evening_slots
        
        count = 0
        for doctor in doctors:
            # Delete existing time slots for this doctor
            TimeSlot.objects.filter(doctor=doctor).delete()
            
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
        
        self.stdout.write(self.style.SUCCESS(f'Created {count} time slots')) 