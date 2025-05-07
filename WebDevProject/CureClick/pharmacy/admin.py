from django.contrib import admin
from .models import Category, Medicine, PromoCode, Cart, CartItem, Order, OrderItem, Prescription, UserPromoUsage

class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'requires_prescription')
    list_filter = ('category', 'requires_prescription')
    search_fields = ('name', 'description')

class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'valid_from', 'valid_to', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'description')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'status', 'final_price', 'created_at')
    list_filter = ('status',)
    search_fields = ('full_name', 'email')
    inlines = [OrderItemInline]

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
    inlines = [CartItemInline]

class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'order', 'status', 'upload_date')
    list_filter = ('status',)

class UserPromoUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'promo', 'usage_count', 'last_used')

admin.site.register(Category)
admin.site.register(Medicine, MedicineAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Prescription, PrescriptionAdmin)
admin.site.register(UserPromoUsage, UserPromoUsageAdmin)