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
        fields = ("username", "full_name", "email", 'role', "is_staff")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Việt hóa các nhãn
        self.fields['username'].label = "Tên đăng nhập"
        self.fields['full_name'].label = "Họ và Tên"
        self.fields['email'].label = "Địa chỉ email"
        self.fields['role'].label = "Vai trò"
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