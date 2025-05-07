from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Medicine, Category, Cart, CartItem, Order, OrderItem, PromoCode, UserPromoUsage
from .forms import CheckoutForm, PrescriptionForm, PromoCodeForm, MedicineForm
# from accounts.models import UserProfile

from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

@staff_member_required
def order_list_view(request):
    orders_queryset = Order.objects.all().order_by('-created_at')
    
    # Apply filters
    order_id = request.GET.get('order_id')
    customer = request.GET.get('customer')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if order_id:
        orders_queryset = orders_queryset.filter(id=order_id)
    
    if customer:
        orders_queryset = orders_queryset.filter(
            Q(full_name__icontains=customer) | 
            Q(email__icontains=customer)
        )
    
    if status:
        orders_queryset = orders_queryset.filter(status=status)
    
    if date_from:
        orders_queryset = orders_queryset.filter(created_at__date__gte=date_from)
    
    if date_to:
        orders_queryset = orders_queryset.filter(created_at__date__lte=date_to)
    
    # Get the total count before pagination
    total_orders = orders_queryset.count()
    
    # Count orders by status
    pending_count = Order.objects.filter(status='pending').count()
    processing_count = Order.objects.filter(status='processing').count()
    shipped_count = Order.objects.filter(status='shipped').count()
    delivered_count = Order.objects.filter(status='delivered').count()
    cancelled_count = Order.objects.filter(status='cancelled').count()
    
    # Pagination
    paginator = Paginator(orders_queryset, 10)  # Show 10 orders per page
    page = request.GET.get('page')
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        orders = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        orders = paginator.page(paginator.num_pages)
    
    context = {
        'orders': orders,
        'total_orders': total_orders,  # Add total orders count to context
        'pending_count': pending_count,
        'processing_count': processing_count,
        'shipped_count': shipped_count,
        'delivered_count': delivered_count,
        'cancelled_count': cancelled_count,
    }
    return render(request, 'pharmacy/order_list.html', context)

@staff_member_required
def order_management_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES).keys():
            order.status = new_status
            order.save()
            messages.success(request, f"Order status updated to {order.get_status_display()}.")
            return redirect('pharmacy:order_management', order_id=order.id)
    
    context = {
        'order': order,
    }
    return render(request, 'pharmacy/order_management.html', context)

def home_view(request):
    featured_medicines = Medicine.objects.all().order_by('-created_at')[:6]
    categories = Category.objects.all()
    
    context = {
        'featured_medicines': featured_medicines,
        'categories': categories,
    }
    return render(request, 'pharmacy/home.html', context)

def medicine_list_view(request):
    medicines = Medicine.objects.all()
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        medicines = medicines.filter(category_id=category_id)
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    categories = Category.objects.all()
    
    context = {
        'medicines': medicines,
        'categories': categories,
        'current_category': category_id,
        'query': query,
    }
    return render(request, 'pharmacy/medicine_list.html', context)

def medicine_detail_view(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    related_medicines = Medicine.objects.filter(category=medicine.category).exclude(pk=pk)[:4]
    
    context = {
        'medicine': medicine,
        'related_medicines': related_medicines,
    }
    return render(request, 'pharmacy/medicine_detail.html', context)

@login_required
def add_to_cart(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)
    
    # Check if item requires prescription
    if medicine.requires_prescription:
        messages.info(request, "This medicine requires a prescription. You'll need to upload it during checkout.")
    
    # Get or create user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Check if item already in cart
    try:
        cart_item = CartItem.objects.get(cart=cart, medicine=medicine)
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"Added another {medicine.name} to your cart.")
    except CartItem.DoesNotExist:
        CartItem.objects.create(cart=cart, medicine=medicine)
        messages.success(request, f"{medicine.name} added to your cart.")
    
    return redirect('pharmacy:cart')

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from your cart.")
    return redirect('pharmacy:cart')

@login_required
def update_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0 and quantity <= cart_item.medicine.stock:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, "Cart updated successfully.")
    else:
        messages.error(request, f"Invalid quantity. Maximum available: {cart_item.medicine.stock}")
    
    return redirect('pharmacy:cart')

@login_required
def cart_view(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
    except Cart.DoesNotExist:
        cart = None
        cart_items = []
    
    # Handle promo code application
    promo_form = PromoCodeForm()
    promo_error = None
    
    if request.method == 'POST' and cart:
        promo_form = PromoCodeForm(request.POST)
        if promo_form.is_valid():
            promo_code = promo_form.cleaned_data['code']
            try:
                promo = PromoCode.objects.get(code=promo_code, is_active=True)
                
                # Check if promo code is valid
                if not promo.is_valid():
                    promo_error = "This promo code has expired."
                    messages.error(request, promo_error)
                else:
                    # Check if user has usage limit
                    user_usage, created = UserPromoUsage.objects.get_or_create(user=request.user, promo=promo)
                    if user_usage.usage_count >= promo.usage_limit:
                        promo_error = "You've already used this promo code the maximum number of times."
                        messages.error(request, promo_error)
                    else:
                        # Check minimum order value
                        if cart.get_total_price() < promo.min_order_value:
                            promo_error = f"Your order total must be at least Rs.{promo.min_order_value} to use this code."
                            messages.error(request, promo_error)
                        else:
                            cart.promo_code = promo
                            cart.save()
                            
                            # Increment usage count
                            user_usage.usage_count += 1
                            user_usage.save()
                            
                            messages.success(request, f"Promo code '{promo_code}' applied successfully!")
                
            except PromoCode.DoesNotExist:
                promo_error = "Invalid promo code."
                messages.error(request, promo_error)
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'promo_form': promo_form,
        'promo_error': promo_error,
    }
    return render(request, 'pharmacy/cart.html', context)

