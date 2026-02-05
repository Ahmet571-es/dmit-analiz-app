# -*- coding: utf-8 -*-
"""
Created on Thu Feb  5 22:38:54 2026

@author: YYYNÇİGGGİİÜÜÜÜĞĞĞ
"""

import os
import json
import base64
import streamlit as st  # <--- Streamlit eklendi
from openai import OpenAI
from dotenv import load_dotenv

# --- API ANAHTARI YAPILANDIRMASI (HATA ÇÖZÜMÜ) ---
# Bu blok, Streamlit Cloud'da "Secrets"tan, bilgisayarda ".env"den okur.
try:
    GROK_API_KEY = st.secrets["GROK_API_KEY"]
except (FileNotFoundError, KeyError, AttributeError):
    load_dotenv()
    GROK_API_KEY = os.getenv("GROK_API_KEY")

# Eğer anahtar hala yoksa boş string ata (Crash olmasın, fonksiyon içinde kontrol edilsin)
if not GROK_API_KEY:
    GROK_API_KEY = "key-not-found"

# İstemci Başlatma
client = OpenAI(api_key=GROK_API_KEY, base_url="https://api.x.ai/v1")

# Modeller (Senin belirttiğin gibi)
VISION_MODEL = "grok-4"
# REASONING_MODEL değişkenini API erişiminize göre güncelleyin.
REASONING_MODEL = "grok-4-1-fast-reasoning" 

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# --- 1. VISION ANALİZİ (Supreme Expert Prompt) ---
def analyze_fingerprint(image_bytes, finger_label):
    # API Key kontrolü
    if not GROK_API_KEY or GROK_API_KEY == "key-not-found":
        return {"type": "UL", "rc": 10, "confidence": "Demo", "note": "API Key Eksik (Secrets Ayarlayın)", "dmit_insight": "Demo"}

    base64_image = encode_image(image_bytes)
    
    # KULLANICININ VERDİĞİ ÖZEL PROMPT (DEĞİŞTİRİLMEDİ)
    system_prompt = """
You are a supreme dermatoglyphics expert for Genetic Test DMIT reports, combining Harold Cummins principles with FBI forensic ridge counting. Analyze the single fingerprint image with exhaustive precision, matching the provided Genetic Test report style exactly.

CRITICAL ASSUMPTIONS:
- Single fingertip image, tip upward (distal top).
- Enhance mentally for contrast/smudges; assume standard adult print.
- Use exact codes from report: A (Yay), AT (Çadırlı Yay), UL (Döngü/Ulnar Loop default), RL (Radyal Döngü), W (Spiral/Whorl), S (Çift Döngü/Double Loop).

EXHAUSTIVE STEP-BY-STEP REASONING:
1. Detect deltas (triradii) and core (innermost recurve).
2. Classify precisely:
   - A: Smooth horizontal flow, no delta.
   - AT: Central tent/spike upward.
   - UL: Loop opens little finger side (right hand rightward).
   - RL: Loop opens thumb side (rare).
   - W: Concentric/spiral, 2 deltas.
   - S: Two interlocking loops (S-shape).
   - Unknown if ambiguous.
3. Auto-detect loop direction: Little finger flow = UL; thumb = RL.
4. Ridge Count (RC) exhaustive rules:
   - A/AT: Always 0.
   - Loops (UL/RL): Shortest straight line delta to core; count every crossing/touching ridge (exclude delta/core). Double-count islands/bifurcations.
   - Whorls (W/S): Count both deltas to core(s); use HIGHER value.
   - Conservative on poor quality: Lower estimate.
   - No clear core/delta: RC=0.
5. Confidence: High (crystal clear), Medium (minor blur), Low (smudged/heavy noise).
6. DMIT Insight: Brief note on potential (e.g., high RC whorl = strong analytical/technical).

OUTPUT STRICTLY VALID JSON ONLY:
{
  "type": "W",
  "rc": 22,
  "confidence": "High",
  "note": "Clear whorl with concentric circles, higher delta-core 22 ridges, strong analytical potential for Technical/Engineering areas.",
  "dmit_insight": "High RC suggests elevated analytical and technical aptitude (similar to 82% Technical in reports)."
}

If impossible: {"type": "Unknown", "rc": 0, "confidence": "Low", "note": "Very poor quality - recommend high-resolution re-scan with ink or scanner."}
    """

    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Analyze this fingerprint image: {finger_label}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                },
            ],
            temperature=0.0,
            max_tokens=300,
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        return {"type": "Error", "rc": 0, "confidence": "Low", "note": str(e)}

# --- 2. NOBEL REPORT (Reasoning Prompt) ---
def generate_nobel_report(student_name, age, finger_data, scores):
    # API Key kontrolü
    if not GROK_API_KEY or GROK_API_KEY == "key-not-found":
        return "HATA: API Anahtarı eksik. Lütfen Streamlit Secrets ayarlarını yapın."
    
    # Veri Hazırlığı
    patterns_summary = ""
    for _, row in finger_data.iterrows():
        patterns_summary += f"- {row['finger_code']}: {row['pattern_type']} (RC: {row['ridge_count']}) - Insight: {row['dmit_insight']}\n"

    scores_summary = json.dumps(scores, indent=2, ensure_ascii=False)

    # KULLANICININ VERDİĞİ DEV PROMPT (DEĞİŞTİRİLMEDİ)
    prompt = f"""
You are a world-class DMIT (Dermatoglyphics Multiple Intelligence Test) expert producing professional Genetic Test reports (Nobel Koçluk style). Generate an EXTREMELY COMPREHENSIVE, motivational, and personalized report in Turkish ONLY.

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

    try:
        response = client.chat.completions.create(
            model=REASONING_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert Genetic Test Analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=6000 # Uzun rapor için limit yüksek
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Rapor oluşturulurken hata: {str(e)}"
