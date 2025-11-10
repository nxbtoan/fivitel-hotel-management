from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .forms import CustomerRegistrationForm, AdminUserCreationForm, UserUpdateForm, PasswordResetEmailForm, PasswordResetCodeForm, SetNewPasswordForm
from .models import CustomUser
import random

# ==============================================================================
# PHẦN 1: VIEWS ĐĂNG KÝ, ĐĂNG NHẬP VÀ XÁC THỰC KHI QUÊN MẬT KHẨU PHÍA NGƯỜI DÙNG
# ==============================================================================
def register(request):
    """
    View xử lý trang đăng ký công khai cho khách hàng.
    """
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

# --- Quy trình Đặt lại Mật khẩu bằng OTP ---
def request_password_reset_code(request):
    """
    Bước 1: Nhận email, tạo mã OTP, lưu mã vào session, và gửi email.
    """
    if request.method == 'POST':
        form = PasswordResetEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = CustomUser.objects.get(email__iexact=email)
            
            # 1. Tạo mã OTP 6 chữ số
            code = str(random.randint(100000, 999999))
            
            # 2. Lưu mã và user_id vào session để kiểm tra ở bước sau
            request.session['reset_otp_code'] = code
            request.session['reset_otp_user_id'] = user.id
            # Đặt thời gian hết hạn (ví dụ: 10 phút)
            request.session.set_expiry(600) 
            
            # 3. Gửi email
            try:
                send_mail(
                    subject='[Fivitel] Mã xác thực đặt lại mật khẩu của bạn',
                    message=f'Mã xác thực của bạn là: {code}\n\nMã này sẽ hết hạn trong 10 phút.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                )
                messages.success(request, "Đã gửi mã xác thực đến email của bạn. Vui lòng kiểm tra.")
            except Exception as e:
                messages.error(request, f"Lỗi khi gửi email: {e}")
                return redirect('password_reset_request')
                
            # 4. Chuyển hướng đến trang xác thực mã
            return redirect('password_reset_verify')
    else:
        form = PasswordResetEmailForm()
    
    return render(request, 'registration/password_reset_request.html', {'form': form})


def verify_password_reset_code(request):
    """
    Bước 2: Nhận mã OTP người dùng nhập, so sánh với mã trong session.
    """
    if 'reset_otp_user_id' not in request.session:
        messages.error(request, "Phiên đặt lại mật khẩu đã hết hạn hoặc không hợp lệ. Vui lòng thử lại.")
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = PasswordResetCodeForm(request.POST)
        if form.is_valid():
            submitted_code = form.cleaned_data['code']
            stored_code = request.session.get('reset_otp_code')
            
            if submitted_code == stored_code:
                # Xác thực thành công, đánh dấu trong session và chuyển đến bước 3
                request.session['reset_otp_verified'] = True
                return redirect('password_reset_set_new')
            else:
                messages.error(request, "Mã xác thực không chính xác.")
    else:
        form = PasswordResetCodeForm()
        
    return render(request, 'registration/password_reset_verify.html', {'form': form})

def set_new_password(request):
    """
    Bước 3: Người dùng đã xác thực, cho phép đặt mật khẩu mới.
    """
    user_id = request.session.get('reset_otp_user_id')
    is_verified = request.session.get('reset_otp_verified')
    
    # Kiểm tra xem người dùng đã đi đúng 2 bước trước chưa
    if not user_id or not is_verified:
        messages.error(request, "Bạn không có quyền truy cập trang này. Vui lòng thử lại.")
        return redirect('password_reset_request')
        
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "Tài khoản không còn tồn tại.")
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            # Đặt mật khẩu mới cho user
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            
            # Xóa toàn bộ session sau khi hoàn tất
            request.session.flush()
            
            messages.success(request, "Đổi mật khẩu thành công! Vui lòng đăng nhập.")
            return redirect('login')
    else:
        form = SetNewPasswordForm()
        
    return render(request, 'registration/password_reset_set_new.html', {'form': form})

