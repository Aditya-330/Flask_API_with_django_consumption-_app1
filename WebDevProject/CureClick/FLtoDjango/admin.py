from django.contrib import admin
from .models import Doctor, TimeSlot, ConsultationType, UserBooking, UserProfile

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'consultation_type', 'rating', 'experience', 'consultation_fee', 'doctor_code', 'clinic', 'city', 'active')
    search_fields = ('name', 'doctor_code', 'active')

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'formatted_start_time', 'formatted_end_time', 'category', 'is_available')
    list_filter = ('category', 'is_available', 'doctor')

    def formatted_start_time(self, obj):
        return obj.start_time.strftime('%I:%M %p')
    formatted_start_time.short_description = 'Start Time'

    def formatted_end_time(self, obj):
        return obj.end_time.strftime('%I:%M %p')
    formatted_end_time.short_description = 'End Time'


@admin.register(ConsultationType)
class ConsultationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'requires_referral', 'emergency_specialty')
    search_fields = ('name', 'common_symptoms', 'description')
    list_filter = ('requires_referral', 'emergency_specialty')
    

@admin.register(UserBooking)
class UserBookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'consultation_type', 'doctor', 'selected_date', 'selected_time', 'consultation_fee', 'platform_fee', 
                    'total_amount', 'status')
    search_fields = ('full_name', 'doctor', 'selected_date', 'selected_time', 'consultation_type', )
    list_filter = ('consultation_fee', 'full_name', 'doctor', 'consultation_type')
    
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'age', 'primary_phone', 'gender', 'blood_type', 'date_of_birth', 
                    'address_line1', 'city', 'state', 'pin_code')
    search_fields = ('full_name', 'age', 'email', 'primary_phone', 'city' )
    list_filter = ('full_name', 'email', 'city', 'gender')