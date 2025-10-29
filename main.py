import streamlit as st
import pandas as pd
import re
from openai import OpenAI

# 🔑 API key OpenRouter (thay bằng key của cô)
OPENROUTER_API_KEY = "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"

# ⚙️ Cấu hình OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# ---------------------------
# 🧠 HÀM GỌI GPT TẠO ĐỀ
# ---------------------------
def tao_de_tu_ai(lop, mon):
    prompt = f"""
    Hãy tạo 5 câu hỏi trắc nghiệm (mỗi câu có 4 lựa chọn A, B, C, D)
    phù hợp học sinh lớp {lop} môn {mon}.
    Ghi rõ "Đáp án đúng:" ở cuối mỗi câu. Viết rõ ràng, dễ hiểu.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Lỗi khi gọi GPT: {e}"

# ---------------------------
# ✍️ HÀM XỬ LÝ & CHẤM ĐIỂM
# ---------------------------
def tach_cau_hoi_va_dap_an(de):
    """Tách từng câu hỏi ra dạng [(câu hỏi, đáp án đúng)]"""
    cau_hoi_list = []
    pattern = r"(\d+\..*?)(?=\n\d+\.|$)"
    matches = re.findall(pattern, de, re.S)

    for m in matches:
        dap_an_match = re.search(r"Đáp án đúng\s*[:\-]?\s*([A-D])", m, re.I)
        dap_an = dap_an_match.group(1).upper() if dap_an_match else None
        noi_dung = re.sub(r"Đáp án đúng.*", "", m).strip()
        cau_hoi_list.append((noi_dung, dap_an))
    return cau_hoi_list

def cham_diem(danh_sach, lua_chon_hs):
    """Tính điểm dựa theo đáp án học sinh"""
    dung = 0
    for i, (_, dap_an) in enumerate(danh_sach):
        if i < len(lua_chon_hs) and lua_chon_hs[i] == dap_an:
            dung += 1
    return dung

# ---------------------------
# 🌈 GIAO DIỆN STREAMLIT
# ---------------------------

st.title("🎓 Ứng dụng tạo & làm bài kiểm tra AI (Tiểu học)")

menu = st.sidebar.selectbox("Chọn chế độ:", ["Học sinh", "Giáo viên (Admin)"])

# ---------------------------
# 👩‍🏫 GIAO DIỆN GIÁO VIÊN
# ---------------------------
if menu == "Giáo viên (Admin)":
    admin_user = st.text_input("Tên đăng nhập")
    admin_pass = st.text_input("Mật khẩu", type="password")

    if admin_user == "admin" and admin_pass == "123":
        st.success("✅ Đăng nhập thành công!")
        st.subheader("📋 Danh sách kết quả học sinh")
        try:
            df = pd.read_csv("ketqua.csv")
            st.dataframe(df)
        except:
            st.info("Chưa có học sinh nào nộp bài.")
    else:
        st.warning("Nhập tài khoản admin để xem kết quả (admin / 123)")

# ---------------------------
# 🧒 GIAO DIỆN HỌC SINH
# ---------------------------
else:
    ten = st.text_input("👧 Nhập họ tên của em:")
    lop = st.selectbox("🏫 Chọn khối lớp:", ["1", "2", "3", "4", "5"])
    mon = st.selectbox("📘 Chọn môn học:", ["Toán", "Tiếng Việt", "Tiếng Anh"])

    if st.button("🤖 Tạo đề thi bằng AI"):
        st.info("AI đang tạo đề... vui lòng đợi...")
        de_bai = tao_de_tu_ai(lop, mon)
        st.session_state.de_bai = de_bai
        st.session_state.cau_hoi = tach_cau_hoi_va_dap_an(de_bai)
        st.session_state.dap_an_hs = [""] * len(st.session_state.cau_hoi)
        st.success("✅ Đề thi đã sẵn sàng!")

    # Nếu đã có đề thi
    if "cau_hoi" in st.session_state:
        st.subheader("📄 Bài kiểm tra")
        for i, (noi_dung, dap_an) in enumerate(st.session_state.cau_hoi):
    # Đảm bảo xuống dòng trước các lựa chọn A., B., C., D.
            noi_dung_hien_thi = re.sub(r"(?<!\n)([A-D]\.)", r"\n\1", noi_dung)
            st.markdown(f"**{noi_dung_hien_thi.strip()}**")

            st.session_state.dap_an_hs[i] = st.radio(
                f"Chọn đáp án cho câu {i+1}:",
                ["A", "B", "C", "D"],
                index=None,
                key=f"cau_{i}"
            )

        if st.button("📤 Nộp bài"):
            # ⚠️ Kiểm tra xem có câu nào chưa chọn không
            if "" in st.session_state.dap_an_hs:
                st.error("⚠️ Em chưa chọn đủ đáp án cho tất cả các câu hỏi!")
            else:
                diem = cham_diem(st.session_state.cau_hoi, st.session_state.dap_an_hs)
                st.success(f"✅ Em làm đúng {diem}/{len(st.session_state.cau_hoi)} câu!")

                new_row = pd.DataFrame([[ten, lop, mon, diem]],
                                       columns=["Họ tên", "Lớp", "Môn", "Điểm"])
                try:
                    old = pd.read_csv("ketqua.csv")
                    df = pd.concat([old, new_row], ignore_index=True)
                except:
                    df = new_row
                df.to_csv("ketqua.csv", index=False)
                st.balloons()
