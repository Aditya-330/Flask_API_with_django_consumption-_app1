from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# models.py (updated UserProfile model)
# models.py (updated UserProfile model)
class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )
    
    BLOOD_TYPE_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('unknown', 'Unknown'),
    )
    
      
    RELATIONSHIP_CHOICES = (
        ('parent', 'Parent'),
        ('spouse', 'Spouse'),
        ('sibling', 'Sibling'),
        ('relative', 'Relative'),
        ('friend', 'Friend'),
        ('other', 'Other'),
    )
    
    id = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    blood_type = models.CharField(max_length=10, choices=BLOOD_TYPE_CHOICES, blank=True)
    primary_phone = models.CharField(max_length=10, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pin_code = models.CharField(max_length=20, blank=True)
    profile_image = models.URLField(max_length=500, blank=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=10, blank=True)
    emergency_contact_email = models.EmailField(max_length=255, blank=True)
    emergency_contact_relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, blank=True)
    
    def _str_(self):
        return f"{self.full_name}'s Profile"


class ConsultationType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    common_symptoms = models.TextField(blank=True)
    requires_referral = models.BooleanField(default=False)
    emergency_specialty = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
# In models.py - fix duplicate fields in Doctor model
class Doctor(models.Model):
    name = models.CharField(max_length=100)
    consultation_type = models.ForeignKey(ConsultationType, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    reviews = models.IntegerField(null=True, blank=True)  # Remove duplicate
    experience = models.IntegerField(null=True, blank=True)  # Remove duplicate
    consultation_fee = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)  # Use consistent type
    doctor_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    clinic = models.CharField(max_length=100, null=True, blank=True)
    bio = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    active = models.BooleanField(default=True)
    photo_url = models.URLField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"Dr. {self.name} ({self.doctor_code or 'No Code'})"
    


class TimeSlot(models.Model):
    TIME_CATEGORIES = (
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
    )
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    category = models.CharField(max_length=10, choices=TIME_CATEGORIES)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        start = self.start_time.strftime('%I:%M %p')
        end = self.end_time.strftime('%I:%M %p')
        return f"{self.doctor.name} — {start} to {end} ({self.category.capitalize()})"


class UserBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    consultation_type = models.ForeignKey(ConsultationType, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    selected_date = models.DateField()
    selected_time = models.TimeField()  # Ensure the TimeSlot is properly referenced here
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)  # Use correct type for fee
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"Booking for {self.user.username} - {self.consultation_type.name} with Dr. {self.doctor.name} on {self.selected_date}"
