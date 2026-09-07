/**
 * SportBookAI v2.0 - Single Page Application Client Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    // State
    let token = localStorage.getItem('token');
    let currentUser = null;
    let courtsList = [];
    let currentSelectedDate = getTodayString();
    
    // Auth UI Toggle
    const loginScreen = document.getElementById('login-screen');
    const appInterface = document.getElementById('app-interface');
    
    // Tab contents
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Check initial auth status
    checkAuth();
    
    // ==========================================
    // Authentication Functions
    // ==========================================
    function checkAuth() {
        token = localStorage.getItem('token');
        if (token) {
            fetchCurrentUser();
        } else {
            showLogin();
        }
    }
    
    async function fetchCurrentUser() {
        try {
            const res = await fetch('/api/auth/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.status === 401) {
                logout();
                return;
            }
            currentUser = await res.json();
            showApp();
        } catch (e) {
            console.error("Lỗi lấy profile:", e);
            logout();
        }
    }
    
    function showLogin() {
        loginScreen.style.display = 'flex';
        appInterface.style.display = 'none';
    }
    
    function showApp() {
        loginScreen.style.display = 'none';
        appInterface.style.display = 'flex';
        
        // Update user display profile
        document.getElementById('user-display-name').textContent = currentUser.ho_ten;
        document.getElementById('user-display-role').textContent = currentUser.vai_tro;
        document.getElementById('topbar-user-name').textContent = currentUser.ho_ten;
        
        const userIcon = document.getElementById('user-icon');
        const topbarIcon = document.getElementById('topbar-user-icon');
        if (currentUser.vai_tro === 'CUSTOMER') {
            userIcon.className = 'fa-solid fa-user';
            topbarIcon.className = 'fa-solid fa-user';
        } else if (currentUser.vai_tro === 'STAFF') {
            userIcon.className = 'fa-solid fa-user-tie';
            topbarIcon.className = 'fa-solid fa-user-tie';
        } else {
            userIcon.className = 'fa-solid fa-user-shield';
            topbarIcon.className = 'fa-solid fa-user-shield';
        }
        
        // Dynamic tabs visibility based on roles
        const navBookings = document.getElementById('nav-bookings');
        const navOps = document.getElementById('nav-operations');
        const navInsights = document.getElementById('nav-insights');
        const navAdmin = document.getElementById('nav-admin');
        
        if (currentUser.vai_tro === 'CUSTOMER') {
            if (navBookings) navBookings.style.display = 'none';
            if (navOps) navOps.style.display = 'none';
            if (navInsights) navInsights.style.display = 'none';
            if (navAdmin) navAdmin.style.display = 'none';
        } else if (currentUser.vai_tro === 'STAFF') {
            if (navBookings) navBookings.style.display = 'flex';
            if (navOps) navOps.style.display = 'flex';
            if (navInsights) navInsights.style.display = 'flex';
            if (navAdmin) navAdmin.style.display = 'none';
        } else {
            // ADMIN
            if (navBookings) navBookings.style.display = 'flex';
            if (navOps) navOps.style.display = 'flex';
            if (navInsights) navInsights.style.display = 'flex';
            if (navAdmin) navAdmin.style.display = 'flex';
        }
        
        // Initialize/load initial page components
        initApp();
    }
    
    function logout() {
        localStorage.removeItem('token');
        token = null;
        currentUser = null;
        showLogin();
    }
    
    document.getElementById('btn-logout').addEventListener('click', logout);
    
    // Auth Tab Switch
    const btnTabLogin = document.getElementById('btn-tab-login');
    const btnTabRegister = document.getElementById('btn-tab-register');
    const formLogin = document.getElementById('form-login');
    const formRegister = document.getElementById('form-register');
    
    btnTabLogin.addEventListener('click', () => {
        btnTabLogin.classList.add('active');
        btnTabRegister.classList.remove('active');
        formLogin.style.display = 'block';
        formRegister.style.display = 'none';
        hideAuthAlert();
        if (huskyGuard) huskyGuard.classList.remove('is-covering', 'is-peeking');
    });
    
    btnTabRegister.addEventListener('click', () => {
        btnTabRegister.classList.add('active');
        btnTabLogin.classList.remove('active');
        formRegister.style.display = 'block';
        formLogin.style.display = 'none';
        hideAuthAlert();
        if (huskyGuard) huskyGuard.classList.remove('is-covering', 'is-peeking');
    });
    
    // Helper wait function for animations
    const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    // Husky Mascot Elements & Interactivity
    const huskyGuard = document.getElementById('husky-guard');
    const pupilLeft = document.getElementById('pupil-left');
    const pupilRight = document.getElementById('pupil-right');
    const mascotStatusText = document.getElementById('mascot-status-text');
    const mainLoginCard = document.getElementById('main-login-card');
    
    // Auth Alert Banner Helpers
    function showAuthAlert(msg) {
        const alertBox = document.getElementById('auth-alert');
        const alertMsg = document.getElementById('auth-alert-msg');
        if (alertBox && alertMsg) {
            alertMsg.textContent = msg;
            alertBox.style.display = 'flex';
        }
        if (mainLoginCard) {
            mainLoginCard.classList.remove('shake');
            void mainLoginCard.offsetWidth; // trigger reflow
            mainLoginCard.classList.add('shake');
        }
        if (huskyGuard) {
            huskyGuard.classList.remove('is-covering', 'is-peeking', 'is-happy');
            huskyGuard.classList.add('is-sad');
            setTimeout(() => huskyGuard.classList.remove('is-sad'), 800);
        }
    }
    
    function hideAuthAlert() {
        const alertBox = document.getElementById('auth-alert');
        if (alertBox) alertBox.style.display = 'none';
    }

    // Eye Tracking on Username typing
    function updateEyePosition(inputVal) {
        if (!huskyGuard || huskyGuard.classList.contains('is-covering')) return;
        const len = inputVal ? inputVal.length : 0;
        const offsetX = Math.min(Math.max((len - 6) * 0.7, -7), 7);
        const offsetY = len > 0 ? 2 : 0;
        
        if (pupilLeft) pupilLeft.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
        if (pupilRight) pupilRight.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
    }

    const loginUsernameInput = document.getElementById('login-username');
    const regUsernameInput = document.getElementById('reg-username');

    [loginUsernameInput, regUsernameInput].forEach(inp => {
        if (inp) {
            inp.addEventListener('input', (e) => updateEyePosition(e.target.value));
            inp.addEventListener('focus', (e) => {
                if (huskyGuard) huskyGuard.classList.remove('is-covering', 'is-peeking');
                updateEyePosition(e.target.value);
            });
            inp.addEventListener('blur', () => {
                if (pupilLeft) pupilLeft.style.transform = `translate(0px, 0px)`;
                if (pupilRight) pupilRight.style.transform = `translate(0px, 0px)`;
            });
        }
    });

    // Paw Covering on Password Input (Focus, Input, Keydown, Click)
    const loginPasswordInput = document.getElementById('login-password');
    const regPasswordInput = document.getElementById('reg-password');
    const regConfirmPasswordInput = document.getElementById('reg-confirm-password');

    function coverEyes() {
        if (!huskyGuard) return;
        if (!huskyGuard.classList.contains('is-peeking')) {
            huskyGuard.classList.remove('is-happy', 'is-sad');
            huskyGuard.classList.add('is-covering');
        }
        if (mascotStatusText) mascotStatusText.textContent = "Suỵt! Linh vật đang che mắt bảo vệ mật khẩu của bạn.";
    }

    function uncoverEyes() {
        if (!huskyGuard) return;
        huskyGuard.classList.remove('is-covering', 'is-peeking');
        if (mascotStatusText) mascotStatusText.textContent = "Chào mừng! Linh vật AI đang gác cổng hệ thống.";
    }

    [loginPasswordInput, regPasswordInput, regConfirmPasswordInput].forEach(pwInp => {
        if (pwInp) {
            ['focus', 'input', 'keydown', 'click'].forEach(evtType => {
                pwInp.addEventListener(evtType, coverEyes);
            });
            pwInp.addEventListener('blur', uncoverEyes);
        }
    });

    // Password Toggle Eye Buttons
    const btnToggleLoginPw = document.getElementById('btn-toggle-login-pw');
    const iconLoginPw = document.getElementById('icon-login-pw');
    if (btnToggleLoginPw && loginPasswordInput) {
        btnToggleLoginPw.addEventListener('click', (e) => {
            e.preventDefault();
            const isPw = loginPasswordInput.type === 'password';
            loginPasswordInput.type = isPw ? 'text' : 'password';
            if (iconLoginPw) iconLoginPw.className = isPw ? 'fa-regular fa-eye-slash' : 'fa-regular fa-eye';
            
            if (huskyGuard) {
                if (isPw) {
                    huskyGuard.classList.remove('is-covering');
                    huskyGuard.classList.add('is-peeking');
                } else {
                    huskyGuard.classList.remove('is-peeking');
                    huskyGuard.classList.add('is-covering');
                }
            }
        });
    }

    const btnToggleRegPw = document.getElementById('btn-toggle-reg-pw');
    const iconRegPw = document.getElementById('icon-reg-pw');
    if (btnToggleRegPw && regPasswordInput) {
        btnToggleRegPw.addEventListener('click', (e) => {
            e.preventDefault();
            const isPw = regPasswordInput.type === 'password';
            regPasswordInput.type = isPw ? 'text' : 'password';
            if (iconRegPw) iconRegPw.className = isPw ? 'fa-regular fa-eye-slash' : 'fa-regular fa-eye';
        });
    }

    // Password Strength Meter
    if (regPasswordInput) {
        regPasswordInput.addEventListener('input', (e) => {
            const val = e.target.value;
            const fill = document.getElementById('pw-strength-fill');
            if (!fill) return;
            if (val.length === 0) {
                fill.className = 'strength-indicator';
            } else if (val.length < 6) {
                fill.className = 'strength-indicator strength-weak';
            } else if (val.length < 10) {
                fill.className = 'strength-indicator strength-medium';
            } else {
                fill.className = 'strength-indicator strength-strong';
            }
        });
    }

    // Login Form Submit with 3D Door Walkthrough Sequence
    formLogin.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAuthAlert();
        
        const username = document.getElementById('login-username').value.trim();
        const pass = document.getElementById('login-password').value;
        const doorBtn = document.getElementById('btn-door-submit');
        
        if (!username || !pass) {
            showAuthAlert("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!");
            return;
        }

        // 3D Door Walkthrough Animation Sequence
        if (doorBtn) doorBtn.classList.add('dooropen');
        await wait(300); // 1. Door panel opens
        
        if (doorBtn) doorBtn.classList.add('walking');
        await wait(450); // 2. Stickman walks toward door
        
        if (doorBtn) doorBtn.classList.add('out');
        await wait(350); // 3. Stickman enters door
        
        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ten_dang_nhap: username, mat_khau: pass })
            });
            
            if (!res.ok) {
                // Reset door animation
                if (doorBtn) doorBtn.classList.remove('dooropen', 'walking', 'out');
                
                const err = await res.json();
                const errMsg = err.detail || "Đăng nhập thất bại. Vui lòng kiểm tra lại!";
                showAuthAlert(errMsg);
                showToast(errMsg, "error");
                return;
            }
            
            const data = await res.json();
            localStorage.setItem('token', data.access_token);
            token = data.access_token;
            
            // Happy Mascot bounce!
            if (huskyGuard) {
                huskyGuard.classList.remove('is-covering', 'is-peeking', 'is-sad');
                huskyGuard.classList.add('is-happy');
            }
            
            showToast("Đăng nhập thành công!");
            await wait(450);
            
            // Reset door & mascot
            if (doorBtn) doorBtn.classList.remove('dooropen', 'walking', 'out');
            if (huskyGuard) huskyGuard.classList.remove('is-happy');
            
            checkAuth();
        } catch (err) {
            if (doorBtn) doorBtn.classList.remove('dooropen', 'walking', 'out');
            showAuthAlert("Lỗi kết nối máy chủ. Vui lòng thử lại!");
            showToast("Lỗi kết nối máy chủ", "error");
        }
    });

    // Register Form Submit with Client Validation
    formRegister.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAuthAlert();
        
        const username = document.getElementById('reg-username').value.trim();
        const pass = document.getElementById('reg-password').value;
        const confirmPass = document.getElementById('reg-confirm-password').value;
        const fullname = document.getElementById('reg-fullname').value.trim();
        const phone = document.getElementById('reg-phone').value.trim();
        const email = document.getElementById('reg-email').value.trim();
        
        // Client validations
        if (pass !== confirmPass) {
            showAuthAlert("Mật khẩu xác nhận không khớp. Vui lòng kiểm tra lại!");
            document.getElementById('reg-confirm-password').classList.add('input-invalid');
            return;
        } else {
            document.getElementById('reg-confirm-password').classList.remove('input-invalid');
        }
        
        if (pass.length < 6) {
            showAuthAlert("Mật khẩu phải có độ dài tối thiểu 6 ký tự!");
            return;
        }
        
        const phoneRegex = /^(03|05|07|08|09)\d{8}$/;
        if (!phoneRegex.test(phone)) {
            showAuthAlert("Số điện thoại không hợp lệ (phải gồm 10 chữ số, ví dụ 0988123456)!");
            document.getElementById('reg-phone').classList.add('input-invalid');
            return;
        } else {
            document.getElementById('reg-phone').classList.remove('input-invalid');
        }
        
        const data = {
            ten_dang_nhap: username,
            mat_khau: pass,
            ho_ten: fullname,
            so_dien_thoai: phone,
            email: email || null
        };
        
        try {
            const res = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (!res.ok) {
                const err = await res.json();
                const errMsg = err.detail || "Đăng ký thất bại. Vui lòng kiểm tra lại!";
                showAuthAlert(errMsg);
                showToast(errMsg, "error");
                return;
            }
            
            showToast("Đăng ký thành công! Vui lòng đăng nhập.");
            
            // Switch tab & prefill username
            btnTabLogin.click();
            if (loginUsernameInput) loginUsernameInput.value = username;
            if (loginPasswordInput) loginPasswordInput.focus();
        } catch (err) {
            showAuthAlert("Lỗi kết nối máy chủ");
            showToast("Lỗi kết nối máy chủ", "error");
        }
    });

    // ==========================================
    // Main App Initialization
    // ==========================================
    function initApp() {
        document.getElementById('query-date-input').value = currentSelectedDate;
        document.getElementById('bk-date').value = currentSelectedDate;
        
        // Clear listeners and attach them
        initEventListeners();
        
        // Fetch core data
        fetchCourts();
        fetchStatsSummary();
        
        // Load default tab
        document.querySelector('[data-tab="tab-dashboard"]').click();
    }
    
    function initEventListeners() {
        // Tab Navigation
        navItems.forEach(btn => {
            btn.onclick = () => {
                const targetTab = btn.getAttribute('data-tab');
                navItems.forEach(b => b.classList.remove('active'));
                tabContents.forEach(tc => tc.classList.remove('active'));
                
                btn.classList.add('active');
                document.getElementById(targetTab).classList.add('active');
                
                // Set page titles
                const titleMap = {
                    'tab-dashboard': { title: 'Trang Chủ Tổng Quan', subtitle: 'Tổng quan tình hình hoạt động và thông báo mới' },
                    'tab-schedule': { title: 'Lịch Sân Trực Quan', subtitle: 'Tình trạng chi tiết các loại sân' },
                    'tab-booking-form': { title: 'Đặt Sân Mới', subtitle: 'Tạo đơn đặt giữ chỗ sân bóng' },
                    'tab-bookings': { title: 'Quản Lý Đơn Đặt Sân', subtitle: 'Chi tiết lịch sử đặt sân của hệ thống' },
                    'tab-operations': { title: 'Nghiệp Vụ Vận Hành', subtitle: 'Bàn giao sân, sử dụng dịch vụ nước ngọt, thanh toán' },
                    'tab-insights': { title: 'Báo Cáo & AI Insights', subtitle: 'Phân tích doanh thu và đề xuất khuyến mại' },
                    'tab-admin': { title: 'Cấu Hình Hệ Thống', subtitle: 'Quản lý thông tin sân bãi và bảng giá' }
                };
                if (titleMap[targetTab]) {
                    document.getElementById('page-title').textContent = titleMap[targetTab].title;
                    document.getElementById('page-subtitle').textContent = titleMap[targetTab].subtitle;
                }
                
                if (targetTab === 'tab-dashboard') fetchDashboardData();
                if (targetTab === 'tab-schedule') fetchSchedule();
                if (targetTab === 'tab-bookings') fetchBookings();
                if (targetTab === 'tab-operations') fetchOperationsData();
                if (targetTab === 'tab-insights') fetchStatsSummary();
                if (targetTab === 'tab-admin') loadAdminCourtsTable();
            };
        });
        
        document.getElementById('query-date-input').onchange = (e) => {
            currentSelectedDate = e.target.value;
            fetchSchedule();
        };
        
        document.getElementById('btn-refresh-schedule').onclick = () => fetchSchedule();
        document.getElementById('btn-refresh-bookings').onclick = () => fetchBookings();
        
        // Forms Submits
        document.getElementById('form-create-booking').onsubmit = handleCreateBooking;
        
        // Floating Chatbot triggers
        const chatbotTrigger = document.getElementById('chatbot-trigger');
        const chatbotContainer = document.getElementById('chatbot-container');
        const chatbotCloseBtn = document.getElementById('chatbot-close-btn');
        const btnChatbotSend = document.getElementById('btn-chatbot-send');
        const chatbotUserInput = document.getElementById('chatbot-user-input');

        if (chatbotTrigger && chatbotContainer && chatbotCloseBtn) {
            chatbotTrigger.onclick = () => {
                chatbotContainer.classList.toggle('active');
                if (chatbotContainer.classList.contains('active')) {
                    chatbotUserInput.focus();
                }
            };

            chatbotCloseBtn.onclick = () => {
                chatbotContainer.classList.remove('active');
            };
        }

        if (btnChatbotSend && chatbotUserInput) {
            btnChatbotSend.onclick = handleChatbotSubmit;
            chatbotUserInput.onkeydown = (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleChatbotSubmit();
                }
            };
        }

        // Quick prompts in chatbot
        document.querySelectorAll('.chatbot-quick-prompts .chip-prompt').forEach(chip => {
            chip.onclick = () => {
                chatbotUserInput.value = chip.getAttribute('data-text');
                handleChatbotSubmit();
            };
        });
        
        // Operation triggers
        document.getElementById('btn-op-checkin').onclick = handleOpCheckin;
        document.getElementById('btn-op-addservice').onclick = handleOpAddService;
        document.getElementById('btn-op-checkout').onclick = handleOpCheckout;
        
        // Admin forms
        document.getElementById('form-admin-create-court').onsubmit = handleAdminCreateCourt;
        document.getElementById('form-admin-add-pricing').onsubmit = handleAdminAddPricing;

        // Admin Court CRUD Triggers
        const btnRefreshCourts = document.getElementById('btn-refresh-admin-courts');
        if (btnRefreshCourts) btnRefreshCourts.onclick = loadAdminCourtsTable;

        const formEditCourt = document.getElementById('form-edit-court');
        if (formEditCourt) formEditCourt.onsubmit = handleEditCourtSubmit;

        const btnCloseEditModal = document.getElementById('btn-close-edit-court-modal');
        if (btnCloseEditModal) btnCloseEditModal.onclick = closeEditCourtModal;

        const btnCancelEditModal = document.getElementById('btn-cancel-edit-court');
        if (btnCancelEditModal) btnCancelEditModal.onclick = closeEditCourtModal;
        
        // Modals close
        document.getElementById('btn-close-invoice-modal').onclick = () => document.getElementById('modal-invoice').classList.remove('active');
        document.getElementById('btn-invoice-done').onclick = () => document.getElementById('modal-invoice').classList.remove('active');
        document.getElementById('btn-close-notif-modal').onclick = () => document.getElementById('modal-ai-notification').classList.remove('active');
        document.getElementById('btn-close-notif-action').onclick = () => document.getElementById('modal-ai-notification').classList.remove('active');
        
        document.getElementById('btn-copy-zalo').onclick = () => {
            const txt = document.getElementById('ai-zalo-text').innerText;
            navigator.clipboard.writeText(txt).then(() => {
                showToast("Đã sao chép tin nhắn nhắc lịch!");
            });
        };
        
        document.getElementById('btn-load-ai-insights').onclick = handleAIReport;
        
        // Xóa thông báo
        const btnClearNotif = document.getElementById('btn-dash-clear-notif');
        if (btnClearNotif) {
            btnClearNotif.onclick = async () => {
                try {
                    const res = await fetch('/api/van-hanh/notifications/clear', {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    if (res.ok) {
                        showToast("Đã xóa sạch thông báo!");
                        fetchNotifications();
                    }
                } catch (e) {
                    console.error("Lỗi xóa thông báo:", e);
                }
            };
        }
    }
    
    async function fetchDashboardData() {
        if (!currentUser) return;
        
        const custView = document.getElementById('dash-view-customer');
        const staffView = document.getElementById('dash-view-staff');
        const adminView = document.getElementById('dash-view-admin');
        
        if (currentUser.vai_tro === 'CUSTOMER') {
            if (custView) custView.style.display = 'block';
            if (staffView) staffView.style.display = 'none';
            if (adminView) adminView.style.display = 'none';
            
            const nameEl = document.getElementById('cust-greeting-name');
            if (nameEl) nameEl.textContent = currentUser.ho_ten;
            await fetchCustomerDashboard();
        } else if (currentUser.vai_tro === 'STAFF') {
            if (custView) custView.style.display = 'none';
            if (staffView) staffView.style.display = 'block';
            if (adminView) adminView.style.display = 'none';
            
            const nameEl = document.getElementById('staff-greeting-name');
            if (nameEl) nameEl.textContent = currentUser.ho_ten;
            await fetchStaffDashboard();
        } else {
            // ADMIN
            if (custView) custView.style.display = 'none';
            if (staffView) staffView.style.display = 'none';
            if (adminView) adminView.style.display = 'block';
            
            const nameEl = document.getElementById('dash-greeting-name');
            if (nameEl) nameEl.textContent = currentUser.ho_ten;
            await fetchAdminDashboard();
        }
        
        fetchNotifications();
    }

    async function fetchCustomerDashboard() {
        const myListEl = document.getElementById('cust-my-bookings-list');
        const myCountEl = document.getElementById('cust-my-count');
        const statMyBookings = document.getElementById('cust-stat-my-bookings');
        const statReputation = document.getElementById('cust-stat-reputation');
        const statDepositPaid = document.getElementById('cust-stat-deposit-paid');
        
        if (myListEl) myListEl.innerHTML = `<div class="loading-spinner"><i class="fa-solid fa-circle-notch fa-spin"></i> Đang tải lịch thi đấu của bạn...</div>`;
        
        try {
            const res = await fetch('/api/dat-san/bookings', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const allBookings = await res.json();
                const myBookings = allBookings.filter(b => b.ma_khach_hang === currentUser.tai_khoan_id && b.trang_thai !== 'da_huy');
                
                if (statMyBookings) statMyBookings.textContent = myBookings.length;
                if (statReputation) statReputation.textContent = currentUser.diem_uy_tin || 100;
                if (myCountEl) myCountEl.textContent = `${myBookings.length} trận`;
                
                const totalDeposit = myBookings.reduce((sum, b) => sum + (b.tien_coc || 0), 0);
                if (statDepositPaid) statDepositPaid.textContent = `${totalDeposit.toLocaleString('vi-VN')} ₫`;
                
                if (myBookings.length === 0) {
                    if (myListEl) {
                        myListEl.innerHTML = `
                            <div class="placeholder-text" style="padding: 24px 16px; text-align: center;">
                                <i class="fa-solid fa-futbol text-primary" style="font-size: 2rem; margin-bottom: 8px;"></i>
                                <p style="color: #fff; font-weight: 700; margin-bottom: 4px;">Bạn chưa có trận đấu nào được đặt lịch!</p>
                                <p class="text-sm text-muted" style="margin-bottom: 12px;">Hãy bấm "Đặt Sân Ngay" để chọn khung giờ đẹp nhất.</p>
                                <button class="btn btn-primary" onclick="document.querySelector('[data-tab=tab-booking-form]').click()">
                                    <i class="fa-solid fa-plus"></i> Đặt Sân Ngay
                                </button>
                            </div>
                        `;
                    }
                } else {
                    myBookings.sort((a, b) => a.ngay_da.localeCompare(b.ngay_da) || a.gio_bat_dau.localeCompare(b.gio_bat_dau));
                    if (myListEl) {
                        myListEl.innerHTML = myBookings.map(b => {
                            let badgeClass = 'badge-confirmed';
                            let stateText = 'ĐÃ XÁC NHẬN';
                            if (b.trang_thai === 'dang_da') {
                                badgeClass = 'badge-playing';
                                stateText = '🔴 ĐANG ĐÁ';
                            } else if (b.trang_thai === 'cho_coc') {
                                badgeClass = 'badge-confirmed';
                                stateText = 'GIỮ CHỖ (10P)';
                            }
                            
                            const pitchName = b.san ? b.san.ten_san : b.ma_san;
                            return `
                                <div class="fixture-match-card">
                                    <div class="fixture-left">
                                        <div class="fixture-icon"><i class="fa-solid fa-futbol"></i></div>
                                        <div class="fixture-details">
                                            <h4>${pitchName}</h4>
                                            <div class="fixture-meta">
                                                <span><i class="fa-regular fa-calendar text-neon"></i> ${b.ngay_da}</span>
                                                <span><i class="fa-regular fa-clock text-neon"></i> ${b.gio_bat_dau.slice(0, 5)} - ${b.gio_ket_thuc.slice(0, 5)}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="fixture-right">
                                        <span class="fixture-status-badge ${badgeClass}">${stateText}</span>
                                        <span class="fixture-code">${b.ma_don}</span>
                                    </div>
                                </div>
                            `;
                        }).join('');
                    }
                }
            }
        } catch (e) {
            console.error("Lỗi fetch lịch cá nhân:", e);
            if (myListEl) myListEl.innerHTML = `<div class="error-text">Không thể kết xuất dữ liệu thi đấu cá nhân.</div>`;
        }
    }

    async function fetchStaffDashboard() {
        const staffListEl = document.getElementById('staff-upcoming-list');
        const staffTodayCount = document.getElementById('staff-today-count');
        const statPlaying = document.getElementById('staff-stat-playing');
        const statPending = document.getElementById('staff-stat-pending');
        const statCompleted = document.getElementById('staff-stat-completed');
        
        if (staffListEl) staffListEl.innerHTML = `<div class="loading-spinner"><i class="fa-solid fa-circle-notch fa-spin"></i> Đang tải lịch vận hành ca trực...</div>`;
        
        try {
            const res = await fetch('/api/dat-san/bookings', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const allBookings = await res.json();
                const todayStr = currentSelectedDate;
                const todayBookings = allBookings.filter(b => b.ngay_da === todayStr && b.trang_thai !== 'da_huy');
                
                if (staffTodayCount) staffTodayCount.textContent = `${todayBookings.length} trận`;
                
                const playingCount = todayBookings.filter(b => b.trang_thai === 'dang_da').length;
                const pendingCount = todayBookings.filter(b => b.trang_thai === 'da_xac_nhan' || b.trang_thai === 'cho_coc').length;
                const completedCount = todayBookings.filter(b => b.trang_thai === 'hoan_tat').length;
                
                if (statPlaying) statPlaying.textContent = playingCount;
                if (statPending) statPending.textContent = pendingCount;
                if (statCompleted) statCompleted.textContent = completedCount;
                
                if (todayBookings.length === 0) {
                    if (staffListEl) staffListEl.innerHTML = `<div class="placeholder-text"><i class="fa-solid fa-clipboard-check text-primary"></i> Ca trực hôm nay chưa có đơn đặt cần xử lý.</div>`;
                } else {
                    todayBookings.sort((a, b) => a.gio_bat_dau.localeCompare(b.gio_bat_dau));
                    if (staffListEl) {
                        staffListEl.innerHTML = todayBookings.map(b => {
                            let badgeClass = 'badge-confirmed';
                            let stateText = 'CHỜ VÀO SÂN';
                            let actionBtn = `<button class="btn btn-xs btn-primary" onclick="quickCheckIn('${b.ma_don}')"><i class="fa-solid fa-right-to-bracket"></i> Check-in</button>`;
                            
                            if (b.trang_thai === 'dang_da') {
                                badgeClass = 'badge-playing';
                                stateText = '🔴 ĐANG ĐÁ';
                                actionBtn = `<button class="btn btn-xs btn-danger" onclick="quickCheckOut('${b.ma_don}')"><i class="fa-solid fa-right-from-bracket"></i> Check-out</button>`;
                            } else if (b.trang_thai === 'hoan_tat') {
                                badgeClass = 'badge-confirmed';
                                stateText = 'HOÀN TẤT';
                                actionBtn = `<span class="text-muted text-xs">Đã xong</span>`;
                            }
                            
                            const pitchName = b.san ? b.san.ten_san : b.ma_san;
                            const clientName = b.khach_hang_ten || 'Đội Đăng Ký';
                            
                            return `
                                <div class="fixture-match-card">
                                    <div class="fixture-left">
                                        <div class="fixture-icon"><i class="fa-solid fa-user-gear"></i></div>
                                        <div class="fixture-details">
                                            <h4>${pitchName} - <small style="color:var(--text-muted);">${clientName}</small></h4>
                                            <div class="fixture-meta">
                                                <span><i class="fa-regular fa-clock text-neon"></i> ${b.gio_bat_dau.slice(0, 5)} - ${b.gio_ket_thuc.slice(0, 5)}</span>
                                                <span><i class="fa-solid fa-barcode text-neon"></i> ${b.ma_don}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="fixture-right">
                                        <span class="fixture-status-badge ${badgeClass}">${stateText}</span>
                                        <div style="margin-top: 4px;">${actionBtn}</div>
                                    </div>
                                </div>
                            `;
                        }).join('');
                    }
                }
            }
        } catch (e) {
            console.error("Lỗi fetch lịch staff:", e);
            if (staffListEl) staffListEl.innerHTML = `<div class="error-text">Không thể kết xuất dữ liệu ca trực.</div>`;
        }
    }

    async function fetchAdminDashboard() {
        const upcomingListEl = document.getElementById('dash-upcoming-list');
        const todayCountEl = document.getElementById('dash-today-count');
        
        if (upcomingListEl) {
            upcomingListEl.innerHTML = `<div class="loading-spinner"><i class="fa-solid fa-circle-notch fa-spin"></i> Đang tải lịch thi đấu hôm nay...</div>`;
        }
        
        try {
            const bookingsRes = await fetch('/api/dat-san/bookings', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (bookingsRes.ok) {
                const allBookings = await bookingsRes.json();
                
                const todayStr = currentSelectedDate;
                const todayBookings = allBookings.filter(b => b.ngay_da === todayStr && b.trang_thai !== 'da_huy');
                
                if (todayCountEl) todayCountEl.textContent = `${todayBookings.length} trận`;
                
                const statTotalBookings = document.getElementById('stat-total-bookings');
                const statBookingProgress = document.getElementById('stat-booking-progress');
                const activeBookingsCount = allBookings.filter(b => b.trang_thai !== 'da_huy').length;
                if (statTotalBookings) statTotalBookings.textContent = activeBookingsCount;
                if (statBookingProgress) {
                    const pct = Math.min(100, Math.max(15, activeBookingsCount * 20));
                    statBookingProgress.style.width = `${pct}%`;
                }

                if (todayBookings.length === 0) {
                    if (upcomingListEl) {
                        upcomingListEl.innerHTML = `<div class="placeholder-text"><i class="fa-solid fa-trophy text-primary" style="margin-right: 6px;"></i> Hôm nay chưa có trận đấu nào được đặt lịch. Bấm "Đặt Sân Nhanh" để tạo trận đấu mới!</div>`;
                    }
                } else {
                    todayBookings.sort((a, b) => a.gio_bat_dau.localeCompare(b.gio_bat_dau));
                    
                    if (upcomingListEl) {
                        upcomingListEl.innerHTML = todayBookings.map(b => {
                            let badgeClass = 'badge-confirmed';
                            let stateText = 'ĐÃ XÁC NHẬN';
                            let statusDot = '<i class="fa-solid fa-circle text-primary" style="font-size: 0.5rem; margin-right: 4px;"></i>';
                            
                            if (b.trang_thai === 'dang_da') {
                                badgeClass = 'badge-playing';
                                stateText = 'ĐANG THI ĐẤU';
                                statusDot = '<i class="fa-solid fa-circle pulse-live text-danger" style="font-size: 0.5rem; margin-right: 4px;"></i>';
                            } else if (b.trang_thai === 'hoan_tat') {
                                badgeClass = 'badge-confirmed';
                                stateText = 'HOÀN TẤT';
                            } else if (b.trang_thai === 'cho_coc') {
                                badgeClass = 'badge-confirmed';
                                stateText = 'GIỮ CHỖ (10P)';
                            }
                            
                            const pitchName = b.san ? b.san.ten_san : b.ma_san;
                            const clientName = b.khach_hang_ten || 'Đội Bóng Đăng Ký';
                            
                            return `
                                <div class="fixture-match-card">
                                    <div class="fixture-left">
                                        <div class="fixture-icon"><i class="fa-solid fa-futbol"></i></div>
                                        <div class="fixture-details">
                                            <h4>${pitchName}</h4>
                                            <div class="fixture-meta">
                                                <span><i class="fa-regular fa-clock text-neon"></i> ${b.gio_bat_dau.slice(0, 5)} - ${b.gio_ket_thuc.slice(0, 5)}</span>
                                                <span><i class="fa-solid fa-user-shield text-neon"></i> ${clientName}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="fixture-right">
                                        <span class="fixture-status-badge ${badgeClass}">${statusDot} ${stateText}</span>
                                        <span class="fixture-code">${b.ma_don}</span>
                                    </div>
                                </div>
                            `;
                        }).join('');
                    }
                }
            }
        } catch (e) {
            console.error("Lỗi fetch lịch admin:", e);
            if (upcomingListEl) upcomingListEl.innerHTML = `<div class="error-text">Không thể kết xuất dữ liệu thi đấu.</div>`;
        }
    }

    // Quick helper functions for Staff 1-Click action buttons
    window.quickCheckIn = (maDon) => {
        document.querySelector('[data-tab=tab-operations]').click();
        const checkinInput = document.getElementById('op-checkin-madon');
        if (checkinInput) {
            checkinInput.value = maDon;
            checkinInput.focus();
        }
    };

    window.quickCheckOut = (maDon) => {
        document.querySelector('[data-tab=tab-operations]').click();
        const checkoutInput = document.getElementById('op-checkout-madon');
        if (checkoutInput) {
            checkoutInput.value = maDon;
            checkoutInput.focus();
        }
    };
    
    async function fetchNotifications() {
        const notifListEl = document.getElementById('dash-notif-list');
        const notifCountEl = document.getElementById('dash-notif-count');
        const topbarBadgeEl = document.querySelector('.notification-badge');
        
        try {
            const notifRes = await fetch('/api/van-hanh/notifications', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (notifRes.ok) {
                const list = await notifRes.json();
                
                notifCountEl.textContent = list.length;
                if (topbarBadgeEl) {
                    topbarBadgeEl.textContent = list.length;
                    topbarBadgeEl.style.display = list.length > 0 ? 'flex' : 'none';
                }
                
                if (list.length === 0) {
                    notifListEl.innerHTML = `<div class="placeholder-text">Không có thông báo mới nào được ghi nhận.</div>`;
                } else {
                    notifListEl.innerHTML = list.map(n => {
                        const dateStr = n.ngay_gui ? new Date(n.ngay_gui).toLocaleTimeString('vi-VN', {hour: '2-digit', minute:'2-digit'}) : '';
                        return `
                            <div style="background-color: rgba(255,255,255,0.02); border-left: 3px solid var(--secondary); padding: 10px 14px; border-radius: var(--radius-sm); font-size: 0.82rem; border-top: 1px solid var(--border-color); border-right: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color);">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-weight: 500;">
                                    <span style="color: var(--secondary);"><i class="fa-solid fa-sparkles"></i> AI Thông Báo</span>
                                    <span class="text-muted" style="font-size: 0.72rem;">${dateStr}</span>
                                </div>
                                <div style="color: #cbd5e1; line-height: 1.4;">${n.noi_dung}</div>
                            </div>
                        `;
                    }).join('');
                }
            }
        } catch (e) {
            console.error("Lỗi fetch thông báo:", e);
        }
    }

    // ==========================================
    // Data Fetch Operations
    // ==========================================
    async function fetchCourts() {
        try {
            const res = await fetch('/api/san', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            courtsList = await res.json();
            
            // Populate selects
            const bkCourt = document.getElementById('bk-court-id');
            const fltCourt = document.getElementById('filter-court-select');
            const admPricingSan = document.getElementById('adm-p-san');
            
            bkCourt.innerHTML = courtsList.map(c => 
                `<option value="${c.ma}">${c.ten_san} (${c.loai_san.ten_loai})</option>`
            ).join('');
            
            fltCourt.innerHTML = courtsList.map(c => 
                `<option value="${c.ma}">${c.ten_san}</option>`
            ).join('');
            
            admPricingSan.innerHTML = courtsList.map(c => 
                `<option value="${c.ma}">${c.ten_san}</option>`
            ).join('');
            
            // For admin court create, populate LoaiSan selector (Chỉ Sân 7 và Sân 11)
            const admLoai = document.getElementById('adm-c-loai');
            if (admLoai) {
                admLoai.innerHTML = `
                    <option value="1">Sân 7</option>
                    <option value="2">Sân 11</option>
                `;
            }
        } catch (e) {
            console.error("Lỗi fetch courts:", e);
        }
    }
    
    async function fetchSchedule() {
        const scheduleMatrix = document.getElementById('schedule-matrix');
        const courtId = document.getElementById('filter-court-select').value;
        if (!courtId) return;
        
        scheduleMatrix.innerHTML = `<div class="loading-spinner"><i class="fa-solid fa-circle-notch fa-spin"></i> Đang tải ma trận khung giờ...</div>`;
        
        try {
            const res = await fetch(`/api/dat-san/schedule?ngay=${currentSelectedDate}&san_id=${courtId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            
            if (data.slots.length === 0) {
                scheduleMatrix.innerHTML = `<div class="placeholder-text">Không có khung giờ nào khả dụng trong ngày.</div>`;
                return;
            }
            
            let html = `<div class="matrix-grid">`;
            data.slots.forEach(slot => {
                let statusClass = slot.trang_thai.toLowerCase();
                let statusLabel = "";
                
                if (slot.trang_thai === 'AVAILABLE') statusLabel = "Trống (Đặt ngay)";
                else if (slot.trang_thai === 'LOCKED') statusLabel = "Đang giữ chỗ (Chờ cọc)";
                else if (slot.trang_thai === 'BOOKED') statusLabel = `Đã đặt (${slot.ten_khach || 'Ẩn danh'})`;
                else if (slot.trang_thai === 'MAINTENANCE') statusLabel = "Bảo trì sân";
                
                const timeStr = `${slot.gio_bat_dau.substring(0, 5)} - ${slot.gio_ket_thuc.substring(0, 5)}`;
                
                html += `
                    <div class="slot-card ${statusClass}" onclick="window.quickSelectSlot('${slot.san_id}', '${timeStr}')">
                        <div class="slot-time">${timeStr}</div>
                        <div class="slot-price">${slot.don_gia.toLocaleString()} ₫</div>
                        <div class="slot-status">${statusLabel}</div>
                        ${slot.ma_don ? `<div class="slot-booking-code">${slot.ma_don}</div>` : ''}
                    </div>
                `;
            });
            html += `</div>`;
            scheduleMatrix.innerHTML = html;
        } catch (e) {
            scheduleMatrix.innerHTML = `<div class="error-text">Không thể kết nối đến máy chủ.</div>`;
        }
    }
    
    // Globals for onclick selection in grid
    window.quickSelectSlot = (sanId, timeStr) => {
        document.getElementById('bk-court-id').value = sanId;
        const [start, end] = timeStr.split(' - ');
        document.getElementById('bk-start-time').value = start;
        document.getElementById('bk-end-time').value = end;
        document.getElementById('bk-date').value = currentSelectedDate;
        
        // Switch tab to booking form
        document.querySelector('[data-tab="tab-booking-form"]').click();
        showToast("Đã chọn sân và khung giờ đá!");
    };
    
    async function fetchBookings() {
        const tableBody = document.getElementById('bookings-table-body');
        tableBody.innerHTML = `<tr><td colspan="8" class="text-center"><i class="fa-solid fa-circle-notch fa-spin"></i> Đang tải danh sách đơn đặt...</td></tr>`;
        
        try {
            const res = await fetch('/api/dat-san/bookings', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const bookings = await res.json();
            
            if (bookings.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">Chưa có đơn đặt sân nào trên hệ thống.</td></tr>`;
                return;
            }
            
            let html = "";
            bookings.forEach(b => {
                // Trạng thái badge
                let statusBadge = "";
                if (b.trang_thai === 'cho_coc') statusBadge = `<span class="badge badge-warning">Chờ cọc</span>`;
                else if (b.trang_thai === 'da_xac_nhan') statusBadge = `<span class="badge badge-success">Đã xác nhận</span>`;
                else if (b.trang_thai === 'dang_da') statusBadge = `<span class="badge badge-primary">Đang thi đấu</span>`;
                else if (b.trang_thai === 'hoan_tat') statusBadge = `<span class="badge badge-secondary">Hoàn tất</span>`;
                else if (b.trang_thai === 'da_huy') statusBadge = `<span class="badge badge-danger">Đã hủy</span>`;
                
                // Hạn giữ chỗ
                let expTimer = "";
                if (b.trang_thai === 'cho_coc' && b.lock_expires_at) {
                    const diffMs = new Date(b.lock_expires_at) - new Date();
                    if (diffMs > 0) {
                        const mins = Math.floor(diffMs / 60000);
                        const secs = Math.floor((diffMs % 60000) / 1000);
                        expTimer = `<div class="lock-timer" style="color: #ef4444; font-size: 11px; font-weight: 600;">Còn lại ${mins}m ${secs}s</div>`;
                    } else {
                        expTimer = `<div class="lock-timer" style="color: #6b7280; font-size: 11px;">Hết hạn lock</div>`;
                    }
                }
                
                // Nút thao tác
                let actions = "";
                if (currentUser.vai_tro !== 'CUSTOMER') {
                    if (b.trang_thai === 'cho_coc') {
                        actions += `<button class="btn btn-xs btn-primary btn-action" onclick="window.confirmDepositPrompt('${b.ma_don}', ${b.tien_coc})">Xác nhận cọc</button>`;
                    }
                    if (b.trang_thai === 'da_xac_nhan') {
                        actions += `<button class="btn btn-xs btn-secondary btn-action" onclick="window.triggerReminder('${b.ma_don}')">AI nhắc lịch</button>`;
                    }
                }
                
                if (b.trang_thai === 'cho_coc' || b.trang_thai === 'da_xac_nhan') {
                    actions += ` <button class="btn btn-xs btn-danger btn-action" onclick="window.cancelBookingPrompt('${b.ma_don}')">Hủy đơn</button>`;
                }
                
                if (actions === "") actions = `<span class="text-muted">Không có</span>`;
                
                const timeStr = `${b.gio_bat_dau.substring(0, 5)} - ${b.gio_ket_thuc.substring(0, 5)}`;
                
                html += `
                    <tr>
                        <td><strong>${b.ma_don}</strong>${expTimer}</td>
                        <td>${b.khach_hang_ten || 'N/A'}</td>
                        <td>${b.san ? b.san.ten_san : b.ma_san}</td>
                        <td>${formatDateString(b.ngay_da)}</td>
                        <td>${timeStr}</td>
                        <td>${b.tien_coc.toLocaleString()} ₫</td>
                        <td>${statusBadge}</td>
                        <td>${actions}</td>
                    </tr>
                `;
            });
            tableBody.innerHTML = html;
        } catch (e) {
            tableBody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Lỗi tải danh sách đơn đặt.</td></tr>`;
        }
    }
    
    // Globals for action triggers
    window.confirmDepositPrompt = async (maDon, currentDeposit) => {
        const amt = prompt("Nhập số tiền cọc đã nhận từ khách (VND):", "200000");
        if (amt === null) return;
        
        try {
            const res = await fetch('/api/dat-san/booking/confirm-deposit', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ ma_don: maDon, so_tien: parseFloat(amt), phuong_thuc: 'chuyen_khoan' })
            });
            
            if (res.ok) {
                showToast("Xác nhận tiền cọc thành công!");
                fetchBookings();
            } else {
                const err = await res.json();
                showToast(err.detail || "Lỗi xác nhận cọc", "error");
            }
        } catch (e) {
            showToast("Lỗi kết nối", "error");
        }
    };
    
    window.cancelBookingPrompt = async (maDon) => {
        if (!confirm(`Bạn có chắc chắn muốn hủy đơn đặt sân ${maDon}? Nếu hủy trước 24h, khách sẽ được hoàn tiền cọc tự động.`)) return;
        
        try {
            const res = await fetch(`/api/dat-san/booking/cancel?ma_don=${maDon}`, {
                method: 'POST',
                headers: { 
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (res.ok) {
                showToast("Đã hủy đơn đặt sân thành công!");
                fetchBookings();
            } else {
                const err = await res.json();
                showToast(err.detail || "Lỗi hủy đơn", "error");
            }
        } catch (e) {
            showToast("Lỗi kết nối", "error");
        }
    };
    
    window.triggerReminder = async (maDon) => {
        showToast("Đang gửi yêu cầu AI nhắc lịch...");
        try {
            const res = await fetch('/api/ai/reminder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ ma_don: maDon })
            });
            
            if (res.ok) {
                const data = await res.json();
                document.getElementById('ai-zalo-text').innerText = data.noi_dung_tin_nhan;
                document.getElementById('modal-ai-notification').classList.add('active');
            } else {
                const err = await res.json();
                showToast(err.detail || "Lỗi sinh tin nhắn AI", "error");
            }
        } catch (e) {
            showToast("Lỗi kết nối", "error");
        }
    };
    
    async function fetchStatsSummary() {
        try {
            const res = await fetch('/api/bao-cao/dashboard', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) return;
            const data = await res.json();
            
            document.getElementById('stat-total-courts').textContent = data.tong_san;
            document.getElementById('stat-total-bookings').textContent = data.tong_dat_san;
            document.getElementById('stat-total-revenue').textContent = `${data.tong_doanh_thu.toLocaleString()} ₫`;
            document.getElementById('stat-active-courts').textContent = `${data.san_hoat_dong}/${data.tong_san}`;
        } catch (e) {
            console.error("Lỗi load stats dashboard:", e);
        }
    }
    
    async function fetchOperationsData() {
        // Load danh mục dịch vụ phục vụ cho thêm nước ngọt/đồ thuê
        try {
            const res = await fetch('/api/dich-vu', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const services = await res.json();
            
            const sSelect = document.getElementById('op-service-id');
            sSelect.innerHTML = services.map(s => 
                `<option value="${s.dich_vu_id}">${s.ten_dich_vu} - ${s.don_gia.toLocaleString()}đ/${s.don_vi_tinh}</option>`
            ).join('');
        } catch (e) {
            console.error("Lỗi fetch dịch vụ:", e);
        }
    }

    // ==========================================
    // Operations & Forms Handling
    // ==========================================
    async function handleCreateBooking(e) {
        e.preventDefault();
        
        const data = {
            ma_san: document.getElementById('bk-court-id').value,
            ngay_da: document.getElementById('bk-date').value,
            gio_bat_dau: document.getElementById('bk-start-time').value + ":00",
            gio_ket_thuc: document.getElementById('bk-end-time').value + ":00",
            tien_coc: parseFloat(document.getElementById('bk-deposit').value || 0.0),
            ghi_chu: document.getElementById('bk-note').value || null,
            phuong_thuc_thanh_toan: document.getElementById('bk-payment-method').value
        };
        
        try {
            const res = await fetch('/api/dat-san/booking', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(data)
            });
            
            if (!res.ok) {
                const err = await res.json();
                showToast(err.detail || "Không thể đặt giữ sân", "error");
                return;
            }
            
            const booking = await res.json();
            showToast(`Giữ sân thành công! Mã đơn: ${booking.ma_don}`);
            
            // Reset form
            document.getElementById('bk-deposit').value = 0;
            document.getElementById('bk-note').value = "";
            
            // Switch tab to Bookings
            document.querySelector('[data-tab="tab-bookings"]').click();
        } catch (e) {
            showToast("Lỗi kết nối đến máy chủ", "error");
        }
    }
    
    async function handleChatbotSubmit() {
        const inputEl = document.getElementById('chatbot-user-input');
        const messagesEl = document.getElementById('chatbot-messages');
        const promptInput = inputEl.value.trim();
        
        if (!promptInput || promptInput.length < 3) {
            showToast("Vui lòng mô tả chi tiết nhu cầu đá bóng của bạn!", "warning");
            return;
        }
        
        // 1. Xóa nội dung nhập
        inputEl.value = "";
        
        // 2. Thêm tin nhắn của User
        const userMsgHtml = `
            <div class="chatbot-message user">
                <div class="user-avatar"><i class="fa-solid fa-user"></i></div>
                <div class="msg-text">${promptInput}</div>
            </div>
        `;
        messagesEl.insertAdjacentHTML('beforeend', userMsgHtml);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        
        // 3. Tạo placeholder tải thông tin AI
        const loadingId = "chatbot-loading-" + Date.now();
        const loadingMsgHtml = `
            <div class="chatbot-message ai" id="${loadingId}">
                <div class="ai-avatar"><i class="fa-solid fa-sparkles"></i></div>
                <div class="msg-text"><i class="fa-solid fa-circle-notch fa-spin"></i> Đang quét khung giờ trống...</div>
            </div>
        `;
        messagesEl.insertAdjacentHTML('beforeend', loadingMsgHtml);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        
        try {
            const res = await fetch('/api/ai/consult', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ user_prompt: promptInput, ngay_mong_muon: currentSelectedDate })
            });
            
            // Xóa placeholder tải thông tin
            const loadEl = document.getElementById(loadingId);
            if (loadEl) loadEl.remove();
            
            if (!res.ok) {
                const errMsgHtml = `
                    <div class="chatbot-message ai">
                        <div class="ai-avatar"><i class="fa-solid fa-sparkles"></i></div>
                        <div class="msg-text">Gặp sự cố kết nối với AI. Bạn xem trực quan trên Lịch Sân Trực Quan nhé.</div>
                    </div>
                `;
                messagesEl.insertAdjacentHTML('beforeend', errMsgHtml);
                messagesEl.scrollTop = messagesEl.scrollHeight;
                return;
            }
            
            const data = await res.json();
            
            // Tạo các thẻ gợi ý sân bóng khả dụng
            let recommendedHtml = "";
            if (data.recommended_slots && data.recommended_slots.length > 0) {
                recommendedHtml = `
                    <div class="recommended-cards-title">Các Khung Giờ Khả Dụng Được AI Gợi Ý:</div>
                    <div class="recommended-cards-grid">
                        ${data.recommended_slots.map(slot => `
                            <div class="recommended-card">
                                <div class="rec-title">${slot.ten_san}</div>
                                <div class="rec-time"><i class="fa-regular fa-clock"></i> Khung giờ: ${slot.khung_gio}</div>
                                <div class="rec-price"><i class="fa-solid fa-tag"></i> Giá: ${slot.don_gia.toLocaleString()}đ</div>
                                <div class="rec-reason">${slot.ly_do}</div>
                                <button class="btn btn-xs btn-primary btn-block" onclick="window.quickSelectSlot('${slot.san_id}', '${slot.khung_gio}')" style="margin-top: 10px;">Đặt Giữ Sân</button>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
            
            const aiMsgHtml = `
                <div class="chatbot-message ai">
                    <div class="ai-avatar"><i class="fa-solid fa-sparkles"></i></div>
                    <div class="msg-text">
                        ${data.assistant_message}
                        ${recommendedHtml}
                    </div>
                </div>
            `;
            messagesEl.insertAdjacentHTML('beforeend', aiMsgHtml);
            messagesEl.scrollTop = messagesEl.scrollHeight;
            
        } catch (e) {
            const loadEl = document.getElementById(loadingId);
            if (loadEl) loadEl.remove();
            
            const errMsgHtml = `
                <div class="chatbot-message ai">
                    <div class="ai-avatar"><i class="fa-solid fa-sparkles"></i></div>
                    <div class="msg-text">Lỗi hệ thống AI tư vấn. Không thể kết nối với dịch vụ.</div>
                </div>
            `;
            messagesEl.insertAdjacentHTML('beforeend', errMsgHtml);
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }
    }
    
    // ==========================================
    // Operations & Check-in / Out Logic
    // ==========================================
    async function handleOpCheckin() {
        const maDon = document.getElementById('op-checkin-madon').value;
        const ghiChu = document.getElementById('op-checkin-note').value;
        
        if (!maDon) {
            showToast("Vui lòng nhập mã đơn đặt sân", "warning");
            return;
        }
        
        try {
            const res = await fetch('/api/van-hanh/check-in', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ ma_don: maDon, ghi_chu: ghiChu })
            });
            
            if (res.ok) {
                showToast("Check-in nhận sân thành công! Trận đấu đã chuyển sang trạng thái Đang thi đấu.");
                document.getElementById('op-service-madon').value = maDon;
                document.getElementById('op-checkout-madon').value = maDon;
                
                // Show preview of service
                loadServiceUsagePreview(maDon);
            } else {
                const err = await res.json();
                showToast(err.detail || "Check-in thất bại", "error");
            }
        } catch (e) {
            showToast("Lỗi kết nối", "error");
        }
    }
    
    async function handleOpAddService() {
        const maDon = document.getElementById('op-service-madon').value;
        const serviceId = parseInt(document.getElementById('op-service-id').value);
        const qty = parseInt(document.getElementById('op-service-quantity').value);
        
        if (!maDon || !serviceId) {
            showToast("Vui lòng nhập mã đơn đặt sân đang hoạt động!", "warning");
            return;
        }
        
        try {
            const res = await fetch('/api/van-hanh/add-service', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ ma_don: maDon, dich_vu_id: serviceId, so_luong: qty })
            });
            
            if (res.ok) {
                showToast("Đã thêm dịch vụ thành công!");
                loadServiceUsagePreview(maDon);
            } else {
                const err = await res.json();
                showToast(err.detail || "Thêm dịch vụ thất bại", "error");
            }
        } catch (e) {
            showToast("Lỗi kết nối", "error");
        }
    }
    
    async function loadServiceUsagePreview(maDon) {
        const preview = document.getElementById('service-usage-preview');
        const body = document.getElementById('service-usage-body');
        
        try {
            const res = await fetch(`/api/van-hanh/service-usage?ma_don=${maDon}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) return;
            const usages = await res.json();
            
            if (usages.length === 0) {
                preview.style.display = 'none';
                return;
            }
            
            preview.style.display = 'block';
            body.innerHTML = usages.map(u => `
                <tr>
                    <td>${u.ten_dich_vu}</td>
                    <td>${u.so_luong}</td>
                    <td>${u.don_gia_tai_ban.toLocaleString()} đ</td>
                    <td>${u.thanh_tien.toLocaleString()} đ</td>
                </tr>
            `).join('');
        } catch (e) {
            console.error("Lỗi hiển thị dịch vụ dùng:", e);
        }
    }
    
    async function handleOpCheckout() {
        const maDon = document.getElementById('op-checkout-madon').value;
        const method = document.getElementById('op-checkout-method').value;
        
        if (!maDon) {
            showToast("Vui lòng nhập mã đơn đặt sân quyết toán!", "warning");
            return;
        }
        
        try {
            const res = await fetch(`/api/van-hanh/check-out?phuong_thuc=${method}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ ma_don: maDon })
            });
            
            if (res.ok) {
                const invoice = await res.json();
                showInvoiceModal(invoice);
                showToast("Check-out quyết toán thành công!");
                
                // Clear fields
                document.getElementById('op-checkin-madon').value = "";
                document.getElementById('op-service-madon').value = "";
                document.getElementById('op-checkout-madon').value = "";
                document.getElementById('service-usage-preview').style.display = 'none';
            } else {
                const err = await res.json();
                showToast(err.detail || "Quyết toán thất bại", "error");
            }
        } catch (e) {
            showToast("Lỗi kết nối", "error");
        }
    }
    
    function showInvoiceModal(inv) {
        const container = document.getElementById('invoice-details-content');
        
        let html = `
            <div class="invoice-title">HÓA ĐƠN CHI TIẾT SÂN BÓNG</div>
            <div class="invoice-meta">Mã hóa đơn: <strong>${inv.ma_hoa_don}</strong></div>
            <div class="invoice-meta">Mã đơn đặt sân: <strong>${inv.ma_don}</strong></div>
            <hr style="border: 0; border-top: 1px dashed rgba(255, 255, 255, 0.1); margin: 12px 0;">
            <div class="invoice-row"><span>Tiền thuê sân:</span><strong>${inv.tien_san.toLocaleString()} đ</strong></div>
            <div class="invoice-row"><span>Tiền dịch vụ:</span><strong>${inv.tong_dich_vu.toLocaleString()} đ</strong></div>
            <div class="invoice-row text-danger"><span>Trừ tiền cọc đã cọc:</span><strong>-${inv.tien_coc_da_tru.toLocaleString()} đ</strong></div>
            
            <div class="invoice-total"><span>Cần thanh toán:</span><span>${inv.tong_thanh_toan.toLocaleString()} đ</span></div>
            
            <div class="invoice-barcode">
                <div class="barcode-lines"></div>
                <div class="barcode-number">${inv.ma_hoa_don}</div>
            </div>
            
            <div class="invoice-footer-text">Cảm ơn anh/chị đã tin tưởng dịch vụ. Chúc anh/chị luôn giữ vững đam mê bóng đá phủi! ⚽</div>
        `;
        
        container.innerHTML = html;
        document.getElementById('modal-invoice').classList.add('active');
    }
    
    // ==========================================
    // AI Insights / Revenue Reports
    // ==========================================
    async function handleAIReport() {
        const summary = document.getElementById('ai-insight-summary');
        const list = document.getElementById('ai-promotions-list');
        
        summary.innerHTML = `<div class="loading-spinner"><i class="fa-solid fa-circle-notch fa-spin"></i> AI đang kết nối, truy xuất dữ liệu doanh thu thực tế và tổng hợp báo cáo...</div>`;
        list.innerHTML = "";
        
        const tuNgay = new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString().split('T')[0];
        const denNgay = new Date().toISOString().split('T')[0];
        
        try {
            const res = await fetch('/api/ai/report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ tu_ngay: tuNgay, den_ngay: denNgay })
            });
            
            if (res.ok) {
                const data = await res.json();
                summary.innerHTML = `
                    <div style="font-size: 14px; line-height: 1.6; color: #f1f5f9; padding: 10px;">
                        <h4 style="color: #34d399; margin-bottom: 10px;"><i class="fa-solid fa-sparkles"></i> Phân Tích Tổng Quan Bằng Trí Tuệ Nhân Tạo:</h4>
                        ${data.tom_tat}
                        <div style="margin-top: 15px; font-weight: 600;">Tỷ lệ lấp đầy trung bình tuần qua: <span style="color: #34d399;">${data.ty_le_lap_day}%</span></div>
                    </div>
                `;
                
                list.innerHTML = data.de_xuat.map(dx => `
                    <div class="promo-card">
                        <div class="promo-header"><i class="fa-solid fa-percent"></i> Đề Xuất Tối Ưu Lấp Đầy</div>
                        <div class="promo-body">${dx}</div>
                    </div>
                `).join('');
            } else {
                summary.innerHTML = `<div class="error-text">Lỗi phân tích AI. Vui lòng kiểm tra lại GEMINI_API_KEY.</div>`;
            }
        } catch (e) {
            summary.innerHTML = `<div class="error-text">Không thể kết nối.</div>`;
        }
    }
    
    // ==========================================
    // Admin Operations
    // ==========================================
    async function handleAdminCreateCourt(e) {
        e.preventDefault();
        
        const data = {
            ma: document.getElementById('adm-c-ma').value,
            ten_san: document.getElementById('adm-c-ten').value,
            loai_san_id: parseInt(document.getElementById('adm-c-loai').value),
            vi_tri: document.getElementById('adm-c-vitri').value || null,
            mo_ta_ai: document.getElementById('adm-c-mota').value || null
        };
        
        try {
            const res = await fetch('/api/san', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(data)
            });
            
            if (res.ok) {
                showToast("Thêm sân bóng mới thành công!");
                document.getElementById('form-admin-create-court').reset();
                fetchCourts();
            } else {
                const err = await res.json();
                showToast(err.detail || "Thêm sân thất bại", "error");
            }
        } catch (e) {
            showToast("Lỗi kết nối", "error");
        }
    }
    
    async function handleAdminAddPricing(e) {
        e.preventDefault();
        
        const data = {
            san_id: document.getElementById('adm-p-san').value,
            gio_bat_dau: document.getElementById('adm-p-start').value + ":00",
            gio_ket_thuc: document.getElementById('adm-p-end').value + ":00",
            don_gia: parseFloat(document.getElementById('adm-p-gia').value),
            loai_ngay: document.getElementById('adm-p-loai-ngay').value
        };
        
        try {
            const res = await fetch('/api/san/pricing', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(data)
            });
            
            if (res.ok) {
                showToast("Thiết lập bảng giá thành công!");
                document.getElementById('form-admin-add-pricing').reset();
            } else {
                const err = await res.json();
                showToast(err.detail || "Lỗi thêm bảng giá", "error");
            }
        } catch (e) {
            showToast("Lỗi kết nối", "error");
        }
    }

    // ==========================================
    // Admin Court Management (CRUD: Read, Update, Delete)
    // ==========================================
    async function loadAdminCourtsTable() {
        const tbody = document.getElementById('admin-courts-table-body');
        if (!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="7" class="text-center"><i class="fa-solid fa-circle-notch fa-spin"></i> Đang tải dữ liệu sân bóng...</td></tr>';
        
        try {
            const res = await fetch('/api/san');
            if (!res.ok) throw new Error("Không thể tải danh sách sân");
            const courts = await res.json();
            
            if (courts.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Chưa có sân bóng nào.</td></tr>';
                return;
            }
            
            tbody.innerHTML = courts.map(c => {
                let badgeClass = 'badge-success';
                let badgeText = '🟢 Hoạt động';
                if (c.trang_thai === 'maintenance') {
                    badgeClass = 'badge-warning';
                    badgeText = '🟡 Bảo trì';
                } else if (c.trang_thai === 'inactive') {
                    badgeClass = 'badge-danger';
                    badgeText = '🔴 Tạm ngưng';
                }
                
                const loaiName = c.loai_san ? c.loai_san.ten_loai : (c.loai_san_id === 1 ? 'Sân 7' : 'Sân 11');
                
                return `
                    <tr>
                        <td><strong style="color: var(--color-primary);">${c.ma}</strong></td>
                        <td><strong>${c.ten_san}</strong></td>
                        <td><span class="court-badge">${loaiName}</span></td>
                        <td>${c.vi_tri || '—'}</td>
                        <td><span class="badge ${badgeClass}">${badgeText}</span></td>
                        <td style="max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${c.mo_ta_ai || ''}">${c.mo_ta_ai || '—'}</td>
                        <td style="text-align: center; white-space: nowrap;">
                            <button class="btn btn-secondary btn-sm" onclick="openEditCourtModal('${c.ma}')" title="Chỉnh sửa thông tin sân" style="margin-right: 6px; padding: 4px 10px;">
                                <i class="fa-solid fa-pen-to-square"></i> Sửa
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="handleDeleteCourt('${c.ma}', '${c.ten_san}')" title="Xóa hoặc chuyển sang ngưng hoạt động" style="padding: 4px 10px;">
                                <i class="fa-solid fa-trash-can"></i> Xóa
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Lỗi khi tải danh sách sân bóng</td></tr>';
        }
    }

    window.openEditCourtModal = async function(ma) {
        try {
            const res = await fetch('/api/san');
            const courts = await res.json();
            const court = courts.find(c => c.ma === ma);
            if (!court) {
                showToast("Không tìm thấy thông tin sân!", "error");
                return;
            }
            
            document.getElementById('edit-c-ma').value = court.ma;
            document.getElementById('edit-c-ten').value = court.ten_san;
            document.getElementById('edit-c-vitri').value = court.vi_tri || '';
            document.getElementById('edit-c-mota').value = court.mo_ta_ai || '';
            document.getElementById('edit-c-trang-thai').value = court.trang_thai;
            
            // Populate loai_san select
            const loaiSelect = document.getElementById('edit-c-loai');
            loaiSelect.innerHTML = `
                <option value="1" ${court.loai_san_id === 1 ? 'selected' : ''}>Sân 7 người</option>
                <option value="2" ${court.loai_san_id === 2 ? 'selected' : ''}>Sân 11 người</option>
            `;
            
            document.getElementById('modal-edit-court').style.display = 'flex';
        } catch (e) {
            showToast("Lỗi mở form chỉnh sửa", "error");
        }
    };

    window.closeEditCourtModal = function() {
        const modal = document.getElementById('modal-edit-court');
        if (modal) modal.style.display = 'none';
    };

    async function handleEditCourtSubmit(e) {
        e.preventDefault();
        const ma = document.getElementById('edit-c-ma').value;
        const data = {
            ten_san: document.getElementById('edit-c-ten').value.trim(),
            loai_san_id: parseInt(document.getElementById('edit-c-loai').value),
            trang_thai: document.getElementById('edit-c-trang-thai').value,
            vi_tri: document.getElementById('edit-c-vitri').value.trim() || null,
            mo_ta_ai: document.getElementById('edit-c-mota').value.trim() || null
        };
        
        try {
            const res = await fetch(`/api/san/${ma}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(data)
            });
            
            if (res.ok) {
                showToast(`Cập nhật thông tin sân "${ma}" thành công!`);
                closeEditCourtModal();
                loadAdminCourtsTable();
                fetchCourts();
            } else {
                const err = await res.json();
                showToast(err.detail || "Cập nhật sân thất bại", "error");
            }
        } catch (e) {
            showToast("Lỗi kết nối máy chủ", "error");
        }
    }

    window.handleDeleteCourt = async function(ma, tenSan) {
        if (!confirm(`Bạn có chắc chắn muốn xóa sân "${tenSan}" (${ma})?\n\n- Nếu sân đã có đơn đặt, hệ thống sẽ tự động chuyển sang "Tạm ngưng" (inactive) để bảo vệ lịch sử hóa đơn.\n- Nếu sân chưa có đơn đặt nào, hệ thống sẽ xóa hoàn toàn.`)) {
            return;
        }
        
        try {
            const res = await fetch(`/api/san/${ma}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (res.ok) {
                const result = await res.json();
                showToast(result.message || "Đã xóa sân thành công!");
                loadAdminCourtsTable();
                fetchCourts();
            } else {
                const err = await res.json();
                showToast(err.detail || "Lỗi khi xóa sân", "error");
            }
        } catch (e) {
            showToast("Lỗi kết nối máy chủ", "error");
        }
    };

    // ==========================================
    // Utility Helpers
    // ==========================================
    function getTodayString() {
        const d = new Date();
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    function formatDateString(str) {
        if (!str) return '';
        const parts = str.split('-');
        if (parts.length !== 3) return str;
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        let icon = '<i class="fa-solid fa-circle-check"></i>';
        if (type === 'error') icon = '<i class="fa-solid fa-circle-xmark"></i>';
        if (type === 'warning') icon = '<i class="fa-solid fa-circle-exclamation"></i>';
        
        toast.innerHTML = `${icon} <span>${message}</span>`;
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    function formatCourtType(type) {
        if (type === 'FOOTBALL_5') return 'Sân 5';
        if (type === 'FOOTBALL_7') return 'Sân 7';
        if (type === 'FOOTBALL_11') return 'Sân 11';
        if (type === 'FUTSAL') return 'Futsal';
        return type;
    }
});
