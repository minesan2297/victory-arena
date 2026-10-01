"""Cấu hình chung và các fixtures tái sử dụng cho toàn bộ Pytest Suite."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app as fastapi_app
from app.models import VaiTro, TaiKhoan, LoaiSan, San, BangGia
from app.auth.security import hash_password


@pytest.fixture(scope="function")
def client_and_db():
    """Tạo Database In-Memory cô lập cho từng test case, đảm bảo 100% không đụng chạm DB thật."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed VaiTro hệ thống
    v_admin = VaiTro(ten_vai_tro="ADMIN", mo_ta="Quản trị viên")
    v_staff = VaiTro(ten_vai_tro="STAFF", mo_ta="Nhân viên")
    v_customer = VaiTro(ten_vai_tro="CUSTOMER", mo_ta="Khách hàng")
    session.add_all([v_admin, v_staff, v_customer])
    session.commit()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    client = TestClient(fastapi_app)

    yield client, session

    fastapi_app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def authenticated_client(client_and_db):
    """Fixture tạo client khách hàng đã đăng nhập sẵn với JWT Token."""
    client, session = client_and_db
    client.post('/api/auth/register', json={
        'ten_dang_nhap': 'testuser',
        'mat_khau': '123456',
        'ho_ten': 'Test User',
        'so_dien_thoai': '0912345678'
    })
    res_login = client.post('/api/auth/login', json={
        'ten_dang_nhap': 'testuser',
        'mat_khau': '123456'
    })
    token = res_login.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    return client, headers


@pytest.fixture(scope="function")
def staff_client(client_and_db):
    """Fixture tạo client nhân viên (STAFF) có quyền check-in, check-out, lập hóa đơn."""
    client, session = client_and_db
    v_staff = session.query(VaiTro).filter_by(ten_vai_tro="STAFF").first()
    staff_user = TaiKhoan(
        ten_dang_nhap="staff01",
        mat_khau_hash=hash_password("staff123"),
        ho_ten="Nhân Viên Sân",
        so_dien_thoai="0911000222",
        vai_tro_id=v_staff.vai_tro_id,
        trang_thai="active"
    )
    session.add(staff_user)
    session.commit()

    res_login = client.post('/api/auth/login', json={
        'ten_dang_nhap': 'staff01',
        'mat_khau': 'staff123'
    })
    token = res_login.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    return client, headers


@pytest.fixture(scope="function")
def admin_client(client_and_db):
    """Fixture tạo client quản trị viên (ADMIN) có quyền xem báo cáo doanh thu."""
    client, session = client_and_db
    v_admin = session.query(VaiTro).filter_by(ten_vai_tro="ADMIN").first()
    admin_user = TaiKhoan(
        ten_dang_nhap="admin01",
        mat_khau_hash=hash_password("admin123"),
        ho_ten="Quản Trị Viên",
        so_dien_thoai="0911000333",
        vai_tro_id=v_admin.vai_tro_id,
        trang_thai="active"
    )
    session.add(admin_user)
    session.commit()

    res_login = client.post('/api/auth/login', json={
        'ten_dang_nhap': 'admin01',
        'mat_khau': 'admin123'
    })
    token = res_login.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    return client, headers
