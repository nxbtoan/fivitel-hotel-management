from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .forms import CustomerRegistrationForm, AdminUserCreationForm, UserUpdateForm 
from .models import CustomUser

def register(request):
    """View xử lý trang đăng ký công khai cho khách hàng."""
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Tài khoản {username} đã được tạo thành công! Vui lòng đăng nhập.')
            return redirect('login')
    else:
        form = CustomerRegistrationForm()
        
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

# --- Các view quản lý nhân sự trong dashboard ---

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
    
@login_required
def profile_update_view(request):
    """
    Hiển thị và xử lý form cập nhật thông tin cá nhân.
    - GET: Hiển thị form với thông tin hiện tại của người dùng.
    - POST: Lưu lại các thay đổi và hiển thị thông báo thành công.
    """
    if request.method == 'POST':
        # Khởi tạo form với dữ liệu người dùng gửi lên và instance là user hiện tại
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thông tin tài khoản của bạn đã được cập nhật thành công!')
            return redirect('profile_update') # Tải lại chính trang này
    else:
        # Khi mới truy cập, hiển thị form với thông tin hiện tại của user
        form = UserUpdateForm(instance=request.user)

    context = {
        'form': form
    }
    return render(request, 'registration/profile_update.html', context)

# Hàm kiểm tra user có phải là Admin không
def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin để đảm bảo chỉ Admin mới có thể truy cập."""
    def test_func(self):
        return is_admin(self.request.user)
    
class UserListView(AdminRequiredMixin, ListView):
    """View hiển thị danh sách tất cả các tài khoản người dùng."""
    model = CustomUser
    template_name = 'users/dashboard_user_list.html'
    context_object_name = 'users'
    queryset = CustomUser.objects.order_by('username') # Sắp xếp theo username

class UserCreateView(AdminRequiredMixin, CreateView):
    """View hiển thị form để tạo mới một người dùng (nhân viên)."""
    model = CustomUser
    form_class = AdminUserCreationForm # Sử dụng form tùy chỉnh
    template_name = 'users/dashboard_user_form.html'
    success_url = reverse_lazy('user_list_admin')

class UserUpdateView(AdminRequiredMixin, UpdateView):
    """View hiển thị form để chỉnh sửa thông tin và vai trò của người dùng."""
    model = CustomUser
    template_name = 'users/dashboard_user_form.html'
    fields = ['username', 'full_name', 'email', 'role', 'is_staff', 'is_active'] # Các trường Admin được phép sửa
    success_url = reverse_lazy('user_list_admin')

class UserDeleteView(AdminRequiredMixin, DeleteView):
    """View xử lý việc xóa một người dùng."""
    model = CustomUser
    success_url = reverse_lazy('user_list_admin')