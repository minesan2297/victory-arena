import re
import unicodedata
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, date, time
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

OUT_OF_SCOPE_RESPONSE = "Xin lỗi! Điều này không nằm trọng phạm vi của tôi! Xin lỗi và cảm ơn bạn đã đặt câu hỏi"

class AIService:
    @classmethod
    def _call_gemini(cls, db: Session, kieu_goi: KieuGoiAI, system_instruction: str, user_prompt: str) -> Optional[str]:
        settings = get_settings()
        
        # Lấy hoặc tạo AIConfig
        ai_config = db.query(AIConfig).filter(
            AIConfig.provider == 'google',
            AIConfig.model == settings.gemini_model,
            AIConfig.trang_thai == 'active'
        ).first()
        
        if not ai_config:
            ai_config = AIConfig(
                provider='google',
                model=settings.gemini_model,
                prompt_template=system_instruction,
                trang_thai='active'
            )
            db.add(ai_config)
            db.commit()
            db.refresh(ai_config)
            
        if not settings.gemini_api_key:
            # Ghi nhận log AI request với trạng thái thất bại do thiếu API key
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
            
        start_time = datetime.utcnow()
        try:
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel(
                model_name=settings.gemini_model,
                system_instruction=system_instruction
            )
            response = model.generate_content(user_prompt)
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
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
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            # Ghi nhận log AI request lỗi
            ai_req = AIRequest(
                ai_config_id=ai_config.ai_config_id,
                kieu_goi=kieu_goi.value,
                prompt_input=user_prompt,
                ket_qua=str(e),
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
        - Chỉ chấp nhận các câu hỏi liên quan đến sân bóng, đặt sân, lịch đá, giá tiền, và dịch vụ sân bóng.
        - Trả về (is_relevant: bool, intent: str).
        - Nếu ngoài phạm vi (linh tinh, bừa bãi, không liên quan) -> return (False, "out_of_scope").
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
            r'\b(dich|translate|tieng anh|tieng trung|tieng nhat)\b',
            r'\b(nguoi yeu|yeu toi|to tinh|hen ho|tan gai|tan trai)\b',
            r'\b(an gi|an com|an uong)\b',
        ]
        for pat in off_topic_patterns:
            if re.search(pat, p_norm):
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
            'het san'
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

        # Nếu không chứa bất kỳ từ khóa chuyên môn/lời chào hợp lệ nào -> Ngoài phạm vi
        if not (has_pitch or has_booking or has_service or has_facility_greeting):
            return False, "out_of_scope"

        # Phân loại intent cụ thể
        if has_service and not (has_booking and any(k in p_norm for k in ['khung gio', 'gio', 'trong', 'slot', 'toi nay', 'ngay mai'])):
            return True, "court_service"
        if any(k in p_norm for k in ['quy dinh', 'noi quy', 'chinh sach', 'hoan coc', 'tien coc', 'dia chi', 'o dau', 'mo cua', 'dong cua']):
            return True, "court_policy_info"
        if has_facility_greeting and not (has_pitch or has_booking or has_service):
            return True, "general_greeting"

        return True, "pitch_booking"

    @classmethod
    def consult_pitch(cls, db: Session, user_prompt: str, ngay_mong_muon: Optional[date] = None) -> AIConsultResponse:
        query_date = ngay_mong_muon or date.today()
        
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

        # 4. Chuẩn bị prompt gửi LLM (kèm Guardrail nghiêm ngặt)
        system_instruction = (
            "Bạn là trợ lý AI chuyên nghiệp của Cụm sân bóng đá Victory Arena.\n"
            "PHẠM VI TRẢ LỜI CỦA BẠN CHỈ GIỚI HẠN TRONG CÁC VẤN ĐỀ LIÊN QUAN ĐẾN:\n"
            "1. Sân bóng đá (các loại Sân 5, Sân 7, Sân 11, mặt cỏ, cơ sở vật chất, địa chỉ, khung giờ hoạt động 06:00-23:00).\n"
            "2. Đặt sân, giữ sân (kiểm tra khung giờ trống, giá thuê, giữ chỗ 10 phút, đặt cọc 30%, đổi lịch, hủy lịch hoàn cọc 100% trước 24h, thanh toán).\n"
            "3. Các dịch vụ tại sân bóng (nước giải khát Revive/nước khoáng, thuê áo bít, giày đá bóng, bóng thi đấu, trọng tài, tủ đồ, tắm tráng, gửi xe).\n"
            "4. Lời chào hỏi lịch sự và tư vấn bóng đá phong trào thân thiện.\n\n"
            "QUY TẮC BẢO VỆ PHẠM VI BẮT BUỘC:\n"
            "- Nếu câu hỏi hoặc yêu cầu của người dùng là nội dung bừa bãi, linh tinh, hoặc KHÔNG LIÊN QUAN đến sân bóng đá, đặt sân, hay dịch vụ của sân bóng "
            "(ví dụ: hỏi thời tiết, nấu ăn, lập trình/viết code, giải toán, thơ ca, chính trị, tán gẫu ngoài lề, câu chữ vô nghĩa, spam...):\n"
            f"BẠN PHẢI TRẢ LỜI DUY NHẤT CÂU SAU ĐÂY VÀ KHÔNG ĐƯỢC NÓI THÊM BẤT KỲ ĐIỀU GÌ KHÁC:\n"
            f'"{OUT_OF_SCOPE_RESPONSE}"\n\n'
            "- Tuyệt đối không trả lời, không giải thích những nội dung ngoài phạm vi trên."
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
            # Chế độ Fallback quy tắc
            if intent == "court_service":
                assistant_message = (
                    "Dạ, tại Cụm sân bóng đá Victory Arena có đầy đủ các dịch vụ tiện ích phục vụ anh em thi đấu:\n"
                    f"- 🥤 Nước giải khát: {', '.join(dv_nuoc) if dv_nuoc else 'Revive, Nước suối, Bò húc...'}\n"
                    f"- 🎽 Trang thiết bị: {', '.join(dv_tb) if dv_tb else 'Áo bít, Giày đá bóng, Bóng thi đấu...'}\n"
                    "- 🚗 Tiện ích miễn phí: Bãi đỗ xe an toàn, phòng thay đồ, vòi tắm tráng nước sạch và hệ thống đèn LED cao áp chuẩn thi đấu.\n"
                    "Anh/chị cần đặt trước dịch vụ hay đặt lịch sân thì cứ nhắn em hỗ trợ ngay nhé! ⚽🏟️"
                )
            elif intent == "court_policy_info":
                assistant_message = (
                    "Dạ, quy định đặt sân và chính sách bảo đảm tại Victory Arena như sau:\n"
                    "- ⏱️ **Giữ chỗ**: Đơn đặt sân được giữ chỗ tự động trong 10 phút để quý khách chuyển cọc (30% tiền sân).\n"
                    "- 🔄 **Chính sách hủy sân**: Nếu hủy trước giờ thi đấu từ 24 tiếng trở lên, hệ thống sẽ tự động hoàn 100% tiền cọc. Hủy dưới 24 tiếng sẽ không được hoàn cọc theo quy định sân.\n"
                    "- 🔁 **Đổi lịch thi đấu**: Hỗ trợ đổi khung giờ hoặc đổi sân trước giờ đá 12 tiếng nếu còn lịch trống.\n"
                    "- ⏰ **Giờ mở cửa**: Cụm sân hoạt động từ 06:00 đến 23:00 tất cả các ngày trong tuần (kể cả lễ tết).\n"
                    "Anh/chị cần kiểm tra lịch trống khung giờ nào thì báo em hỗ trợ ngay nhé! ⚽🏟️"
                )
            elif intent == "general_greeting":
                assistant_message = (
                    "Dạ xin chào anh/chị! Em là trợ lý AI chuyên môn của Cụm sân bóng đá Victory Arena. "
                    "Hiện tại cụm sân bên em có hệ thống Sân 5, Sân 7 và Sân 11 đạt tiêu chuẩn thi đấu, kèm đầy đủ dịch vụ giải khát, thuê áo bít, giày và bóng thi đấu. "
                    "Anh/chị cần em hỗ trợ tìm sân trống, báo giá hay tư vấn dịch vụ nào cho đội mình không ạ? ⚽🏟️"
                )
            else:
                slots_str = ", ".join([f"{r.ten_san} ({r.khung_gio} - Giá: {r.don_gia:,.0f}đ)" for r in recommended])
                if recommended:
                    assistant_message = f"Dạ, ngày {query_date.strftime('%d/%m/%Y')} hệ thống đang còn trống các khung giờ cho {loai_san_khach_tim} như sau: {slots_str}. Anh/chị xem có khung giờ nào phù hợp với đội mình không ạ? Trận đấu sẽ được giữ chỗ trong 10 phút để anh/chị chuyển cọc nhé! ⚽🏟️"
                else:
                    assistant_message = f"Dạ, hiện tại loại {loai_san_khach_tim} trong ngày {query_date.strftime('%d/%m/%Y')} đã kín lịch hoặc đang bảo trì mất rồi ạ. Anh/chị có muốn tham khảo sang loại sân khác hoặc ngày khác không ạ?"

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
            "Bạn là trợ lý AI gửi tin nhắn tự động. Hãy soạn thảo một tin nhắn nhắc nhở lịch thi đấu bóng đá ngắn gọn, "
            "vui vẻ, đầy đủ thông tin (bao gồm: Tên khách hàng, Tên sân, Ngày đá, Khung giờ, Số tiền cọc đã đóng, và lưu ý chuẩn bị nước uống/giày đá bóng phù hợp)."
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
                f"⚽ [SportBookAI] Nhắc lịch đá: Xin chào anh/chị {booking.khach_hang.ho_ten}! "
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
            ngay_gui=datetime.utcnow()
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
            "Bạn là chuyên gia phân tích dữ liệu kinh doanh sân bóng. Hãy viết tóm tắt đánh giá hiệu suất hoạt động, "
            "chỉ ra các khung giờ cao điểm, thấp điểm và đề xuất chiến dịch khuyến mại (ví dụ giảm 20-30% giờ thấp điểm) "
            "để tối ưu công suất hoạt động của sân bóng."
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
