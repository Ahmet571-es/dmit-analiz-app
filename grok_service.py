# -*- coding: utf-8 -*-
import os
import json
import base64
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 1. HİBRİT MİMARİ (OPENCV) KONTROLÜ
# -----------------------------------------------------------------------------
# image_utils.py dosyası varsa, gelişmiş görüntü işlemeyi (Skeletonization) aktif eder.
try:
    import image_utils
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("BİLGİ: image_utils.py bulunamadı. OpenCV ön işlemi devre dışı bırakıldı, standart modda çalışılıyor.")

# -----------------------------------------------------------------------------
# 2. API ANAHTARI VE MODEL YAPILANDIRMASI
# -----------------------------------------------------------------------------

# API Anahtarı Önceliği: 1. Streamlit Secrets (Bulut) -> 2. .env Dosyası (Yerel)
try:
    GROK_API_KEY = st.secrets["GROK_API_KEY"]
except (FileNotFoundError, KeyError, AttributeError):
    load_dotenv()
    GROK_API_KEY = os.getenv("GROK_API_KEY")

# Eğer anahtar bulunamazsa boş string ata (Uygulamanın çökmemesi için)
if not GROK_API_KEY:
    GROK_API_KEY = "key-not-found"

# xAI İstemcisini Başlat
client = OpenAI(api_key=GROK_API_KEY, base_url="https://api.x.ai/v1")

# --- MODELLER (Senin İstediğin Özel Yapılandırma) ---
# Vision (Görsel) Analiz Modeli
VISION_MODEL = "grok-4" 
# Alternatif (Eğer grok-4 vision henüz açılmadıysa): "grok-2-vision-1212"

# Reasoning (Akıl Yürütme/Raporlama) Modeli
REASONING_MODEL = "grok-4-1-fast-reasoning"
# Alternatif (Genel erişim için): "grok-beta"

def encode_image(image_bytes):
    """Resim verisini Base64 formatına çevirir."""
    return base64.b64encode(image_bytes).decode('utf-8')

