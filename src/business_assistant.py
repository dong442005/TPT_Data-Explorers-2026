import os
import re
import json
import logging
import textwrap
import pandas as pd  # Thư viện Pandas để đọc các file kết quả mô hình ML
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv
load_dotenv()

# ===== CẤU HÌNH HỆ THỐNG VÀ BẢO MẬT =====
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "tnbike_db")
DEFAULT_DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

DB_URL = os.getenv("TNBIKE_DB_URL", DEFAULT_DB_URL)
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY", "[ENCRYPTION_KEY]")
MODELING_DIR = os.getenv("MODELING_DIR", "outputs/modeling")  # Thư mục chứa các file CSV kết quả ML

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class AIBusinessAssistantSmart:
    """
    Trợ lý Kinh doanh Thông minh - Đêm Chung Kết
    Tích hợp song song SQL (Dữ liệu hiện tại/Quá khứ) và ML CSV (Dữ liệu dự báo Tương lai).
    Cam kết kiểm soát nghiêm ngặt số lượng Request để triệt tiêu lỗi 429 và 503.
    """
    def __init__(self, db_url: str = DB_URL):
        self.db_url = db_url
        
        # 1. Kết nối trực tiếp vào cơ sở dữ liệu PostgreSQL với schema tnbike
        try:
            self.db = SQLDatabase.from_uri(
                self.db_url,
                schema="tnbike"
            )
            logger.info("✅ Đã kết nối Database thành công (Schema: tnbike).")
        except Exception as e:
            logger.error(f"❌ Lỗi kết nối Database: {e}")
            raise

        # 2. Cơ chế tĩnh hóa động cấu trúc bảng bằng Python thuần (Tốn 0 request LLM)
        self.cached_schema = self._get_or_update_schema_cache()

        # 3. Khởi tạo mô hình ngôn ngữ lớn gemini-3.5-flash ở cấu hình tối ưu nhất
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash", 
            google_api_key=GOOGLE_API_KEY,
            temperature=0,
            max_retries=5
        )
        logger.info("🧠 Bộ não Gemini 3.5-Flash đã sẵn sàng ở trạng thái tối ưu nhất.")

    def _get_or_update_schema_cache(self, cache_filename="tnbike_schema.json") -> str:
        """
        Tự động phát hiện cấu trúc bảng mới thay đổi, cập nhật tệp JSON cục bộ 
        và nạp cấu trúc vào Prompt (Tốn 0 request gọi tới Gemini).
        """
        current_tables = self.db.get_usable_table_names()
        should_update = False
        cached_data = {}
        
        if os.path.exists(cache_filename):
            try:
                with open(cache_filename, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                if set(cached_data.keys()) != set(current_tables):
                    logger.info("🔄 Phát hiện thay đổi bảng dữ liệu! Đang cập nhật tệp cache cục bộ...")
                    should_update = True
            except Exception:
                should_update = True
        else:
            logger.info("📁 Không tìm thấy dữ liệu cấu trúc đệm. Đang khởi tạo 'tnbike_schema.json'...")
            should_update = True
            
        if should_update:
            cached_data = {}
            for table in current_tables:
                cached_data[table] = self.db.get_table_info([table])
            with open(cache_filename, "w", encoding="utf-8") as f:
                json.dump(cached_data, f, ensure_ascii=False, indent=4)
            logger.info("✅ Đồng bộ tệp 'tnbike_schema.json' thành công!")
            
        return "\n\n".join(cached_data.values())

    def _clean_sql_query(self, raw_sql) -> str:
        """Bộ lọc làm sạch câu lệnh SQL, xử lý an toàn cho cả dạng chuỗi và danh sách phức tạp"""
        clean_text = ""
        
        if isinstance(raw_sql, list):
            for item in raw_sql:
                if isinstance(item, dict) and 'text' in item:
                    clean_text += item['text']
                elif isinstance(item, str):
                    clean_text += item
                elif hasattr(item, 'text'):
                    clean_text += item.text
        elif isinstance(raw_sql, str):
            clean_text = raw_sql
        else:
            clean_text = str(raw_sql)
            
        clean = clean_text.strip()
        clean = re.sub(r"```sql", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"```", "", clean)
        return clean.strip()

    def _parse_llm_content(self, raw_content) -> str:
        """Bộ lọc phân tách dữ liệu đầu ra chuyên sâu: Khắc phục triệt để lỗi bọc chuỗi danh sách [] và lỗi render mã LaTeX rightarrow"""
        clean_output = ""
        
        if isinstance(raw_content, list):
            for item in raw_content:
                if isinstance(item, dict) and 'text' in item:
                    clean_output += item['text']
                elif isinstance(item, str):
                    clean_output += item
                elif hasattr(item, 'text'):
                    clean_output += item.text
        elif isinstance(raw_content, str):
            clean_output = raw_content
        else:
            clean_output = str(raw_content)
            
        # Thay thế mã text thô của ký tự LaTeX thành mũi tên hiển thị scannable đẹp mắt
        clean_output = clean_output.replace("rightarrow", " ➔ ")
        return clean_output.strip()

    # =========================================================================
    # PHẦN THÊM MỚI: XỬ LÝ DỮ LIỆU ĐẦU RA CỦA CÁC MÔ HÌNH MACHINE LEARNING (CSV)
    # =========================================================================
    def _read_csv_to_markdown(self, filename: str, nrows: int = 15) -> str:
        """Đọc tệp tin CSV kết quả mô hình và chuyển sang bảng Markdown để LLM tiếp nhận tri thức"""
        file_path = os.path.join(MODELING_DIR, filename)
        if not os.path.exists(file_path):
            return f"[Lưu ý: Không tìm thấy tệp dữ liệu dự báo {filename}]"
        try:
            df = pd.read_csv(file_path)
            return df.head(nrows).to_markdown(index=False)
        except Exception as e:
            logger.error(f"Lỗi đọc dữ liệu CSV {filename}: {e}")
            return f"[Lỗi hệ thống khi trích xuất dữ liệu từ {filename}]"

    def _answer_with_csv_models(self, question: str) -> str:
        """Luồng xử lý chuyên biệt cho câu hỏi dự báo tương lai sử dụng tri thức từ ML Models"""
        logger.info("📊 Đang nạp dữ liệu từ các file CSV kết quả ML...")
        
        # Thu thập tri thức từ các tệp báo cáo mô hình hóa mà bạn của bạn đã export
        group_share_data = self._read_csv_to_markdown("phase3_group_share_forecast_q2_2026.csv")
        dealer_ranking_data = self._read_csv_to_markdown("phase3_dealer_priority_ranking_q2_2026.csv", nrows=12)
        color_forecast_data = self._read_csv_to_markdown("phase3_color_summary_q2_2026.csv")
        
        forecasting_prompt = textwrap.dedent(f"""
        Bạn là Chuyên gia Phân tích Dự báo Chiến lược xuất sắc của Thống Nhất Bike.
        Người dùng đang hỏi về các kịch bản xu hướng, phân hạng khách hàng hoặc dự báo nhu cầu tương lai trong Quý 2 năm 2026.
        Hãy dựa vào kết quả đầu ra thực tế từ các MÔ HÌNH MACHINE LEARNING dưới đây để phân tích và trả lời câu hỏi.
        
        [DỮ LIỆU THỊ PHẦN & DOANH THU DỰ BÁO Q2/2026 - MÔ HÌNH TIME SERIES]:
        {group_share_data}
        
        [DỮ LIỆU XẾP HẠNG ƯU TIÊN ĐẠI LÝ Q2/2026 - MÔ HÌNH PHÂN LOẠI HÀNH VI]:
        {dealer_ranking_data}
        
        [DỮ LIỆU XU HƯỚNG NHU CẦU THEO MÀU SẮC Q2/2026 - MÔ HÌNH PHÂN TÍCH NHÓM]:
        {color_forecast_data}
        
        YÊU CẦU TRÌNH BÀY & PHÂN TÍCH CHIẾN LƯỢC:
        1. Câu trả lời bằng tiếng Việt chuyên nghiệp, bám sát các con số khoa học từ mô hình ML phía trên cung cấp. Tuyệt đối không tự suy diễn các con số nằm ngoài dữ liệu.
        2. Định dạng rõ ràng tiền tệ dạng VNĐ và sản lượng. Trình bày danh sách gạch đầu dòng trực quan, dễ nắm bắt thông tin.
        3. LUÔN LUÔN tạo một phần có tiêu đề "💡 Khuyến nghị hành động (Prescriptive Actions)" ở cuối để đề xuất các giải pháp chiến lược khả thi dựa trên phân tích tương lai này nhằm ghi điểm tuyệt đối với Hội đồng Giám khảo.
        
        CÂU HỎI CỦA USER: {question}
        """)
        
        logger.info("📝 [Request 1/1] Đang yêu cầu Gemini phân tích dữ liệu CSV tương lai...")
        response = self.llm.invoke(forecasting_prompt)
        
        # Áp dụng bộ lọc dọn dẹp chuẩn hóa đầu ra cho luồng CSV tương lai
        return self._parse_llm_content(response.content)

    # =========================================================================
    # LUỒNG XỬ LÝ CHÍNH: KHÔNG THAY ĐỔI LOGIC CŨ, TÍCH HỢP BỘ ĐỊNH TUYẾN THÔNG MINH
    # =========================================================================
    def answer_question(self, question: str) -> str:
        """Quy trình thực thi SQL Chain cố định 2 bước nghiêm ngặt + Bộ định tuyến phân tầng thông minh"""
        if not question or not isinstance(question, str):
            return "❌ Câu hỏi không hợp lệ."
        
        logger.info(f"🚀 Bắt đầu xử lý câu hỏi: {question}")
        
        # --- BỘ ĐỊNH TUYẾN THÔNG MINH (SMART ROUTER CỦA BẠN) ---
        # Chỉ kích hoạt luồng CSV khi có các từ khóa mang tính chất dự báo, nhìn nhận tương lai rõ rệt
        forecasting_keywords = ["dự báo", "dự đoán", "kịch bản", "forecast", "predict", "xu hướng", "sắp tới", "năm tới", "năm sau", "tháng sau", "quý sau", "sẽ", "tiếp theo"]
        
        # Điều kiện loại trừ nghiêm ngặt: Nếu câu hỏi chứa từ chỉ định quá khứ/thực tế, bắt buộc ép chạy luồng SQL
        is_history_intent = any(hw in question.lower() for hw in ["thống kê", "lịch sử", "đã bán", "thực tế", "hiện tại", 'liệt kê'])
        
        if any(kw in question.lower() for kw in forecasting_keywords) and not is_history_intent:
            logger.info("🔮 Phát hiện câu hỏi dự báo tương lai, chuyển hướng sang đọc file CSV (ML Models)...")
            return self._answer_with_csv_models(question)
        # -----------------------------------------------------

        try:
            # === BƯỚC 1: Đọc JSON và yêu cầu LLM viết duy nhất câu lệnh SQL (Request 1) ===
            sql_generation_prompt = textwrap.dedent(f"""
            You are a precise PostgreSQL expert. Your only job is to write a valid SQL query based on the user's question and the provided database schema.
            
            CRITICAL RULES:
            1. Output ONLY the raw SQL query. Do NOT write any explanations, do NOT wrap it in markdown code blocks unless necessary, just the query text.
            2. Use the exact table names and schema prefix 'tnbike.' (e.g., tnbike.fact_sales, tnbike.customer).
            3. Be smart with text filters: always use LOWER() and LIKE '%value%' for product names or regions to avoid typo mismatches (e.g., if user asks for 'neon', look for '%neo%').
            
            DATABASE SCHEMA:
            {self.cached_schema}
            
            USER QUESTION: {question}
            """)
            
            logger.info("🔮 [Request 1/2] Đang yêu cầu Gemini viết lệnh SQL...")
            sql_response = self.llm.invoke(sql_generation_prompt)
            sql_query = self._clean_sql_query(sql_response.content)
            logger.info(f"📜 Câu lệnh SQL được sinh ra:\n{sql_query}")
            
            # === BƯỚC 2: Thực thi SQL trực tiếp vào Database thông qua Python ===
            logger.info("⚙️ Đang thực thi SQL vào PostgreSQL...")
            db_result = self.db.run(sql_query)
            logger.info(f"📊 Kết quả thô từ DB: {db_result}")
            
            # === BƯỚC 3: Đưa kết quả thô cho LLM đóng gói thành câu trả lời BI hoàn chỉnh (Request 2) ===
            final_response_prompt = textwrap.dedent(f"""
            Bạn là một Chuyên viên Phân tích Dữ liệu Kinh doanh (BI Analyst) xuất sắc của Thống Nhất Bike.
            Hãy dựa vào kết quả truy vấn thực tế từ Database dưới đây để trả lời câu hỏi của người dùng.
            
            YÊU CẦU TRÌNH BÀY:
            1. Trả lời bằng tiếng Việt một cách chuyên nghiệp, súc tích dựa trên ĐÚNG số liệu được cho.
            2. Format các số tiền bằng VNĐ (ví dụ: 1,000,000 VNĐ) và định dạng số lượng rõ ràng.
            3. Trình bày danh sách dưới dạng gạch đầu dòng scannable.
            4. LUÔN LUÔN thêm một phần "💡 Insight & Khuyến nghị" ngắn gọn, sắc sảo ở cuối câu trả lời dựa trên những con số này để ghi điểm với Ban giám khảo.
            
            CÂU HỎI CỦA USER: {question}
            KẾT QUẢ TRUY VẤN TỪ DATABASE: {db_result}
            """)
            
            logger.info("📝 [Request 2/2] Đang yêu cầu Gemini đóng gói câu trả lời và Insight...")
            final_response = self.llm.invoke(final_response_prompt)
            
            # Áp dụng bộ lọc dọn dẹp chuẩn hóa đầu ra cho luồng SQL hiện tại
            return self._parse_llm_content(final_response.content)

        except Exception as e:
            logger.error(f"💥 Thất bại hệ thống: {e}")
            return "⚠️ Xin lỗi, tôi đã gặp khó khăn khi xử lý dữ liệu. Vui lòng thử lại hoặc điều chỉnh câu hỏi một chút!"

if __name__ == "__main__":
    assistant = AIBusinessAssistantSmart()
    # Chạy thử nghiệm đồng thời hai luồng để xác thực độ chính xác của bộ định tuyến
    print("\n--- LUỒNG 1: TRUY VẤN SỐ LIỆU QUÁ KHỨ (SQL) ---")
    print(assistant.answer_question("thống kê doanh thu 3 tháng của năm 2026"))
    
    print("\n--- LUỒNG 2: ĐỐI CHIẾU DỰ BÁO TƯƠNG LAI (ML CSV) ---")
    print(assistant.answer_question("dự đoán doanh thu trong tháng 4, tháng 5, và tháng 6 của năm 2026"))
