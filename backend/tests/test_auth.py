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


# ============================================================
# Test Case Chức năng Đổi Mật Khẩu (TC1 - TC7)
# Khớp 100% với bảng quyết định trong tài liệu kiểm thử
# C1: mat_khau_hien_tai | C2: mat_khau_moi | C3: xac_nhan_mat_khau_moi
# ============================================================

@pytest.fixture
def authenticated_client(client_and_db):
    """Fixture tạo client đã đăng nhập sẵn để test đổi mật khẩu."""
    client, session = client_and_db
    # Đăng ký tài khoản với mật khẩu ban đầu là 123456
    client.post('/api/auth/register', json={
        'ten_dang_nhap': 'testuser',
        'mat_khau': '123456',
        'ho_ten': 'Test User',
        'so_dien_thoai': '0912345678'
    })
    # Đăng nhập lấy token
    res_login = client.post('/api/auth/login', json={
        'ten_dang_nhap': 'testuser',
        'mat_khau': '123456'
    })
    token = res_login.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    return client, headers


def test_doi_mat_khau_tc1_thanh_cong(authenticated_client):
    """TC1: Đổi mật khẩu thành công — C1=T, C2=T, C3=T.
    Mật khẩu hiện tại: 123456 | Mới: Abc@123 | Xác nhận: Abc@123
    """
    client, headers = authenticated_client
    res = client.post('/api/auth/change-password', json={
        'mat_khau_hien_tai': '123456',
        'mat_khau_moi': 'Abc@123',
        'xac_nhan_mat_khau_moi': 'Abc@123'
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()['message'] == 'Đổi mật khẩu thành công'


def test_doi_mat_khau_tc2_xac_nhan_khong_khop(authenticated_client):
    """TC2: Đổi mật khẩu thất bại — C1=T, C2=T, C3=F.
    Xác nhận mật khẩu không khớp với mật khẩu mới.
    Mới: Abc@123 | Xác nhận: Abc@999
    """
    client, headers = authenticated_client
    res = client.post('/api/auth/change-password', json={
        'mat_khau_hien_tai': '123456',
        'mat_khau_moi': 'Abc@123',
        'xac_nhan_mat_khau_moi': 'Abc@999'
    }, headers=headers)
    assert res.status_code == 422
    assert 'không khớp' in res.json()['detail']


def test_doi_mat_khau_tc3_xac_nhan_de_trong(authenticated_client):
    """TC3: Đổi mật khẩu thất bại — C1=T, C2=T, C3=B.
    Xác nhận mật khẩu để trống.
    """
    client, headers = authenticated_client
    res = client.post('/api/auth/change-password', json={
        'mat_khau_hien_tai': '123456',
        'mat_khau_moi': 'Abc@123',
        'xac_nhan_mat_khau_moi': ''
    }, headers=headers)
    assert res.status_code == 422
    assert 'xác nhận mật khẩu mới' in res.json()['detail'].lower()


def test_doi_mat_khau_tc4_mat_khau_moi_de_trong(authenticated_client):
    """TC4: Đổi mật khẩu thất bại — C1=T, C2=B, C3=–.
    Mật khẩu mới để trống.
    """
    client, headers = authenticated_client
    res = client.post('/api/auth/change-password', json={
        'mat_khau_hien_tai': '123456',
        'mat_khau_moi': '',
        'xac_nhan_mat_khau_moi': ''
    }, headers=headers)
    assert res.status_code == 422
    assert 'mật khẩu mới' in res.json()['detail'].lower()


def test_doi_mat_khau_tc5_mat_khau_moi_khong_hop_le(authenticated_client):
    """TC5: Đổi mật khẩu thất bại — C1=T, C2=F, C3=–.
    Mật khẩu mới không hợp lệ (ít hơn 6 ký tự).
    Mật khẩu mới: 123
    """
    client, headers = authenticated_client
    res = client.post('/api/auth/change-password', json={
        'mat_khau_hien_tai': '123456',
        'mat_khau_moi': '123',
        'xac_nhan_mat_khau_moi': '123'
    }, headers=headers)
    assert res.status_code == 422
    assert 'không hợp lệ' in res.json()['detail']


def test_doi_mat_khau_tc6_mat_khau_hien_tai_sai(authenticated_client):
    """TC6: Đổi mật khẩu thất bại — C1=F, C2=–, C3=–.
    Mật khẩu hiện tại nhập sai.
    """
    client, headers = authenticated_client
    res = client.post('/api/auth/change-password', json={
        'mat_khau_hien_tai': 'sai_mat_khau',
        'mat_khau_moi': 'Abc@123',
        'xac_nhan_mat_khau_moi': 'Abc@123'
    }, headers=headers)
    assert res.status_code == 400
    assert 'không đúng' in res.json()['detail']


def test_doi_mat_khau_tc7_mat_khau_hien_tai_de_trong(authenticated_client):
    """TC7: Đổi mật khẩu thất bại — C1=B, C2=–, C3=–.
    Mật khẩu hiện tại để trống.
    """
    client, headers = authenticated_client
    res = client.post('/api/auth/change-password', json={
        'mat_khau_hien_tai': '',
        'mat_khau_moi': 'Abc@123',
        'xac_nhan_mat_khau_moi': 'Abc@123'
    }, headers=headers)
    assert res.status_code == 422
    assert 'mật khẩu hiện tại' in res.json()['detail'].lower()


def test_doi_mat_khau_thuc_su_luu_vao_db(client_and_db):
    """Xác minh mật khẩu mới thực sự được lưu vào database:
    Sau khi đổi mật khẩu thành công, đăng nhập với mật khẩu cũ phải thất bại,
    đăng nhập với mật khẩu mới phải thành công.
    """
    client, session = client_and_db

    # 1. Đăng ký tài khoản
    client.post('/api/auth/register', json={
        'ten_dang_nhap': 'dbverifyuser',
        'mat_khau': 'OldPass123',
        'ho_ten': 'DB Verify User',
        'so_dien_thoai': '0911222333'
    })

    # 2. Đăng nhập lấy token
    res_login = client.post('/api/auth/login', json={
        'ten_dang_nhap': 'dbverifyuser',
        'mat_khau': 'OldPass123'
    })
    assert res_login.status_code == 200
    token = res_login.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # 3. Đổi mật khẩu
    res_change = client.post('/api/auth/change-password', json={
        'mat_khau_hien_tai': 'OldPass123',
        'mat_khau_moi': 'NewPass456',
        'xac_nhan_mat_khau_moi': 'NewPass456'
    }, headers=headers)
    assert res_change.status_code == 200
    assert res_change.json()['message'] == 'Đổi mật khẩu thành công'

    # 4. Đăng nhập bằng mật khẩu CŨ → PHẢI THẤT BẠI (xác minh DB đã cập nhật)
    res_old = client.post('/api/auth/login', json={
        'ten_dang_nhap': 'dbverifyuser',
        'mat_khau': 'OldPass123'
    })
    assert res_old.status_code == 401, "Mật khẩu cũ vẫn hoạt động — DB chưa được cập nhật!"

    # 5. Đăng nhập bằng mật khẩu MỚI → PHẢI THÀNH CÔNG
    res_new = client.post('/api/auth/login', json={
        'ten_dang_nhap': 'dbverifyuser',
        'mat_khau': 'NewPass456'
    })
    assert res_new.status_code == 200, "Mật khẩu mới không hoạt động — DB chưa lưu đúng!"
    assert 'access_token' in res_new.json()

