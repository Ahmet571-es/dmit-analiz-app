# -*- coding: utf-8 -*-
"""
Created on Thu Feb  5 22:40:53 2026

@author: YYYNÇİGGGİİÜÜÜÜĞĞĞ
"""

import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
from db_manager import DBManager
from grok_service import analyze_fingerprint, generate_nobel_report
from dmit_engine import DMITEngine

# Sayfa Ayarları
st.set_page_config(page_title="DMIT Genetic Test Pro", layout="wide", page_icon="🧬")

# Custom CSS
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stButton>button {width: 100%; border-radius: 8px; font-weight: bold; height: 3em;}
    .instruction-box {background-color: #e1f5fe; padding: 15px; border-radius: 10px; border-left: 5px solid #0288d1;}
    </style>
""", unsafe_allow_html=True)

# Veritabanı
db = DBManager()

# Session State
if 'student_id' not in st.session_state:
    st.session_state['student_id'] = None
if 'finger_step' not in st.session_state:
    st.session_state['finger_step'] = 0

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3062/3062331.png", width=80)
    st.title("🧬 DMIT Sistemi")
    menu = st.radio("Menü Seçimi", ["Öğrenci Girişi & Analiz", "Yönetici (Koç) Paneli"])
    
    st.markdown("---")
    st.info("**Sistem Durumu:**\n\n🟢 Vision: Grok-2\n\n🟣 Reasoning: Grok-Beta")

# --- ÖĞRENCİ ARAYÜZÜ ---
def student_interface():
    st.title("🧬 Öğrenci Analiz Portalı")
    
    # Giriş Ekranı
    if st.session_state['student_id'] is None:
        st.markdown("### Hoşgeldiniz! Lütfen kayıt olun.")
        with st.form("login_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Ad Soyad", placeholder="Örn: Ahmet Yılmaz")
            age = col2.number_input("Yaş", min_value=3, max_value=90, value=10)
            
            submitted = st.form_submit_button("Analizi Başlat")
            if submitted and name:
                exist_id = db.get_student_id(name)
                if exist_id:
                    st.error("Bu isimle kayıtlı bir analiz zaten var.")
                else:
                    new_id = db.add_student(name, age)
                    st.session_state['student_id'] = new_id
                    st.session_state['student_name'] = name
                    st.session_state['student_age'] = age
                    st.rerun()

    # Parmak İzi Yükleme Sihirbazı
    elif st.session_state['finger_step'] < 10:
        finger_map = [
            ("L1", "Sol Baş Parmak"), ("L2", "Sol İşaret"), ("L3", "Sol Orta"), ("L4", "Sol Yüzük"), ("L5", "Sol Serçe"),
            ("R1", "Sağ Baş Parmak"), ("R2", "Sağ İşaret"), ("R3", "Sağ Orta"), ("R4", "Sağ Yüzük"), ("R5", "Sağ Serçe")
        ]
        
        step = st.session_state['finger_step']
        code, label = finger_map[step]
        
        # Talimatlar
        st.markdown(f"""
        <div class="instruction-box">
            <h4>📸 Fotoğraf Çekim Talimatları</h4>
            <ul>
                <li><strong>Arka Plan:</strong> Beyaz kağıt kullanın.</li>
                <li><strong>Işık:</strong> Gölge düşmeyen, aydınlık bir ortam seçin.</li>
                <li><strong>Odak:</strong> Kamerayı yaklaştırın (Makro Mod) ve ekrana dokunarak odaklayın.</li>
                <li><strong>Açı:</strong> Parmağın tam tepesinden çekin.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric("İlerleme", f"%{(step)*10}")
            st.subheader(f"Şu anki Parmak: {label}")
            st.markdown(f"# `{code}`")
        
        with col2:
            uploaded_file = st.file_uploader(f"{label} Resmini Yükle", type=['jpg', 'png', 'jpeg'], key=f"up_{step}")
            
            if uploaded_file:
                st.image(uploaded_file, width=300, caption=f"{label} Önizleme")
                
                if st.button("✅ Resmi Onayla ve Analiz Et", type="primary"):
                    with st.spinner(f"Grok-Vision (Supreme Expert) parmak izini inceliyor..."):
                        img_bytes = uploaded_file.getvalue()
                        
                        # VISION API ÇAĞRISI
                        result = analyze_fingerprint(img_bytes, f"{label} ({code})")
                        
                        # DB Kayıt
                        db.save_fingerprint_analysis(st.session_state['student_id'], code, result, img_bytes)
                        
                        # Geri Bildirim
                        if result.get('type') == 'Unknown':
                            st.warning("⚠️ Desen tam netleşmedi ama kaydedildi. (Manuel kontrol gerekebilir)")
                        else:
                            st.success(f"Tespit: {result.get('type')} | RC: {result.get('rc')}")
                            st.caption(f"Not: {result.get('note')}")
                        
                        time.sleep(1)
                        st.session_state['finger_step'] += 1
                        st.rerun()
    
    else:
        # Bitiş Ekranı
        st.balloons()
        st.success("Tüm parmak izleri başarıyla alındı ve analiz edildi!")
        st.info("Raporunuz oluşturulmak üzere Koçunuza iletildi. Uygulamayı kapatabilirsiniz.")
        if st.button("Çıkış Yap"):
            st.session_state.clear()
            st.rerun()

# --- YÖNETİCİ ARAYÜZÜ ---
def admin_interface():
    st.title("🛡️ Yönetici & Raporlama Paneli")
    
    password = st.sidebar.text_input("Yönetici Şifresi", type="password")
    if password != "admin123":
        st.warning("Erişim için şifre giriniz.")
        return

    students = db.get_all_students()
    if students.empty:
        st.info("Henüz kayıtlı öğrenci yok.")
        return

    st.dataframe(students)
    
    selected_student = st.selectbox("Raporlanacak Öğrenci Seçin", students['full_name'])
    
    if selected_student:
        s_id = db.get_student_id(selected_student)
        s_info = db.get_student_info(s_id) # (id, name, age, date, status)
        finger_data = db.get_student_data(s_id)
        
        if len(finger_data) < 10:
            st.warning(f"Dikkat: Bu öğrencinin sadece {len(finger_data)} parmak izi var. Rapor eksik çıkabilir.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Kapsamlı NOBEL Raporu Oluştur (AI)", type="primary"):
                engine = DMITEngine(finger_data)
                scores = engine.results
                
                status_box = st.status("Grok-Reasoning Raporu Yazıyor...", expanded=True)
                status_box.write("🧠 Beyin lobu verileri hesaplanıyor...")
                time.sleep(1)
                status_box.write("📝 13 Bölümlük analiz kurgulanıyor...")
                
                # REASONING API ÇAĞRISI
                report_md = generate_nobel_report(selected_student, s_info[2], finger_data, scores)
                
                status_box.update(label="✅ Rapor Hazır!", state="complete", expanded=False)
                
                st.markdown("### 📄 Rapor Önizleme")
                st.markdown(report_md)
                
                st.download_button(
                    label="📥 Raporu İndir (.md)",
                    data=report_md,
                    file_name=f"{selected_student}_Nobel_DMIT.md",
                    mime="text/markdown"
                )

        with col2:
            st.subheader("Hızlı Bakış (Grafikler)")
            if len(finger_data) > 0:
                engine = DMITEngine(finger_data)
                scores = engine.results
                
                # Radar Grafiği: Loblar
                lobes = scores['lobes']
                fig = go.Figure(data=go.Scatterpolar(
                    r=list(lobes.values()),
                    theta=list(lobes.keys()),
                    fill='toself',
                    name='Loblar'
                ))
                fig.update_layout(title="Beyin Lobu Dağılımı")
                st.plotly_chart(fig, use_container_width=True)

# --- ÇALIŞTIRMA ---
if menu == "Öğrenci Girişi & Analiz":
    student_interface()
else:
    admin_interface()