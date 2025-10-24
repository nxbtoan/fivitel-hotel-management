document.addEventListener("DOMContentLoaded", function() {
    // Kiểm tra xem trình duyệt có hỗ trợ IntersectionObserver không
    if (!('IntersectionObserver' in window)) {
        console.log("Trình duyệt không hỗ trợ IntersectionObserver, hiệu ứng sẽ không hoạt động.");
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
                observer.unobserve(entry.target); // Ngừng quan sát sau khi đã hiển thị để tối ưu
            }
        });
    }, {
        threshold: 0.1 // Kích hoạt khi 10% của element lọt vào màn hình
    });

    // Lấy tất cả các phần tử có class 'fade-in-element'
    const elementsToAnimate = document.querySelectorAll(".fade-in-element");
    
    // Áp dụng class 'hidden' ban đầu và bắt đầu quan sát
    elementsToAnimate.forEach((element) => {
        element.classList.add("hidden");
        observer.observe(element);
    });

    const swiper = new Swiper('.testimonial-slider', {
        // Hiển thị 1 slide trên mobile, 2 slide trên desktop
        slidesPerView: 1,
        spaceBetween: 30, // Khoảng cách giữa các slide
        
        // Responsive breakpoints
        breakpoints: {
        // Khi chiều rộng màn hình >= 768px
        768: {
            slidesPerView: 2,
            spaceBetween: 30
        }
        },
        
        loop: true, // Lặp lại vô tận
        autoplay: {
            delay: 5000,
            disableOnInteraction: false,
        },
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
        },
        // Kết nối với các nút điều khiển tùy chỉnh
        navigation: {
            nextEl: '.swiper-button-next-custom',
            prevEl: '.swiper-button-prev-custom',
        },
    });
});