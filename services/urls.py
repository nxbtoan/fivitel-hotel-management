from django.urls import path
from . import views

urlpatterns = [
    # URL cho trang hiển thị dịch vụ công khai
    path('', views.PublicServiceListView.as_view(), name='public_service_list'),
    # URL cho trang chi tiết dịch vụ
    path('<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),

    # URL cho trang dashboard quản lý dịch vụ
    path('dashboard/', views.ServiceListView.as_view(), name='service_list'),
    # URL cho tạo mới dịch vụ
    path('dashboard/new/', views.service_create_view, name='service_create'),
    # URL cho chỉnh sửa dịch vụ
    path('dashboard/<int:pk>/edit/', views.service_update_view, name='service_update'),
    # URL cho xóa dịch vụ
    path('dashboard/<int:pk>/delete/', views.ServiceDeleteView.as_view(), name='service_delete'),


    # URL cho quản lý loại dịch vụ
    path('dashboard/categories/', views.ServiceCategoryListView.as_view(), name='service_category_list'),
    # URL cho tạo mới loại dịch vụ
    path('dashboard/categories/new/', views.ServiceCategoryCreateView.as_view(), name='service_category_create'),
    # URL cho chỉnh sửa loại dịch vụ
    path('dashboard/categories/<int:pk>/edit/', views.ServiceCategoryUpdateView.as_view(), name='service_category_update'),
    # URL cho xóa loại dịch vụ
    path('dashboard/categories/<int:pk>/delete/', views.ServiceCategoryDeleteView.as_view(), name='service_category_delete'),
]