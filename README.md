# Website Quản lý & Chăm sóc Khách hàng - Khách sạn FIVITEL ĐÀ NẴNG

Đây là dự án website được xây dựng bằng Django nhằm mục đích quản lý hoạt động đặt phòng và triển khai hệ thống chăm sóc khách hàng (CRM) cho khách sạn FIVITEL ĐÀ NẴNG.

---

## ## Các Chức Năng Chính

Dự án bao gồm 3 nhóm chức năng chính:

### 1. Đặt phòng & Quản lý Cơ bản
- [cite_start]**Tài khoản:** Đăng ký, Đăng nhập cho Khách hàng và Nhân viên[cite: 2].
- [cite_start]**Đặt phòng:** Tìm kiếm phòng, xem chi tiết và đặt phòng trực tuyến[cite: 2].
- **Quản lý Đơn đặt phòng:** Khách hàng tự xem/sửa/hủy đơn. [cite_start]Nhân viên quản lý tất cả các đơn[cite: 2].
- [cite_start]**Thanh toán:** Tích hợp cổng thanh toán và gửi email/SMS xác nhận tự động[cite: 2].
- [cite_start]**Quản lý Phòng:** Thêm, sửa, xóa thông tin loại phòng và phòng cho Quản lý/Lễ tân[cite: 2].
- [cite_start]**Quản lý Tài khoản Nội bộ:** Quản lý tài khoản và phân quyền cho nhân viên[cite: 2].

### 2. Chăm sóc Khách hàng (CRM)
- [cite_start]**Tư vấn:** Khách hàng gửi yêu cầu tư vấn, nhân viên CSKH xử lý và phản hồi[cite: 6].
- [cite_start]**Khiếu nại:** Khách hàng gửi khiếu nại (kèm hình ảnh), nhân viên CSKH xử lý theo quy trình[cite: 8].
- [cite_start]**Hỗ trợ sau lưu trú:** Tiếp nhận các yêu cầu đặc biệt sau khi khách hàng đã trả phòng[cite: 10].
- [cite_start]**CRM Automation:** Tự động gửi email/khảo sát để chăm sóc khách hàng sau lưu trú[cite: 10].

### 3. Quản lý Dịch vụ Khách sạn
- [cite_start]**Xem Dịch vụ:** Khách hàng xem danh mục các dịch vụ của khách sạn (Spa, nhà hàng, tour...)[cite: 13].
- [cite_start]**Quản lý Dịch vụ:** Quản lý có thể thêm, sửa, xóa thông tin các dịch vụ[cite: 13].

---

## ## Công Nghệ Sử Dụng
- **Backend:** Python, Django
- **Database:** SQLite (for development)
- **CI/CD:** GitHub Actions

---

## ## Hướng Dẫn Cài Đặt và Chạy Dự Án

1.  **Clone repository:**
    ```bash
    git clone [https://github.com/nxbtoan/fivitel-hotel-management.git](https://github.com/nxbtoan/fivitel-hotel-management.git)
    cd fivitel-hotel-management
    ```

2.  **Tạo và kích hoạt môi trường ảo:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\Activate.ps1
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Chạy migrations để tạo cơ sở dữ liệu:**
    ```bash
    python manage.py migrate
    ```

5.  **Tạo tài khoản admin:**
    ```bash
    python manage.py createsuperuser
    ```

6.  **Chạy server:**
    ```bash
    python manage.py runserver
    ```
    Truy cập trang web tại `http://127.0.0.1:8000` và trang admin tại `http://127.0.0.1:8000/admin`.