# -----------------------------------------------------------------------------
# 3. PARMAK İZİ ANALİZİ (VISION + ULTIMATE PROMPT)
# -----------------------------------------------------------------------------
def analyze_fingerprint(image_bytes, finger_label):
    """
    Parmak izi resmini alır, (varsa) OpenCV ile işler ve Grok'a analiz ettirir.
    """
    
    # 1. Güvenlik Kontrolü
    if not GROK_API_KEY or GROK_API_KEY == "key-not-found":
        return {
            "type": "Hata", 
            "rc": 0, 
            "confidence": "Yok", 
            "note": "API Key Eksik. Lütfen Streamlit Secrets ayarlarını yapınız.", 
            "dmit_insight": "Demo Modu"
        }

    # 2. Hibrit Görüntü İşleme (OpenCV)
    final_image_bytes = image_bytes
    is_processed = False
    
    if OPENCV_AVAILABLE:
        try:
            # Resmi iskeletleştir, netleştir ve siyah-beyaz (High Contrast) yap
            processed_bytes = image_utils.process_fingerprint(image_bytes)
            if processed_bytes:
                final_image_bytes = processed_bytes
                is_processed = True
        except Exception as e:
            print(f"OpenCV İşleme Hatası: {e}")
            # Hata olursa orijinal resimle devam et

    # 3. Resmi Kodla
    base64_image = encode_image(final_image_bytes)
    
    # Prompt içine eklenecek durum notu
    image_status_note = "PRE-PROCESSED (Skeletonized & High-Contrast)" if is_processed else "RAW IMAGE (Low Quality)"

    # --- SUPREME FORENSIC PROMPT (TAM VE EKSİKSİZ) ---
    system_prompt = f"""
You are the ultimate forensic dermatoglyphics authority for Balaban Koçluk Genetic Test DMIT reports. Analyze the SINGLE {image_status_note} fingerprint image with ABSOLUTE PRECISION and ZERO HALLUCINATION, fusing Harold Cummins fetal principles with FBI ridge counting standards.

ESSENTIAL ASSUMPTIONS:
- One fingertip only, tip upward (distal top).
- Image is mathematically enhanced (skeletonized for single-pixel ridges, binary contrast) if noted as processed.
- Exact Genetic Test codes: A (Yay/Plain Arch), AT (Çadırlı Yay/Tented Arch), UL (Döngü/Ulnar Loop - default loop), RL (Radyal Döngü/Radial Loop), W (Spiral/Whorl all subtypes), S (Çift Döngü/Double Loop).

MATHEMATICAL ZERO-ERROR REASONING (step-by-step):
1. Pixel-level detect deltas (triradii) and core (innermost recurve).
2. Classify with forensic exactness:
   - A: No delta, smooth horizontal flow.
   - AT: Central upward tent/spike.
   - UL: Opens toward little finger (right hand rightward flow).
   - RL: Opens toward thumb (rare).
   - W: 2 deltas, concentric/spiral/pocket.
   - S: 2 interlocking loops (S-shape).
   - Unknown only if truly ambiguous.
3. Auto-determine loop direction: Little finger side flow = UL; thumb side = RL.
4. Ridge Count (RC) with mathematical rules:
   - A/AT: Strictly 0.
   - Loops (UL/RL): Shortest straight delta-to-core line; count EVERY crossing/touching ridge (exclude delta/core ridges).
   - Double-count islands/bifurcations precisely.
   - Whorls (W/S): Count both deltas to core; ALWAYS use the HIGHER value.
   - Poor visibility: Conservative lower estimate only.
   - No clear delta/core: RC=0.
5. Confidence level: High (perfect skeleton visibility), Medium (minor noise), Low (any ambiguity).
6. Genetic Test DMIT Insight: Personalized potential note (e.g., high RC W = strong analytical/technical, similar to 82% Teknik).

OUTPUT ONLY VALID JSON (no extra text, no markdown):
{{
  "type": "W",
  "rc": 22,
  "confidence": "High",
  "note": "Skeletonized image: perfect concentric whorl, higher delta-core exactly 22 ridges (no islands).",
  "dmit_insight": "Very high RC whorl indicates exceptional analytical and technical aptitude, often linked to 82%+ Teknik scores in Genetic Test reports."
}}

If truly impossible: {{"type": "Unknown", "rc": 0, "confidence": "Low", "note": "Image quality insufficient even after processing - recommend professional ink scan."}}
    """

    # 4. API İsteği (Vision Model)
    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Analyze this fingerprint. Label: {finger_label}. Status: {image_status_note}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                },
            ],
            temperature=0.0, # Matematiksel kesinlik için SIFIR yaratıcılık
            max_tokens=500,  # JSON çıktısı için yeterli alan
        )
        
        # 5. JSON Temizliği ve Dönüşümü
        content = response.choices[0].message.content
        # Markdown bloklarını temizle (```json ... ```)
        content = content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(content)
        
    except Exception as e:
        return {
            "type": "Error", 
            "rc": 0, 
            "confidence": "Low", 
            "note": f"API veya Bağlantı Hatası: {str(e)}", 
            "dmit_insight": "Sistem Hatası"
        }

