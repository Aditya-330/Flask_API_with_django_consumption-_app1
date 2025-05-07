import os
import sys
import django
import random
from datetime import time, timedelta
import string
from django.utils import timezone
import base64

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/CureClick')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CureClick.settings")
try:
    django.setup()
    print("Django setup successful")
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

# Import Django models
from FLtoDjango.models import ConsultationType, Doctor, TimeSlot

DEFAULT_PROFILE_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512" width="100" height="100"><path fill="#4a90e2" d="M224 256c70.7 0 128-57.3 128-128S294.7 0 224 0S96 57.3 96 128s57.3 128 128 128zm-45.7 48C79.8 304 0 383.8 0 482.3C0 498.7 13.3 512 29.7 512H418.3c16.4 0 29.7-13.3 29.7-29.7C448 383.8 368.2 304 269.7 304H178.3z"/>
</svg>
"""

# Convert the SVG to a base64 data URL
DEFAULT_PROFILE_ICON_BASE64 = f"data:image/svg+xml;base64,{base64.b64encode(DEFAULT_PROFILE_ICON.strip().encode()).decode()}"

def create_consultation_types():
    """Create 19 diverse consultation types"""
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
        {
            'name': 'Gastroenterology',
            'description': 'Diagnosis and treatment of digestive system disorders',
            'requires_referral': True,
            'emergency_specialty': False
        },
        {
            'name': 'Obstetrics & Gynecology',
            'description': 'Medical care for women, pregnancy, and reproductive health',
            'requires_referral': False,
            'emergency_specialty': True
        },
        {
            'name': 'Psychiatry',
            'description': 'Mental health diagnosis and treatment',
            'requires_referral': True,
            'emergency_specialty': False
        },
        {
            'name': 'Ophthalmology',
            'description': 'Eye health and vision care',
            'requires_referral': False,
            'emergency_specialty': False
        },
        {
            'name': 'ENT',
            'description': 'Ear, nose, and throat diagnosis and treatment',
            'requires_referral': False,
            'emergency_specialty': False
        },
        {
            'name': 'Endocrinology',
            'description': 'Hormone-related disorders and diabetes management',
            'requires_referral': True,
            'emergency_specialty': False
        },
        {
            'name': 'Pulmonology',
            'description': 'Respiratory system diagnosis and treatment',
            'requires_referral': True,
            'emergency_specialty': True
        },
        {
            'name': 'Nephrology',
            'description': 'Kidney disease diagnosis and treatment',
            'requires_referral': True,
            'emergency_specialty': True
        },
        {
            'name': 'Urology',
            'description': 'Urinary tract and male reproductive system treatment',
            'requires_referral': False,
            'emergency_specialty': False
        },
        {
            'name': 'Oncology',
            'description': 'Cancer diagnosis and treatment',
            'requires_referral': True,
            'emergency_specialty': False
        },
        {
            'name': 'Rheumatology',
            'description': 'Autoimmune and inflammatory disorders treatment',
            'requires_referral': True,
            'emergency_specialty': False
        },
        {
            'name': 'Dentistry',
            'description': 'Oral health diagnosis and treatment',
            'requires_referral': False,
            'emergency_specialty': False
        },
        {
            'name': 'Physiotherapy',
            'description': 'Physical rehabilitation and pain management',
            'requires_referral': False,
            'emergency_specialty': False
        }
    ]
    
    count = 0
    created_types = []
    
    # Clear existing consultation types
    ConsultationType.objects.all().delete()
    
    for ct_data in consultation_types:
        ct = ConsultationType.objects.create(
            name=ct_data['name'],
            description=ct_data['description'],
            requires_referral=ct_data['requires_referral'],
            emergency_specialty=ct_data['emergency_specialty']
        )
        
        count += 1
        created_types.append(ct)
        print(f'Created consultation type: {ct.name}')
    
    print(f'Created {count} new consultation types')
    return created_types

def create_doctors(consultation_types):
    """Create over 600 doctors across different consultation types and cities"""
    # Expanded list of cities
    cities = {
        'Mumbai': ['Andheri', 'Bandra', 'Colaba', 'Dadar', 'Juhu', 'Powai', 'Worli'],
        'Delhi': ['Connaught Place', 'Dwarka', 'Hauz Khas', 'Karol Bagh', 'Rohini', 'Saket'],
        'Bangalore': ['Indiranagar', 'Koramangala', 'Whitefield', 'Jayanagar', 'HSR Layout', 'MG Road'],
        'Chennai': ['Adyar', 'Anna Nagar', 'T. Nagar', 'Velachery', 'Besant Nagar'],
        'Hyderabad': ['Banjara Hills', 'Gachibowli', 'Jubilee Hills', 'Madhapur', 'Secunderabad'],
        'Kolkata': ['Park Street', 'Salt Lake', 'New Town', 'Alipore', 'Ballygunge'],
        'Pune': ['Aundh', 'Baner', 'Koregaon Park', 'Viman Nagar', 'Kothrud'],
        'Jaipur': ['Malviya Nagar', 'Vaishali Nagar', 'C-Scheme', 'Mansarovar', 'Raja Park'],
        'Ahmedabad': ['Navrangpura', 'Satellite', 'Bodakdev', 'CG Road', 'Prahlad Nagar'],
        'Lucknow': ['Gomti Nagar', 'Hazratganj', 'Indira Nagar', 'Aliganj'],
        'Chandigarh': ['Sector 8', 'Sector 17', 'Sector 35', 'Sector 43'],
        'Indore': ['Vijay Nagar', 'Saket', 'New Palasia', 'Rajendra Nagar'],
        'Bhopal': ['MP Nagar', 'Arera Colony', 'Shahpura', 'Kolar Road'],
        'Nagpur': ['Dharampeth', 'Ramdaspeth', 'Civil Lines', 'Sadar'],
        'Kochi': ['Panampilly Nagar', 'Kakkanad', 'Fort Kochi', 'Edappally'],
        'Guwahati': ['Zoo Road', 'GS Road', 'Fancy Bazar', 'Dispur'],
        'Visakhapatnam': ['MVP Colony', 'Dwaraka Nagar', 'Beach Road', 'Siripuram']
    }
    
    # List of doctor surnames sorted by region (for diversity)
    surnames = {
        'North': ['Sharma', 'Gupta', 'Singh', 'Verma', 'Kumar', 'Arora', 'Kapoor', 'Malhotra', 'Bhatia', 'Khanna'],
        'South': ['Reddy', 'Nair', 'Rao', 'Pillai', 'Iyer', 'Krishnan', 'Subramaniam', 'Naidu', 'Menon', 'Thomas'],
        'East': ['Banerjee', 'Chatterjee', 'Mukherjee', 'Das', 'Bose', 'Sen', 'Dutta', 'Roy', 'Ghosh', 'Sarkar'],
        'West': ['Patel', 'Shah', 'Joshi', 'Desai', 'Mehta', 'Gandhi', 'Parekh', 'Chauhan', 'Doshi', 'Sheth']
    }
    
    # Common male and female first names
    first_names = {
        'Male': ['Aditya', 'Rajesh', 'Sunil', 'Vikram', 'Rahul', 'Amit', 'Deepak', 'Sanjay', 'Rohit', 'Nitin',
                'Varun', 'Mohit', 'Harish', 'Anand', 'Rakesh', 'Ashok', 'Dinesh', 'Ramesh', 'Gaurav', 'Sameer'],
        'Female': ['Anjali', 'Shikha', 'Priya', 'Neha', 'Pooja', 'Swati', 'Divya', 'Kavita', 'Meena', 'Sunita',
                  'Ritu', 'Anita', 'Namita', 'Deepika', 'Shalini', 'Preeti', 'Sneha', 'Jyoti', 'Arti', 'Smita']
    }
    
    # Qualifications by specialization
    qualifications = {
        'General Medicine': ['MBBS', 'MD (Medicine)', 'DNB (Medicine)'],
        'Cardiology': ['MBBS, MD, DM (Cardiology)', 'MBBS, DNB (Cardiology)', 'MBBS, FRCP, CCT (Cardiology)'],
        'Dermatology': ['MBBS, MD (Dermatology)', 'MBBS, DVD', 'MBBS, FRCP, Dermatology'],
        'Orthopedics': ['MBBS, MS (Ortho)', 'MBBS, DNB (Ortho)', 'MBBS, FRCS (Ortho)'],
        'Pediatrics': ['MBBS, MD (Pediatrics)', 'MBBS, DCH', 'MBBS, DNB (Pediatrics)'],
        'Neurology': ['MBBS, MD, DM (Neurology)', 'MBBS, DNB (Neurology)', 'MBBS, FRCP, Neurology'],
        'Gastroenterology': ['MBBS, MD, DM (Gastro)', 'MBBS, DNB (Gastro)', 'MBBS, MRCP, Gastroenterology'],
        'Obstetrics & Gynecology': ['MBBS, MS (OB-GYN)', 'MBBS, DNB (OB-GYN)', 'MBBS, MRCOG'],
        'Psychiatry': ['MBBS, MD (Psychiatry)', 'MBBS, DPM', 'MBBS, MRCPsych'],
        'Ophthalmology': ['MBBS, MS (Ophth)', 'MBBS, DNB (Ophth)', 'MBBS, FRCS (Ophth)'],
        'ENT': ['MBBS, MS (ENT)', 'MBBS, DNB (ENT)', 'MBBS, FRCS (ORL)'],
        'Endocrinology': ['MBBS, MD, DM (Endocrinology)', 'MBBS, DNB (Endocrinology)', 'MBBS, MRCP (Endocrinology)'],
        'Pulmonology': ['MBBS, MD (Pulmonology)', 'MBBS, DNB (Respiratory Medicine)', 'MBBS, MRCP (Respiratory)'],
        'Nephrology': ['MBBS, MD, DM (Nephrology)', 'MBBS, DNB (Nephrology)', 'MBBS, FRCP (Nephrology)'],
        'Urology': ['MBBS, MS, MCh (Urology)', 'MBBS, DNB (Urology)', 'MBBS, FRCS (Urology)'],
        'Oncology': ['MBBS, MD, DM (Oncology)', 'MBBS, DNB (Oncology)', 'MBBS, MRCP (Oncology)'],
        'Rheumatology': ['MBBS, MD, DM (Rheumatology)', 'MBBS, DNB (Rheumatology)', 'MBBS, FRCP (Rheumatology)'],
        'Dentistry': ['BDS', 'BDS, MDS (Orthodontics)', 'BDS, MDS (Endodontics)'],
        'Physiotherapy': ['BPT', 'BPT, MPT (Orthopedics)', 'BPT, MPT (Neurology)']
    }
    
    # Clear existing doctors
    Doctor.objects.all().delete()
    
    total_doctors = 0
    
    # Calculate how many doctors per consultation type and city
    # We want minimum 2 doctors for each city and consultation type
    doctors_per_city_type = 3
    
    created_doctors = []
    doctor_count = 1000  # Starting ID for doctors (DOC1000)
    
    # Create a dictionary to store doctors by city and consultation type
    doctors_by_city_and_type = {}
    
    # First pass: create at least 2 doctors for each city and consultation type combination
    for ct in consultation_types:
        for city in cities.keys():
            for _ in range(doctors_per_city_type):
                # Pick a random area from this city
                area = random.choice(cities[city])
                
                # Generate doctor details
                gender = random.choice(['Male', 'Female'])
                first_name = random.choice(first_names[gender])
                region = random.choice(list(surnames.keys()))
                last_name = random.choice(surnames[region])
                
                # Full name with title
                name = f"{first_name} {last_name}"
                
                # Generate sequential doctor code
                doctor_code = f"DOC{doctor_count}"
                doctor_count += 1
                
                # Random experience (2-35 years)
                experience = random.randint(2, 35)
                
                # Rating tends to be higher for more experienced doctors
                base_rating = min(4.0, 3.5 + (experience / 35))
                rating = round(min(5.0, random.uniform(base_rating - 0.5, base_rating + 0.9)), 1)
                
                # Reviews based on experience (more experienced doctors tend to have more reviews)
                reviews = random.randint(10, 50) + (experience * random.randint(5, 15))
                
                # Consultation fee based on experience, specialty, and city tier
                city_tier = {'Mumbai': 3, 'Delhi': 3, 'Bangalore': 3, 'Chennai': 2, 'Hyderabad': 2, 
                            'Kolkata': 2, 'Pune': 2, 'Jaipur': 1, 'Ahmedabad': 1, 'Lucknow': 1, 
                            'Chandigarh': 1, 'Indore': 1, 'Bhopal': 1, 'Nagpur': 1, 'Kochi': 1, 
                            'Guwahati': 1, 'Visakhapatnam': 1}
                            
                base_fee = 500
                specialty_factor = 1.5 if ct.requires_referral else 1.0
                emergency_factor = 1.3 if ct.emergency_specialty else 1.0
                experience_factor = 1 + (experience / 35)
                city_factor = city_tier.get(city, 1) * 0.5
                
                # Calculate fee and round to nearest 100
                raw_fee = base_fee * specialty_factor * emergency_factor * experience_factor * city_factor
                consultation_fee = round(raw_fee / 100) * 100
                
                # Select random qualification for this specialty
                qualification = random.choice(qualifications.get(ct.name, ['MBBS']))
                
                # Generate clinic name (some variations for realism)
                clinic_formats = [
                    f"{name} Clinic",
                    f"{last_name} {ct.name} Center",
                    f"{city} {ct.name} Clinic",
                    f"HealthPlus {ct.name}",
                    f"MediCare {ct.name} Specialists"
                ]
                clinic_name = f"{random.choice(clinic_formats)}, {area}"
                
                # Generate bio with more personalized details
                bio_templates = [
                    f"Experienced {ct.name} specialist with {experience} years of practice. {qualification}. Specializes in advanced diagnostic and treatment techniques.",
                    f"{qualification} with {experience} years of clinical experience in {ct.name}. Known for patient-centered care approach.",
                    f"Senior consultant in {ct.name} with {experience} years of experience. {qualification}. Special interest in minimally invasive procedures.",
                    f"Renowned {ct.name} expert with {experience} years of practice. {qualification}. Focuses on preventive care and holistic treatment methods.",
                    f"{qualification} practicing {ct.name} for {experience} years. Expertise in managing complex cases with compassionate care."
                ]
                bio = random.choice(bio_templates)
                
                # Create the doctor
                doctor = Doctor.objects.create(
                    doctor_code=doctor_code,
                    name=name,
                    consultation_type=ct,
                    rating=rating,
                    reviews=reviews,
                    experience=experience,
                    consultation_fee=consultation_fee,
                    clinic=clinic_name,
                    bio=bio,
                    city=city,
                    active=True,
                    photo_url=DEFAULT_PROFILE_ICON_BASE64 
                )
                
                created_doctors.append(doctor)
                total_doctors += 1
                
                # Store doctor in the dictionary by city and consultation type
                key = (city, ct.name)
                if key not in doctors_by_city_and_type:
                    doctors_by_city_and_type[key] = []
                doctors_by_city_and_type[key].append(doctor)
    
    # Second pass: Add additional doctors to reach the minimum target of 600
    target_remaining = max(0, 600 - total_doctors)
    if target_remaining > 0:
        # Distribute remaining doctors randomly
        for _ in range(target_remaining):
            # Pick a random city and consultation type
            city = random.choice(list(cities.keys()))
            ct = random.choice(consultation_types)
            area = random.choice(cities[city])
            
            # Generate doctor details (same as above)
            gender = random.choice(['Male', 'Female'])
            first_name = random.choice(first_names[gender])
            region = random.choice(list(surnames.keys()))
            last_name = random.choice(surnames[region])
            
            name = f"{first_name} {last_name}"
            doctor_code = f"DOC{doctor_count}"
            doctor_count += 1
            
            experience = random.randint(2, 35)
            base_rating = min(4.0, 3.5 + (experience / 35))
            rating = round(min(5.0, random.uniform(base_rating - 0.5, base_rating + 0.9)), 1)
            reviews = random.randint(10, 50) + (experience * random.randint(5, 15))
            
            city_tier = {'Mumbai': 3, 'Delhi': 3, 'Bangalore': 3, 'Chennai': 2, 'Hyderabad': 2, 
                        'Kolkata': 2, 'Pune': 2, 'Jaipur': 1, 'Ahmedabad': 1, 'Lucknow': 1, 
                        'Chandigarh': 1, 'Indore': 1, 'Bhopal': 1, 'Nagpur': 1, 'Kochi': 1, 
                        'Guwahati': 1, 'Visakhapatnam': 1}
                        
            base_fee = 500
            specialty_factor = 1.5 if ct.requires_referral else 1.0
            emergency_factor = 1.3 if ct.emergency_specialty else 1.0
            experience_factor = 1 + (experience / 35)
            city_factor = city_tier.get(city, 1) * 0.5
            
            raw_fee = base_fee * specialty_factor * emergency_factor * experience_factor * city_factor
            consultation_fee = round(raw_fee / 100) * 100
            
            qualification = random.choice(qualifications.get(ct.name, ['MBBS']))
            
            clinic_formats = [
                f"{name} Clinic",
                f"{last_name} {ct.name} Center",
                f"{city} {ct.name} Clinic",
                f"HealthPlus {ct.name}",
                f"MediCare {ct.name} Specialists"
            ]
            clinic_name = f"{random.choice(clinic_formats)}, {area}"
            
            bio_templates = [
                f"Experienced {ct.name} specialist with {experience} years of practice. {qualification}. Specializes in advanced diagnostic and treatment techniques.",
                f"{qualification} with {experience} years of clinical experience in {ct.name}. Known for patient-centered care approach.",
                f"Senior consultant in {ct.name} with {experience} years of experience. {qualification}. Special interest in minimally invasive procedures.",
                f"Renowned {ct.name} expert with {experience} years of practice. {qualification}. Focuses on preventive care and holistic treatment methods.",
                f"{qualification} practicing {ct.name} for {experience} years. Expertise in managing complex cases with compassionate care."
            ]
            bio = random.choice(bio_templates)
            
            doctor = Doctor.objects.create(
                doctor_code=doctor_code,
                name=name,
                consultation_type=ct,
                rating=rating,
                reviews=reviews,
                experience=experience,
                consultation_fee=consultation_fee,
                clinic=clinic_name,
                bio=bio,
                city=city,
                active=True,
                photo_url=DEFAULT_PROFILE_ICON_BASE64 
            )
            
            created_doctors.append(doctor)
            total_doctors += 1
            
            key = (city, ct.name)
            if key not in doctors_by_city_and_type:
                doctors_by_city_and_type[key] = []
            doctors_by_city_and_type[key].append(doctor)
            
            if total_doctors % 50 == 0:
                print(f'Created {total_doctors} doctors so far...')
    
    # Verify coverage
    print(f'Created {total_doctors} new doctors across {len(consultation_types)} specialties')
    
    # Check if each city has at least one doctor for each consultation type
    all_cities = set(cities.keys())
    all_consultation_types = set(ct.name for ct in consultation_types)
    
    missing_combinations = []
    
    for city in all_cities:
        for ct_name in all_consultation_types:
            key = (city, ct_name)
            if key not in doctors_by_city_and_type or not doctors_by_city_and_type[key]:
                missing_combinations.append(key)
    
    if missing_combinations:
        print(f"WARNING: Found {len(missing_combinations)} missing city-consultation type combinations:")
        for city, ct_name in missing_combinations:
            print(f"  - {city}: {ct_name}")
    else:
        print("SUCCESS: All cities have doctors for all consultation types!")
    
    return created_doctors, doctors_by_city_and_type



def create_time_slots(doctors, doctors_by_city_and_type):
    """Create exactly 3 time slots (morning, afternoon, evening) for each doctor"""
    
    # Delete existing time slots
    TimeSlot.objects.all().delete()
    
    # Define time slot periods for each doctor - FULL BLOCKS as requested
    time_slot_periods = {
        'morning': {
            'start_time': time(8, 0),   # 8:00 AM
            'end_time': time(11, 0)     # 11:00 AM (3 hour block)
        },
        'afternoon': {
            'start_time': time(13, 0),  # 1:00 PM
            'end_time': time(15, 0)     # 3:00 PM (2 hour block)
        },
        'evening': {
            'start_time': time(17, 0),  # 5:00 PM
            'end_time': time(20, 0)     # 8:00 PM (3 hour block)
        }
    }
    
    # Different time offsets based on city to ensure variation between doctors
    city_offsets = {
        'Mumbai': 0,
        'Delhi': 30,
        'Bangalore': 15,
        'Chennai': -15,
        'Hyderabad': 15,
        'Kolkata': -30,
        'Pune': 0,
        'Jaipur': 15,
        'Ahmedabad': 0,
        'Lucknow': 15,
        'Chandigarh': 0,
        'Indore': 15,
        'Bhopal': 0,
        'Nagpur': 15,
        'Kochi': -15,
        'Guwahati': -30,
        'Visakhapatnam': 0
    }
    
    count = 0
    print("Creating time slots for each doctor...")
    
    # For each doctor, create exactly 3 time slots (morning, afternoon, evening)
    for doctor in doctors:
        city = doctor.city
        consultation_type = doctor.consultation_type.name
        offset_minutes = city_offsets.get(city, 0)
        
        # Add some individual variation based on doctor ID to stagger slots
        doctor_id_num = int(doctor.doctor_code[3:])  # Extract numeric part from DOC1000
        individual_offset = (doctor_id_num % 4) * 15  # 0, 15, 30, or 45 minutes
        
        # Create one slot for each period
        for period, time_info in time_slot_periods.items():
            # Apply city offset and individual doctor offset to start time
            base_start_minutes = time_info['start_time'].hour * 60 + time_info['start_time'].minute
            total_offset = (offset_minutes + individual_offset) % 60  # Keep offset within reasonable bounds
            
            adjusted_start_minutes = base_start_minutes + total_offset
            start_hour = adjusted_start_minutes // 60
            start_minute = adjusted_start_minutes % 60
            slot_start = time(start_hour, start_minute)
            
            # Apply same offset to end time
            base_end_minutes = time_info['end_time'].hour * 60 + time_info['end_time'].minute
            adjusted_end_minutes = base_end_minutes + total_offset
            end_hour = adjusted_end_minutes // 60
            end_minute = adjusted_end_minutes % 60
            slot_end = time(end_hour, end_minute)
            
            # Create time slot with the FULL TIME BLOCK (not 30-minute appointments)
            TimeSlot.objects.create(
                doctor=doctor,
                start_time=slot_start,
                end_time=slot_end,
                is_available=True,
                category=period  # Store which period this slot belongs to
            )
            
            count += 1
            
            if count % 300 == 0:
                print(f"Created {count} time slots so far...")
    
    print(f'Created {count} time slots total - exactly 3 per doctor')
    
    
    # Example of how to filter time slots by city and consultation type
    print("\nExample: Filtering time slots by city and consultation type")
    for (city, consultation_type), doctors_list in doctors_by_city_and_type.items():
        doctor_count = len(doctors_list)
        if doctor_count >= 5:  # Just pick a few examples with reasonable number of doctors
            slot_count = TimeSlot.objects.filter(doctor__in=doctors_list).count()
            print(f"City: {city}, Consultation: {consultation_type}")
            print(f"  - Doctors: {doctor_count}")
            print(f"  - Time slots: {slot_count} (should be {doctor_count * 3})")
            
            # List the first 5 slots as examples
            example_slots = TimeSlot.objects.filter(doctor__in=doctors_list)[:5]
            print("  - Sample slots:")
            for slot in example_slots:
                print(f"    - Dr. {slot.doctor.name} ({slot.category}): {slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}")
            print("")
            
            # Only show a few examples
            if city == "Mumbai" or city == "Delhi":
                break
    
    print(f'Created {count} time slots - exactly 3 per doctor')

# Run if script is executed directly
if __name__ == "__main__":
    # Create consultation types first
    consultation_types = create_consultation_types()
    
    # Create doctors based on consultation types
    doctors, doctors_by_city_and_type = create_doctors(consultation_types)
    
    # Create time slots for doctors
    total_slots = create_time_slots(doctors, doctors_by_city_and_type)
    
    print(f"\nTotal data created:")
    print(f"- {len(consultation_types)} consultation types")
    print(f"- {len(doctors)} doctors")
    print(f"- {total_slots} time slots")