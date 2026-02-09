import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import plotly.express as px

# Yerel Modüller
import db_manager
import grok_service
import image_utils  # Bulanıklık kontrolü için şart

# -----------------------------------------------------------------------------
# 1. SAYFA VE TASARIM AYARLARI
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DMIT Genetik Analiz | Balaban Koçluk",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Özel CSS Tasarımı
st.markdown("""
<style>
    /* Genel Arka Plan */
    .stApp {
        background: linear-gradient(to bottom right, #f8fafc, #eef2ff);
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Başlıklar */
    h1 { color: #1e3a8a; font-weight: 800; }
    h2, h3 { color: #334155; }
    
    /* Bilgi Kutusu */
    .instruction-box {
        background-color: #fffbeb;
        border-left: 5px solid #f59e0b;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        font-size: 0.95em;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Durum Kartları (Dashboard) */
    .status-card {
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 5px;
        font-size: 0.85em;
        transition: all 0.3s ease;
    }
    .status-pending { 
        background-color: #e2e8f0; 
        color: #64748b; 
        border: 1px dashed #cbd5e1; 
    }
    .status-done { 
        background-color: #dcfce7; 
        color: #166534; 
        border: 1px solid #86efac; 
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
    
    /* Radio ve Selectbox İyileştirmeleri */
    div.row-widget.stRadio > div {
        flex-direction: row;
        gap: 15px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. SESSION STATE (HAFIZA YÖNETİMİ)
# -----------------------------------------------------------------------------
# Kimlik Doğrulama Durumu
if 'auth_status' not in st.session_state:
    st.session_state['auth_status'] = None
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None

# Öğrenci Bilgileri (Yaş ve Cinsiyet)
if 'student_age' not in st.session_state:
    st.session_state['student_age'] = 12
if 'student_gender' not in st.session_state:
    st.session_state['student_gender'] = "Belirtilmemiş"

# Geçici Resim Klasörü (Toplu Yükleme İçin)
if 'finger_folder' not in st.session_state:
    st.session_state['finger_folder'] = {}

# Sonuçlar
if 'results' not in st.session_state:
    st.session_state['results'] = {}

# Veritabanını Başlat
db_manager.init_db()

# -----------------------------------------------------------------------------
# 3. YARDIMCI FONKSİYONLAR
# -----------------------------------------------------------------------------
def login_student(name, surname, age, gender):
    """Öğrenci girişi yapar ve bilgileri hafızaya alır."""
    if name and surname:
        st.session_state['auth_status'] = 'student'
        st.session_state['current_user'] = f"{name} {surname}"
        st.session_state['student_age'] = age
        st.session_state['student_gender'] = gender
        st.rerun()
    else:
        st.warning("⚠️ Lütfen Ad ve Soyad alanlarını doldurunuz.")

def login_teacher(username, password):
    """Yönetici girişi yapar (Balaban Koçluk)."""
    if username == "Balaban Koçluk" and password == "Balaban_İstanbul_Gümüşhane":
        st.session_state['auth_status'] = 'teacher'
        st.session_state['current_user'] = "Yönetici (Balaban Koçluk)"
        st.rerun()
    else:
        st.error("❌ Hatalı kullanıcı adı veya şifre!")

def logout():
    """Çıkış yapar ve hafızayı temizler."""
    st.session_state['auth_status'] = None
    st.session_state['current_user'] = None
    st.session_state['finger_folder'] = {}
    st.session_state['results'] = {}
    st.rerun()

# -----------------------------------------------------------------------------
# 4. GÖRSELLEŞTİRME FONKSİYONU (PLOTLY DASHBOARD)
# -----------------------------------------------------------------------------
def render_dmit_dashboard(scores):
    """
    Öğrenci puanlarını alıp Plotly ile profesyonel grafikler çizer.
    """
    if not scores: return

    # --- VERİ HAZIRLIĞI ---
    lobes = scores.get("lobes", {})
    tfrc = scores.get("tfrc", 100)
    
    # Grupları Hesapla (Grok Service Mantığıyla - Görsel Tahmin)
    teknik = lobes.get('prefrontal',0) + lobes.get('parietal',0)
    sosyal = lobes.get('temporal',0) + lobes.get('frontal',0)
    matematik = lobes.get('frontal',0) + lobes.get('parietal',0)
    fen = lobes.get('occipital',0) + lobes.get('parietal',0)
    
    # 1. TFRC GÖSTERGESİ (GAUGE CHART)
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = tfrc,
        title = {'text': "Toplam Öğrenme Kapasitesi (TFRC)"},
        gauge = {
            'axis': {'range': [None, 200]},
            'bar': {'color': "#1e3a8a"},
            'steps' : [
                {'range': [0, 90], 'color': "#fee2e2"},   # Düşük
                {'range': [90, 140], 'color': "#fef3c7"}, # Normal
                {'range': [140, 200], 'color': "#dcfce7"}], # Yüksek
            'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': tfrc}}
    ))
    
    # 2. BEYİN LOBLARI RADAR GRAFİĞİ
    l_vals = list(lobes.values())
    l_keys = list(lobes.keys())
    tr_map = {
        'prefrontal': 'Prefrontal (Yönetim)',
        'frontal': 'Frontal (Mantık)',
        'parietal': 'Parietal (Bedensel)',
        'temporal': 'Temporal (İşitsel)',
        'occipital': 'Oksipital (Görsel)'
    }
    r_keys = [tr_map.get(k, k) for k in l_keys]
    
    fig_radar = go.Figure(data=go.Scatterpolar(
        r=l_vals,
        theta=r_keys,
        fill='toself',
        name='Beyin Lobları',
        line_color='#7c3aed'
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(l_vals)+10])),
        title="Beyin Lobu Dağılımı",
        margin=dict(t=40, b=40, l=40, r=40)
    )

    # 3. YETENEK ALANLARI (BAR CHART)
    cats = ['Teknik / Mühendislik', 'Sosyal / Dil', 'Matematik / Mantık', 'Fen / Doğa']
    vals = [teknik, sosyal, matematik, fen]
    colors = ['#3b82f6', '#ec4899', '#f59e0b', '#10b981']
    
    fig_bar = go.Figure(go.Bar(
        x=vals,
        y=cats,
        orientation='h',
        marker_color=colors,
        text=vals,
        textposition='auto'
    ))
    fig_bar.update_layout(title="Yetenek Alanları Puanı", margin=dict(t=30, b=30, l=30, r=30))

    # --- GRAFİKLERİ EKRANA BAS ---
    st.markdown("### 📊 Görsel Analiz Özeti")
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_gauge, use_container_width=True)
    with col2:
        st.plotly_chart(fig_radar, use_container_width=True)
        
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown("---")

# -----------------------------------------------------------------------------
# 5. ANA UYGULAMA AKIŞI
# -----------------------------------------------------------------------------
def main():
    # --- YAN MENÜ (SIDEBAR) ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2920/2920349.png", width=80)
        st.title("DMIT Sistemi")
        st.markdown("Genetik Potansiyel Analizi")
        st.markdown("---")
        
        if st.session_state['auth_status']:
            st.success(f"👤 **{st.session_state['current_user']}**")
            
            # Öğrenciyse detayları göster
            if st.session_state['auth_status'] == 'student':
                st.caption(f"🎂 Yaş: {st.session_state['student_age']}")
                st.caption(f"⚧️ Cinsiyet: {st.session_state['student_gender']}")
                
                # Dosya İlerleme Çubuğu
                count = len(st.session_state['finger_folder'])
                st.progress(count / 10, text=f"Dosya: {count}/10")
            
            st.markdown("---")
            if st.button("🚪 Çıkış Yap", use_container_width=True):
                logout()
        
        st.markdown("---")
        st.caption("🔒 Güvenli Veri Tabanı")
        st.caption("© 2026 Balaban Koçluk")

    # --- GİRİŞ EKRANI ---
    if st.session_state['auth_status'] is None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("<h1 style='text-align: center;'>Genetik Analiz Platformu</h1>", unsafe_allow_html=True)
            st.info("👋 Hoş geldiniz. Lütfen analize başlamak için giriş yapınız.")
            
            tab_student, tab_teacher = st.tabs(["🎓 ÖĞRENCİ GİRİŞİ", "👨‍🏫 YÖNETİCİ GİRİŞİ"])
            
            # 1. Öğrenci Giriş Sekmesi
            with tab_student:
                st.markdown("### 📝 Öğrenci Bilgileri")
                s_name = st.text_input("Adınız", placeholder="Örn: Ahmet")
                s_surname = st.text_input("Soyadınız", placeholder="Örn: Yılmaz")
                
                # YAŞ ve CİNSİYET
                col_age, col_gender = st.columns(2)
                with col_age:
                    s_age = st.number_input("Yaşınız", min_value=3, max_value=90, value=12, step=1)
                with col_gender:
                    s_gender = st.selectbox("Cinsiyetiniz", ["Erkek", "Kadın"])
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🚀 Giriş Yap ve Başla", type="primary", use_container_width=True):
                    login_student(s_name, s_surname, s_age, s_gender)
            
            # 2. Yönetici Giriş Sekmesi
            with tab_teacher:
                st.markdown("### 🔒 Yetkili Girişi")
                t_user = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı Adı")
                t_pass = st.text_input("Şifre", type="password", placeholder="Şifre")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔐 Yönetici Girişi", use_container_width=True):
                    login_teacher(t_user, t_pass)

    # --- ÖĞRENCİ EKRANI (TOPLU YÜKLEME MODU) ---
    elif st.session_state['auth_status'] == 'student':
        
        # Başlık ve Karşılama
        st.markdown(f"## 🧬 Merhaba, {st.session_state['current_user']}")
        
        # Kullanım Kılavuzu
        with st.expander("ℹ️ NASIL KULLANILIR? (Lütfen Okuyunuz)", expanded=False):
            st.markdown("""
            <div class="instruction-box">
                <b>Adım 1:</b> Aşağıdan bir parmak seçin (Örn: Sol Başparmak).<br>
                <b>Adım 2:</b> Kamera veya Galeri ile fotoğrafı yükleyin.<br>
                <b>Adım 3:</b> '📂 Klasöre Kaydet' butonuna basın. (Bunu 10 parmak için yapın).<br>
                <b>Adım 4:</b> Tüm parmaklar klasöre eklendikten sonra en alttaki '✅ ANALİZİ BAŞLAT' butonuna basın.
            </div>
            """, unsafe_allow_html=True)

        # ---------------------------------------------------------
        # BÖLÜM 1: DOSYA DURUM PANELİ (DASHBOARD)
        # ---------------------------------------------------------
        st.markdown("### 📁 Dosya Klasörünüz")
        st.caption("Aşağıdaki tablo yüklediğiniz parmakları gösterir. Lütfen tüm kutuları yeşil yapınız.")
        
        # Parmak İsimleri ve Sırası
        fingers_order = ["L1", "L2", "L3", "L4", "L5", "R1", "R2", "R3", "R4", "R5"]
        fingers_names = {
            "L1": "Sol Baş", "L2": "Sol İşaret", "L3": "Sol Orta", "L4": "Sol Yüzük", "L5": "Sol Serçe",
            "R1": "Sağ Baş", "R2": "Sağ İşaret", "R3": "Sağ Orta", "R4": "Sağ Yüzük", "R5": "Sağ Serçe"
        }

        # Dashboard Grid (5+5)
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

        # ---------------------------------------------------------
        # BÖLÜM 2: YÜKLEME ALANI & İŞLEM
        # ---------------------------------------------------------
        col_left, col_right = st.columns([1, 1.5], gap="large")
        
        with col_left:
            st.markdown("### 📸 Resim Ekleme")
            
            # 1. Parmak Seçimi
            selected_finger_code = st.selectbox(
                "1. Hangi parmağı yükleyeceksiniz?", 
                list(fingers_names.keys()), 
                format_func=lambda x: f"{x} - {fingers_names[x]}"
            )

            # 2. Kaynak Seçimi
            input_method = st.radio("2. Yöntem Seçiniz:", ("📁 Galeri / Dosya", "📸 Kamera"), horizontal=True)
            
            uploaded_file = None
            if input_method == "📁 Galeri / Dosya":
                uploaded_file = st.file_uploader(f"{fingers_names[selected_finger_code]} Yükle", type=['png', 'jpg', 'jpeg'], key=f"up_{selected_finger_code}")
            else:
                uploaded_file = st.camera_input(f"{fingers_names[selected_finger_code]} Çek", key=f"cam_{selected_finger_code}")

            # 3. Klasöre Ekleme İşlemi (BULANIKLIK KONTROLÜ İLE)
            if uploaded_file:
                st.image(uploaded_file, width=150, caption="Önizleme")
                img_bytes = uploaded_file.getvalue()

                # --- YENİ: DEDEKTİF (BULANIKLIK KONTROLÜ) ---
                # image_utils.py içinde check_image_quality fonksiyonu olmalı
                is_ok, score, msg = image_utils.check_image_quality(img_bytes)

                if st.button(f"📂 {fingers_names[selected_finger_code]} Resmini Klasöre Koy", type="secondary", use_container_width=True):
                    if not is_ok:
                        # Bulanık ise kaydetme, hata ver
                        st.error(msg)
                    else:
                        # Net ise kaydet
                        st.session_state['finger_folder'][selected_finger_code] = img_bytes
                        st.success(f"✅ Eklendi! (Netlik Puanı: {int(score)})")
                        time.sleep(0.5)
                        st.rerun()

        with col_right:
            st.markdown("### 🏁 İşlemi Tamamla")
            total_files = len(st.session_state['finger_folder'])
            st.write(f"Klasörünüzde şu an **{total_files}** adet parmak resmi var.")
            
            if total_files < 10:
                st.warning("⚠️ Analizi başlatmak için lütfen 10 parmağın hepsini yükleyiniz.")
            else:
                st.success("Tüm parmaklar hazır! Aşağıdaki butona basarak toplu analiz işlemini başlatabilirsiniz.")
                
                # --- FİNAL BUTONU ---
                if st.button("✅ TÜM RESİMLERİ SİSTEME YÜKLE VE ANALİZİ BAŞLAT", type="primary", use_container_width=True):
                    
                    progress_bar = st.progress(0, text="Görüntü tespiti başlatılıyor...")
                    status_text = st.empty()
                    
                    # Kullanıcı Bilgileri
                    student_full_name = st.session_state['current_user']
                    s_age = st.session_state['student_age']
                    s_gender = st.session_state['student_gender']
                    
                    # DÖNGÜ: Her bir resmi sırayla işle
                    for i, (f_code, img_bytes) in enumerate(st.session_state['finger_folder'].items()):
                        
                        status_text.text(f"⏳ İşleniyor: {fingers_names[f_code]} (Grok Vision + OpenCV)...")
                        
                        # 1. Analiz Et (Grok Service)
                        result = grok_service.analyze_fingerprint(img_bytes, f_code)
                        
                        # 2. Veritabanına Kaydet
                        db_manager.add_fingerprint_record(
                            student_name=student_full_name,
                            student_age=s_age,
                            student_gender=s_gender,
                            finger_code=f_code,
                            image_path="memory",
                            pattern_type=result.get("type", "Unknown"),
                            ridge_count=result.get("rc", 0),
                            confidence=result.get("confidence", "Low"),
                            dmit_insight=result.get("dmit_insight", "")
                        )
                        
                        progress_bar.progress((i + 1) / 10)
                        time.sleep(0.2) 
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.balloons()
                    st.success("✅ Parmak resimleriniz başarıyla analiz edildi ve yetkili koçunuzun sistemine gönderildi.")
                    
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
                    
                    # 1. Verileri Çek
                    finger_data = db_manager.get_student_data(selected_student)
                    
                    if finger_data.empty:
                        st.error("Bu öğrenciye ait veri bulunamadı.")
                    else:
                        try:
                            real_age = finger_data.iloc[0]['student_age']
                            real_gender = finger_data.iloc[0]['student_gender']
                        except KeyError:
                            real_age = 12
                            real_gender = "Belirtilmemiş"
                        
                        st.caption(f"Veritabanı Bilgisi -> Yaş: {real_age}, Cinsiyet: {real_gender}")

                        # 2. Puanları Hesapla
                        scores = db_manager.calculate_dmit_scores(finger_data)
                        
                        # 3. GRAFİK PANELİNİ GÖSTER (YENİ)
                        render_dmit_dashboard(scores)

                        # 4. Raporu Oluştur (Yapay Zeka)
                        with st.spinner("Yapay Zeka (Grok Reasoning) detaylı metin raporunu yazıyor..."):
                            report_text = grok_service.generate_nobel_report(selected_student, real_age, real_gender, finger_data, scores)
                            
                            st.markdown("### 📝 Detaylı Yazılı Rapor")
                            st.markdown(report_text)
                            st.download_button(
                                label="📥 Raporu İndir (MD/PDF)",
                                data=report_text,
                                file_name=f"{selected_student}_Rapor.md",
                                mime="text/markdown"
                            )

if __name__ == "__main__":
    main()
