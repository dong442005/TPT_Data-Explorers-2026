import streamlit as st
from src.ai_business_assistant_accurate import AIBusinessAssistantSmart
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 1. Cấu hình trang (phải để đầu tiên)
st.set_page_config(
    page_title="Thống Nhất Bike AI",
    page_icon="🚲",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 2. Thêm Custom CSS để giao diện tinh tế hơn (không lòe loẹt)
st.markdown("""
<style>
    /* Tùy chỉnh màu nền ứng dụng hơi xám nhạt cho dịu mắt */
    .stApp {
        background-color: #f8f9fa;
    }
    /* Tiêu đề màu xanh dương đậm */
    h1 {
        color: #1e3a8a;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Làm nổi bật khung chat của AI với nền trắng và bóng đổ nhẹ */
    .stChatMessage:nth-child(even) {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        padding: 10px;
    }
    /* Bo góc cho nút bấm */
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #1e3a8a;
        color: #1e3a8a;
    }
</style>
""", unsafe_allow_html=True)

# 3. Sidebar (Thanh bên) để giao diện trông giống một Web App chuyên nghiệp
with st.sidebar:
    st.title("🚲 Thống Nhất Bike")
    st.markdown("---")
    st.markdown("💡 **Gợi ý câu hỏi cho bạn:**")
    st.markdown("- *Thống kê doanh thu các tháng*")
    st.markdown("- *Màu nào bán chạy nhất?*")
    st.markdown("- *Top đại lý mang lại doanh thu*")
    st.markdown("- *Sản phẩm nào bán chạy nhất?*")
    st.markdown("---")
    
    # Nút xóa lịch sử chat (rất tiện khi test)
    if st.button("🗑️ Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()
        
    st.caption("Phiên bản: 2.0 - Data Query Engine")

# 4. Tiêu đề chính của trang
st.title("Trợ lý Kinh doanh AI 🤖")
st.caption("Hệ thống truy vấn dữ liệu bán hàng trực tiếp, nhanh chóng và chính xác 100%.")

# 5. Khởi tạo AI và lời chào đầu tiên
if "assistant" not in st.session_state:
    with st.spinner("Đang kết nối cơ sở dữ liệu..."):
        st.session_state.assistant = AIBusinessAssistantSmart()
    # Lời chào mặc định khi mở web
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào bạn! Tôi là trợ lý dữ liệu của Thống Nhất Bike. Bạn muốn xem báo cáo gì hôm nay?"}
    ]

# 6. Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. Ô nhập liệu cho người dùng
if prompt := st.chat_input("Nhập câu hỏi của bạn vào đây (vd: Thống kê doanh thu)..."):
    # Hiển thị câu hỏi
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Xử lý và hiển thị câu trả lời
    with st.chat_message("assistant"):
        with st.spinner("Đang trích xuất dữ liệu..."):
            response = st.session_state.assistant.answer_question(prompt)
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})