/**
 * MINI VICTORY v2.0 - LANDING PAGE CONTROLLER
 * Single Source of Truth for App Navigation: APP_URL
 * Synchronizes Theme with Main App via localStorage key: 'va_theme'
 */

// 1. DUY NHẤT MỘT HẰNG SỐ ĐƯỜNG DẪN ỨNG DỤNG CHÍNH (theo ràng buộc số 4)
const APP_URL = 'index.html';

document.addEventListener('DOMContentLoaded', () => {
    initThemeManager();
    initNavigation();
    initScrollReveal();
    initAppRoutingButtons();
    initFaqAccordion();
    initHuskyMicroInteraction();
});

/* ==========================================================================
   THEME SYNCHRONIZATION MODULE (Dark / Light)
   Reads & writes to 'va_theme', sets html[data-theme]
   ========================================================================== */
function initThemeManager() {
    const themeBtn = document.getElementById('btn-theme-toggle');
    const themeIcon = document.getElementById('theme-toggle-icon');
    const themeText = document.getElementById('theme-toggle-text');
    
    const mobileThemeBtn = document.getElementById('btn-mobile-theme-toggle');
    const mobileThemeIcon = document.getElementById('mobile-theme-toggle-icon');
    const mobileThemeText = document.getElementById('mobile-theme-toggle-text');

    function getStoredTheme() {
        try {
            return localStorage.getItem('va_theme') || 'dark';
        } catch (e) {
            return 'dark';
        }
    }

    function setStoredTheme(theme) {
        try {
            localStorage.setItem('va_theme', theme);
        } catch (e) {
            console.warn('[Theme] Không thể lưu theme vào localStorage:', e);
        }
    }

    function updateUI(theme) {
        const isLight = theme === 'light';
        const iconSvg = isLight ? '☀️' : '🌙';
        const labelText = isLight ? 'Sáng' : 'Tối';

        if (themeIcon) themeIcon.textContent = iconSvg;
        if (themeText) themeText.textContent = labelText;
        if (mobileThemeIcon) mobileThemeIcon.textContent = iconSvg;
        if (mobileThemeText) mobileThemeText.textContent = labelText;

        if (themeBtn) {
            themeBtn.setAttribute('title', isLight ? 'Chuyển sang Giao diện Tối' : 'Chuyển sang Giao diện Sáng');
            themeBtn.setAttribute('aria-label', isLight ? 'Chuyển sang Giao diện Tối' : 'Chuyển sang Giao diện Sáng');
        }
    }

    function applyTheme(theme) {
        const validTheme = (theme === 'light') ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', validTheme);
        setStoredTheme(validTheme);
        updateUI(validTheme);
    }

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || getStoredTheme();
        const nextTheme = (currentTheme === 'light') ? 'dark' : 'light';
        applyTheme(nextTheme);

        // Icon rotation animation
        if (themeIcon) {
            themeIcon.classList.add('theme-icon-rotate');
            setTimeout(() => themeIcon.classList.remove('theme-icon-rotate'), 400);
        }
    }

    // Initialize state
    const currentTheme = document.documentElement.getAttribute('data-theme') || getStoredTheme();
    applyTheme(currentTheme);

    if (themeBtn) {
        themeBtn.addEventListener('click', toggleTheme);
    }
    if (mobileThemeBtn) {
        mobileThemeBtn.addEventListener('click', toggleTheme);
    }
}

/* ==========================================================================
   NAVIGATION & MOBILE DRAWER MODULE
   ========================================================================== */
function initNavigation() {
    const mobileToggle = document.getElementById('btn-mobile-nav');
    const mobileDrawer = document.getElementById('mobile-drawer');
    const navLinks = document.querySelectorAll('.nav-link, .mobile-nav-link');

    if (mobileToggle && mobileDrawer) {
        mobileToggle.addEventListener('click', () => {
            const isOpen = mobileDrawer.classList.toggle('is-open');
            mobileToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            mobileToggle.innerHTML = isOpen 
                ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>'
                : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
        });

        // Close drawer when clicking any anchor link
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (mobileDrawer.classList.contains('is-open')) {
                    mobileDrawer.classList.remove('is-open');
                    mobileToggle.setAttribute('aria-expanded', 'false');
                    mobileToggle.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
                }
            });
        });

        // Close drawer when clicking outside
        document.addEventListener('click', (e) => {
            if (mobileDrawer.classList.contains('is-open') && 
                !mobileDrawer.contains(e.target) && 
                !mobileToggle.contains(e.target)) {
                mobileDrawer.classList.remove('is-open');
                mobileToggle.setAttribute('aria-expanded', 'false');
                mobileToggle.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
            }
        });
    }
}

/* ==========================================================================
   ROUTING CTA BUTTONS MODULE
   All login / register buttons route via APP_URL
   ========================================================================== */
function initAppRoutingButtons() {
    const appButtons = document.querySelectorAll('[data-app-route]');
    appButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const routeType = btn.getAttribute('data-app-route');
            if (routeType === 'register') {
                window.location.href = APP_URL + '#register';
            } else {
                window.location.href = APP_URL + '#login';
            }
        });
    });
}

/* ==========================================================================
   SCROLL REVEAL (IntersectionObserver with reduced-motion support)
   ========================================================================== */
function initScrollReveal() {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const revealElements = document.querySelectorAll('.reveal-on-scroll');

    if (prefersReducedMotion || !('IntersectionObserver' in window)) {
        revealElements.forEach(el => el.classList.add('is-visible'));
        return;
    }

    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                obs.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.12,
        rootMargin: '0px 0px -40px 0px'
    });

    revealElements.forEach(el => observer.observe(el));
}

/* ==========================================================================
   FAQ ACCORDION ENHANCEMENT
   Smooth auto-close behavior when another item opens
   ========================================================================== */
function initFaqAccordion() {
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        item.addEventListener('toggle', () => {
            if (item.open) {
                faqItems.forEach(otherItem => {
                    if (otherItem !== item && otherItem.open) {
                        otherItem.removeAttribute('open');
                    }
                });
            }
        });
    });
}

/* ==========================================================================
   HUSKY MASCOT HERO MICRO-INTERACTION
   Fun friendly interaction when clicking the Mascot badge
   ========================================================================== */
function initHuskyMicroInteraction() {
    const mascotBadge = document.getElementById('hero-husky-mascot-card');
    const mascotBubble = document.getElementById('hero-husky-msg-text');
    if (!mascotBadge || !mascotBubble) return;

    const friendlyMessages = [
        "Chào bạn! Cần tìm sân 7 hay sân 11 tối nay?",
        "Sân 7A - Phủi Pro vừa có ca 18:30 cực đẹp!",
        "Đặt sân quét VietQR chỉ mất đúng 30 giây nha!",
        "Cần tư vấn chiến thuật bắt đối? Hỏi mình ngay!"
    ];
    let msgIndex = 0;

    mascotBadge.addEventListener('click', () => {
        msgIndex = (msgIndex + 1) % friendlyMessages.length;
        mascotBubble.style.opacity = '0';
        mascotBubble.style.transform = 'translateY(4px)';
        setTimeout(() => {
            mascotBubble.textContent = friendlyMessages[msgIndex];
            mascotBubble.style.opacity = '1';
            mascotBubble.style.transform = 'translateY(0)';
        }, 150);
    });
}
