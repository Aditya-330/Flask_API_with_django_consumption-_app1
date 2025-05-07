from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('', views.home_view, name='index'),
    path('whyAb/', views.why_view, name='whyAb'),
    path('docDash/', views.doc_dashboard_view, name= 'docDash'),
    path('book/', views.book_view, name='book'),
    path('confirm/', views.confirm_view, name='confirm'),
    path('reschedule/<int:booking_id>/', views.reschedule_appointment, name='reschedule'),
    path('myApp/', views.myApp_view, name='myApp'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout')
]