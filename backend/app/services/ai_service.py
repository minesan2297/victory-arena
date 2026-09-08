from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, date, time
import json
from typing import Optional, List
import google.generativeai as genai
from app.config import get_settings
from app.models.ai_models import AIConfig, AIRequest, BaoCao, ThongBao
from app.models.dat_san import DatSan, LichDat
from app.models.san import San
from app.models.hoa_don import ThanhToan
from app.models.enums import KieuGoiAI, KenhGui, TrangThaiGui, TrangThaiAI
from app.schemas.ai_schema import RecommendedSlot, AIConsultResponse, AIReminderResponse, AIReportResponse
from app.services.dat_san_service import DatSanService

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

    @classmethod
    def consult_pitch(cls, db: Session, user_prompt: str, ngay_mong_muon: Optional[date] = None) -> AIConsultResponse:
        query_date = ngay_mong_muon or date.today()
        
        # 1. Trích xuất loại sân khách mong muốn từ prompt (Chỉ hỗ trợ Sân 7 và Sân 11)
        loai_san_khach_tim = "Sân 7" # Mặc định là Sân 7
        if "11" in user_prompt or "lớn" in user_prompt or "fifa" in user_prompt:
            loai_san_khach_tim = "Sân 11"
        else:
            loai_san_khach_tim = "Sân 7"
            
        # 2. Lấy danh sách lịch trống thực tế cho loại sân đó
        all_courts = db.query(San).all()
        matching_courts = [c for c in all_courts if c.loai_san.ten_loai == loai_san_khach_tim]
        if not matching_courts and all_courts:
            matching_courts = [all_courts[0]]
            loai_san_khach_tim = matching_courts[0].loai_san.ten_loai
            
        available_slots = []
        for court in matching_courts:
            sched = DatSanService.get_day_schedule(db, query_date, court.ma)
            for slot in sched.slots:
                if slot.trang_thai == 'AVAILABLE':
                    available_slots.append(slot)
                    
        # 3. Tạo đề xuất 3 slots tốt nhất
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
            
        # 4. Chuẩn bị prompt gửi LLM
        system_instruction = (
            "Bạn là trợ lý AI chuyên nghiệp tư vấn đặt sân bóng đá. Nhiệm vụ của bạn là dựa trên danh sách các khung giờ trống thực tế "
            "được cung cấp dưới định dạng JSON để đưa ra câu trả lời tư vấn thuyết phục, nhiệt tình, chuẩn văn phong bóng đá phủi. "
            "Nếu có khung giờ trống, hãy khích lệ khách đặt. Nếu không, hãy khéo léo gợi ý ngày khác hoặc loại sân khác. "
            "Chỉ đề xuất các khung giờ nằm trong danh sách thực tế trống được gửi kèm, tuyệt đối không được tự ý ảo giác ra giờ khác."
        )
        
        context_data = {
            "ngay_tu_van": query_date.strftime("%Y-%m-%d"),
            "yeu_cau_nguoi_dung": user_prompt,
            "loai_san_trich_xuat": loai_san_khach_tim,
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
        
        # 5. Nếu LLM trả về kết quả, sử dụng kết quả đó. Nếu không, fallback sang rule-based.
        if llm_response:
            assistant_message = llm_response.strip()
        else:
            # Fallback
            slots_str = ", ".join([f"{r.ten_san} ({r.khung_gio} - Giá: {r.don_gia:,.0f}đ)" for r in recommended])
            if recommended:
                assistant_message = f"Dạ, ngày {query_date.strftime('%d/%m/%Y')} hệ thống đang còn trống các khung giờ cho {loai_san_khach_tim} như sau: {slots_str}. Anh/chị xem có khung giờ nào phù hợp với đội mình không ạ? Trận đấu sẽ được giữ chỗ trong 10 phút để anh/chị chuyển cọc nhé! ⚽🏟️"
            else:
                assistant_message = f"Dạ, hiện tại loại {loai_san_khach_tim} trong ngày {query_date.strftime('%d/%m/%Y')} đã kín lịch hoặc đang bảo trì mất rồi ạ. Anh/chị có muốn tham khảo sang loại sân khác hoặc ngày khác không ạ?"
                
        return AIConsultResponse(
            assistant_message=assistant_message,
            co_san_phu_hop=len(recommended) > 0,
            recommended_slots=recommended,
            analyzed_intent={"loai_san": loai_san_khach_tim, "ngay": str(query_date)}
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
