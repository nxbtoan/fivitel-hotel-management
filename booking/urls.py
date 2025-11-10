from django.urls import path, include
from . import views

urlpatterns = [
    # --- URLS CHUNG & CHO KHÁCH HÀNG ---
    path('', views.room_type_list_view, name='room_type_list_view'),
    path('<int:room_type_id>/', views.room_class_list_view, name='room_class_list'),
    path('options/<int:room_class_id>/', views.booking_options_view, name='booking_options'),
    path('checkout/', views.checkout_view, name='checkout'),

    # --- URLS DÀNH CHO NGƯỜI DÙNG ĐÃ ĐĂNG NHẬP ---
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('my-bookings/<int:pk>/', views.booking_detail_view, name='booking_detail'),
    path('my-bookings/<int:pk>/cancel/', views.cancel_booking_view, name='cancel_booking'),
    path('my-bookings/<int:pk>/edit/', views.edit_booking_view, name='edit_booking'),
    path('payment/<int:booking_pk>/', views.payment_guidance_view, name='payment_guidance'),

    # --- URLS DÀNH RIÊNG CHO KHÁCH VÃNG LAI (SỬ DỤNG UUID) ---
    path('guest/booking/<uuid:booking_code>/', views.guest_booking_detail_view, name='guest_booking_detail'),
    path('guest/payment/<uuid:booking_code>/', views.guest_payment_guidance_view, name='guest_payment_guidance'),

    # --- BAO GỒM TẤT CẢ CÁC URL CỦA DASHBOARD ---
    path('dashboard/', include('booking.dashboard_urls')),

    path('dashboard/checkin-booking/<int:pk>/', views.check_in_booking_view, name='check_in_booking'),
]