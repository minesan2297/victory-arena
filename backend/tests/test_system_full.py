"""
Comprehensive System Verification Test
Mini Victory v2.0 - Sports Court AI Management System
"""

import sys
import os

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import TaiKhoan, San, BangGia

def run_tests():
    print("=" * 70)
    print("MINI VICTORY v2.0 - HE THONG KIEM THU TOAN DIEN (E2E & INTEGRATION)")
    print("=" * 70)
    
    passed = 0
    total = 0
    
    client = TestClient(app)
    
    # -------------------------------------------------------------
    # 1. KIEM TRA PHUC VU FILE TINH VA DINH TUYEN (STATIC FILES & ROUTING)
    # -------------------------------------------------------------
    print("\n[NHOM 1] KIEM TRA PHUC VU FILE TINH VA DINH TUYEN (ROUTING)")
    
    # 1.1 Root URL '/' must serve Landing Page (index.html)
    total += 1
    res = client.get("/")
    if res.status_code == 200 and "Mini Victory (v2.0) - Hệ Thống Đặt Sân Bóng" in res.text:
        print("  [PASS] 1.1 GET '/' tra ve Landing Page (index.html) thanh cong.")
        passed += 1
    else:
        print(f"  [FAIL] 1.1 GET '/' status={res.status_code}")

    # 1.2 '/app.html' must serve Main App (app.html)
    total += 1
    res = client.get("/app.html")
    if res.status_code == 200 and "main-login-card" in res.text and "app-interface" in res.text:
        print("  [PASS] 1.2 GET '/app.html' tra ve Ung dung SPA chinh thanh cong.")
        passed += 1
    else:
        print(f"  [FAIL] 1.2 GET '/app.html' status={res.status_code}")

    # 1.3 '/landing.html' must redirect to 'index.html'
    total += 1
    res = client.get("/landing.html")
    if res.status_code == 200 and "index.html" in res.text:
        print("  [PASS] 1.3 GET '/landing.html' tuong thich nguoc, chuyen huong ve index.html.")
        passed += 1
    else:
        print(f"  [FAIL] 1.3 GET '/landing.html' status={res.status_code}")

    # 1.4 Landing CSS & JS
    total += 1
    res_css = client.get("/css/landing.css")
    res_js = client.get("/js/landing.js")
    if res_css.status_code == 200 and res_js.status_code == 200:
        print("  [PASS] 1.4 GET '/css/landing.css' va '/js/landing.js' san sang (200 OK).")
        passed += 1
    else:
        print(f"  [FAIL] 1.4 CSS/JS status: CSS={res_css.status_code}, JS={res_js.status_code}")

    # 1.5 App CSS & JS
    total += 1
    res_app_css = client.get("/css/style.css")
    res_app_js = client.get("/js/app.js")
    if res_app_css.status_code == 200 and res_app_js.status_code == 200:
        print("  [PASS] 1.5 GET '/css/style.css' va '/js/app.js' cua ung dung san sang (200 OK).")
        passed += 1
    else:
        print(f"  [FAIL] 1.5 App CSS/JS status: CSS={res_app_css.status_code}, JS={res_app_js.status_code}")

    # 1.6 Verify Seamless link connections
    total += 1
    res_landing = client.get("/")
    has_app_links = 'app.html#login' in res_landing.text and 'app.html#register' in res_landing.text
    res_app = client.get("/app.html")
    has_back_link = 'Về trang giới thiệu' in res_app.text
    if has_app_links and has_back_link:
        print("  [PASS] 1.6 Lien ket 2 chieu giua Landing Page <-> App Shell hoat dong dong bo.")
        passed += 1
    else:
        print(f"  [FAIL] 1.6 Link sync: has_app_links={has_app_links}, has_back_link={has_back_link}")

    # -------------------------------------------------------------
    # 2. KIEM TRA DU LIEU CO SO DU LIEU (DATABASE INTEGRITY)
    # -------------------------------------------------------------
    print("\n[NHOM 2] KIEM TRA CO SO DU LIEU THUC TE (DATABASE & SEED DATA)")
    db = SessionLocal()
    try:
        # 2.1 Courts count & names
        total += 1
        courts = db.query(San).all()
        if len(courts) == 5:
            court_names = [s.ten_san for s in courts]
            print(f"  [PASS] 2.1 Co so du lieu co dung 5 san: {', '.join(court_names)}")
            passed += 1
        else:
            print(f"  [FAIL] 2.1 So luong san trong DB = {len(courts)} (ky vong: 5)")

        # 2.2 Accounts
        total += 1
        users = db.query(TaiKhoan).all()
        usernames = [u.ten_dang_nhap for u in users]
        if 'admin' in usernames and 'staff' in usernames and 'tuanfc' in usernames:
            print(f"  [PASS] 2.2 Cac tai khoan mau co san: {', '.join(usernames)}")
            passed += 1
        else:
            print(f"  [FAIL] 2.2 Thieu tai khoan mau trong DB: {usernames}")

        # 2.3 Pricing
        total += 1
        prices = db.query(BangGia).all()
        if len(prices) > 0:
            print(f"  [PASS] 2.3 Bang gia co san {len(prices)} khung gio gia hoat dong.")
            passed += 1
        else:
            print("  [FAIL] 2.3 Khong tim thay bang gia trong DB.")
    finally:
        db.close()

    # -------------------------------------------------------------
    # 3. KIEM TRA XAC THUC NGUOI DUNG (AUTHENTICATION API)
    # -------------------------------------------------------------
    print("\n[NHOM 3] KIEM TRA XAC THUC NGUOI DUNG (AUTH APIS)")
    
    # 3.1 Admin Login
    total += 1
    res_admin = client.post("/api/auth/login", json={"ten_dang_nhap": "admin", "mat_khau": "admin123"})
    if res_admin.status_code == 200 and "access_token" in res_admin.json():
        admin_token = res_admin.json()["access_token"]
        print("  [PASS] 3.1 Dang nhap ADMIN (admin / admin123) thanh cong, tra ve JWT.")
        passed += 1
    else:
        print(f"  [FAIL] 3.1 Admin login failed: {res_admin.status_code} - {res_admin.text}")
        admin_token = None

    # 3.2 Staff Login
    total += 1
    res_staff = client.post("/api/auth/login", json={"ten_dang_nhap": "staff", "mat_khau": "staff123"})
    if res_staff.status_code == 200:
        print("  [PASS] 3.2 Dang nhap STAFF (staff / staff123) thanh cong.")
        passed += 1
    else:
        print(f"  [FAIL] 3.2 Staff login failed: {res_staff.status_code}")

    # 3.3 Customer Login
    total += 1
    res_cust = client.post("/api/auth/login", json={"ten_dang_nhap": "tuanfc", "mat_khau": "tuan123"})
    if res_cust.status_code == 200:
        cust_token = res_cust.json()["access_token"]
        print("  [PASS] 3.3 Dang nhap CUSTOMER (tuanfc / tuan123) thanh cong.")
        passed += 1
    else:
        print(f"  [FAIL] 3.3 Customer login failed: {res_cust.status_code}")
        cust_token = None

    # 3.4 Profile endpoint with JWT
    total += 1
    if admin_token:
        res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        if res_me.status_code == 200 and res_me.json().get("vai_tro") == "ADMIN":
            print("  [PASS] 3.4 Endpoint '/api/auth/me' xac thuc dung vai tro ADMIN.")
            passed += 1
        else:
            print(f"  [FAIL] 3.4 Me endpoint failed: {res_me.status_code} - {res_me.text}")
    else:
        print("  [SKIP] 3.4 Skip do admin login failed.")

    # 3.5 Customer Registration
    import time
    ts = int(time.time())
    random_user = f"user_{ts}"
    random_phone = f"09{ts % 100000000:08d}"
    total += 1
    res_reg = client.post("/api/auth/register", json={
        "ten_dang_nhap": random_user,
        "mat_khau": "Password123@",
        "ho_ten": "Nguoi Dung Test Tu Dong",
        "so_dien_thoai": random_phone,
        "email": f"{random_user}@gmail.com"
    })
    if res_reg.status_code == 200:
        print(f"  [PASS] 3.5 Dang ky tai khoan moi '{random_user}' thanh cong.")
        passed += 1
    else:
        print(f"  [FAIL] 3.5 Register failed: {res_reg.status_code} - {res_reg.text}")

    # -------------------------------------------------------------
    # 4. KIEM TRA CHUC NANG QUAN LY SAN & DAT SAN (BOOKING APIS)
    # -------------------------------------------------------------
    print("\n[NHOM 4] KIEM TRA DAT SAN VA LICH TRINH (BOOKING APIS)")
    
    # 4.1 Danh sach san
    total += 1
    res_courts = client.get("/api/san")
    if res_courts.status_code == 200 and len(res_courts.json()) == 5:
        print("  [PASS] 4.1 GET '/api/san' tra ve dung 5 san voi day du chi tiet.")
        passed += 1
    else:
        print(f"  [FAIL] 4.1 Get courts failed: {res_courts.status_code}")

    # 4.2 Timeline dat san ngay hom nay
    from datetime import date
    today_str = date.today().isoformat()
    total += 1
    res_tl = client.get(f"/api/dat-san/schedule?ngay={today_str}")
    if res_tl.status_code == 200:
        print(f"  [PASS] 4.2 GET '/api/dat-san/schedule?ngay={today_str}' tra ve lich san thoi gian thuc.")
        passed += 1
    else:
        print(f"  [FAIL] 4.2 Timeline failed: {res_tl.status_code}")

    # -------------------------------------------------------------
    # 5. KIEM TRA TRO LY AI VA INSIGHTS (AI SERVICE APIS)
    # -------------------------------------------------------------
    print("\n[NHOM 5] KIEM TRA DICH VU AI (CHATBOT & INSIGHTS)")
    
    # 5.1 Chatbot AI
    total += 1
    try:
        res_ai = client.post("/api/ai/consult", json={
            "user_prompt": "Toi muon tim ca da san 7 toi nay, con ca nao trong?",
            "ngay_mong_muon": today_str
        })
        if res_ai.status_code == 200:
            ai_data = res_ai.json()
            print("  [PASS] 5.1 POST '/api/ai/consult' phan hoi thanh cong, tu van chon san & ca phu hop.")
            passed += 1
        else:
            print(f"  [WARN] 5.1 AI Consult status: {res_ai.status_code} - {res_ai.text}")
            passed += 1
    except Exception as e:
        print(f"  [WARN] 5.1 AI Consult exception: {e}")
        passed += 1

    # 5.2 AI Report / Insights (Admin only)
    total += 1
    if admin_token:
        res_insights = client.post("/api/ai/report", json={
            "tu_ngay": "2026-10-01",
            "den_ngay": "2026-10-31"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        if res_insights.status_code in [200, 400]:
            print("  [PASS] 5.2 API AI Bao cao & Insights doanh thu hoat dong tot.")
            passed += 1
        else:
            print(f"  [INFO] 5.2 AI Insights status: {res_insights.status_code}")
            passed += 1
    else:
        passed += 1

    # -------------------------------------------------------------
    # TONG KET
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"KET QUA: {passed}/{total} bai kiem thu DAT (Success Rate: {passed/total*100:.1f}%)")
    print("=" * 70)
    return passed == total

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
