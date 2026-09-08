/**
 * Victory Arena v2.0 - Frontend API Configuration & Fetch Interceptor
 * Tự động đồng bộ và định tuyến tất cả các lệnh gọi API sang Backend Server (Port 8000).
 */

// Cấu hình Base URL của Backend RESTful API
window.API_CONFIG = {
    // Nếu chạy qua Live Server/HTTP Server trên cổng 3000 hoặc khác, tự động trỏ về http://127.0.0.1:8000
    // Nếu được backend phục vụ trực tiếp trên cổng 8000, giữ nguyên đường dẫn tương đối
    BASE_URL: (window.location.port === '8000') ? '' : 'http://127.0.0.1:8000'
};

// Fetch URL Interceptor: Tự động bổ sung tiền tố API_BASE_URL cho mọi request /api/...
(function() {
    const originalFetch = window.fetch;
    window.fetch = function(resource, init) {
        if (typeof resource === 'string') {
            if (resource.startsWith('/api/')) {
                resource = window.API_CONFIG.BASE_URL + resource;
            }
        } else if (resource instanceof Request) {
            const url = resource.url;
            if (url.startsWith('/api/')) {
                resource = new Request(window.API_CONFIG.BASE_URL + url, resource);
            } else if (url.startsWith(window.location.origin + '/api/')) {
                const apiPath = url.substring(window.location.origin.length);
                resource = new Request(window.API_CONFIG.BASE_URL + apiPath, resource);
            }
        }
        return originalFetch.call(this, resource, init);
    };
})();
