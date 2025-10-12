from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "full_name", "email", "date_of_birth", "nationality", "phone_number")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Đánh dấu các trường bắt buộc
        self.fields['full_name'].required = True
        self.fields['phone_number'].required = True

