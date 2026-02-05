import sqlite3
import pandas as pd

# Veritabanı dosya adı
DB_NAME = "dmit_system.db"

def init_db():
    """
    Veritabanını ve gerekli tabloları oluşturur.
    Eğer tablo zaten varsa dokunmaz.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
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

def add_fingerprint_record(student_name, finger_code, image_path, pattern_type, ridge_count, confidence, dmit_insight):
    """
    Öğrencinin parmak izi analiz sonucunu kaydeder.
    Aynı parmak daha önce varsa, eskisini silip yenisini yazar (Güncelleme mantığı).
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Önce bu parmakla ilgili eski kayıt varsa temizle (Tekrarlı kayıt olmasın)
    c.execute("DELETE FROM fingerprints WHERE student_name = ? AND finger_code = ?", (student_name, finger_code))
    
    # Yeni kaydı ekle
    c.execute('''
        INSERT INTO fingerprints (student_name, finger_code, image_path, pattern_type, ridge_count, confidence, dmit_insight)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (student_name, finger_code, image_path, pattern_type, ridge_count, confidence, dmit_insight))
    
    conn.commit()
    conn.close()

def get_all_students():
    """
    Sistemdeki kayıtlı tüm öğrencilerin listesini döndürür.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT student_name FROM fingerprints")
    students = [row[0] for row in c.fetchall()]
    conn.close()
    return students

def get_student_data(student_name):
    """
    Belirli bir öğrencinin tüm parmak izi verilerini DataFrame olarak döndürür.
    """
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM fingerprints WHERE student_name = ?", conn, params=(student_name,))
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def calculate_dmit_scores(df):
    """
    Parmak izi verilerine bakarak (Ridge Count vb.) temel DMIT puanlarını hesaplar.
    Bu puanlar Grok'a rapor yazarken yardımcı veri olarak gönderilir.
    """
    if df.empty:
        return {}

    # Toplam Ridge Count (TFRC)
    total_rc = df['ridge_count'].sum()
    
    # Basit bir örnek mantık (Gerçek formüller çok daha karmaşıktır)
    # Burada desen tiplerine göre yetenek eğilimlerini simüle ediyoruz.
    whorl_count = len(df[df['pattern_type'].str.contains('W', na=False)])
    loop_count = len(df[df['pattern_type'].str.contains('L', na=False)])
    
    scores = {
        "tfrc": int(total_rc),
        "whorl_count": whorl_count,
        "loop_count": loop_count,
        "learning_potential": "High" if total_rc > 100 else "Moderate",
        # Beyin Lobu Dağılımı (Örnek Veri)
        "lobes": {
            "prefrontal": 20 + (whorl_count * 2),
            "frontal": 20,
            "parietal": 20,
            "temporal": 20 + (loop_count * 2),
            "occipital": 20
        }
    }
    return scores
