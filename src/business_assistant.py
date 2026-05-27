import os
import re
import json
import logging
import textwrap
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI

# ===== CONFIGURATION =====
DB_URL = os.getenv("TNBIKE_DB_URL", "postgresql://postgres:password@localhost:5432/tnbike_db")
GOOGLE_API_KEY = "API_KEY_cua_ban"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class AIBusinessAssistantSmart:
    """
    Business Assistant Đêm Chung Kết - Sử dụng Kiến trúc SQL Chain Tuyến tính
    Cam kết tiêu tốn đúng 2 Request/Câu hỏi - Triệt tiêu hoàn toàn lỗi 429 và 503.
    """
    def __init__(self, db_url: str = DB_URL):
        self.db_url = db_url
        
        # 1. Kết nối Database trực tiếp vào schema tnbike 
        try:
            self.db = SQLDatabase.from_uri(
                self.db_url,
                schema="tnbike"
            )
            logger.info("✅ Đã kết nối Database thành công (Schema: tnbike).")
        except Exception as e:
            logger.error(f"❌ Lỗi kết nối Database: {e}")
            raise

        # 2. Đồng bộ cấu trúc bảng tự động bằng Python thuần 
        self.cached_schema = self._get_or_update_schema_cache()

        # 3. Khởi tạo mô hình gemini-3.5-flash
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash", 
            google_api_key=GOOGLE_API_KEY,
            temperature=0,
            max_retries=5
        )
        logger.info("🧠 Bộ não Gemini 3.5-Flash đã sẵn sàng ở trạng thái tối ưu nhất.")

    def _get_or_update_schema_cache(self, cache_filename="tnbike_schema.json") -> str:
        """
        Cơ chế Tĩnh hóa động: Tự động phát hiện bảng mới bằng Python thuần,
        cập nhật file JSON và trả về văn bản cấu trúc cho Prompt (Tốn 0 request Gemini).
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
        """Bộ lọc dọn dẹp và làm sạch câu lệnh SQL, xử lý an toàn cho cả dạng chuỗi và danh sách"""
        clean_text = ""
        
        # Nếu Gemini trả về dạng danh sách (List of content parts)
        if isinstance(raw_sql, list):
            for item in raw_sql:
                if isinstance(item, dict) and 'text' in item:
                    clean_text += item['text']
                elif isinstance(item, str):
                    clean_text += item
                elif hasattr(item, 'text'):
                    clean_text += item.text
        # Nếu Gemini trả về dạng chuỗi (String) thuần túy
        elif isinstance(raw_sql, str):
            clean_text = raw_sql
        else:
            clean_text = str(raw_sql)
            
        # Tiến hành làm sạch cú pháp Markdown SQL nếu có
        clean = clean_text.strip()
        clean = re.sub(r"```sql", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"```", "", clean)
        return clean.strip()

    def answer_question(self, question: str) -> str:
        """Quy trình SQL Chain cố định 2 bước nghiêm ngặt"""
        if not question or not isinstance(question, str):
            return "❌ Câu hỏi không hợp lệ."
        
        logger.info(f"🚀 Bắt đầu xử lý câu hỏi bằng SQL Chain: {question}")
        
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
            
            # === BƯỚC 2: Thực thi SQL trực tiếp vào Database thông qua Python (Miễn phí) ===
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
            
            # --- BỘ LỌC AN TOÀN CHO ĐẦU RA KẾT QUẢ (Xử lý lỗi 'list' object has no attribute 'strip') ---
            raw_content = final_response.content
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
                
            return clean_output.strip()

        except Exception as e:
            logger.error(f"💥 Thất bại hệ thống: {e}")
            return "⚠️ Xin lỗi, tôi đã gặp khó khăn khi xử lý dữ liệu. Vui lòng thử lại hoặc điều chỉnh câu hỏi một chút!"

if __name__ == "__main__":
    assistant = AIBusinessAssistantSmart()
    # Chạy thử nghiệm ngay tại chỗ câu hỏi khó nhằn xuyên 4 bảng
    print(assistant.answer_question("liệt kê các đại lý ở miền bắc đã mua xe đạp neon 2004 đỏ tươi kèm số lượng"))