from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Service, ServiceCategory

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

class ServiceCreateView(AdminRequiredMixin, CreateView):
    """View hiển thị form để tạo mới một dịch vụ."""
    model = Service
    template_name = 'services/dashboard_service_form.html'
    fields = ['category', 'name', 'description', 'price', 'image']
    success_url = reverse_lazy('service_list')

class ServiceUpdateView(AdminRequiredMixin, UpdateView):
    """View hiển thị form để chỉnh sửa một dịch vụ."""
    model = Service
    template_name = 'services/dashboard_service_form.html'
    fields = ['category', 'name', 'description', 'price', 'image']
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