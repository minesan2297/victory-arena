import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app as fastapi_app
from app.models import VaiTro, TaiKhoan, LoaiSan, San, BangGia, DatSan, LichDat, ThanhToan
from app.models.ai_models import ThongBao

from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="function")
def client_and_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed VaiTro
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

def test_register_success(client_and_db):
    client, session = client_and_db
    res = client.post('/api/auth/register', json={
        'ten_dang_nhap': 'nguyenvana',
        'mat_khau': 'password123',
        'ho_ten': 'Nguyễn Văn A',
        'so_dien_thoai': '0988111222',
        'email': 'vana@gmail.com'
    })
    assert res.status_code == 200
    data = res.json()
    assert data['ten_dang_nhap'] == 'nguyenvana'
    assert data['vai_tro'] == 'CUSTOMER'

def test_register_reject_vietnamese_diacritics_in_username(client_and_db):
    """Tên đăng nhập có dấu tiếng Việt phải bị từ chối."""
    client, session = client_and_db
    res = client.post('/api/auth/register', json={
        'ten_dang_nhap': 'nguyễn_văn_a',
        'mat_khau': 'password123',
        'ho_ten': 'Nguyễn Văn A',
        'so_dien_thoai': '0988111223'
    })
    assert res.status_code == 422
    assert "chỉ được chứa chữ cái không dấu" in res.json()['detail']

def test_register_reject_whitespace_in_username(client_and_db):
    """Tên đăng nhập chứa khoảng trắng phải bị từ chối."""
    client, session = client_and_db
    res = client.post('/api/auth/register', json={
        'ten_dang_nhap': 'user name 99',
        'mat_khau': 'password123',
        'ho_ten': 'Nguyễn Văn B',
        'so_dien_thoai': '0988111224'
    })
    assert res.status_code == 422
    assert "khoảng trắng" in res.json()['detail']

def test_register_reject_whitespace_in_password(client_and_db):
    """Mật khẩu chứa khoảng trắng phải bị từ chối."""
    client, session = client_and_db
    res = client.post('/api/auth/register', json={
        'ten_dang_nhap': 'uservalid',
        'mat_khau': 'pass word 123',
        'ho_ten': 'Nguyễn Văn C',
        'so_dien_thoai': '0988111225'
    })
    assert res.status_code == 422
    assert "Mật khẩu không được chứa khoảng trắng" in res.json()['detail']

def test_register_reject_only_spaces_password(client_and_db):
    """Mật khẩu chỉ toàn dấu cách phải bị từ chối."""
    client, session = client_and_db
    res = client.post('/api/auth/register', json={
        'ten_dang_nhap': 'uservalid2',
        'mat_khau': '      ',
        'ho_ten': 'Nguyễn Văn D',
        'so_dien_thoai': '0988111226'
    })
    assert res.status_code == 422

def test_register_reject_invalid_phone(client_and_db):
    """Số điện thoại không đúng chuẩn đầu số VN phải bị từ chối."""
    client, session = client_and_db
    res = client.post('/api/auth/register', json={
        'ten_dang_nhap': 'userphone',
        'mat_khau': 'password123',
        'ho_ten': 'Nguyễn Văn E',
        'so_dien_thoai': '0123456789'
    })
    assert res.status_code == 422
    assert "Số điện thoại không hợp lệ" in res.json()['detail']

def test_login_success_and_whitespace_trim(client_and_db):
    """Đăng nhập thành công, tự động trim khoảng trắng thừa đầu/cuối của username."""
    client, session = client_and_db
    # 1. Đăng ký
    client.post('/api/auth/register', json={
        'ten_dang_nhap': 'playerone',
        'mat_khau': 'playerpass123',
        'ho_ten': 'Player One',
        'so_dien_thoai': '0988999888'
    })
    # 2. Đăng nhập với khoảng trắng thừa ở đầu/cuối
    res = client.post('/api/auth/login', json={
        'ten_dang_nhap': '   playerone   ',
        'mat_khau': 'playerpass123'
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_login_reject_empty_password(client_and_db):
    """Đăng nhập với mật khẩu rỗng hoặc toàn dấu cách."""
    client, session = client_and_db
    res = client.post('/api/auth/login', json={
        'ten_dang_nhap': 'playerone',
        'mat_khau': '   '
    })
    assert res.status_code == 422