@login_required
def remove_promo(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart.promo_code = None
        cart.save()
        messages.success(request, "Promo code removed.")
    except Cart.DoesNotExist:
        pass
    
    return redirect('pharmacy:cart')

@login_required
def checkout_view(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
        
        # Check if cart is empty
        if not cart_items.exists():
            messages.error(request, "Your cart is empty. Add some items before checkout.")
            return redirect('pharmacy:cart')
            
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty. Add some items before checkout.")
        return redirect('pharmacy:medicine_list')
    
    # Check if any item requires prescription
    requires_prescription = any(item.medicine.requires_prescription for item in cart_items)
    prescription_form = PrescriptionForm() if requires_prescription else None
    
    # Pre-populate checkout form with user profile data if available
    initial_data = {}
    try:
        profile = request.user.profile
        initial_data = {
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'email': request.user.email,
            'phone_number': profile.phone_number,
            'address': profile.address,
            'city': profile.city,
            'state': profile.state,
            'zipcode': profile.zipcode,
        }
    except:
    # except UserProfile.DoesNotExist:
        pass
    
    checkout_form = CheckoutForm(initial=initial_data)
    
    if request.method == 'POST':
        checkout_form = CheckoutForm(request.POST)
        prescription_form = PrescriptionForm(request.POST, request.FILES) if requires_prescription else None
        
        # Validate forms
        forms_valid = checkout_form.is_valid()
        if requires_prescription:
            forms_valid = forms_valid and prescription_form.is_valid()
        
        if forms_valid:
            # Create order
            order = checkout_form.save(commit=False)
            order.user = request.user
            order.total_price = cart.get_total_price()
            order.discount_amount = cart.get_discount_amount()
            order.final_price = cart.get_final_price()
            order.promo_code = cart.promo_code
            order.save()
            
            # Save order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    medicine=cart_item.medicine,
                    price=cart_item.medicine.price,
                    quantity=cart_item.quantity
                )
                
                # Update stock
                medicine = cart_item.medicine
                medicine.stock -= cart_item.quantity
                medicine.save()
            
            # Save prescription if needed
            if requires_prescription and prescription_form:
                prescription = prescription_form.save(commit=False)
                prescription.user = request.user
                prescription.order = order
                prescription.save()
            
            # Update promo code usage if applicable
            if cart.promo_code:
                user_usage, created = UserPromoUsage.objects.get_or_create(
                    user=request.user, 
                    promo=cart.promo_code
                )
                user_usage.usage_count += 1
                user_usage.save()
            
            # Clear cart
            cart.items.all().delete()
            cart.promo_code = None
            cart.save()
            
            messages.success(request, "Order placed successfully! Thank you for shopping with us.")
            return redirect('pharmacy:order_confirmation', order_id=order.id)
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'checkout_form': checkout_form,
        'prescription_form': prescription_form,
        'requires_prescription': requires_prescription,
    }
    return render(request, 'pharmacy/checkout.html', context)

@login_required
def order_confirmation_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'pharmacy/order_confirmation.html', context)

@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'pharmacy/orders.html', context)

@staff_member_required
def medicine_management_view(request):
    medicines = Medicine.objects.all().order_by('-updated_at')
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Category filter
    category_id = request.GET.get('category')
    if category_id:
        medicines = medicines.filter(category_id=category_id)
        
    categories = Category.objects.all()
    
    context = {
        'medicines': medicines,
        'categories': categories,
        'current_category': category_id,
        'query': query
    }
    return render(request, 'pharmacy/medicine_management.html', context)

@staff_member_required
def add_medicine_view(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Medicine added successfully!")
            return redirect('pharmacy:medicine_management')
    else:
        form = MedicineForm()
    
    context = {
        'form': form,
        'title': 'Add New Medicine'
    }
    return render(request, 'pharmacy/medicine_form.html', context)

@staff_member_required
def edit_medicine_view(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    
    if request.method == 'POST':
        form = MedicineForm(request.POST, request.FILES, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, f"{medicine.name} updated successfully!")
            return redirect('pharmacy:medicine_management')
    else:
        form = MedicineForm(instance=medicine)
    
    context = {
        'form': form,
        'medicine': medicine,
        'title': f'Edit {medicine.name}'
    }
    return render(request, 'pharmacy/medicine_form.html', context)

@staff_member_required
def delete_medicine_view(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    
    if request.method == 'POST':
        name = medicine.name
        medicine.delete()
        messages.success(request, f"{name} deleted successfully!")
        return redirect('pharmacy:medicine_management')
    
    context = {
        'medicine': medicine
    }
    return render(request, 'pharmacy/medicine_confirm_delete.html', context)
