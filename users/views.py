from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from .forms import CustomUserCreationForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Tài khoản {username} đã được tạo thành công! Vui lòng đăng nhập.')
            return redirect('login') # Chuyển hướng đến trang đăng nhập sau khi thành công
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'registration/register.html', {'form': form})

@login_required
def logout_view(request):
    """
    Xử lý việc đăng xuất người dùng và chuyển hướng về trang đăng nhập.
    """
    logout(request)
    messages.success(request, "Bạn đã đăng xuất thành công.")
    return redirect('login')

@login_required
def homepage(request):
    return render(request, 'homepage.html')

def is_staff_member(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_staff_member)
def staff_dashboard_view(request):
    """
    Hiển thị trang tổng quan (dashboard) dành riêng cho các nhân viên.
    View này yêu cầu người dùng phải đăng nhập và có cờ is_staff = True.
    """
    context = {
        'user': request.user
    }
    return render(request, 'dashboard.html', context)

@login_required
def login_redirect_view(request):
    """
    View trung gian sau khi đăng nhập.
    Kiểm tra vai trò (role) của người dùng và chuyển hướng (redirect) họ
    đến trang chủ phù hợp (trang của khách hoặc trang dashboard của nhân viên).
    """
    # Kiểm tra xem người dùng có phải là nhân viên hay không
    if request.user.is_staff:
        # Nếu là nhân viên, chuyển đến trang dashboard
        return redirect('staff_dashboard')
    else:
        # Nếu là khách hàng, chuyển đến trang chủ thông thường
        return redirect('homepage')