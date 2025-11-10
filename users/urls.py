from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Đăng ký người dùng mới
    path('register/', views.register, name='register'),

    # Đăng nhập người dùng
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),

    # Đăng xuất người dùng
    path('logout/', views.logout_view, name='logout'),

    # Trang chủ sau khi đăng nhập
    path('redirect/', views.login_redirect_view, name='login_redirect'),

    # Cập nhật hồ sơ người dùng
    path('profile/', views.profile_update_view, name='profile_update'),

    # --- QUY TRÌNH ĐỔI MẬT KHẨU ---
    # Bước 1: Yêu cầu mã
    path('password-reset/request/', views.request_password_reset_code, name='password_reset_request'),
    # Bước 2: Xác thực mã
    path('password-reset/verify/', views.verify_password_reset_code, name='password_reset_verify'),
    # Bước 3: Đặt mật khẩu mới
    path('password-reset/set-new/', views.set_new_password, name='password_reset_set_new'),

    # --- CÁC URL MỚI CHO QUẢN LÝ NHÂN SỰ ---
    path('dashboard/users/', views.UserListView.as_view(), name='user_list_admin'),
    path('dashboard/users/new/', views.UserCreateView.as_view(), name='user_create'),
    path('dashboard/users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_update'),
    path('<int:pk>/toggle-active/', views.toggle_user_active_view, name='user_toggle_active'),
]