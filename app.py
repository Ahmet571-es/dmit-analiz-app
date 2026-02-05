import streamlit as st
import pandas as pd
import db_manager
import grok_service
import time

# -----------------------------------------------------------------------------
# 1. SAYFA VE TASARIM AYARLARI (CSS BÜYÜSÜ BURADA)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DMIT Genetik Analiz",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Özel CSS Tasarımı
st.markdown("""
<style>
    /* 1. Genel Sayfa Arka Planı */
    .stApp {
        background: linear-gradient(to bottom right, #f0f2f6, #e2eafc);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* 2. Başlıklar */
    h1 {
        color: #1e3a8a; /* Koyu Lacivert */
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        font-weight: 700;
    }
    h2, h3 {
        color: #2c3e50;
    }

    /* 3. Özel Buton Tasarımı (Gradyan ve Yuvarlak) */
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
        border-color: transparent;
        color: white;
    }
    
    /* 4. Giriş Kutuları (Input Fields) */
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 1px solid #cbd5e1;
        padding: 10px;
    }
    .stTextInput>div>div>input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }

    /* 5. Kart Görünümü İçin Çerçeveler */
    div[data-testid="stExpander"] {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* 6. Sidebar (Yan Menü) */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Sekme (Tab) Tasarımı */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 10px 10px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #eff6ff;
        color: #1e40af;
        border-bottom: 2px solid #3b82f6;
    }

</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. SESSION STATE
# -----------------------------------------------------------------------------
if 'auth_status' not in st.session_state:
    st.session_state['auth_status'] = None
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None
if 'analysis_data' not in st.session_state:
    st.session_state['analysis_data'] = {}

db_manager.init_db()

# -----------------------------------------------------------------------------
# 3. YARDIMCI FONKSİYONLAR
# -----------------------------------------------------------------------------
def login_student(name, surname):
    if name and surname:
        st.session_state['auth_status'] = 'student'
        st.session_state['current_user'] = f"{name} {surname}"
        st.rerun()
    else:
        st.warning("⚠️ Lütfen Ad ve Soyad alanlarını doldurunuz.")

def login_teacher(username, password):
    if username == "admin" and password == "1234":
        st.session_state['auth_status'] = 'teacher'
        st.session_state['current_user'] = "Yönetici"
        st.rerun()
    else:
        st.error("❌ Hatalı kullanıcı adı veya şifre!")

def logout():
    st.session_state['auth_status'] = None
    st.session_state['current_user'] = None
    st.session_state['results'] = {}
    st.rerun()

# -----------------------------------------------------------------------------
# 4. ANA UYGULAMA
# -----------------------------------------------------------------------------
def main():
    # --- YAN MENÜ ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2920/2920349.png", width=100) # DNA ikonu
        st.title("DMIT Sistemi")
        st.markdown("Genetik Potansiyel Analizi")
        st.markdown("---")
        
        if st.session_state['auth_status']:
            st.success(f"👤 Aktif: **{st.session_state['current_user']}**")
            if st.button("🚪 Çıkış Yap"):
                logout()
        
        st.markdown("---")
        st.caption("🔒 Güvenli Veri Tabanı")
        st.caption("© 2026 Nobel Koçluk")

    # --- GİRİŞ EKRANI ---
    if st.session_state['auth_status'] is None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("<h1 style='text-align: center;'>Genetik Analiz Platformu</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>Lütfen giriş yapmak için rolünüzü seçiniz.</p>", unsafe_allow_html=True)
            st.markdown("---")
            
            tab_student, tab_teacher = st.tabs(["🎓 ÖĞRENCİ GİRİŞİ", "👨‍🏫 YÖNETİCİ GİRİŞİ"])
            
            with tab_student:
                st.markdown("### 👋 Hoş Geldin!")
                s_name = st.text_input("Adınız", placeholder="Örn: Ahmet")
                s_surname = st.text_input("Soyadınız", placeholder="Örn: Yılmaz")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🚀 Analize Başla", use_container_width=True):
                    login_student(s_name, s_surname)
            
            with tab_teacher:
                st.markdown("### 🔒 Yetkili Girişi")
                t_user = st.text_input("Kullanıcı Adı", placeholder="admin")
                t_pass = st.text_input("Şifre", type="password", placeholder="****")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔐 Sisteme Gir", use_container_width=True):
                    login_teacher(t_user, t_pass)

    # --- ÖĞRENCİ EKRANI ---
    elif st.session_state['auth_status'] == 'student':
        st.markdown(f"## 🧬 Merhaba, {st.session_state['current_user']}")
        st.info("💡 **Bilgi:** Lütfen parmaklarınızı sırasıyla seçip, net bir şekilde fotoğrafını yükleyiniz.")
        
        # Parmak Seçimi ve İlerleme
        fingers = {
            "L1": "Sol Başparmak", "L2": "Sol İşaret", "L3": "Sol Orta", "L4": "Sol Yüzük", "L5": "Sol Serçe",
            "R1": "Sağ Başparmak", "R2": "Sağ İşaret", "R3": "Sağ Orta", "R4": "Sağ Yüzük", "R5": "Sağ Serçe"
        }
        
        # Güzel bir kutu içinde seçim
        with st.container():
            col_sel1, col_sel2 = st.columns([1, 3])
            with col_sel1:
                st.write("### 👇 Seçim Yap")
            with col_sel2:
                selected_finger_code = st.selectbox(
                    "Analiz edilecek parmağı seçiniz:", 
                    list(fingers.keys()), 
                    format_func=lambda x: f"{x} - {fingers[x]}"
                )

        st.markdown("---")

        # İki Kolonlu Tasarım
        col_img, col_res = st.columns(2, gap="large")
        
        with col_img:
            st.markdown("#### 1. 📸 Fotoğraf Yükle")
            uploaded_file = st.file_uploader(f"{fingers[selected_finger_code]} Resmi", type=['png', 'jpg', 'jpeg'])
            if uploaded_file:
                st.image(uploaded_file, caption="Yüklenen Resim", use_container_width=True)
            
        with col_res:
            st.markdown("#### 2. 🧠 Yapay Zeka Analizi")
            
            if uploaded_file is not None:
                if st.button("✨ ANALİZİ BAŞLAT", use_container_width=True):
                    with st.status("Grok AI Görüntüyü İşliyor...", expanded=True) as status:
                        st.write("🔍 Görüntü netleştiriliyor...")
                        time.sleep(1)
                        st.write("🧬 Desen taranıyor (Loop/Whorl/Arch)...")
                        time.sleep(1)
                        
                        # Grok Vision Analizi
                        image_bytes = uploaded_file.getvalue()
                        result = grok_service.analyze_fingerprint(image_bytes, selected_finger_code)
                        
                        # Kaydet
                        if 'results' not in st.session_state:
                            st.session_state['results'] = {}
                        st.session_state['results'][selected_finger_code] = result
                        
                        status.update(label="✅ Analiz Tamamlandı!", state="complete", expanded=False)

                    # Sonuç Gösterimi (Kart Stilinde)
                    if result.get("type") == "Error":
                        st.error(f"Hata: {result.get('note')}")
                    else:
                        st.success("Tespiti Başarılı!")
                        st.markdown(f"""
                        <div style="background-color: #f0fdf4; padding: 20px; border-radius: 10px; border: 1px solid #bbf7d0;">
                            <h3 style="color: #166534; margin:0;">Sonuç: {result.get('type')}</h3>
                            <p><strong>Ridge Count (RC):</strong> {result.get('rc')}</p>
                            <p><strong>Güven Skoru:</strong> {result.get('confidence')}</p>
                            <hr>
                            <p style="font-style: italic;">"{result.get('dmit_insight')}"</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("👈 Analiz için lütfen önce sol taraftan resim yükleyin.")

        st.markdown("---")
        
        # Tamamla Butonu (Devasa ve Dikkat Çekici)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✅ TÜM İŞLEMLERİ BİTİR VE GÖNDER", type="primary", use_container_width=True):
            if 'results' in st.session_state and len(st.session_state['results']) > 0:
                student_full_name = st.session_state['current_user']
                for f_code, data in st.session_state['results'].items():
                    db_manager.add_fingerprint_record(
                        student_name=student_full_name,
                        finger_code=f_code,
                        image_path="memory",
                        pattern_type=data.get("type", "Unknown"),
                        ridge_count=data.get("rc", 0),
                        confidence=data.get("confidence", "Low"),
                        dmit_insight=data.get("dmit_insight", "")
                    )
                st.balloons()
                st.success("Veriler başarıyla merkeze iletildi! Yönlendiriliyorsunuz...")
                time.sleep(3)
                logout()
            else:
                st.error("Henüz hiç parmak analizi yapmadınız!")

    # --- ÖĞRETMEN EKRANI ---
    elif st.session_state['auth_status'] == 'teacher':
        st.markdown("## 👨‍🏫 Yönetim ve Raporlama Merkezi")
        
        col_t1, col_t2 = st.columns([1, 2])
        
        with col_t1:
            st.markdown("### 📋 Öğrenci Listesi")
            students = db_manager.get_all_students()
            if not students:
                st.info("Sistemde kayıtlı öğrenci yok.")
            else:
                selected_student = st.radio("Raporlanacak Öğrenci:", students)

        with col_t2:
            st.markdown("### 📝 Rapor İşlemleri")
            if students and selected_student:
                st.write(f"Seçilen: **{selected_student}**")
                
                if st.button("🧬 NOBEL GENETİK RAPORU OLUŞTUR", type="primary"):
                    with st.spinner("Yapay Zeka raporu yazıyor... Lütfen bekleyiniz..."):
                        finger_data = db_manager.get_student_data(selected_student)
                        if finger_data.empty:
                            st.error("Veri bulunamadı.")
                        else:
                            scores = db_manager.calculate_dmit_scores(finger_data)
                            report_text = grok_service.generate_nobel_report(selected_student, 12, finger_data, scores)
                            
                            st.markdown("---")
                            st.markdown(report_text)
                            st.download_button(
                                label="📥 Raporu İndir (MD/PDF)",
                                data=report_text,
                                file_name=f"{selected_student}_Rapor.md",
                                mime="text/markdown"
                            )

if __name__ == "__main__":
    main()
