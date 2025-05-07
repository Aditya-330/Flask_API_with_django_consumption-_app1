from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static



app_name = 'pharmacy'

urlpatterns = [
    # path('', views.home_view, name='home'),
    path('medicines/', views.medicine_list_view, name='medicine_list'),
    path('medicine/<int:pk>/', views.medicine_detail_view, name='medicine_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:medicine_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-item/<int:cart_item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-promo/', views.remove_promo, name='remove_promo'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation_view, name='order_confirmation'),
    path('orders/', views.orders_view, name='orders'),
    path('staff/orders/', views.order_list_view, name='order_list'),
    path('staff/orders/<int:order_id>/', views.order_management_view, name='order_management'),
    
    # Medicine management
    path('staff/medicines/', views.medicine_management_view, name='medicine_management'),
    path('staff/medicines/add/', views.add_medicine_view, name='add_medicine'),
    path('staff/medicines/edit/<int:pk>/', views.edit_medicine_view, name='edit_medicine'),
    path('staff/medicines/delete/<int:pk>/', views.delete_medicine_view, name='delete_medicine'),
]   
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