# ==============================================================================
# PHẦN 2: VIEWS CỦA NGƯỜI DÙNG (KHÁCH HÀNG & CHUNG)
# ==============================================================================
@login_required
def homepage(request):
    return render(request, 'homepage.html')

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

# ==============================================================================
# PHẦN 3: HÀM HỖ TRỢ PHÂN QUYỀN (HELPERS & MIXINS)
# ==============================================================================
def is_staff_member(user):
    return user.is_authenticated and user.role in [
        CustomUser.Role.RECEPTION, 
        CustomUser.Role.SUPPORT, 
        CustomUser.Role.ADMIN
    ]

# Hàm kiểm tra user có phải là Admin không
def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin để đảm bảo chỉ Nhân viên mới có thể truy cập."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['STAFF', 'ADMIN']
class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin để đảm bảo chỉ Admin mới có thể truy cập."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'ADMIN'
    
# ==============================================================================
# PHẦN 4: VIEWS QUẢN LÝ DASHBOARD (STAFF & ADMIN)
# ==============================================================================
@login_required
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

class UserListView(AdminRequiredMixin, ListView):
    """
    View hiển thị danh sách tất cả các tài khoản người dùng.
    """
    model = CustomUser
    template_name = 'users/dashboard_user_list.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        return CustomUser.objects.order_by('username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. Lấy filter
        role_filter = self.request.GET.get('role')

        # 2. Tạo danh sách NHÂN VIÊN
        staff_users = CustomUser.objects.filter(is_staff=True).order_by('role', 'username')

        # 3. Áp dụng filter (nếu có) CHỈ cho danh sách nhân viên
        valid_roles = [CustomUser.Role.RECEPTION, CustomUser.Role.SUPPORT, CustomUser.Role.ADMIN]
        if role_filter in valid_roles:
            staff_users = staff_users.filter(role=role_filter)
        
        # 4. Tạo danh sách KHÁCH HÀNG
        customer_users = CustomUser.objects.filter(is_staff=False, role=CustomUser.Role.CUSTOMER).order_by('-date_joined')

        # 5. Gửi các lựa chọn filter
        context['role_choices'] = [
            (CustomUser.Role.RECEPTION, CustomUser.Role.RECEPTION.label),
            (CustomUser.Role.SUPPORT, CustomUser.Role.SUPPORT.label),
            (CustomUser.Role.ADMIN, CustomUser.Role.ADMIN.label),
        ]

        # 6. Gửi 2 danh sách riêng biệt ra template
        context['staff_users'] = staff_users
        context['customer_users'] = customer_users
        context['current_filter'] = role_filter
        
        return context

class UserCreateView(AdminRequiredMixin, CreateView):
    """
    (Admin) View hiển thị form để tạo mới một người dùng (nhân viên).
    """
    model = CustomUser
    form_class = AdminUserCreationForm # Form này đã sửa ở bước trước
    template_name = 'users/dashboard_user_form.html'
    success_url = reverse_lazy('user_list_admin')

class UserUpdateView(AdminRequiredMixin, UpdateView):
    """
    (Admin) View hiển thị form để chỉnh sửa thông tin và vai trò của người dùng.
    """
    model = CustomUser
    template_name = 'users/dashboard_user_form.html'
    fields = ['username', 'full_name', 'email', 'role', 'is_active']
    success_url = reverse_lazy('user_list_admin')

@login_required
@user_passes_test(is_admin)
def toggle_user_active_view(request, pk):
    """
    (Admin) Xử lý việc Khóa (deactivate) hoặc Mở khóa (activate) tài khoản.
    """
    user_to_toggle = get_object_or_404(CustomUser, pk=pk)
    
    if user_to_toggle == request.user:
        messages.error(request, "Bạn không thể tự khóa tài khoản của chính mình.")
        return redirect('user_list_admin')

    if request.method == 'POST':
        user_to_toggle.is_active = not user_to_toggle.is_active
        user_to_toggle.save()

        action = "Mở khóa" if user_to_toggle.is_active else "Khóa"
        messages.success(request, f"Đã {action} tài khoản '{user_to_toggle.username}' thành công.")
        return redirect('user_list_admin')
    else:
        return redirect('user_list_admin')