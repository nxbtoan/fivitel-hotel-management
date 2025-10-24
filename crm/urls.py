from django.urls import path
from . import views

urlpatterns = [
    # --- URLS CHO KHÁCH HÀNG ---
    path('request/', views.consultation_request_view, name='consultation_request'),
    path('complaint/', views.complaint_submission_view, name='submit_complaint'),
    path('my-tickets/', views.my_tickets_view, name='my_tickets'),
    path('my-tickets/<int:pk>/', views.customer_ticket_detail_view, name='customer_ticket_detail'),

    # --- URLS CHO NHÂN VIÊN ---
    # URL cho trang quản lý yêu cầu (tư vấn, hỗ trợ...)
    path('dashboard/requests/', views.manage_requests_view, name='manage_requests'),
    
    # URL cho trang quản lý khiếu nại
    path('dashboard/complaints/', views.manage_complaints_view, name='manage_complaints'),

    # URL cho trang chi tiết yêu cầu và khiếu nại
    path('dashboard/ticket/<int:pk>/', views.ticket_detail_view, name='ticket_detail'),
    path('dashboard/ticket/<int:pk>/resolve/', views.resolve_ticket_view, name='resolve_ticket'),
]