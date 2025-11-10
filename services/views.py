from django.urls import reverse_lazy, reverse
from django.db.models import Q, Prefetch
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.contrib import messages

from .models import Service, ServiceCategory, ServiceImage
from .forms import ServiceForm, ServiceImageInlineFormSet

# Hàm kiểm tra user có phải là Admin không
def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin để đảm bảo chỉ Admin mới có thể truy cập."""
    def test_func(self):
        return is_admin(self.request.user)

class ServiceListView(AdminRequiredMixin, ListView):
    """View hiển thị danh sách tất cả các dịch vụ."""
    model = Service
    template_name = 'services/dashboard_service_list.html'
    context_object_name = 'services'
    paginate_by = 10 # Tùy chọn: Thêm phân trang nếu danh sách dài

    def get_queryset(self):
        """Ghi đè để thêm logic tìm kiếm."""
        queryset = super().get_queryset().select_related('category').order_by('name')
        query = self.request.GET.get('q')
        if query:
            # Tìm kiếm theo Tên dịch vụ HOẶC Tên loại dịch vụ
            queryset = queryset.filter(
                Q(name__icontains=query) | 
                Q(category__name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        """Gửi tham số tìm kiếm ra template để hiển thị lại trong ô input."""
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context
    
class PublicServiceListView(ListView):
    """
    View hiển thị danh sách các loại dịch vụ và dịch vụ con cho khách hàng.
    """
    model = ServiceCategory
    template_name = 'services/public_service_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        # Chỉ lấy các dịch vụ đang hoạt động
        active_services = Service.objects.filter(status=Service.Status.ACTIVE)
        
        # Tải trước các dịch vụ liên quan
        return ServiceCategory.objects.prefetch_related(
            Prefetch('services', queryset=active_services, to_attr='active_services')
        ).all()
    
class ServiceDetailView(DetailView):
    """
    View hiển thị chi tiết một dịch vụ cụ thể.
    """
    model = Service
    template_name = 'services/service_detail.html' 
    context_object_name = 'service'

    def get_queryset(self):
        """
        Lấy dịch vụ và các ảnh gallery liên quan.
        """
        return Service.objects.filter(status=Service.Status.ACTIVE).prefetch_related(
            'gallery_images'
        )

@user_passes_test(is_admin)
@transaction.atomic
def service_create_view(request):
    """
    View hiển thị form để tạo mới một dịch vụ VÀ gallery ảnh.
    """
    if request.method == 'POST':
        # Khởi tạo 2 form với dữ liệu POST
        form = ServiceForm(request.POST, request.FILES)
        formset = ServiceImageInlineFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            # 1. Lưu form Service (cha)
            service_instance = form.save()
            
            # 2. Gán instance cha cho formset con
            formset.instance = service_instance
            
            # 3. Lưu formset (các ảnh gallery)
            formset.save()
            
            messages.success(request, f"Đã tạo mới dịch vụ '{service_instance.name}' thành công.")
            return redirect('service_list')
        else:
            # Nếu có lỗi, hiển thị lại trang với lỗi
            messages.error(request, "Vui lòng kiểm tra lại các lỗi bên dưới.")
            
    else: # GET request
        form = ServiceForm()
        formset = ServiceImageInlineFormSet()

    context = {
        'form': form,
        'formset': formset,
        'is_new': True # Biến để template biết đây là form tạo mới
    }
    return render(request, 'services/dashboard_service_form.html', context)

@user_passes_test(is_admin)
@transaction.atomic
def service_update_view(request, pk):
    """
    View hiển thị form để chỉnh sửa một dịch vụ VÀ gallery ảnh.
    """
    service_instance = get_object_or_404(Service, pk=pk)

    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=service_instance)
        formset = ServiceImageInlineFormSet(request.POST, request.FILES, instance=service_instance)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            messages.success(request, f"Đã cập nhật dịch vụ '{service_instance.name}' thành công.")
            return redirect('service_list')
        else:
            messages.error(request, "Vui lòng kiểm tra lại các lỗi bên dưới.")
            
    else: # GET request
        form = ServiceForm(instance=service_instance)
        formset = ServiceImageInlineFormSet(instance=service_instance)

    context = {
        'form': form,
        'formset': formset,
        'is_new': False,
        'service': service_instance
    }
    return render(request, 'services/dashboard_service_form.html', context)

class ServiceUpdateView(AdminRequiredMixin, UpdateView):
    """View hiển thị form để chỉnh sửa một dịch vụ."""
    model = Service
    template_name = 'services/dashboard_service_form.html'
    fields = ['category', 'name', 'description', 'status', 'price', 'image']
    success_url = reverse_lazy('service_list')

class ServiceDeleteView(AdminRequiredMixin, DeleteView):
    """View hiển thị trang xác nhận trước khi xóa một dịch vụ."""
    model = Service
    template_name = 'services/dashboard_service_confirm_delete.html'
    success_url = reverse_lazy('service_list')

class ServiceCategoryListView(AdminRequiredMixin, ListView):
    """View hiển thị danh sách tất cả các loại dịch vụ."""
    model = ServiceCategory
    template_name = 'services/dashboard_service_category_list.html'
    context_object_name = 'categories'

class ServiceCategoryCreateView(AdminRequiredMixin, CreateView):
    """View hiển thị form để tạo mới một loại dịch vụ."""
    model = ServiceCategory
    template_name = 'services/dashboard_service_category_form.html'
    fields = ['name', 'description', 'image']
    success_url = reverse_lazy('service_category_list')

class ServiceCategoryUpdateView(AdminRequiredMixin, UpdateView):
    """View hiển thị form để chỉnh sửa một loại dịch vụ."""
    model = ServiceCategory
    template_name = 'services/dashboard_service_category_form.html'
    fields = ['name', 'description', 'image']
    success_url = reverse_lazy('service_category_list')

class ServiceCategoryDeleteView(AdminRequiredMixin, DeleteView):
    """View xử lý việc xóa một loại dịch vụ."""
    model = ServiceCategory
    success_url = reverse_lazy('service_category_list')