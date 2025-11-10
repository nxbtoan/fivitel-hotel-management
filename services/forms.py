from django import forms
from .models import Service, ServiceImage

class ServiceForm(forms.ModelForm):
    """
    Form chính để nhập thông tin Dịch vụ.
    Chúng ta dùng Textarea để các ô nhập text lớn hơn.
    """
    class Meta:
        model = Service
        
        fields = [
            'category', 'name', 'description', 'price', 'price_unit', 
            'image', 'highlights', 'terms_conditions', 'status'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'highlights': forms.Textarea(attrs={'rows': 5}),
            'terms_conditions': forms.Textarea(attrs={'rows': 5}),
        }

class ServiceImageForm(forms.ModelForm):
    """Form cho từng ảnh trong gallery."""
    class Meta:
        model = ServiceImage
        fields = ['image', 'alt_text']

ServiceImageInlineFormSet = forms.inlineformset_factory(
    Service,                         # Model cha
    ServiceImage,                    # Model con
    form=ServiceImageForm,           # Form cho model con
    extra=3,                         # Hiển thị 3 form trống để upload
    can_delete=True,                 # Cho phép xóa ảnh cũ (khi update)
    can_delete_extra=True,
    min_num=0,
)