from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
def homepage(request):
    return render(request, 'homepage.html')