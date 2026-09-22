/**
 * Victory Arena v2.0 - Frontend API Configuration & Dynamic Fetch Interceptor
 * Tự động nhận diện Hostname và định tuyến chính xác tất cả các lệnh gọi API
 * sang Backend RESTful Server (Port 8000), hỗ trợ đa thiết bị: Localhost, Mạng LAN, WiFi và Live Server.
 */

// Hàm xác định API Base URL thông minh theo ngữ cảnh thực tế của Client
function resolveBackendBaseUrl() {
    // 1. Cho phép cấu hình ghi đè từ LocalStorage nếu cần thiết
    const storedUrl = localStorage.getItem('VICTORY_API_BASE_URL');
    if (storedUrl && storedUrl.trim() !== '') {
        return storedUrl.trim().replace(/\/+$/, '');
    }

    // 2. Nếu trang đang chạy trực tiếp từ chính Backend Server (Port 8000)
    // Dùng đường dẫn tương đối để tận dụng Same-Origin, loại bỏ hoàn toàn rào cản CORS
    if (window.location.port === '8000') {
        return '';
    }

    // 3. Nếu người dùng nhấp đúp mở trực tiếp file HTML (giao thức file://)
    if (window.location.protocol === 'file:') {
        return 'http://127.0.0.1:8000';
    }

    // 4. Nếu truy cập qua HTTP / HTTPS (Port 3000, Port 5500 Live Server, hoặc IP Mạng LAN)
    // Tự động sử dụng đúng Hostname (IP máy chủ) hiện tại kết hợp với Port 8000 của Backend
    const protocol = window.location.protocol || 'http:';
    const hostname = window.location.hostname || '127.0.0.1';
    return `${protocol}//${hostname}:8000`;
}

// Cấu hình Base URL toàn cục
window.API_CONFIG = {
    BASE_URL: resolveBackendBaseUrl(),
    refresh: function() {
        this.BASE_URL = resolveBackendBaseUrl();
    }
};

// Fetch URL Interceptor: Tự động bổ sung tiền tố Backend URL cho mọi request /api/...
(function() {
    const originalFetch = window.fetch;
    window.fetch = function(resource, init) {
        const baseUrl = window.API_CONFIG.BASE_URL;

        if (typeof resource === 'string') {
            if (resource.startsWith('/api/')) {
                resource = baseUrl + resource;
            } else if (resource.startsWith('api/')) {
                resource = baseUrl + '/' + resource;
            }
        } else if (resource instanceof Request) {
            const url = resource.url;
            if (url.startsWith('/api/')) {
                resource = new Request(baseUrl + url, resource);
            } else if (url.startsWith('api/')) {
                resource = new Request(baseUrl + '/' + url, resource);
            } else if (url.startsWith(window.location.origin + '/api/')) {
                const apiPath = url.substring(window.location.origin.length);
                resource = new Request(baseUrl + apiPath, resource);
            }
        }

        return originalFetch.call(this, resource, init).catch(error => {
            console.error('[API Connection Error] Không thể kết nối tới Backend tại:', baseUrl, error);
            throw error;
        });
    };
})();
