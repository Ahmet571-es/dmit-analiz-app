import streamlit as st
import pandas as pd
import db_manager
import grok_service
import time

# -----------------------------------------------------------------------------
# 1. SAYFA VE TASARIM AYARLARI
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
    .stApp {
        background: linear-gradient(to bottom right, #f8fafc, #eef2ff);
        font-family: 'Segoe UI', sans-serif;
    }
    h1 { color: #1e3a8a; font-weight: 800; }
    h2, h3 { color: #334155; }
    
    /* Yönerge Kutusu */
    .instruction-box {
        background-color: #fffbeb;
        border-left: 5px solid #f59e0b;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        font-size: 0.95em;
    }

    /* Durum Kartları */
    .status-card {
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 5px;
        font-size: 0.85em;
    }
    .status-pending { background-color: #e2e8f0; color: #64748b; border: 1px dashed #cbd5e1; }
    .status-done { background-color: #dcfce7; color: #166534; border: 1px solid #86efac; }

    /* Butonlar */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: transform 0.2s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    
    /* Radio Butonu Özelleştirme */
    div.row-widget.stRadio > div {
        flex-direction: row;
        gap: 20px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. SESSION STATE (HAFIZA)
# -----------------------------------------------------------------------------
if 'auth_status' not in st.session_state:
    st.session_state['auth_status'] = None
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None

# --- ÖNEMLİ: Geçici Resim Klasörü ---
# Kullanıcı resimleri yükledikçe buraya dolacak. Analiz henüz yapılmayacak.
if 'finger_folder' not in st.session_state:
    st.session_state['finger_folder'] = {}  # Örn: {'L1': b'resim_data', 'R1': b'resim_data'}

# Sonuçların tutulduğu yer
if 'results' not in st.session_state:
    st.session_state['results'] = {}

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
    if username == "Balaban Koçluk" and password == "Balaban_İstanbul_Gümüşhane":
        st.session_state['auth_status'] = 'teacher'
        st.session_state['current_user'] = "Yönetici (Balaban Koçluk)"
        st.rerun()
    else:
        st.error("❌ Hatalı kullanıcı adı veya şifre!")

def logout():
    st.session_state['auth_status'] = None
    st.session_state['current_user'] = None
    st.session_state['finger_folder'] = {}
    st.session_state['results'] = {}
    st.rerun()

# -----------------------------------------------------------------------------
# 4. ANA UYGULAMA
# -----------------------------------------------------------------------------
def main():
    # --- YAN MENÜ ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2920/2920349.png", width=80)
        st.title("DMIT Sistemi")
        st.markdown("Genetik Potansiyel Analizi")
        st.markdown("---")
        
        if st.session_state['auth_status']:
            st.success(f"👤 **{st.session_state['current_user']}**")
            # İlerleme Durumu (Sidebar'da gösterim)
            if st.session_state['auth_status'] == 'student':
                count = len(st.session_state['finger_folder'])
                st.progress(count / 10, text=f"Dosya Durumu: {count}/10")
            
            st.markdown("---")
            if st.button("🚪 Çıkış Yap", use_container_width=True):
                logout()
        
        st.caption("🔒 Güvenli Veri Tabanı")

    # --- GİRİŞ EKRANI ---
    if st.session_state['auth_status'] is None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("<h1 style='text-align: center;'>Genetik Analiz Platformu</h1>", unsafe_allow_html=True)
            st.info("👋 Hoş geldiniz. Lütfen analize başlamak için giriş yapınız.")
            
            tab_student, tab_teacher = st.tabs(["🎓 ÖĞRENCİ GİRİŞİ", "👨‍🏫 YÖNETİCİ GİRİŞİ"])
            
            with tab_student:
                s_name = st.text_input("Adınız", placeholder="Örn: Ahmet")
                s_surname = st.text_input("Soyadınız", placeholder="Örn: Yılmaz")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🚀 Giriş Yap ve Başla", type="primary", use_container_width=True):
                    login_student(s_name, s_surname)
            
            with tab_teacher:
                t_user = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı Adı")
                t_pass = st.text_input("Şifre", type="password", placeholder="Şifre")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔐 Yönetici Girişi", use_container_width=True):
                    login_teacher(t_user, t_pass)

    # --- ÖĞRENCİ EKRANI (TOPLU YÜKLEME MODU) ---
    elif st.session_state['auth_status'] == 'student':
        
        # 1. Başlık ve Yönerge
        st.markdown(f"## 🧬 Merhaba, {st.session_state['current_user']}")
        
        with st.expander("ℹ️ NASIL KULLANILIR? (Lütfen Okuyunuz)", expanded=False):
            st.markdown("""
            <div class="instruction-box">
                <b>Adım 1:</b> Aşağıdan bir parmak seçin (Örn: Sol Başparmak).<br>
                <b>Adım 2:</b> Kamera veya Galeri ile fotoğrafı yükleyin.<br>
                <b>Adım 3:</b> '📂 Klasöre Kaydet' butonuna basın. (Bunu 10 parmak için yapın).<br>
                <b>Adım 4:</b> Tüm parmaklar klasöre eklendikten sonra en alttaki '✅ ANALİZİ BAŞLAT' butonuna basın.
            </div>
            """, unsafe_allow_html=True)

        # 2. DOSYA DURUM PANELİ (DASHBOARD)
        st.markdown("### 📁 Dosya Klasörünüz")
        st.caption("Aşağıdaki tablo yüklediğiniz parmakları gösterir. Lütfen tüm kutuları yeşil yapınız.")
        
        fingers_order = ["L1", "L2", "L3", "L4", "L5", "R1", "R2", "R3", "R4", "R5"]
        fingers_names = {
            "L1": "Sol Baş", "L2": "Sol İşaret", "L3": "Sol Orta", "L4": "Sol Yüzük", "L5": "Sol Serçe",
            "R1": "Sağ Baş", "R2": "Sağ İşaret", "R3": "Sağ Orta", "R4": "Sağ Yüzük", "R5": "Sağ Serçe"
        }

        # 5'li iki satır halinde gösterim
        cols = st.columns(5)
        for i, f_code in enumerate(fingers_order[:5]): # Sol El
            uploaded = f_code in st.session_state['finger_folder']
            style = "status-done" if uploaded else "status-pending"
            icon = "✅" if uploaded else "⭕"
            cols[i].markdown(f"<div class='status-card {style}'>{icon} {fingers_names[f_code]}</div>", unsafe_allow_html=True)
        
        cols2 = st.columns(5)
        for i, f_code in enumerate(fingers_order[5:]): # Sağ El
            index = i
            uploaded = f_code in st.session_state['finger_folder']
            style = "status-done" if uploaded else "status-pending"
            icon = "✅" if uploaded else "⭕"
            cols2[index].markdown(f"<div class='status-card {style}'>{icon} {fingers_names[f_code]}</div>", unsafe_allow_html=True)

        st.markdown("---")

        # 3. YÜKLEME ALANI
        col_left, col_right = st.columns([1, 1.5], gap="large")
        
        with col_left:
            st.markdown("### 📸 Resim Ekleme")
            
            # Hangi parmak?
            selected_finger_code = st.selectbox(
                "1. Hangi parmağı yükleyeceksiniz?", 
                list(fingers_names.keys()), 
                format_func=lambda x: f"{x} - {fingers_names[x]}"
            )

            # Kaynak Seçimi
            input_method = st.radio("2. Yöntem Seçiniz:", ("📁 Galeri / Dosya", "📸 Kamera"), horizontal=True)
            
            uploaded_file = None
            if input_method == "📁 Galeri / Dosya":
                uploaded_file = st.file_uploader(f"{fingers_names[selected_finger_code]} Yükle", type=['png', 'jpg', 'jpeg'], key=f"up_{selected_finger_code}")
            else:
                uploaded_file = st.camera_input(f"{fingers_names[selected_finger_code]} Çek", key=f"cam_{selected_finger_code}")

            # Klasöre Ekle Butonu
            if uploaded_file:
                # Önizleme
                st.image(uploaded_file, width=150, caption="Önizleme")
                if st.button(f"📂 {fingers_names[selected_finger_code]} Resmini Klasöre Koy", type="secondary"):
                    # Byte verisini alıp hafızaya atıyoruz
                    st.session_state['finger_folder'][selected_finger_code] = uploaded_file.getvalue()
                    st.success(f"✅ {fingers_names[selected_finger_code]} klasöre eklendi! Sıradakine geçebilirsiniz.")
                    time.sleep(1)
                    st.rerun()

        with col_right:
            st.markdown("### 🏁 İşlemi Tamamla")
            st.write("Klasörünüzde şu an **{}** adet parmak resmi var.".format(len(st.session_state['finger_folder'])))
            
            if len(st.session_state['finger_folder']) < 10:
                st.warning("⚠️ Analizi başlatmak için lütfen 10 parmağın hepsini yükleyiniz.")
            else:
                st.success("Tüm parmaklar hazır! Aşağıdaki butona basarak görüntü tespiti işlemini başlatabilirsiniz.")
                
                # --- FİNAL BUTONU ---
                if st.button("✅ TÜM RESİMLERİ SİSTEME YÜKLE VE ANALİZİ BAŞLAT", type="primary", use_container_width=True):
                    
                    progress_bar = st.progress(0, text="Görüntü tespiti başlatılıyor...")
                    status_text = st.empty()
                    
                    student_full_name = st.session_state['current_user']
                    total_files = len(st.session_state['finger_folder'])
                    
                    # DÖNGÜ: Her bir resmi sırayla Grok'a gönder
                    for i, (f_code, img_bytes) in enumerate(st.session_state['finger_folder'].items()):
                        
                        status_text.text(f"⏳ İşleniyor: {fingers_names[f_code]} (Grok Vision + OpenCV)...")
                        
                        # 1. Analiz Et (Grok Service)
                        result = grok_service.analyze_fingerprint(img_bytes, f_code)
                        
                        # 2. Veritabanına Kaydet
                        db_manager.add_fingerprint_record(
                            student_name=student_full_name,
                            finger_code=f_code,
                            image_path="memory", # Şimdilik fiziksel yol yok
                            pattern_type=result.get("type", "Unknown"),
                            ridge_count=result.get("rc", 0),
                            confidence=result.get("confidence", "Low"),
                            dmit_insight=result.get("dmit_insight", "")
                        )
                        
                        # İlerleme Çubuğu Güncelle
                        progress_bar.progress((i + 1) / total_files)
                        time.sleep(0.5) # Kullanıcı görsün diye minik bekleme
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Final Başarı Mesajı (Kullanıcının istediği metin)
                    st.balloons()
                    st.success("✅ Parmak resimleriniz başarıyla analiz edildi ve yetkili koçunuzun sistemine gönderildi.")
                    
                    # Hafızayı Temizle
                    st.session_state['finger_folder'] = {}
                    time.sleep(5)
                    logout()

    # --- ÖĞRETMEN EKRANI ---
    elif st.session_state['auth_status'] == 'teacher':
        st.markdown("## 👨‍🏫 Yönetim ve Raporlama Merkezi")
        st.caption(f"Yönetici: {st.session_state['current_user']}")
        
        col_t1, col_t2 = st.columns([1, 2])
        
        with col_t1:
            st.markdown("### 📋 Öğrenci Listesi")
            students = db_manager.get_all_students()
            if not students:
                st.info("Sistemde kayıtlı öğrenci yok.")
                selected_student = None
            else:
                selected_student = st.radio("Raporlanacak Öğrenciyi Seç:", students)

        with col_t2:
            st.markdown("### 📝 Rapor İşlemleri")
            if selected_student:
                st.info(f"Seçilen Öğrenci: **{selected_student}**")
                
                if st.button("🧬 BALABAN GENETİK RAPORU OLUŞTUR", type="primary"):
                    with st.spinner("Yapay Zeka (Grok Reasoning) raporu yazıyor... Bu işlem detaylı olduğu için 1-2 dakika sürebilir."):
                        finger_data = db_manager.get_student_data(selected_student)
                        if finger_data.empty:
                            st.error("Bu öğrenciye ait veri bulunamadı.")
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
