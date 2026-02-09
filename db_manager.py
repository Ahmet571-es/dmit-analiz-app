import sqlite3
import pandas as pd
import os

# Versiyon 2: Yeni şema için isim değişikliği (Eski hataları önler)
DB_NAME = "dmit_system_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabloyu oluştururken yaş ve cinsiyet alanlarını da ekliyoruz
    c.execute('''
        CREATE TABLE IF NOT EXISTS fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            student_age INTEGER,    -- Yeni Alan
            student_gender TEXT,    -- Yeni Alan
            finger_code TEXT,
            image_path TEXT,
            pattern_type TEXT,
            ridge_count INTEGER,
            confidence TEXT,
            dmit_insight TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_fingerprint_record(student_name, student_age, student_gender, finger_code, image_path, pattern_type, ridge_count, confidence, dmit_insight):
    """
    Öğrenci verilerini yaş ve cinsiyet dahil kaydeder.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Eski kaydı temizle (Aynı parmak için güncelleme mantığı)
    c.execute("DELETE FROM fingerprints WHERE student_name = ? AND finger_code = ?", (student_name, finger_code))
    
    # Yeni verileri ekle
    c.execute('''
        INSERT INTO fingerprints (student_name, student_age, student_gender, finger_code, image_path, pattern_type, ridge_count, confidence, dmit_insight)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (student_name, student_age, student_gender, finger_code, image_path, pattern_type, ridge_count, confidence, dmit_insight))
    
    conn.commit()
    conn.close()

def get_all_students():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Hata önlemek için tablo yoksa boş liste dön
    try:
        c.execute("SELECT DISTINCT student_name FROM fingerprints")
        students = [row[0] for row in c.fetchall()]
    except:
        students = []
    conn.close()
    return students

def get_student_data(student_name):
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM fingerprints WHERE student_name = ?", conn, params=(student_name,))
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def calculate_dmit_scores(df):
    if df.empty:
        return {}

    total_rc = df['ridge_count'].sum()
    # Pattern analizleri (Pattern Type içinde geçen harfe göre sayar)
    whorl_count = len(df[df['pattern_type'].str.contains('W', na=False)])
    loop_count = len(df[df['pattern_type'].str.contains('L', na=False)]) # UL, RL, L hepsi dahil
    
    scores = {
        "tfrc": int(total_rc),
        "whorl_count": whorl_count,
        "loop_count": loop_count,
        "learning_potential": "Yüksek" if total_rc > 100 else "Normal",
        "lobes": {
            "prefrontal": 20 + (whorl_count * 2),
            "frontal": 20,
            "parietal": 20,
            "temporal": 20 + (loop_count * 2),
            "occipital": 20
        }
    }
    return scores
