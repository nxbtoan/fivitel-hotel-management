from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomerRegistrationForm(UserCreationForm):
    """
    Form dùng cho trang đăng ký công khai.
    Không chứa các trường 'role' và 'is_staff'.
    Người dùng tạo qua form này sẽ mặc định là CUSTOMER.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Các trường khách hàng cần điền
        fields = ("username", "full_name", "email", "date_of_birth", "nationality", "phone_number")
        widgets = {'date_of_birth': forms.DateInput(attrs={'type': 'date'}),}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tùy chỉnh và Việt hóa các nhãn
        self.fields['username'].label = "Tên đăng nhập"
        self.fields['full_name'].label = "Họ và Tên"
        self.fields['email'].label = "Địa chỉ email"
        self.fields['date_of_birth'].label = "Ngày sinh"
        self.fields['phone_number'].label = "Số điện thoại"
        self.fields['nationality'].label = "Quốc tịch"
        
        # Đặt các trường này là bắt buộc
        self.fields['full_name'].required = True
        self.fields['phone_number'].required = True

class AdminUserCreationForm(UserCreationForm):
    """
    Form dùng trong trang dashboard để Admin tạo tài khoản mới (nhân viên).
    Chứa đầy đủ các trường 'role' và 'is_staff' để phân quyền.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Các trường Admin cần điền khi tạo nhân viên
        fields = ("username", "full_name", "email", "date_of_birth", 'role', "is_staff")
        widgets = {'date_of_birth': forms.DateInput(attrs={'type': 'date'}),}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Việt hóa các nhãn
        self.fields['username'].label = "Tên đăng nhập"
        self.fields['full_name'].label = "Họ và Tên"
        self.fields['email'].label = "Địa chỉ email"
        self.fields['role'].label = "Vai trò"
        self.fields['role'].choices = [
            (CustomUser.Role.STAFF, 'Nhân viên'),
            (CustomUser.Role.ADMIN, 'Quản lý'),
        ]
        self.fields['is_staff'].label = "Là nhân viên"

class UserUpdateForm(forms.ModelForm):
    """
    Form cho phép người dùng tự cập nhật thông tin cá nhân của họ.
    Đã được nâng cấp để tự động thêm class CSS.
    """
    class Meta:
        model = CustomUser
        fields = ('full_name', 'email', 'phone_number', 'date_of_birth', 'nationality')
        # Tùy chỉnh widget cho ô chọn ngày
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Ghi đè hàm __init__ để thêm class 'form-control' vào tất cả các widget.
        """
        super().__init__(*args, **kwargs)
        # Lặp qua tất cả các trường trong form
        for field_name, field in self.fields.items():
            # Lấy các thuộc tính hiện có của widget
            existing_attrs = field.widget.attrs
            # Thêm class 'form-control' vào
            existing_attrs['class'] = existing_attrs.get('class', '') + ' form-control'

class PasswordResetEmailForm(forms.Form):
    """Form nhập email để yêu cầu mã."""
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Không tìm thấy tài khoản nào với địa chỉ email này.")
        return email

class PasswordResetCodeForm(forms.Form):
    """Form nhập mã OTP."""
    code = forms.CharField(label="Mã xác thực", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '6 chữ số'}))

class SetNewPasswordForm(forms.Form):
    """Form nhập mật khẩu mới."""
    new_password1 = forms.CharField(label="Mật khẩu mới", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(label="Xác nhận mật khẩu", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("Hai mật khẩu không khớp.")
        return cleaned_data