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
    
    /* Yönerge Kutusu Tasarımı */
    .instruction-box {
        background-color: #fffbeb;
        border-left: 5px solid #f59e0b;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Butonlar */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: transform 0.2s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    
    /* Kartlar */
    div[data-testid="stExpander"] {
        border: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-radius: 10px;
    }
    
    /* Radio Butonu Yatay ve Şık Yapma */
    div.row-widget.stRadio > div {
        flex-direction: row;
        align-items: stretch;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label {
        background-color: #ffffff;
        padding: 10px 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-right: 10px;
        transition: all 0.3s;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover {
        background-color: #eff6ff;
        border-color: #3b82f6;
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
    # --- GÜNCELLENEN GİRİŞ BİLGİLERİ (BALABAN KOÇLUK) ---
    if username == "Balaban Koçluk" and password == "Balaban_İstanbul_Gümüşhane":
        st.session_state['auth_status'] = 'teacher'
        st.session_state['current_user'] = "Yönetici (Balaban Koçluk)"
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
        st.image("https://cdn-icons-png.flaticon.com/512/2920/2920349.png", width=80)
        st.title("DMIT Sistemi")
        st.markdown("Genetik Potansiyel Analizi")
        st.markdown("---")
        
        if st.session_state['auth_status']:
            st.success(f"👤 Aktif: **{st.session_state['current_user']}**")
            if st.button("🚪 Çıkış Yap", use_container_width=True):
                logout()
        
        st.markdown("---")
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

    # --- ÖĞRENCİ EKRANI (ANALİZ) ---
    elif st.session_state['auth_status'] == 'student':
        
        # --- DETAYLI YÖNERGE ---
        st.markdown(f"## 🧬 Merhaba, {st.session_state['current_user']}")
        
        with st.expander("ℹ️ UYGULAMA KULLANIM KILAVUZU (Lütfen Başlamadan Önce Okuyunuz)", expanded=True):
            st.markdown("""
            <div class="instruction-box">
                <h4>📸 Fotoğraf Çekim Sırası ve Kuralları</h4>
                <p>Doğru bir analiz raporu alabilmek için lütfen aşağıdaki adımları sırasıyla uygulayınız:</p>
                <ol>
                    <li><strong>Seçim:</strong> Kamera ile anlık çekim yapabilir veya galeriden fotoğraf yükleyebilirsiniz.</li>
                    <li><strong>Odaklama (Çok Önemli):</strong> Telefon kamerasını parmağınıza yaklaştırın (Makro çekim). Parmak izi çizgileri net olmalıdır.</li>
                    <li><strong>Sıralama:</strong> Lütfen parmak sırasına riayet ediniz (L1 -> R5).</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        fingers = {
            "L1": "Sol Başparmak", "L2": "Sol İşaret", "L3": "Sol Orta", "L4": "Sol Yüzük", "L5": "Sol Serçe",
            "R1": "Sağ Başparmak", "R2": "Sağ İşaret", "R3": "Sağ Orta", "R4": "Sağ Yüzük", "R5": "Sağ Serçe"
        }
        
        # 1. PARMAK SEÇİMİ
        col_sel1, col_sel2 = st.columns([1, 3])
        with col_sel1:
            st.markdown("### 👇 1. Adım: Parmak")
        with col_sel2:
            selected_finger_code = st.selectbox(
                "Analiz edilecek parmağı seçiniz:", 
                list(fingers.keys()), 
                format_func=lambda x: f"{x} - {fingers[x]}"
            )

        col_img, col_res = st.columns(2, gap="large")
        
        with col_img:
            st.markdown(f"#### 2. Adım: Görüntü Kaynağı")
            
            # --- YENİ EKLENEN KISIM: KAMERA / DOSYA SEÇİMİ ---
            input_method = st.radio(
                "Yükleme Yöntemi Seçiniz:",
                ("📁 Galeriden Yükle", "📸 Kamera ile Çek"),
                horizontal=True
            )
            
            uploaded_file = None
            
            if input_method == "📁 Galeriden Yükle":
                uploaded_file = st.file_uploader(f"{fingers[selected_finger_code]} Resmi Seç", type=['png', 'jpg', 'jpeg'], key=f"uploader_{selected_finger_code}")
                if uploaded_file:
                    st.image(uploaded_file, caption="Seçilen Resim", width=300)
            else:
                # Kamera Modu
                camera_photo = st.camera_input(f"{fingers[selected_finger_code]} Çek", key=f"cam_{selected_finger_code}")
                if camera_photo:
                    uploaded_file = camera_photo # Kamera verisini uploaded_file değişkenine ata
                    st.success("Fotoğraf Çekildi!")

        with col_res:
            st.markdown("#### 3. Adım: Yapay Zeka Analizi")
            
            if uploaded_file is not None:
                if st.button("✨ BU PARMAĞI ANALİZ ET", use_container_width=True):
                    with st.status("Grok AI Görüntüyü İşliyor...", expanded=True) as status:
                        st.write("🔍 Görüntü netliği ve kontrastı işleniyor (OpenCV)...")
                        time.sleep(0.5)
                        st.write("🧬 Desen taranıyor (Loop/Whorl/Arch)...")
                        
                        image_bytes = uploaded_file.getvalue()
                        result = grok_service.analyze_fingerprint(image_bytes, selected_finger_code)
                        
                        st.session_state['results'][selected_finger_code] = result
                        status.update(label="✅ Analiz Başarılı!", state="complete", expanded=False)

                    if result.get("type") == "Error":
                        st.error(f"Hata: {result.get('note')}")
                    else:
                        st.success("Tespit Edildi!")
                        st.markdown(f"""
                        <div style="background-color: #f0fdf4; padding: 15px; border-radius: 10px; border: 1px solid #bbf7d0;">
                            <h3 style="color: #166534; margin:0;">Sonuç: {result.get('type')}</h3>
                            <p><strong>Ridge Count (RC):</strong> {result.get('rc')}</p>
                            <p><strong>Güven:</strong> {result.get('confidence')}</p>
                            <p style="font-size: 0.9em;"><em>"{result.get('dmit_insight')}"</em></p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("👈 Lütfen önce sol taraftan fotoğraf yükleyiniz veya çekiniz.")

        st.markdown("---")
        
        st.markdown("### 🏁 Son Adım: Gönderim")
        st.write("Tüm parmakları (L1'den R5'e kadar) analiz ettikten sonra aşağıdaki butona basınız.")
        
        if st.button("✅ TÜM ANALİZLERİ BİTİR VE ÖĞRETMENE GÖNDER", type="primary", use_container_width=True):
            if len(st.session_state['results']) > 0:
                student_full_name = st.session_state['current_user']
                
                progress_text = "Veriler veritabanına işleniyor..."
                my_bar = st.progress(0, text=progress_text)

                for percent_complete, (f_code, data) in enumerate(st.session_state['results'].items()):
                    db_manager.add_fingerprint_record(
                        student_name=student_full_name,
                        finger_code=f_code,
                        image_path="memory",
                        pattern_type=data.get("type", "Unknown"),
                        ridge_count=data.get("rc", 0),
                        confidence=data.get("confidence", "Low"),
                        dmit_insight=data.get("dmit_insight", "")
                    )
                    time.sleep(0.1)
                    my_bar.progress((percent_complete + 1) / len(st.session_state['results']), text=progress_text)
                
                my_bar.empty()
                st.balloons()
                st.success("🎉 Tebrikler! Verileriniz başarıyla kaydedildi. Öğretmeniniz raporu oluşturabilir.")
                time.sleep(4)
                logout()
            else:
                st.error("⚠️ Henüz hiç parmak analizi yapmadınız!")

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