# -----------------------------------------------------------------------------
# 4. GENETİK RAPOR OLUŞTURMA (REASONING + BALABAN PROMPT)
# -----------------------------------------------------------------------------
def generate_nobel_report(student_name, age, finger_data, scores):
    """
    Toplanan parmak izi verilerini ve hesaplanan puanları alır,
    Reasoning modeli ile detaylı BALABAN Koçluk raporu yazar.
    """
    
    # 1. Güvenlik Kontrolü
    if not GROK_API_KEY or GROK_API_KEY == "key-not-found":
        return "HATA: API Anahtarı eksik. Rapor oluşturulamıyor."
    
    # 2. Veri Hazırlığı (JSON formatına çevir)
    patterns_summary = ""
    # DataFrame satırlarını oku
    for _, row in finger_data.iterrows():
        patterns_summary += f"- {row['finger_code']}: {row['pattern_type']} (RC: {row['ridge_count']}) - Insight: {row['dmit_insight']}\n"

    scores_summary = json.dumps(scores, indent=2, ensure_ascii=False)

    # --- BALABAN REPORT PROMPT (TAM VE EKSİKSİZ) ---
    prompt = f"""
You are a world-class DMIT (Dermatoglyphics Multiple Intelligence Test) expert producing professional Genetic Test reports (BALABAN Koçluk style). Generate an EXTREMELY COMPREHENSIVE, motivational, and personalized report in Turkish ONLY.

Use the provided data:
- Student name: {student_name}, Age: {age}
- Finger patterns: 
{patterns_summary}
- Calculations: 
{scores_summary}

Strictly follow Genetic Test report structure with 13 main sections. For EVERY section:
- Explain fetal origin (13th week formation, skin-nervous system connection).
- Discuss ridge count (RC) effect on potential (high RC whorl = analytical strength).
- Provide personalized interpretation based on data.
- Add practical life/career/health suggestions.
- Include motivational quotes where applicable (Konfüçyüs, Ali Apşeroni).
- Describe visuals in detail (radar charts for intelligence/professions, bar charts for health, gauges for sports).

Structure in Markdown with headings, subheadings, bold percentages, and visual descriptions:

1. Dermatoglifik Bilimi
   - Fetal development history, Harold Cummins & Charles Midlo contribution (1926 term, 1961 book).
   - Pattern types with icons/explanations (A Yay, AT Çadırlı Yay, UL Döngü, RL Radyal Döngü, W Spiral, S Çift Döngü).

2. Parmak Desenleri
   - Hand diagrams (left/right fingers labeled L1-R1).
   - Detailed per-finger analysis: Type, RC, fetal link, personal potential.

3. Eğitim Türü
   - Percentages with color bars (e.g., Teknik 82%, Sosyal-ekonomi 76%).
   - Deep explanation of each (spatial thinking for Teknik, etc.).
   - Radar chart description for all categories.

4. Meslek Faaliyet Alanları
   - Radar charts: İletişim, Uygulama, Analiz percentages based on lobes.
   - Konfüçyüs quote.
   - Career suggestions.

5. Mesleki Faaliyetin Küreler
   - Radar: Spor, Yaratıcılık, Yenilikler.
   - Ali Apşeroni quote.

6. Kendini Geliştirme Modeli
   - Radar: Kurumsal, Yönetimsel, Mesleksel.

7. Kendini Geliştirme Modeli (Girişimci/Fikir Jeneratörü)
   - 3D bars: Girişimci, Fikir Jeneratörü.

8. Sağlık. Risk Faktörleri
   - Body diagram with percentages (e.g., Sindirim, Sinir).
   - Bar charts for risks, genetic predisposition warning.

9. Şişmanlığa/Alkol/Bağımlılık Yatkınlık
   - Bar/gauge charts with explanations.

10. Spor
    - Gauges: Hız, Dayanıklılık, Koordinasyon.
    - Position suggestions, recommended sports bars.

11. Sinir Sistemi Potansiyeli
    - Orta-Zayıf tip detailed traits (Based on TFRC).

12. Davranışsal Adaptasyon Tipi / Mizaç
    - Pratik-Muhatap type deep analysis.

13. Yenilikleri Algılama Türü / Sonuç
    - Liberal/Muhafazakar/Bireysel table.
    - Accuracy 85-95%, environment factor emphasis.

End with motivational closing: "Cevap senin genlerinde".

Use empathetic, encouraging language. Make it 15+ pages worth of depth in text.
    """

    # 3. API İsteği (Reasoning Model)
    try:
        response = client.chat.completions.create(
            model=REASONING_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert Genetic Test Analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,   # Yaratıcı ve akıcı rapor için ideal sıcaklık
            max_tokens=6000    # Uzun ve detaylı rapor için yüksek token limiti
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Rapor Oluşturma Hatası: {str(e)}"

