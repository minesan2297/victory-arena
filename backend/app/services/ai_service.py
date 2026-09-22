import re
import unicodedata
import time as pytime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, date, time, timezone, timedelta
import json
from typing import Optional, List, Tuple
import google.generativeai as genai
from app.config import get_settings
from app.models.ai_models import AIConfig, AIRequest, BaoCao, ThongBao
from app.models.dat_san import DatSan, LichDat
from app.models.san import San
from app.models.dich_vu import DanhMucDichVu
from app.models.hoa_don import ThanhToan
from app.models.enums import KieuGoiAI, KenhGui, TrangThaiGui, TrangThaiAI
from app.schemas.ai_schema import RecommendedSlot, AIConsultResponse, AIReminderResponse, AIReportResponse
from app.services.dat_san_service import DatSanService

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

OUT_OF_SCOPE_RESPONSE = "Xin lỗi! Điều này không nằm trong phạm vi của tôi! Xin lỗi và cảm ơn bạn đã đặt câu hỏi"

class AIService:
    @classmethod
    def _call_gemini(cls, db: Session, kieu_goi: KieuGoiAI, system_instruction: str, user_prompt: str) -> Optional[str]:
        settings = get_settings()
        
        ai_config = db.query(AIConfig).first()
        if not ai_config:
            ai_config = AIConfig(
                provider="gemini",
                model=settings.gemini_model,
                prompt_template=system_instruction
            )
            db.add(ai_config)
            db.commit()
            db.refresh(ai_config)
            
        if not settings.gemini_api_key or settings.gemini_api_key == "YOUR_GEMINI_API_KEY_HERE":
            # Ghi nhận log AI request lỗi thiếu API key
            ai_req = AIRequest(
                ai_config_id=ai_config.ai_config_id,
                kieu_goi=kieu_goi.value,
                prompt_input=user_prompt,
                ket_qua="Thiếu GEMINI_API_KEY. Chạy ở chế độ fallback.",
                trang_thai=TrangThaiAI.ERROR.value
            )
            db.add(ai_req)
            db.commit()
            return None
            
        start_perf = pytime.perf_counter()
        try:
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel(
                model_name=settings.gemini_model,
                system_instruction=system_instruction
            )
            # Giới hạn timeout 10s để chống treo hệ thống (Tiêu chí 7 - KT3)
            response = model.generate_content(
                user_prompt,
                request_options={"timeout": 10.0}
            )
            duration = int((pytime.perf_counter() - start_perf) * 1000)
            
            # Ghi nhận log AI request thành công
            ai_req = AIRequest(
                ai_config_id=ai_config.ai_config_id,
                kieu_goi=kieu_goi.value,
                prompt_input=user_prompt,
                ket_qua=response.text,
                thoi_gian_xu_ly_ms=duration,
                trang_thai=TrangThaiAI.SUCCESS.value
            )
            db.add(ai_req)
            db.commit()
            return response.text
        except Exception as e:
            duration = int((pytime.perf_counter() - start_perf) * 1000)
            err_msg = str(e)
            # Nhận diện lỗi Rate Limit (429) hoặc Timeout (Tiêu chí 7 - KT3)
            if "429" in err_msg or "ResourceExhausted" in err_msg:
                log_err = f"[RATE_LIMIT_429] Vượt hạn mức gọi Gemini API: {err_msg}"
            elif "timeout" in err_msg.lower() or "deadline" in err_msg.lower():
                log_err = f"[TIMEOUT_10S] Yêu cầu tới Gemini API vượt quá 10 giây: {err_msg}"
            else:
                log_err = f"[AI_ERROR] {err_msg}"

            # Ghi nhận log AI request lỗi
            ai_req = AIRequest(
                ai_config_id=ai_config.ai_config_id,
                kieu_goi=kieu_goi.value,
                prompt_input=user_prompt,
                ket_qua=log_err,
                thoi_gian_xu_ly_ms=duration,
                trang_thai=TrangThaiAI.ERROR.value
            )
            db.add(ai_req)
            db.commit()
            return None

    @staticmethod
    def _remove_accents(text: str) -> str:
        """Chuẩn hóa chuỗi tiếng Việt: bỏ dấu, chuyển về chữ thường để so khớp từ khóa."""
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        text = text.replace('đ', 'd').replace('Đ', 'D')
        return text.lower()

    @classmethod
    def classify_user_prompt(cls, user_prompt: str) -> Tuple[bool, str]:
        """
        Phân loại câu hỏi của người dùng:
        - Chấp nhận các câu hỏi liên quan đến sân bóng, đặt sân, lịch đá, giá tiền, dịch vụ sân bóng,
          các câu hỏi thời gian (ngày mai, hôm nay, tối mai, thứ 7...) và câu hỏi nối tiếp (thì sao, còn không...).
        - Trả về (is_relevant: bool, intent: str).
        - Nếu ngoài phạm vi (linh tinh, bừa bãi, lập trình, giải toán, nấu ăn...) -> return (False, "out_of_scope").
        """
        raw = user_prompt.strip()
        if len(raw) < 2:
            return False, "out_of_scope"

        p_norm = cls._remove_accents(raw)

        # 1. Các mẫu câu chắc chắn ngoài phạm vi (Lập trình, giải toán, nấu ăn, thời tiết, chính trị, chuyện phiếm ngoài lề...)
        off_topic_patterns = [
            r'\b(code|lap trinh|thuat toan|script|python|java|javascript|c\+\+|html|css|php|sql|golang|rust|typescript|docker|kubernetes|github|react|angular|vue)\b',
            r'\b(toan|bai tap|phuong trinh|dao ham|tich phan|hoa hoc|vat ly|dai so|hinh hoc)\b',
            r'\b(nau an|cong thuc|mon an|canh chua|pho bo|bun bo|com tam|uong thuoc|chua benh)\b',
            r'\b(thoi tiet|nhiet do|du bao thoi tiet|troi hom nay mua hay nang)\b',
            r'\b(chinh tri|bau cu|tong thong|thu tuong|chien tranh|quan su|dang cong san)\b',
            r'\b(chung khoan|co phieu|tien ao|crypto|bitcoin|btc|eth|dau tu|lo de|xo so|soi cau)\b',
            r'\b(chuyen cuoi|chuyen ma|bai tho|lam tho|viet tho|bai van)\b',
            r'\b(dich thuat|dich sang|dich giup|translate|tieng anh|tieng trung|tieng nhat)\b',
            r'\b(nguoi yeu|yeu toi|to tinh|hen ho|tan gai|tan trai)\b',
            r'\b(an gi|an com|an uong)\b',
        ]
        for pat in off_topic_patterns:
            if re.search(pat, p_norm):
                # Ngoại lệ an toàn: Nếu từ khóa là "dich vu" thì không coi là "dich thuat"
                if "dich vu" in p_norm and pat == r'\b(dich thuat|dich sang|dich giup|translate|tieng anh|tieng trung|tieng nhat)\b':
                    continue
                return False, "out_of_scope"

        # Kiểm tra spam toán học, ký tự vô nghĩa không có nguyên âm
        if re.match(r'^[\d\s\+\-\*\/\=\?]+$', p_norm):
            return False, "out_of_scope"
        if len(p_norm) >= 5 and not any(v in p_norm for v in 'aeiouy'):
            return False, "out_of_scope"

        # 2. Danh mục từ khóa hợp lệ thuộc nghiệp vụ sân bóng
        pitch_keywords = [
            'san', 'san bong', 'san co', 'co nhan tao', 'san 5', 'san 7', 'san 11',
            'san mini', 'mat san', 'khung thanh', 'cau mon', 'den chieu', 'chieu sang',
            'victory arena', 'arena', 'bong da', 'da bong', 'da banh', 'tran dau', 'cau thu'
        ]

        booking_keywords = [
            'dat san', 'thue san', 'giu san', 'giu cho', 'tim san', 'book san', 'dat cho',
            'lich', 'lich da', 'lich trong', 'khung gio', 'gio da', 'gio trong', 'ca da', 'slot',
            'trong', 'bat doi', 'cap keo', 'doi lich', 'huy lich', 'doi san', 'doi gio',
            'hoan coc', 'dat coc', 'tien coc', 'tien san', 'bang gia', 'gia san', 'gia thue',
            'bao nhieu tien', 'bao nhieu 1 gio', 'gia bao nhieu', 'co san khong', 'con san khong',
            'het san', 'gia sao', 'dat sao', 'bao nhieu'
        ]

        temporal_keywords = [
            'ngay mai', 'ngay kia', 'ngay mot', 'mai', 'hom nay', 'toi nay', 'chieu nay', 'sang nay',
            'toi mai', 'sang mai', 'chieu mai', 'dem nay', 'trua nay', 'trua mai',
            'cuoi tuan', 'thu 2', 'thu 3', 'thu 4', 'thu 5', 'thu 6', 'thu 7', 'chu nhat',
            'thu hai', 'thu ba', 'thu tu', 'thu nam', 'thu sau', 'thu bay',
            't2', 't3', 't4', 't5', 't6', 't7', 'cn', 'tuan nay', 'tuan sau',
            'gio nao', 'khung gio', 'may gio', 'slot', 'ca da'
        ]

        followup_keywords = [
            'thi sao', 'the con', 'con khong', 'con san', 'co khong', 'co san', 'duoc khong',
            'the nao', 'sao', 'con gio nao', 'con slot nao', 'co cho nao', 'dat duoc khong',
            'con trong khong', 'co trong khong', 'xem giup', 'check giup', 'tim giup', 'tra giup',
            'goi y giup', 'bao gio', 'co slot', 'co gio', 'con slot', 'con gio',
            'con tran nao', 'da duoc khong'
        ]

        service_keywords = [
            'dich vu', 'nuoc', 'nuoc uong', 'giai khat', 'revive', 'sting', 'bo huc',
            'redbull', 'aquafina', 'nuoc suoi', 'tra da', 'chanh muoi', 'ao bit', 'ao luoi',
            'ao bib', 'ao pitch', 'thue ao', 'thue giay', 'giay da bong', 'giay da banh',
            'thue bong', 'muon bong', 'bong thi dau', 'trong tai', 'tu do', 'gui xe', 'giu xe',
            'thay do', 'tam', 'tam trang', 'phong thay do', 'khan tam', 'bang quan'
        ]

        facility_greeting_keywords = [
            'dia chi', 'o dau', 'vi tri', 'mo cua', 'dong cua', 'gio mo', 'hotline', 'so dien thoai',
            'lien he', 'quy dinh', 'noi quy', 'chinh sach', 'mai che', 'chao', 'xin chao', 'hello',
            'hi ad', 'ad oi', 'tu van', 'ho tro'
        ]

        has_pitch = any(kw in p_norm for kw in pitch_keywords)
        has_booking = any(kw in p_norm for kw in booking_keywords)
        has_service = any(kw in p_norm for kw in service_keywords)
        has_facility_greeting = any(kw in p_norm for kw in facility_greeting_keywords)
        has_temporal = any(kw in p_norm for kw in temporal_keywords)
        has_followup = any(kw in p_norm for kw in followup_keywords)

        # Nếu không chứa bất kỳ từ khóa chuyên môn/lời chào/thời gian/câu hỏi hợp lệ nào -> Ngoài phạm vi
        if not (has_pitch or has_booking or has_service or has_facility_greeting or has_temporal or has_followup):
            return False, "out_of_scope"

        # Phân loại intent cụ thể
        if has_service and not (has_booking or has_temporal or any(k in p_norm for k in ['khung gio', 'gio', 'trong', 'slot', 'toi nay', 'ngay mai'])):
            return True, "court_service"
        if any(k in p_norm for k in ['quy dinh', 'noi quy', 'chinh sach', 'hoan coc', 'tien coc', 'dia chi', 'o dau', 'mo cua', 'dong cua']):
            return True, "court_policy_info"
        if has_facility_greeting and not (has_pitch or has_booking or has_service or has_temporal or has_followup):
            return True, "general_greeting"

        return True, "pitch_booking"

    @classmethod
    def extract_target_date(cls, user_prompt: str, base_date: Optional[date] = None) -> date:
        """
        Trích xuất ngày đá bóng mong muốn từ câu hỏi của người dùng:
        - "ngày mai", "mai", "tối mai", "sáng mai", "chiều mai" -> ref_date + 1 ngày
        - "ngày kia", "ngày mốt", "mốt" -> ref_date + 2 ngày
        - "hôm nay", "tối nay", "chiều nay" -> date.today()
        - Định dạng ngày dd/mm hoặc dd/mm/yyyy
        """
        today = date.today()
        ref_date = base_date or today
        p_norm = cls._remove_accents(user_prompt.strip().lower())

        # 1. Từ khóa tương đối chỉ ngày kia / ngày mốt
        if any(k in p_norm for k in ['ngay kia', 'ngay mot', 'mốt']):
            return ref_date + timedelta(days=2)

        # 2. Từ khóa tương đối chỉ ngày mai / mai
        if any(k in p_norm for k in ['ngay mai', 'toi mai', 'sang mai', 'chieu mai', 'trua mai', 'mai thi sao', 'mai con', 'mai co']):
            return ref_date + timedelta(days=1)
        if re.search(r'\bmai\b', p_norm) and not any(k in p_norm for k in ['mai che', 'khuyen mai']):
            return ref_date + timedelta(days=1)

        # 3. Hôm nay / tối nay / chiều nay -> chính là ref_date
        if any(k in p_norm for k in ['hom nay', 'toi nay', 'chieu nay', 'sang nay', 'trua nay', 'nay con']):
            return ref_date

        # 4. Định dạng ngày cụ thể dd/mm hoặc dd/mm/yyyy
        m = re.search(r'\b(\d{1,2})[\/\-](\d{1,2})(?:[\/\-](\d{4}))?\b', p_norm)
        if m:
            day = int(m.group(1))
            month = int(m.group(2))
            year = int(m.group(3)) if m.group(3) else today.year
            try:
                parsed = date(year, month, day)
                if parsed >= today:
                    return parsed
            except ValueError:
                pass

        return ref_date

    @classmethod
    def consult_pitch(cls, db: Session, user_prompt: str, ngay_mong_muon: Optional[date] = None) -> AIConsultResponse:
        # Tự động trích xuất ngày từ câu hỏi tự nhiên nếu có (VD: "ngày mai thì sao" -> ngày mai)
        query_date = cls.extract_target_date(user_prompt, ngay_mong_muon)
        
        # 1. Kiểm tra phạm vi câu hỏi
        is_relevant, intent = cls.classify_user_prompt(user_prompt)
        if not is_relevant or intent == "out_of_scope":
            return AIConsultResponse(
                assistant_message=OUT_OF_SCOPE_RESPONSE,
                co_san_phu_hop=False,
                recommended_slots=[],
                analyzed_intent={"intent": "out_of_scope", "ngay": str(query_date)}
            )

        # 2. Lấy dữ liệu dịch vụ từ CSDL
        dich_vus = db.query(DanhMucDichVu).filter(DanhMucDichVu.trang_thai == 'active').all()
        dv_nuoc = [f"{dv.ten_dich_vu} ({dv.don_gia:,.0f}đ/{dv.don_vi_tinh})" for dv in dich_vus if dv.danh_muc == 'NUOC_UONG']
        dv_tb = [f"{dv.ten_dich_vu} ({dv.don_gia:,.0f}đ/{dv.don_vi_tinh})" for dv in dich_vus if dv.danh_muc == 'TRANG_BI']

        # 3. Xử lý đặt sân hoặc tra cứu lịch trống
        loai_san_khach_tim = "Sân 7"
        if "11" in user_prompt or "lớn" in user_prompt or "fifa" in user_prompt:
            loai_san_khach_tim = "Sân 11"
        elif "5" in user_prompt or "mini" in user_prompt:
            loai_san_khach_tim = "Sân 5"
        else:
            loai_san_khach_tim = "Sân 7"

        all_courts = db.query(San).all()
        matching_courts = [c for c in all_courts if c.loai_san.ten_loai == loai_san_khach_tim]
        if not matching_courts and all_courts:
            matching_courts = [all_courts[0]]
            loai_san_khach_tim = matching_courts[0].loai_san.ten_loai

        available_slots = []
        if intent == "pitch_booking":
            for court in matching_courts:
                sched = DatSanService.get_day_schedule(db, query_date, court.ma)
                for slot in sched.slots:
                    if slot.trang_thai == 'AVAILABLE':
                        available_slots.append(slot)

        # Ưu tiên xếp hạng slot theo khung thời gian mong muốn (sáng / chiều / tối / giờ cao điểm)
        p_norm = cls._remove_accents(user_prompt.lower())
        wants_evening = any(k in p_norm for k in ['toi', 'dem', '18h', '19h', '20h', '21h'])
        wants_morning = any(k in p_norm for k in ['sang', 'som', '6h', '7h', '8h', '9h', '10h'])
        wants_afternoon = any(k in p_norm for k in ['chieu', 'trua', '14h', '15h', '16h'])

        def slot_sort_key(slot):
            sh = slot.gio_bat_dau.hour
            if wants_evening:
                return 0 if sh >= 17 else 1
            if wants_morning:
                return 0 if sh < 12 else 1
            if wants_afternoon:
                return 0 if 12 <= sh < 18 else 1
            # Giờ cao điểm đá bóng thường là 17h-20h
            if 17 <= sh <= 20:
                return 0
            return 1

        available_slots.sort(key=slot_sort_key)

        recommended = []
        for slot in available_slots[:3]:
            khung_gio = f"{slot.gio_bat_dau.strftime('%H:%M')}-{slot.gio_ket_thuc.strftime('%H:%M')}"
            recommended.append(RecommendedSlot(
                san_id=slot.san_id,
                ten_san=slot.ten_san,
                loai_san=slot.loai_san,
                khung_gio=khung_gio,
                don_gia=slot.don_gia,
                ly_do=f"Khung giờ trống lý tưởng cho {slot.loai_san} vào ngày {query_date.strftime('%d/%m/%Y')}."
            ))

        # 4. Chuẩn bị Prompt gửi LLM theo kiến trúc Cognitive Scheduling Engine chuẩn kỹ thuật (KT3)
        system_instruction = (
            "HỆ THỐNG: Victory Arena Cognitive Scheduling & Recommendation Engine (v2.0).\n"
            "VAI TRÒ VẬN HÀNH: Phân hệ lõi xử lý logic tư vấn, phân tích ý định (Intent Recognition) và điều phối khung giờ thi đấu thời gian thực cho Cụm sân bóng đá Victory Arena.\n"
            "QUY TẮC DANH XƯNG & THẨM QUYỀN: Tuyệt đối không xưng là 'nhân viên' hoặc 'trợ lý AI chung chung'. Định vị mọi phản hồi là thông điệp chính thức, khách quan, chính xác từ Nền tảng Quản lý Sân Victory Arena.\n\n"
            "=== BỘ QUY TẮC RÀNG BUỘC KỸ THUẬT BẮT BUỘC (MANDATORY SYSTEM CONSTRAINTS) ===\n"
            "1. CHÍNH SÁCH KHÔNG ẢO GIÁC (ZERO-HALLUCINATION PROTOCOL):\n"
            "- CHỈ ĐƯỢC PHÉP gợi ý các khung giờ và sân bóng xuất hiện chính xác trong mảng 'khung_gio_trong_thuc_te' của dữ liệu đầu vào CSDL.\n"
            "- TUYỆT ĐỐI KHÔNG tự ý suy đoán hoặc tạo ra bất kỳ khung giờ hay sân bóng nào không có trong dữ liệu CSDL.\n\n"
            "2. GIAO THỨC XỬ LÝ HẾT SÂN (OVERBOOKED / FULLY BOOKED PROTOCOL - TIÊU CHÍ KT3):\n"
            "- Khi 'khung_gio_trong_thuc_te' là mảng rỗng [] (100% các khung giờ của loại sân yêu cầu trong ngày đã kín lịch hoặc bảo trì):\n"
            "  + Thông báo rõ ràng: Loại sân yêu cầu trong ngày truy vấn hiện đã kín lịch 100% tất cả các ca thi đấu.\n"
            "  + Tuyệt đối không tự sinh khung giờ ảo.\n"
            "  + Chủ động đề xuất phương án thay thế: gợi ý khách hàng tham khảo ngày tiếp theo (ngày mai / cuối tuần) hoặc chuyển sang loại sân khác còn chỗ.\n"
            "  + Hướng dẫn khách hàng theo dõi bảng Lịch Sân Trực Quan để nhận giữ chỗ ngay nếu có đội bóng khác hủy lịch hoặc nhả cọc.\n\n"
            "3. GIAO THỨC XỬ LÝ DỮ LIỆU THIẾU & CÂU HỎI MƠ HỒ (MISSING DATA INFERENCE PROTOCOL - TIÊU CHÍ KT3):\n"
            "- Khi khách hàng KHÔNG NÊU NGÀY THI ĐẤU: Hệ thống tự động xác định ngày thi đấu là ngày hiện tại ('ngay_tu_van' trong dữ liệu đầu vào), nêu rõ đang tra cứu lịch cho hôm nay và hướng dẫn khách cung cấp ngày khác nếu có nhu cầu.\n"
            "- Khi khách hàng KHÔNG NÊU LOẠI SÂN: Căn cứ vào số lượng người chơi nếu có (10-14 người -> Sân 7; 18-22 người -> Sân 11). Nếu không có cả số người, tự động áp dụng cấu hình mặc định (ưu tiên Sân 7 - loại sân phổ biến nhất cho bóng đá phủi).\n"
            "- Khi câu hỏi cực ngắn hoặc mơ hồ (vd: 'Đặt sân bóng'): Gợi ý các khung giờ vàng tối nay của Sân 7 kèm hướng dẫn ngắn gọn cách bổ sung ngày/giờ mong muốn.\n\n"
            "4. HÀNG RÀO BẢO VỆ PHẠM VI NGHIỆP VỤ (DOMAIN BOUNDARY GUARDRAIL):\n"
            "- Hệ thống chỉ hỗ trợ các nội dung thuộc Cụm sân Victory Arena: tra cứu lịch, đặt giữ chỗ 10 phút, đặt cọc 30%, chính sách hủy hoàn cọc 100% trước 24h, đổi lịch trước 12h, dịch vụ nước uống (Revive, Bò húc...), áo bít, giày và giờ mở cửa 06:00-23:00.\n"
            "- Nếu yêu cầu của người dùng KHÔNG LIÊN QUAN đến sân bóng (lập trình, giải toán, nấu ăn, thời tiết, chính trị, tán gẫu ngoài lề, spam...):\n"
            f"BẮT BUỘC TRẢ LỜI DUY NHẤT CÂU SAU ĐÂY VÀ KHÔNG KÈM THEO BẤT KỲ NỘI DUNG NÀO KHÁC:\n"
            f'"{OUT_OF_SCOPE_RESPONSE}"\n\n'
            "5. ĐỊNH DẠNG & PHONG CÁCH TRÌNH BÀY (OUTPUT SPECIFICATION):\n"
            "- Trình bày mạch lạc bằng Markdown: In đậm tên sân, dùng icon trực quan (⚽, ⏰, 🏟️, 💰).\n"
            "- Nêu rõ khung giờ, mức giá và nhấn mạnh chính sách: 'Đơn đặt sẽ được giữ chỗ tự động trong 10 phút để hoàn tất chuyển cọc'.\n"
            "- Giọng điệu chuyên nghiệp, chính xác, chuẩn mực của một nền tảng quản lý thể thao hiện đại."
        )

        context_data = {
            "intent_xac_dinh": intent,
            "ngay_tu_van": query_date.strftime("%Y-%m-%d"),
            "yeu_cau_nguoi_dung": user_prompt,
            "loai_san_trich_xuat": loai_san_khach_tim,
            "dich_vu_tai_san": {
                "nuoc_uong": dv_nuoc,
                "trang_bi": dv_tb
            },
            "khung_gio_trong_thuc_te": [
                {
                    "san_id": r.san_id,
                    "ten_san": r.ten_san,
                    "khung_gio": r.khung_gio,
                    "gia": r.don_gia
                } for r in recommended
            ]
        }

        llm_response = cls._call_gemini(db, KieuGoiAI.CONSULT, system_instruction, json.dumps(context_data, ensure_ascii=False))

        # 5. Nếu LLM trả về, kiểm tra nếu là từ chối ngoài phạm vi
        if llm_response:
            assistant_message = llm_response.strip()
            if "không nằm trọng phạm vi" in assistant_message.lower() or "không nằm trong phạm vi" in assistant_message.lower():
                return AIConsultResponse(
                    assistant_message=OUT_OF_SCOPE_RESPONSE,
                    co_san_phu_hop=False,
                    recommended_slots=[],
                    analyzed_intent={"intent": "out_of_scope", "ngay": str(query_date)}
                )
        else:
            # Chế độ Fallback quy tắc (Đảm bảo phản hồi mang tính thông báo nền tảng chính thức, không roleplay)
            if intent == "court_service":
                assistant_message = (
                    "Thông tin dịch vụ tiện ích tại Cụm sân bóng đá Victory Arena:\n"
                    f"- 🥤 Danh mục nước giải khát: {', '.join(dv_nuoc) if dv_nuoc else 'Revive, Nước suối, Bò húc...'}\n"
                    f"- 🎽 Danh mục trang thiết bị: {', '.join(dv_tb) if dv_tb else 'Áo bít, Giày đá bóng, Bóng thi đấu...'}\n"
                    "- 🚗 Tiện ích miễn phí: Bãi đỗ xe an toàn, phòng thay đồ, vòi tắm tráng nước sạch và hệ thống đèn LED cao áp chuẩn thi đấu.\n"
                    "Quý khách có thể lựa chọn thêm các dịch vụ trên trực tiếp khi đặt sân hoặc tại quầy lễ tân. ⚽🏟️"
                )
            elif intent == "court_policy_info":
                assistant_message = (
                    "Quy định đặt sân và chính sách bảo đảm tại Cụm sân Victory Arena:\n"
                    "- ⏱️ **Giữ chỗ**: Đơn đặt sân được hệ thống giữ chỗ tự động trong 10 phút để quý khách chuyển cọc (30% tiền sân).\n"
                    "- 🔄 **Chính sách hủy sân**: Hủy trước giờ thi đấu từ 24 tiếng trở lên được hệ thống tự động hoàn 100% tiền cọc. Hủy dưới 24 tiếng không được hoàn cọc theo quy định vận hành.\n"
                    "- 🔁 **Đổi lịch thi đấu**: Hỗ trợ đổi khung giờ hoặc đổi sân trước giờ đá tối thiểu 12 tiếng nếu hệ thống còn lịch trống.\n"
                    "- ⏰ **Giờ mở cửa**: Cụm sân phục vụ từ 06:00 đến 23:00 tất cả các ngày trong tuần (kể cả lễ tết).\n"
                    "Quý khách có thể tra cứu lịch trống trực tiếp trên bảng ma trận hoặc gửi yêu cầu để hệ thống hỗ trợ. ⚽🏟️"
                )
            elif intent == "general_greeting":
                assistant_message = (
                    "Xin chào quý khách! Hệ thống Cụm sân bóng đá Victory Arena xin hân hạnh hỗ trợ. "
                    "Hiện tại cụm sân có hệ thống Sân 5, Sân 7 và Sân 11 đạt tiêu chuẩn thi đấu, kèm đầy đủ dịch vụ giải khát, thuê áo bít, giày và bóng thi đấu. "
                    "Quý khách có thể gửi yêu cầu tìm sân trống, tra cứu bảng giá hoặc đăng ký dịch vụ cho đội bóng của mình. ⚽🏟️"
                )
            else:
                slots_str = ", ".join([f"{r.ten_san} ({r.khung_gio} - Giá: {r.don_gia:,.0f}đ)" for r in recommended])
                if query_date == date.today() + timedelta(days=1):
                    date_label = f"ngày mai ({query_date.strftime('%d/%m/%Y')})"
                elif query_date == date.today():
                    date_label = f"hôm nay ({query_date.strftime('%d/%m/%Y')})"
                else:
                    date_label = f"ngày {query_date.strftime('%d/%m/%Y')}"

                if recommended:
                    assistant_message = f"Hệ thống Victory Arena ghi nhận {date_label} đang còn trống các khung giờ cho {loai_san_khach_tim} như sau: {slots_str}. Quý khách vui lòng chọn khung giờ phù hợp để giữ chỗ trong 10 phút và hoàn tất đặt cọc nhé! ⚽🏟️"
                else:
                    assistant_message = f"Thông báo: Hiện tại loại {loai_san_khach_tim} trong {date_label} đã kín lịch hoặc đang trong thời gian bảo trì. Quý khách vui lòng tham khảo chuyển sang loại sân khác hoặc ngày khác nhé!"

        return AIConsultResponse(
            assistant_message=assistant_message,
            co_san_phu_hop=len(recommended) > 0,
            recommended_slots=recommended,
            analyzed_intent={"intent": intent, "loai_san": loai_san_khach_tim, "ngay": str(query_date)}
        )

    @classmethod
    def generate_reminder(cls, db: Session, ma_don: str) -> AIReminderResponse:
        booking = db.query(DatSan).filter(DatSan.ma_don == ma_don).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt sân")
            
        system_instruction = (
            "HỆ THỐNG: Victory Arena Automated Notification Engine (Phân hệ Tạo Tin Nhắn Tự Động).\n"
            "MỤC TIÊU: Dựa trên dữ liệu đơn đặt sân được cung cấp từ CSDL, soạn thảo thông điệp nhắc lịch thi đấu bóng đá ngắn gọn, "
            "chuẩn xác, đầy đủ các trường thông tin (Tên khách hàng, Tên sân, Ngày đá, Khung giờ, Số tiền cọc đã ghi nhận, và lưu ý chuẩn bị trước trận đấu)."
        )
        
        context_data = {
            "khach_hang": booking.khach_hang.ho_ten,
            "ten_san": booking.san.ten_san,
            "ngay_da": booking.ngay_da.strftime("%d/%m/%Y"),
            "khung_gio": f"{booking.gio_bat_dau.strftime('%H:%M')} - {booking.gio_ket_thuc.strftime('%H:%M')}",
            "tien_coc": booking.tien_coc
        }
        
        llm_response = cls._call_gemini(db, KieuGoiAI.NOTIFY, system_instruction, json.dumps(context_data, ensure_ascii=False))
        
        if llm_response:
            noi_dung = llm_response.strip()
        else:
            noi_dung = (
                f"⚽ [Victory Arena] Nhắc lịch thi đấu: Xin chào quý khách {booking.khach_hang.ho_ten}! "
                f"Đội của mình có lịch hẹn ra sân tại {booking.san.ten_san} vào lúc {booking.gio_bat_dau.strftime('%H:%M')}-{booking.gio_ket_thuc.strftime('%H:%M')} ngày {booking.ngay_da.strftime('%d/%m/%Y')}. "
                f"Số tiền cọc đã ghi nhận: {booking.tien_coc:,.0f}đ. Chúc đội mình có một trận đấu bùng nổ! ⚽🏟️"
            )
            
        # Lưu vào bảng ThongBao
        new_notify = ThongBao(
            tai_khoan_id=booking.ma_khach_hang,
            ma_don=ma_don,
            noi_dung=noi_dung,
            kenh_gui=KenhGui.WEB.value,
            trang_thai_gui=TrangThaiGui.DA_GUI.value,
            ngay_gui=get_utc_now()
        )
        db.add(new_notify)
        db.commit()
        
        return AIReminderResponse(
            ma_don=ma_don,
            noi_dung_tin_nhan=noi_dung,
            kenh='web',
            da_luu=True
        )

    @classmethod
    def analyze_revenue(cls, db: Session, tu_ngay: date, den_ngay: date, admin_user_id: int) -> AIReportResponse:
        # Tính toán dữ liệu thống kê thực tế
        # 1. Tính tổng doanh thu từ các giao dịch thanh toán thành công
        payments = db.query(ThanhToan).filter(
            ThanhToan.trang_thai == 'thanh_cong',
            ThanhToan.thoi_gian >= datetime.combine(tu_ngay, time.min),
            ThanhToan.thoi_gian <= datetime.combine(den_ngay, time.max)
        ).all()
        tong_doanh_thu = sum(p.so_tien for p in payments)
        
        # 2. Tính tỷ lệ lấp đầy (số slots đã đặt / tổng slots hoạt động)
        total_bookings = db.query(DatSan).filter(
            DatSan.ngay_da >= tu_ngay,
            DatSan.ngay_da <= den_ngay,
            DatSan.trang_thai != 'da_huy'
        ).count()
        
        total_courts = db.query(San).filter(San.trang_thai == 'active').count() or 1
        days_count = (den_ngay - tu_ngay).days + 1
        total_possible_slots = total_courts * days_count * 9 # 9 slots/ngày
        ty_le_lap_day = round((total_bookings / total_possible_slots) * 100, 2)
        
        system_instruction = (
            "HỆ THỐNG: Victory Arena Business Intelligence & Revenue Engine (Phân hệ Phân Tích Dữ Liệu Kinh Doanh).\n"
            "MỤC TIÊU: Dựa trên các chỉ số doanh thu thực tế, tỷ lệ lấp đầy sân và số lượng đơn đặt trong kỳ báo cáo từ CSDL, "
            "tổng hợp đánh giá hiệu suất khai thác sân, chỉ rõ các khung giờ cao điểm, thấp điểm và đề xuất chiến lược khuyến mại (giảm giá 20-30% giờ thấp điểm) "
            "nhằm tối ưu hóa công suất vận hành cụm sân."
        )
        
        context_data = {
            "tu_ngay": tu_ngay.strftime("%Y-%m-%d"),
            "den_ngay": den_ngay.strftime("%Y-%m-%d"),
            "tong_doanh_thu": tong_doanh_thu,
            "ty_le_lap_day_phong_tram": ty_le_lap_day,
            "tong_don_dat": total_bookings
        }
        
        llm_response = cls._call_gemini(db, KieuGoiAI.REPORT, system_instruction, json.dumps(context_data, ensure_ascii=False))
        
        if llm_response:
            tom_tat = llm_response.strip()
        else:
            tom_tat = (
                f"Báo cáo tổng kết kinh doanh từ {tu_ngay.strftime('%d/%m/%Y')} đến {den_ngay.strftime('%d/%m/%Y')}. "
                f"Tổng doanh thu đạt: {tong_doanh_thu:,.0f}đ. Tỷ lệ lấp đầy trung bình đạt {ty_le_lap_day}%. "
                f"Hiệu năng hoạt động ổn định ở các khung giờ vàng (17h30-20h), cần có các chương trình kích cầu giảm giá 20% vào khung trưa và sáng sớm."
            )
            
        # Phân tích ra các đề xuất cụ thể (mẫu/hoặc parse từ LLM)
        khung_gio_cao_diem = ["17:00-18:30", "18:30-20:00", "20:00-21:30"]
        de_xuat = [
            "Giảm giá 25% cho tất cả các loại sân vào khung giờ sáng sớm (06:00-07:30) từ Thứ Hai đến Thứ Sáu.",
            "Tặng nước uống miễn phí cho các đội đặt sân khung trưa (14:00-15:30).",
            "Tăng cường chạy quảng cáo fanpage hướng tới đối tượng học sinh, sinh viên đá khung giờ chiều sớm."
        ]
        
        # Lưu vào bảng BaoCao
        new_report = BaoCao(
            tu_ngay=tu_ngay,
            den_ngay=den_ngay,
            tong_doanh_thu=int(tong_doanh_thu),
            ty_le_lap_day=ty_le_lap_day,
            ket_qua_ai_tom_tat=tom_tat,
            nguoi_tao_id=admin_user_id
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        return AIReportResponse(
            bao_cao_id=new_report.bao_cao_id,
            tom_tat=tom_tat,
            ty_le_lap_day=ty_le_lap_day,
            khung_gio_cao_diem=khung_gio_cao_diem,
            de_xuat=de_xuat
        )
