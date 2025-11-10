from django.urls import path
from . import views

urlpatterns = [
    # --- URLS CHO KHÁCH HÀNG ---
    path('request/', views.consultation_request_view, name='consultation_request'),
    path('complaint/', views.complaint_submission_view, name='submit_complaint'),

    path('my-requests/', views.my_requests_view, name='my_requests'),
    path('my-complaints/', views.my_complaints_view, name='my_complaints'),
    # path('my-tickets/', views.my_tickets_view, name='my_tickets'),
    path('my-tickets/<int:pk>/', views.customer_ticket_detail_view, name='customer_ticket_detail'),

    # --- URLS CHO NHÂN VIÊN ---
    path('dashboard/requests/', views.manage_requests_view, name='manage_requests'),
    
    # URL cho trang quản lý khiếu nại
    path('dashboard/complaints/', views.manage_complaints_view, name='manage_complaints'),
    path('dashboard/ticket/<int:pk>/', views.ticket_detail_view, name='ticket_detail'),
    path('dashboard/ticket/<int:pk>/resolve/', views.resolve_ticket_view, name='resolve_ticket'),
    path('dashboard/ticket/<int:pk>/assign/', views.assign_ticket_view, name='assign_ticket'),
    
    # URL cho trang hỗ trợ qua Zalo
    path('support/zalo/', views.zalo_support_view, name='zalo_support'),
]