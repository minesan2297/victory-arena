import pytest
from datetime import date, time, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import VaiTro, TaiKhoan, LoaiSan, San, BangGia, DatSan, LichDat
from app.models.enums import VaiTroEnum
from app.services.ai_service import AIService

@pytest.fixture(scope="function")
def db_session():
    """Tạo database SQLite in-memory cho test suite AI."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    # Seed VaiTro
    v_admin = VaiTro(ten_vai_tro="ADMIN", mo_ta="Quản trị viên")
    v_customer = VaiTro(ten_vai_tro="CUSTOMER", mo_ta="Khách hàng")
    session.add_all([v_admin, v_customer])
    session.flush()

    # Seed LoaiSan
    l7 = LoaiSan(ten_loai="Sân 7", so_nguoi_tieu_chuan=7)
    l5 = LoaiSan(ten_loai="Sân 5", so_nguoi_tieu_chuan=5)
    session.add_all([l7, l5])
    session.flush()

    # Seed TaiKhoan
    customer = TaiKhoan(
        ten_dang_nhap="khach_test",
        mat_khau_hash="hash",
        ho_ten="Phạm Nhật Minh",
        so_dien_thoai="0912345678",
        vai_tro_id=v_customer.vai_tro_id
    )
    session.add(customer)

    # Seed Sân
    s7 = San(ma="SAN7-VANG", ten_san="Sân 7 Sao Vàng", loai_san_id=l7.loai_san_id, trang_thai="active")
    s5 = San(ma="SAN5-MINI", ten_san="Sân 5 Mini", loai_san_id=l5.loai_san_id, trang_thai="active")
    session.add_all([s7, s5])
    session.flush()

    # Seed BangGia
    bg7 = BangGia(san_id=s7.ma, gio_bat_dau=time(6, 0), gio_ket_thuc=time(23, 0), don_gia=500000.0, loai_ngay="thuong")
    bg5 = BangGia(san_id=s5.ma, gio_bat_dau=time(6, 0), gio_ket_thuc=time(23, 0), don_gia=200000.0, loai_ngay="thuong")
    session.add_all([bg7, bg5])
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

def test_ai_consult_recommendation(db_session):
    """Kiểm tra AI tư vấn đúng loại sân theo yêu cầu ngôn ngữ tự nhiên."""
    test_date = date(2026, 9, 5)
    prompt = "Khách muốn tìm sân bóng 7 người tối thứ Sáu khoảng 19h"

    res = AIService.consult_pitch(db_session, user_prompt=prompt, ngay_mong_muon=test_date)

    assert res.co_san_phu_hop is True
    assert len(res.recommended_slots) > 0
    # Tất cả slot gợi ý phải là Sân 7 đúng như intent của khách
    for slot in res.recommended_slots:
        assert slot.loai_san == "Sân 7"
        assert slot.ten_san == "Sân 7 Sao Vàng"
        assert slot.don_gia > 0

def test_ai_notifications_generation(db_session):
    """Kiểm tra AI sinh tin nhắn Zalo nhắc lịch từ đơn đặt sân."""
    customer = db_session.query(TaiKhoan).first()
    s7 = db_session.query(San).filter(San.ma == "SAN7-VANG").first()
    
    # Tạo đơn đặt mẫu
    booking = DatSan(
        ma_don="DS-TEST-AI",
        ma_khach_hang=customer.tai_khoan_id,
        ma_san=s7.ma,
        ngay_da=date(2026, 9, 5),
        gio_bat_dau=time(18, 30),
        gio_ket_thuc=time(20, 0),
        tien_coc=300000.0,
        trang_thai="da_xac_nhan"
    )
    db_session.add(booking)
    db_session.commit()

    # Sinh tin nhắn nhắc lịch
    notif = AIService.generate_reminder(db_session, booking.ma_don)
    assert notif.ma_don == "DS-TEST-AI"
    assert "Phạm Nhật Minh" in notif.noi_dung_tin_nhan
    assert "Sân 7 Sao Vàng" in notif.noi_dung_tin_nhan
    assert "18:30" in notif.noi_dung_tin_nhan

def test_ai_promotions_insight(db_session):
    """Kiểm tra AI phân tích doanh thu và đề xuất khuyến mãi."""
    admin = db_session.query(TaiKhoan).first() # Dùng tạm customer làm admin cho test
    
    insights = AIService.analyze_revenue(
        db_session, 
        tu_ngay=date(2026, 9, 1), 
        den_ngay=date(2026, 9, 7), 
        admin_user_id=admin.tai_khoan_id
    )

    assert insights.ty_le_lap_day >= 0
    assert len(insights.tom_tat) > 0
    assert len(insights.de_xuat) > 0

def test_ai_consult_rejects_off_topic_prompts(db_session):
    """Kiểm tra AI từ chối các câu hỏi linh tinh, bừa bãi, không liên quan đến sân bóng."""
    EXPECTED_REJECTION = "Xin lỗi! Điều này không nằm trọng phạm vi của tôi! Xin lỗi và cảm ơn bạn đã đặt câu hỏi"

    off_topic_queries = [
        "Thời tiết hôm nay thế nào bạn ơi?",
        "Hãy viết code python kết nối cơ sở dữ liệu SQLite",
        "Công thức nấu món canh chua cá lóc miền Tây",
        "Bạn có người yêu chưa?",
        "Kể cho tôi nghe một câu chuyện cười",
        "Giải giúp tôi phương trình bậc hai 2x^2 + 5x - 3 = 0",
        "Tổng thống Mỹ hiện tại là ai?",
        "Viết cho tôi một bài thơ tình lãng mạn",
        "asdfghjkl12345",
        "1 + 1 bằng mấy?",
        "Dịch câu này sang tiếng Anh giúp tôi",
        "Có nên đầu tư mua bitcoin lúc này không?",
        "Hôm nay ăn gì ngon bổ rẻ?"
    ]

    for prompt in off_topic_queries:
        res = AIService.consult_pitch(db_session, user_prompt=prompt)
        assert res.assistant_message == EXPECTED_REJECTION, f"Failed on prompt: {prompt}"
        assert res.co_san_phu_hop is False
        assert len(res.recommended_slots) == 0
        assert res.analyzed_intent.get("intent") == "out_of_scope"

def test_ai_consult_service_and_policy_inquiries(db_session):
    """Kiểm tra AI phản hồi đúng nghiệp vụ khi hỏi về dịch vụ và chính sách sân bóng."""
    # 1. Hỏi về dịch vụ nước uống, trang thiết bị
    res_service = AIService.consult_pitch(db_session, user_prompt="Sân mình có bán nước uống Revive hay cho thuê áo bít không?")
    assert "Xin lỗi! Điều này không nằm trọng phạm vi" not in res_service.assistant_message
    assert "Victory Arena" in res_service.assistant_message
    assert res_service.analyzed_intent.get("intent") == "court_service"

    # 2. Hỏi về quy định tiền cọc và hủy lịch
    res_policy = AIService.consult_pitch(db_session, user_prompt="Quy định đặt cọc và chính sách hủy sân hoàn tiền như thế nào?")
    assert "Xin lỗi! Điều này không nằm trọng phạm vi" not in res_policy.assistant_message
    assert "10 phút" in res_policy.assistant_message or "cọc" in res_policy.assistant_message
    assert res_policy.analyzed_intent.get("intent") == "court_policy_info"

    # 3. Chào hỏi ban đầu
    res_greeting = AIService.consult_pitch(db_session, user_prompt="Xin chào, hỗ trợ tư vấn giúp em với")
    assert "Xin lỗi! Điều này không nằm trọng phạm vi" not in res_greeting.assistant_message
    assert "Victory Arena" in res_greeting.assistant_message
    assert res_greeting.analyzed_intent.get("intent") == "general_greeting"

