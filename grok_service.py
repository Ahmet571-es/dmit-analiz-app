# -*- coding: utf-8 -*-
import os
import json
import base64
import streamlit as st
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 1. HİBRİT MİMARİ KONTROLÜ
# -----------------------------------------------------------------------------
try:
    import image_utils
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("BİLGİ: image_utils.py bulunamadı. Standart mod devrede.")

# -----------------------------------------------------------------------------
# 2. API VE MODEL AYARLARI
# -----------------------------------------------------------------------------
try:
    GROK_API_KEY = st.secrets["GROK_API_KEY"]
except (FileNotFoundError, KeyError, AttributeError):
    load_dotenv()
    GROK_API_KEY = os.getenv("GROK_API_KEY")

if not GROK_API_KEY:
    GROK_API_KEY = "key-not-found"

client = OpenAI(api_key=GROK_API_KEY, base_url="https://api.x.ai/v1")

# Modeller
VISION_MODEL = "grok-4" 
REASONING_MODEL = "grok-4-1-fast-reasoning"

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# -----------------------------------------------------------------------------
# 3. MATEMATİKSEL HESAPLAMA MOTORU (Python Tarafı - Sıfır Hata)
# -----------------------------------------------------------------------------
def calculate_advanced_stats(finger_data):
    if finger_data.empty: return {}
    
    # TFRC
    tfrc = finger_data['ridge_count'].sum()
    if tfrc == 0: tfrc = 1

    rc = {row['finger_code']: row['ridge_count'] for _, row in finger_data.iterrows()}
    for code in ["L1","L2","L3","L4","L5","R1","R2","R3","R4","R5"]:
        if code not in rc: rc[code] = 0

    # Lobes
    lobes = {
        "Sol_Prefrontal": rc.get('R1',0), "Sol_Frontal": rc.get('R2',0), "Sol_Parietal": rc.get('R3',0), "Sol_Temporal": rc.get('R4',0), "Sol_Occipital": rc.get('R5',0),
        "Sag_Prefrontal": rc.get('L1',0), "Sag_Frontal": rc.get('L2',0), "Sag_Parietal": rc.get('L3',0), "Sag_Temporal": rc.get('L4',0), "Sag_Occipital": rc.get('L5',0)
    }
    lobe_percentages = {k: (v / tfrc * 100) for k, v in lobes.items()}

    # Groups
    teknik = (rc['L1'] + rc['R1'] + rc['L3'] + rc['R3']) 
    sosyal = (rc['L4'] + rc['R4'] + rc['L2'] + rc['R2'])
    matematik = (rc['L2'] + rc['R2'] + rc['L3'] + rc['R3'])
    fen = (rc['L5'] + rc['R5'] + rc['L3'] + rc['R3'])
    genel = tfrc / 5 

    # Dominance
    sag_beyin = sum([rc[f] for f in ['L1','L2','L3','L4','L5']])
    sol_beyin = sum([rc[f] for f in ['R1','R2','R3','R4','R5']])
    dominance = "Sağ Beyin Baskın" if sag_beyin > sol_beyin else "Sol Beyin Baskın"
    
    return {
        "tfrc": int(tfrc),
        "lobes": lobe_percentages,
        "groups": {"Teknik": (teknik/tfrc*100), "Sosyal": (sosyal/tfrc*100), "Matematik": (matematik/tfrc*100), "Fen": (fen/tfrc*100), "Genel": (genel/tfrc*100)},
        "dominance": dominance,
        "sag_beyin_total": sag_beyin,
        "sol_beyin_total": sol_beyin
    }

# -----------------------------------------------------------------------------
# 4. GÖRÜNTÜ ANALİZİ (VISION) - 80-SHOT PROMPT (FULL)
# -----------------------------------------------------------------------------
def analyze_fingerprint(image_bytes, finger_label):
    if not GROK_API_KEY or GROK_API_KEY == "key-not-found":
        return {"type": "Hata", "rc": 0, "confidence": "Yok", "note": "API Key Eksik", "dmit_insight": "Demo"}

    final_image_bytes = image_bytes
    is_processed = False
    
    if OPENCV_AVAILABLE:
        try:
            processed_bytes = image_utils.process_fingerprint(image_bytes)
            if processed_bytes:
                final_image_bytes = processed_bytes
                is_processed = True
        except Exception as e:
            print(f"OpenCV Hata: {e}")

    base64_image = encode_image(final_image_bytes)
    image_status_note = "PRE-PROCESSED (Skeletonized & High-Contrast)" if is_processed else "RAW IMAGE"

    # NOT: f-string içinde JSON kullanırken süslü parantezleri {{ }} şeklinde çiftlemeliyiz.
    system_prompt = f"""
You are the ultimate forensic dermatoglyphics authority for Nobel Koçluk Genetic Test DMIT reports. Analyze the SINGLE {image_status_note} fingerprint image with ABSOLUTE PRECISION and ZERO HALLUCINATION, fusing Harold Cummins fetal principles with FBI ridge counting standards.

ESSENTIAL ASSUMPTIONS:
- One fingertip only, tip upward (distal top).
- Image is mathematically enhanced (skeletonized for single-pixel ridges, binary contrast).
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

LEARN FROM THESE 80 DETAILED FEW-SHOT EXAMPLES (mimic exactly for precision - each based on real PDF variations):

Few-Shot 1: High RC Whorl Perfect Concentric (from Ahmet Arif Yılmaz high whorl example)
{{ "type": "W", "rc": 28, "confidence": "High", "note": "Perfect concentric whorl in skeletonized image, higher delta-core exactly 28 ridges, no islands visible.", "dmit_insight": "Very high RC whorl indicates exceptional analytical and technical aptitude, often linked to 82%+ Teknik scores in Genetic Test reports (fetal prefrontal ridge density strong)." }}

Few-Shot 2: Medium RC Ulnar Loop Clear Opening (from ahmet aziz doğan loop example)
{{ "type": "UL", "rc": 15, "confidence": "High", "note": "Clear ulnar loop opening rightward in perfect skeleton, 15 ridges crossed precisely with no islands.", "dmit_insight": "Medium RC loop suggests solid practical and interpersonal skills, similar to 35% Uygulama or higher İletişim contributions (fetal parietal balance moderate)." }}

Few-Shot 3: Low RC Plain Arch Smooth No Delta (from Berrin Gülhan arch example)
{{ "type": "A", "rc": 0, "confidence": "High", "note": "Smooth plain arch with absolutely no delta in skeletonized image.", "dmit_insight": "Low RC arch may indicate balanced but lower intensity in certain lobes, potentially increasing health risk factors in reports (fetal general low ridge formation)." }}

Few-Shot 4: Tented Arch Low RC Central Spike (from alper okten tented example)
{{ "type": "AT", "rc": 4, "confidence": "High", "note": "Central upward tent spike clearly visible in skeleton, low ridge count exactly 4.", "dmit_insight": "Tented arch transition form with moderate potential, often seen in balanced transitional lobes (fetal ridge spike formation)." }}

Few-Shot 5: Radial Loop Rare Medium RC Thumb Opening (from ahmet talha darbaş rare RL example)
{{ "type": "RL", "rc": 12, "confidence": "High", "note": "Rare radial loop opening toward thumb side, 12 ridges counted in skeleton.", "dmit_insight": "Rare radial loop suggests innovative and unconventional thinking potential (fetal prefrontal variant ridge flow)." }}

Few-Shot 6: Double Loop High Interlocking S-Shape (from betül gülebakan creativity high example)
{{ "type": "S", "rc": 26, "confidence": "High", "note": "Clear interlocking S-shape double loop in skeleton, higher delta exactly 26 ridges.", "dmit_insight": "High RC double loop indicates strong creativity and complex thinking, similar to 65% Yaratıcılık scores (fetal occipital/temporal interlocking strong)." }}

Few-Shot 7: Whorl with Double Islands Double-Count (from Akın Sevinç complex whorl example)
{{ "type": "W", "rc": 24, "confidence": "High", "note": "Concentric whorl with 2 islands precisely double-counted in skeleton, total 24 ridges.", "dmit_insight": "Islands add complexity, enhanced analytical depth and multi-tasking potential (fetal prefrontal enhanced bifurcation)." }}

Few-Shot 8: Blurry Low Confidence Heavy Noise Unknown (general low quality example)
{{ "type": "Unknown", "rc": 0, "confidence": "Low", "note": "Heavy residual noise even after skeletonization, core/delta ambiguous - professional re-scan recommended.", "dmit_insight": "Insufficient quality for reliable DMIT insight - ink scan advised for fetal ridge accuracy." }}

Few-Shot 9: Pocket Whorl Variant High Pocket (from Ahmet genç pocket variant example)
{{ "type": "W", "rc": 30, "confidence": "High", "note": "Central pocket loop whorl variant clearly visible, higher delta exactly 30 ridges in skeleton.", "dmit_insight": "Exceptional RC pocket whorl for engineering/technical excellence, linked to 82%+ Teknik (fetal parietal/prefrontal peak pocket)." }}

Few-Shot 10: Medium Confidence Ulnar Loop Minor Noise (from Abdullah Türkyılmaz loop noise example)
{{ "type": "UL", "rc": 18, "confidence": "Medium", "note": "Minor residual noise but clear ulnar loop in skeleton, conservative 18 ridges counted.", "dmit_insight": "Solid medium RC loop for practical and social balance (fetal temporal moderate with minor variation)." }}

Few-Shot 11: Low RC Tented Arch Spike Low (from Ahsen Yazıcıoğlu tented low example)
{{ "type": "AT", "rc": 5, "confidence": "High", "note": "Central spike visible in skeleton, low 5 ridges precisely.", "dmit_insight": "Low RC tented arch moderate transition potential (fetal ridge spike low density)." }}

Few-Shot 12: High RC Double Loop with Islands (from Ahmet Yavuz Gece complex S example)
{{ "type": "S", "rc": 29, "confidence": "High", "note": "Interlocking S with 3 islands double-counted in skeleton, higher 29 ridges.", "dmit_insight": "Very high RC with islands strong creative complexity (%65+ Yaratıcılık fetal occipital enhanced)." }}

Few-Shot 13: Medium RC Radial Rare Thumb (from arif açıkgöz rare RL example)
{{ "type": "RL", "rc": 14, "confidence": "High", "note": "Radial opening clear in skeleton, 14 ridges.", "dmit_insight": "Medium RC rare radial innovative edge (fetal prefrontal thumb flow variant)." }}

Few-Shot 14: Whorl Medium Confidence Minor Noise (from ahmet selim çoban whorl blur example)
{{ "type": "W", "rc": 20, "confidence": "Medium", "note": "Minor noise but concentric visible in skeleton, conservative 20 ridges.", "dmit_insight": "Medium RC whorl analytical moderate (fetal prefrontal with minor variation)." }}

Few-Shot 15: Plain Arch Perfect Zero (from Alperen Adıgüzel arch example)
{{ "type": "A", "rc": 0, "confidence": "High", "note": "Perfect smooth arch no delta in skeleton.", "dmit_insight": "Zero RC balanced low intensity (fetal general low ridge)." }}

Few-Shot 16: Ulnar High with Double Islands (from akif eker loop islands example)
{{ "type": "UL", "rc": 22, "confidence": "High", "note": "Ulnar with 2 islands double-counted in skeleton, 22 ridges.", "dmit_insight": "High RC loop with islands strong practical complexity (fetal parietal islands enhanced)." }}

Few-Shot 17: Spiral Variant Medium Pocket (from Alperen Özdemir spiral example)
{{ "type": "W", "rc": 21, "confidence": "High", "note": "Spiral variant higher delta 21 ridges in skeleton.", "dmit_insight": "Medium-high RC spiral technical balance (fetal parietal spiral moderate)." }}

Few-Shot 18: Unknown Blurry Residual (from Ali Emirhan Ercan low quality example)
{{ "type": "Unknown", "rc": 0, "confidence": "Low", "note": "Residual blur insufficient skeleton, re-scan.", "dmit_insight": "Quality low - no reliable insight." }}

Few-Shot 19: Double Loop Medium Interlocking (from Asude Verda Özdemir S medium example)
{{ "type": "S", "rc": 20, "confidence": "High", "note": "Interlocking medium 20 ridges in skeleton.", "dmit_insight": "Medium RC double loop creativity moderate (fetal occipital interlocking)." }}

Few-Shot 20: Whorl Clean High No Islands (from ahmet yusuf karadogan clean whorl example)
{{ "type": "W", "rc": 25, "confidence": "High", "note": "Clean concentric no islands in skeleton, 25 ridges.", "dmit_insight": "High RC clean whorl pure analytical strength (fetal prefrontal clean high)." }}

Few-Shot 21: Low RC Arch with Minor Spike (from alper okten low arch example)
{{ "type": "A", "rc": 0, "confidence": "High", "note": "Smooth arch with minor variation, no delta.", "dmit_insight": "Low RC balanced low (fetal general minimal)." }}

Few-Shot 22: High RC Ulnar Perfect (from betül genç high loop example)
{{ "type": "UL", "rc": 23, "confidence": "High", "note": "Perfect ulnar high 23 ridges.", "dmit_insight": "High RC ulnar strong practical/social (%76+ Sosyal similar)." }}

Few-Shot 23: Tented Medium Spike (from belkıs müjde tented medium example)
{{ "type": "AT", "rc": 6, "confidence": "High", "note": "Medium tent spike 6 ridges.", "dmit_insight": "Medium RC tented moderate transition." }}

Few-Shot 24: Whorl Low with Noise Conservative (from ASIM KARABIYIK whorl low example)
{{ "type": "W", "rc": 18, "confidence": "Medium", "note": "Noise conservative lower 18 ridges.", "dmit_insight": "Medium RC whorl analytical moderate conservative." }}

Few-Shot 25: Radial Medium Rare (from Ceylin Erol rare RL example)
{{ "type": "RL", "rc": 15, "confidence": "High", "note": "Medium rare radial 15 ridges.", "dmit_insight": "Medium RC rare radial innovation moderate." }}

Few-Shot 26: Double Loop Low Interlocking (from azra arslanoğlu S low example)
{{ "type": "S", "rc": 18, "confidence": "High", "note": "Low interlocking 18 ridges.", "dmit_insight": "Low RC double loop creativity low-moderate." }}

Few-Shot 27: Arch High Confidence Zero (from betül mıngır arch high example)
{{ "type": "A", "rc": 0, "confidence": "High", "note": "High confidence smooth arch zero.", "dmit_insight": "Zero RC balanced low intensity high confidence." }}

Few-Shot 28: Ulnar with Single Island (from aydan açıkgöz loop island example)
{{ "type": "UL", "rc": 19, "confidence": "High", "note": "Ulnar with single island double-count 19 ridges.", "dmit_insight": "RC with island practical enhanced." }}

Few-Shot 29: Spiral High Pocket (from büşranur turkyılmaz spiral high example)
{{ "type": "W", "rc": 27, "confidence": "High", "note": "High pocket spiral 27 ridges.", "dmit_insight": "High RC pocket technical peak." }}

Few-Shot 30: Unknown Medium Noise (from cem cicek medium unknown example)
{{ "type": "Unknown", "rc": 0, "confidence": "Medium", "note": "Medium noise ambiguous - re-scan.", "dmit_insight": "Medium quality limited insight." }}

Few-Shot 31: Low RC Tented Spike Variant (from Bekir Bahadır tented low example)
{{ "type": "AT", "rc": 3, "confidence": "High", "note": "Low spike variant 3 ridges.", "dmit_insight": "Low RC tented low transition." }}

Few-Shot 32: High RC Radial Rare (from bahar şişman rare RL high example)
{{ "type": "RL", "rc": 16, "confidence": "High", "note": "High rare radial 16 ridges.", "dmit_insight": "High RC rare radial strong innovation." }}

Few-Shot 33: Whorl Medium Islands (from banu gençer whorl medium example)
{{ "type": "W", "rc": 22, "confidence": "High", "note": "Medium whorl with islands 22 ridges.", "dmit_insight": "Medium RC islands analytical enhanced." }}

Few-Shot 34: Loop Low Confidence Noise (from ALPER AYDIN loop low example)
{{ "type": "UL", "rc": 12, "confidence": "Low", "note": "Low confidence noise conservative 12 ridges.", "dmit_insight": "Low quality practical limited." }}

Few-Shot 35: Double Loop Perfect High (from Ayşe Sude Türkyılmaz S high example)
{{ "type": "S", "rc": 30, "confidence": "High", "note": "Perfect interlocking high 30 ridges.", "dmit_insight": "Exceptional RC double creativity peak." }}

Few-Shot 36: Arch Medium Smooth (from arda yağız akkuş arch medium example)
{{ "type": "A", "rc": 0, "confidence": "Medium", "note": "Medium smooth arch no delta.", "dmit_insight": "Balanced low with medium visibility." }}

Few-Shot 37: Whorl Variant Low Pocket (from ceylin otuzoğlu pocket low example)
{{ "type": "W", "rc": 19, "confidence": "High", "note": "Low pocket variant 19 ridges.", "dmit_insight": "Low RC pocket technical moderate." }}

Few-Shot 38: Ulnar with Triple Islands (from bartuğ ogulcan loop islands example)
{{ "type": "UL", "rc": 25, "confidence": "High", "note": "Ulnar with triple islands double-count 25 ridges.", "dmit_insight": "High RC islands practical complex strong." }}

Few-Shot 39: Radial Low Rare (from cemal ulvi berber rare RL low example)
{{ "type": "RL", "rc": 10, "confidence": "High", "note": "Low rare radial 10 ridges.", "dmit_insight": "Low RC rare radial innovation low." }}

Few-Shot 40: Spiral Perfect High (from Burak Özdemir spiral high example)
{{ "type": "W", "rc": 29, "confidence": "High", "note": "Perfect spiral high 29 ridges.", "dmit_insight": "High RC spiral analytical peak." }}

Few-Shot 41: Tented High Spike (from Betül Serra Özcan tented high example)
{{ "type": "AT", "rc": 7, "confidence": "High", "note": "High tent spike 7 ridges.", "dmit_insight": "High RC tented strong transition." }}

Few-Shot 42: Double Loop Medium Islands (from cemre gece S medium example)
{{ "type": "S", "rc": 22, "confidence": "High", "note": "Medium interlocking with islands 22 ridges.", "dmit_insight": "Medium RC islands creativity enhanced." }}

Few-Shot 43: Whorl Low Confidence Noise Conservative (from bhr snc whorl low example)
{{ "type": "W", "rc": 17, "confidence": "Low", "note": "Low confidence noise conservative 17 ridges.", "dmit_insight": "Low quality analytical limited conservative." }}

Few-Shot 44: Ulnar Perfect Medium (from Ayşegül biçer loop medium example)
{{ "type": "UL", "rc": 16, "confidence": "High", "note": "Perfect ulnar medium 16 ridges.", "dmit_insight": "Medium RC ulnar practical balanced." }}

Few-Shot 45: Arch Low with Variation (from büşranur turkyılmaz arch low example)
{{ "type": "A", "rc": 0, "confidence": "High", "note": "Low variation smooth arch zero.", "dmit_insight": "Low RC variation balanced risk." }}

Few-Shot 46: Radial High Rare (from cem cicek rare RL high example)
{{ "type": "RL", "rc": 18, "confidence": "High", "note": "High rare radial 18 ridges.", "dmit_insight": "High RC rare radial innovation strong." }}

Few-Shot 47: Spiral Medium Pocket Noise (from Bekir Bahadır spiral medium example)
{{ "type": "W", "rc": 23, "confidence": "Medium", "note": "Medium pocket with minor noise 23 ridges.", "dmit_insight": "Medium RC pocket technical moderate." }}

Few-Shot 48: Double Loop Low Confidence (from bahar şişman S low example)
{{ "type": "S", "rc": 19, "confidence": "Low", "note": "Low confidence interlocking conservative 19 ridges.", "dmit_insight": "Low quality creativity limited." }}

Few-Shot 49: Whorl High with Triple Islands (from banu gençer whorl high example)
{{ "type": "W", "rc": 31, "confidence": "High", "note": "High whorl with triple islands double-count 31 ridges.", "dmit_insight": "Exceptional RC islands analytical complex peak." }}

Few-Shot 50: Loop High Perfect No Islands (from ALPER AYDIN loop high example)
{{ "type": "UL", "rc": 24, "confidence": "High", "note": "High perfect ulnar no islands 24 ridges.", "dmit_insight": "High RC clean loop practical strong." }}

Few-Shot 51: Tented Low Confidence Spike Blur (from Ayşe Sude Türkyılmaz tented low example)
{{ "type": "AT", "rc": 3, "confidence": "Low", "note": "Low confidence spike blur conservative 3 ridges.", "dmit_insight": "Low quality tented limited transition." }}

Few-Shot 52: Radial Medium Noise (from arda yağız akkuş rare RL medium example)
{{ "type": "RL", "rc": 13, "confidence": "Medium", "note": "Medium rare radial with noise conservative 13 ridges.", "dmit_insight": "Medium RC rare radial innovation moderate conservative." }}

Few-Shot 53: Double Loop High Perfect (from ceylin otuzoğlu S high example)
{{ "type": "S", "rc": 32, "confidence": "High", "note": "High perfect interlocking 32 ridges.", "dmit_insight": "Exceptional RC double creativity peak (fetal occipital high)." }}

Few-Shot 54: Whorl Medium Pocket Low (from bartuğ ogulcan pocket low example)
{{ "type": "W", "rc": 19, "confidence": "High", "note": "Medium pocket low 19 ridges.", "dmit_insight": "Medium RC pocket technical moderate low." }}

Few-Shot 55: Arch High with Minor Variation (from cemal ulvi berber arch high example)
{{ "type": "A", "rc": 0, "confidence": "High", "note": "High confidence arch with minor variation zero.", "dmit_insight": "Zero RC balanced high confidence." }}

Few-Shot 56: Ulnar Low with Island (from Burak Özdemir loop low example)
{{ "type": "UL", "rc": 11, "confidence": "High", "note": "Low ulnar with single island double-count 11 ridges.", "dmit_insight": "Low RC island practical low enhanced." }}

Few-Shot 57: Spiral High Variant (from Betül Serra Özcan spiral high example)
{{ "type": "W", "rc": 29, "confidence": "High", "note": "High spiral variant 29 ridges.", "dmit_insight": "High RC spiral analytical peak variant." }}

Few-Shot 58: Unknown High Noise Re-Scan (from cemre gece unknown high example)
{{ "type": "Unknown", "rc": 0, "confidence": "Low", "note": "High noise insufficient skeleton re-scan.", "dmit_insight": "High quality issue no insight." }}

Few-Shot 59: Double Loop Medium Noise Conservative (from bhr snc S medium example)
{{ "type": "S", "rc": 21, "confidence": "Medium", "note": "Medium interlocking noise conservative 21 ridges.", "dmit_insight": "Medium RC creativity moderate conservative." }}

Few-Shot 60: Whorl Perfect Low Islands (from Ayşegül biçer whorl perfect example)
{{ "type": "W", "rc": 26, "confidence": "High", "note": "Perfect whorl low islands 26 ridges.", "dmit_insight": "High RC low islands analytical strong." }}

Few-Shot 61: Tented Medium High Spike (from büşranur turkyılmaz tented medium example)
{{ "type": "AT", "rc": 8, "confidence": "High", "note": "Medium high tent spike 8 ridges.", "dmit_insight": "Medium RC tented strong transition." }}

Few-Shot 62: Radial High Perfect (from cem cicek rare RL high example)
{{ "type": "RL", "rc": 17, "confidence": "High", "note": "High perfect rare radial 17 ridges.", "dmit_insight": "High RC rare radial innovation peak." }}

Few-Shot 63: Double Loop Low Islands (from Bekir Bahadır S low example)
{{ "type": "S", "rc": 17, "confidence": "High", "note": "Low interlocking with islands 17 ridges.", "dmit_insight": "Low RC islands creativity low enhanced." }}

Few-Shot 64: Whorl High Noise Conservative (from bahar şişman whorl high example)
{{ "type": "W", "rc": 23, "confidence": "Medium", "note": "High whorl noise conservative 23 ridges.", "dmit_insight": "High RC conservative analytical moderate." }}

Few-Shot 65: Arch Medium Confidence Variation (from banu gençer arch medium example)
{{ "type": "A", "rc": 0, "confidence": "Medium", "note": "Medium confidence arch variation zero.", "dmit_insight": "Balanced low medium visibility." }}

Few-Shot 66: Ulnar Medium Perfect (from ALPER AYDIN loop medium example)
{{ "type": "UL", "rc": 17, "confidence": "High", "note": "Medium perfect ulnar 17 ridges.", "dmit_insight": "Medium RC ulnar practical balanced." }}

Few-Shot 67: Spiral Low Variant (from Ayşe Sude Türkyılmaz spiral low example)
{{ "type": "W", "rc": 16, "confidence": "High", "note": "Low spiral variant 16 ridges.", "dmit_insight": "Low RC spiral technical low." }}

Few-Shot 68: Unknown Medium Residual (from arda yağız akkuş unknown medium example)
{{ "type": "Unknown", "rc": 0, "confidence": "Medium", "note": "Medium residual ambiguous re-scan.", "dmit_insight": "Medium quality limited insight." }}

Few-Shot 69: Double Loop High Noise (from ceylin otuzoğlu S high example)
{{ "type": "S", "rc": 27, "confidence": "Medium", "note": "High interlocking noise conservative 27 ridges.", "dmit_insight": "High RC creativity moderate conservative." }}

Few-Shot 70: Whorl Medium Clean (from bartuğ ogulcan whorl medium example)
{{ "type": "W", "rc": 22, "confidence": "High", "note": "Medium clean whorl 22 ridges.", "dmit_insight": "Medium RC clean analytical balanced." }}

Few-Shot 71: Tented Low Noise Conservative (from cemal ulvi berber tented low example)
{{ "type": "AT", "rc": 2, "confidence": "Medium", "note": "Low tent noise conservative 2 ridges.", "dmit_insight": "Low RC tented limited transition conservative." }}

Few-Shot 72: Radial Low Perfect (from Burak Özdemir rare RL low example)
{{ "type": "RL", "rc": 9, "confidence": "High", "note": "Low perfect rare radial 9 ridges.", "dmit_insight": "Low RC rare radial innovation low." }}

Few-Shot 73: Double Loop Perfect Medium (from Betül Serra Özcan S medium example)
{{ "type": "S", "rc": 23, "confidence": "High", "note": "Perfect medium interlocking 23 ridges.", "dmit_insight": "Medium RC double creativity balanced." }}

Few-Shot 74: Whorl Low Pocket Conservative (from cemre gece pocket low example)
{{ "type": "W", "rc": 15, "confidence": "High", "note": "Low pocket conservative 15 ridges.", "dmit_insight": "Low RC pocket technical low." }}

Few-Shot 75: Arch High Perfect (from bhr snc arch high example)
{{ "type": "A", "rc": 0, "confidence": "High", "note": "High perfect smooth arch zero.", "dmit_insight": "Zero RC balanced high." }}

Few-Shot 76: Ulnar High Noise Conservative (from Ayşegül biçer loop high example)
{{ "type": "UL", "rc": 21, "confidence": "Medium", "note": "High ulnar noise conservative 21 ridges.", "dmit_insight": "High RC practical moderate conservative." }}

Few-Shot 77: Spiral Medium Variant Noise (from büşranur turkyılmaz spiral medium example)
{{ "type": "W", "rc": 20, "confidence": "Medium", "note": "Medium spiral variant noise conservative 20 ridges.", "dmit_insight": "Medium RC spiral technical moderate conservative." }}

Few-Shot 78: Unknown Low Residual Re-Scan (from cem cicek unknown low example)
{{ "type": "Unknown", "rc": 0, "confidence": "Low", "note": "Low residual insufficient re-scan.", "dmit_insight": "Low quality no insight re-scan." }}

Few-Shot 79: Double Loop Low Perfect (from Bekir Bahadır S low example)
{{ "type": "S", "rc": 16, "confidence": "High", "note": "Low perfect interlocking 16 ridges.", "dmit_insight": "Low RC double creativity low." }}

Few-Shot 80: Whorl High Perfect Variant (from bahar şişman whorl high example)
{{ "type": "W", "rc": 32, "confidence": "High", "note": "High perfect variant whorl 32 ridges.", "dmit_insight": "Exceptional RC variant analytical peak (%97 İletişim similar)." }}

OUTPUT ONLY VALID JSON (no extra text, no markdown):
{{
  "type": "W",
  "rc": 22,
  "confidence": "High",
  "note": "Skeletonized image: perfect concentric whorl, higher delta-core exactly 22 ridges (no islands).",
  "dmit_insight": "Very high RC whorl indicates exceptional analytical and technical aptitude, often linked to 82%+ Teknik scores in Genetic Test reports."
}}

If truly impossible: {{ "type": "Unknown", "rc": 0, "confidence": "Low", "note": "Image quality insufficient even after processing - recommend professional ink scan." }}
"""
    
    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [{"type": "text", "text": f"Analyze this fingerprint. Label: {finger_label}. Status: {image_status_note}"}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}
            ],
            temperature=0.0, # Matematiksel kesinlik için 0
            max_tokens=1000, # Büyük prompt için token arttırıldı
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        return {"type": "Error", "rc": 0, "confidence": "Low", "note": str(e), "dmit_insight": "Hata"}

# -----------------------------------------------------------------------------
# 5. RAPOR FONKSİYONU (REASONING) - 80-SHOT RAPOR PROMPT (FULL)
# -----------------------------------------------------------------------------
def generate_nobel_report(student_name, age, gender, finger_data, scores_ignored):
    if not GROK_API_KEY or GROK_API_KEY == "key-not-found":
        return "HATA: API Anahtarı eksik."

    # Python ile Kesin Hesaplama
    stats = calculate_advanced_stats(finger_data)
    
    raw_finger_list = ""
    for _, row in finger_data.iterrows():
        raw_finger_list += f"{row['finger_code']}: {row['pattern_type']} (RC: {row['ridge_count']}), "

    # --- SENİN 80-SHOT NOBEL RAPOR PROMPTUN (FULL) ---
    prompt = f"""
You are a world-class DMIT expert producing Nobel Koçluk Genetic Test reports. Generate an EXTREMELY COMPREHENSIVE report in Turkish ONLY.

Use raw data:
- Name: {student_name}
- Age: {age}
- Raw finger data: {raw_finger_list} (e.g., L1:W_22 etc.)

FIRST, PERFORM ALL MATHEMATICAL CALCULATIONS STEP-BY-STEP USING RAW DATA (use exact calculated values in bold throughout the report; briefly explain key calculations in relevant sections for transparency):

1. Total Finger Ridge Count (TFRC): **{stats['tfrc']}**
   - High TFRC indicates higher overall genetic potential (fetal ridge density).

2. Brain Lobe Percentages (Standard DMIT Mapping):
   - Right hand controls left brain: R1 (Sol Prefrontal), R2 (Sol Frontal), R3 (Sol Parietal), R4 (Sol Temporal), R5 (Sol Occipital).
   - Left hand controls right brain: L1 (Sağ Prefrontal), L2 (Sağ Frontal), L3 (Sağ Parietal), L4 (Sağ Temporal), L5 (Sağ Occipital).
   - USE THESE EXACT VALUES:
     - Sol Prefrontal: {stats['lobes']['Sol_Prefrontal']:.1f}%
     - Sol Frontal: {stats['lobes']['Sol_Frontal']:.1f}%
     - Sol Parietal: {stats['lobes']['Sol_Parietal']:.1f}%
     - Sol Temporal: {stats['lobes']['Sol_Temporal']:.1f}%
     - Sol Occipital: {stats['lobes']['Sol_Occipital']:.1f}%
     - Sag Prefrontal: {stats['lobes']['Sag_Prefrontal']:.1f}%
     - Sag Frontal: {stats['lobes']['Sag_Frontal']:.1f}%
     - Sag Parietal: {stats['lobes']['Sag_Parietal']:.1f}%
     - Sag Temporal: {stats['lobes']['Sag_Temporal']:.1f}%
     - Sag Occipital: {stats['lobes']['Sag_Occipital']:.1f}%

3. Intelligence / Education / Profession Group Normalization:
   - USE THESE EXACT VALUES:
     - **Teknik: {stats['groups']['Teknik']:.1f}%**
     - **Sosyal-ekonomi / Dil: {stats['groups']['Sosyal']:.1f}%**
     - **Matematik: {stats['groups']['Matematik']:.1f}%**
     - **Fen: {stats['groups']['Fen']:.1f}%**
     - **Genel: {stats['groups']['Genel']:.1f}%**

4. Dominant Brain Side: **{stats['dominance']}**
   - Left brain total %: {stats['sol_beyin_total']}
   - Right brain total %: {stats['sag_beyin_total']}

5. Sports Gauges and Health Bars:
   - Speed (Hız): Normalize parietal RC high → % (e.g., high = 90%).
   - Endurance (Dayanıklılık): Temporal balance.
   - Coordination (Koordinasyon): Occipital/parietal.
   - Health risks: Low RC/pattern match → higher % bar (e.g., many low RC = 90% Sindirim risk).
   - Use pattern bonuses (e.g., many arches = higher certain risks).

Use these EXACT calculated values in bold percentages and comments.

Then generate the report using calculated values.

LEARN FROM THESE 80 DETAILED FEW-SHOT EXAMPLES FROM NOBEL KOÇLUK REPORTS (mimic style, tone, visuals, fetal/ridge comments, quotes exactly):

Few-Shot 1 - Dermatoglifik Bilimi (tüm PDF'ler ortak):
Dermatoglifik bilimi- insan avucu üzerindeki papiller çizgilerin desenini inceleyen bir bilim dalıdır. Bu desenler vücudun fetal gelişiminin 13. haftasında oluşmaya başlar ve yaşam boyu değişmeden kalır. Cilt ve sinir sisteminin toplamının embriyonik kökenli olması dermatoglifik çalışmaların yeterliliğinin garantisidir.
Harold Cummings - Tıp bilimleri doktoru, "dermatoglifikler"in "babası".
Mevcut papillar desenlerin türleri: A Yay, AT Çadırlı Yay, L Döngü, RL Radyal Döngü, W Spiral, S Çift Döngü (ikonlarla gösterim).

Few-Shot 2 - Eğitim Türü (Akın Sevinç.pdf):
**Sosyal-ekonomi 94%**
Çağdaş toplum yapısı ve toplumda gelişen süreçlerin mekanizması ilginizi çekebilir. Size sosyoloji, ekonomi ve hukuk gibi sosyal ve siyasal bilimler uygundur.
**Dil 87%**
Dil algılama yeteneğiniz oldukça gelişmiş, yabancı dil eğitiminde hiç güçlük çekmeyecek, hatta bundan zevk alacağınız. Çevirmenlik, uluslararası ilişkiler, ve de öğretim alanlarında başarılı olmanız mümkündür.
**Teknik 70%**
Herhangi bir modern teknoloji ve gelişmiş teknolojiyi kolay öğrenme yeteneğine sahipsiniz. Muhtemelen programlama, mühendislik veya çeşitli disiplinlerin kesiştiği faaliyetlerle ilgili alanlarda eğitim görmeniz sizin için daha uygun olacaktır.
**Matematik 70%**
Rasyonel bir insansınız, olayların gelişmesiyle ilgili önceden birkaç farklı senaryo planlıyorsunuz, mantıksal bulmacalardan hoşlanıyorsunuz. Size daha çok sibernetik veya teknik uzmanlık gibi kesin uygulamalı bilimler uygundur.
**Fen 36%**
Doğa süreçlerini incelemek ve açıklamak sizin için uygun bir faaliyet alanı olmayabilir. Güçlü olduğunuz yanları daha iyi sergileyebileceğiniz eğitim dallarını seçmenizi tavsiye ederiz.
**Genel 11%**
İnsan faaliyetinin çeşitli alanlarını açıklayan bilim dalları sizler için çok belirsiz ve spekülatif görünebilir. Tarihsel filmleri seyretmek ve bir kitap okumak hoşunuza gidiyor olabilir, ama mesleksel faaliyetiniz için başka bir alan seçmeniz daha doğru olacaktır.
(Fetal köken: Bu yetenekler fetal dönemde temporal/frontal lob ridge oluşumuyla bağlantılıdır. Yüksek RC temporal grup = sosyal/dil güçlü.)
Renkli bar grafik: Soluk sarıdan mora geçişli çubuklar, en yüksek **Sosyal-ekonomi 94%** mor çubuk.
Full radar chart description: 6 köşeli radar, Sosyal-ekonomi ve Dil köşeleri yüksek dolgu, Teknik ve Matematik orta-yüksek.

Few-Shot 3 - Meslek Faaliyet Alanları (Ahmet Arif Yılmaz.pdf):
**İLETİŞİM 82%**
Yüksek iletişim becerileriniz güçlü yanınızdır. İnsanlarla etkileştiğinizde kendinizi daha iyi ve güvenli hissediyorsunuz. Görüşmeler yapmak, şirketi birinci düzeyde temsil etmek, sunumlar organize etmek, toplumsal faaliyetlere katılmak, aracılık yapmak gibi işler size çok uygundur. Yeteneklerinizi uygulayabileceğiniz mesleklerden bazıları: halkla ilişkiler uzmanı, gazetecilik, personel müdürü, müşteri hizmetleri, sekreter, sigorta acentesi, satış temsilcisi, emlakçı, spor koçu, rehber, vb.
"Hoşunuza giden bir iş seçerseniz, ömür boyunca bir gün bile çalışmazsınız" - Konfüçyüs
**UYGULAMA 35%**
Kolaylıkla pratik beceri elde ediyor ve bu becerileri uygulama alanında başarılı oluyorsunuz.
**ANALİZ 11%**
Büyük hacimli bilgi işleme ile ilişkili analitik faaliyetler sizin için o kadar da çekici olmayabilir.
Radar chart: Kırmızı-yeşil dolgu, İletişim köşesi neredeyse tam dolu, Uygulama orta, Analiz düşük.

Few-Shot 4 - Mesleki Faaliyetin Küreler (ahmet aziz doğan.pdf):
**YARATICILIK 65%**
Belirli algoritmaların mekaniksel tekrarı yerine yeni görevler yerine getirmeyi yeğliyorsunuz. Kim bilir, belki bir gün bu sanat eserinin müellifi siz olabilirsiniz. Uygun Mesleler: Aktör, yazar, tasarımcı, çiçekçi, pastacı, fotoğrafçı, koreograf, illüstratör, besteci, ve diğerleri.
**SPOR 65%**
Antrenör, dublör, aerialist, endüstriyel dağcı, profesyonel sporcu, spor eğitmeni, cankurtaran vs. gibi mesleklerde büyük bir potansiyeliniz var.
**YENİLİKLER 10%**
Bu alanda aldığınız düşük puanlar ilkesel açıdan yeni bir şeyler yaratmakla ilgili ve kendi yeteneklerinizi kullanma imkanı vermeyen meslekler sizin için o kadar da uygun değil demektir.
"İyi ki bir kişiye meslek seçerken zorunluluk faktörüne dayanarak değil, ruhsal yatkınlıklarına uygun seçim yapma imkanı veriliyor." - Ali Apşeroni
Radar chart: Sarı-mavi dolgu, Yaratıcılık ve Spor köşeleri orta-yüksek, Yenilikler düşük.

Few-Shot 5 - Sağlık Risk Faktörleri (Berrin Gülhan.pdf):
**DAMARLAR | BEYİN 13%** **KALP VE DAMAR SİSTEMİ 10%** **SİNDİRİM SİSTEMİ 90%** **SİNİR SİSTEMİ 50%** **SIRT / OMURGA 50%** **KARACİĞER / BÖBREKLER 50%**
Vücut diyagramı: Sindirim bölgesi kırmızı vurgulu yüksek risk.
Bar chart: Sindirim uzun kırmızı bar %90, diğerleri orta/kısa.
Genetik yatkınlık uyarısı: Düzenli tıbbi muayene ve sağlıklı yaşam tarzı önerilir.

Few-Shot 6 - Spor (akın berk ejder.pdf):
**HIZ 90%** **DAYANIKLILIK 62%** **KOORDİNASYON 39%**
Gauge chart'lar: Hız gauge iğnesi kırmızı zon %90, Dayanıklılık orta, Koordinasyon düşük.
Takım sporlarında oyun yeriniz: Forvet.
Tavsiye edilen spor dalları horizontal bar: Kısa mesafe koşusu, güç sporları, oyun sporları yeşil vurgulu.

Few-Shot 7 - Kendini Geliştirme (AHMET SELİM.pdf):
**KURUMSAL 90%** radar yüksek dolgu.
**GİRİŞİMCİ 64%** 3D bar yüksek.

Few-Shot 8 - Sinir Sistemi (Ahsen Yazıcıoğlu.pdf):
Orta-zayıf tip traits + fetal TFRC düşük yorum.

Few-Shot 9 - Davranış/Mizaç (Ahmet Yavuz Gece.pdf):
Pratik-muhatap karışık mizaç + fetal lateralizasyon.

Few-Shot 10 - Yenilik Algısı (arif açıkgöz.pdf):
Liberal/muhafazakar tablo + fetal prefrontal yorum.

Few-Shot 11 - Şişmanlık/Alkol (ahmet selim çoban.pdf):
Bar/gauge + lifestyle öneri + fetal düşük RC bağımlılık.

Few-Shot 12 - Parmak Desenleri (Alperen Adıgüzel.pdf):
El diyagramı L1-R1 + per-finger fetal link.

Few-Shot 13 - Eğitim Türü (akif eker.pdf):
**Teknik 70%** mavi bar + mühendislik öneri.

Few-Shot 14 - Sonuç (tüm):
%85-95 doğruluk + çevre faktörü + "Cevap senin genlerinde".

Few-Shot 15 - Eğitim Türü (Alperen Özdemir.pdf):
**Matematik 70%** mantıksal bulmaca + bar dolgu.

Few-Shot 16 - Meslek Alanları (Ali Emirhan Ercan.pdf):
**ANALİZ 11%** düşük radar + yorum.

Few-Shot 17 - Mesleki Küreler (Asude Verda Özdemir.pdf):
**YENİLİKLER 30%** düşük radar + Apşeroni varyasyon.

Few-Shot 18 - Sağlık (ahmet yusuf karadogan.pdf):
**KALP 10%** düşük bar + uyarı.

Few-Shot 19 - Spor (alperen ünaldı.pdf):
**KOORDİNASYON 39%** düşük gauge + öneri.

Few-Shot 20 - Kendini Geliştirme (asım faruk baş.pdf):
**MESLEKSEL 10%** düşük radar.

Few-Shot 21 - Parmak Desenleri (Akif Bayrak.pdf):
Per-finger RC yorum + fetal link.

Few-Shot 22 - Eğitim Türü (batuhan celık.pdf):
**Fen 36%** düşük bar + doğa süreçleri yorum.

Few-Shot 23 - Sağlık (burak tiens.pdf):
**KARACİĞER 50%** orta bar + vücut diyagramı.

Few-Shot 24 - Sonuç varyasyon (bahar ışlak.pdf):
Çevre faktörü vurgu + kapanış varyasyon.

Few-Shot 25 - Eğitim Türü (alper okten.pdf):
**Genel 11%** düşük bar + tarihsel filmler yorum.

Few-Shot 26 - Meslek Alanları (betül genç.pdf):
**İLETİŞİM 97%** yüksek radar + quote varyasyon.

Few-Shot 27 - Sağlık (belkıs müjde.pdf):
**DAMARLAR 13%** düşük bar + uyarı.

Few-Shot 28 - Spor (ASIM KARABIYIK.pdf):
**HIZ 90%** gauge yüksek + koşu öneri.

Few-Shot 29 - Kendini Geliştirme (Ceylin Erol.pdf):
**YÖNETİMSEL 43%** orta radar + yorum.

Few-Shot 30 - Yenilik Algısı (azra arslanoğlu.pdf):
Muhafazakar tablo + prefrontal düşük.

Few-Shot 31 - Eğitim Türü (betül mıngır.pdf):
**Sosyal-ekonomi 76%** bar mor + sosyoloji öneri.

Few-Shot 32 - Parmak Desenleri (aydan açıkgöz.pdf):
El diyagramı + fetal bağlantı.

Few-Shot 33 - Spor (büşranur turkyılmaz.pdf):
**KOORDİNASYON 39%** düşük gauge + takım sporu öneri.

Few-Shot 34 - Sonuç (cem cicek.pdf):
%85-95 doğruluk + çevre + kapanış.

Few-Shot 35 - Sağlık (Bekir Bahadır.pdf):
**SİNİR SİSTEMİ 50%** orta bar + sinir yorumu.

Few-Shot 36 - Meslek Alanları (bahar şişman.pdf):
**UYGULAMA 35%** orta radar + pratik öneri.

Few-Shot 37 - Eğitim Türü (banu gençer.pdf):
**Dil 74%** yeşil bar + çevirmenlik.

Few-Shot 38 - Kendini Geliştirme (ALPER AYDIN.pdf):
**KURUMSAL 70%** radar yüksek + kurumsal yorum.

Few-Shot 39 - Spor (Ayşe Sude Türkyılmaz.pdf):
**DAYANIKLILIK 62%** gauge orta + dayanıklılık öneri.

Few-Shot 40 - Yenilik Algısı (arda yağız akkuş.pdf):
Bireysel tablo + yenilik yorumu.

Few-Shot 41 - Sağlık (ceylin otuzoğlu.pdf):
**KARACİĞER/BÖBREK 50%** orta bar + öneri.

Few-Shot 42 - Mesleki Küreler (bartuğ ogulcan.pdf):
**YARATICILIK 55%** sarı radar + sanat yorumu.

Few-Shot 43 - Parmak Desenleri (cemal ulvi berber.pdf):
Per-finger + fetal link varyasyon.

Few-Shot 44 - Sonuç varyasyon (Burak Özdemir.pdf):
Çevre faktörü + motive kapanış + "Cevap senin genlerinde".

Few-Shot 45 - Eğitim Türü (Betül Serra Özcan.pdf):
**Teknik 70%** mavi bar + mühendislik öneri + fetal prefrontal yüksek.

Few-Shot 46 - Meslek Alanları (cemre gece.pdf):
**UYGULAMA 35%** orta radar + pratik beceri + fetal parietal orta.

Few-Shot 47 - Sağlık (bhr snc.pdf):
**SİNİR SİSTEMİ 50%** orta bar + sinir yorumu + fetal TFRC orta.

Few-Shot 48 - Spor (Ayşegül biçer.pdf):
**DAYANIKLILIK 62%** gauge orta + dayanıklılık öneri + fetal temporal.

Few-Shot 49 - Kendini Geliştirme (büşranur turkyılmaz.pdf):
**YÖNETİMSEL 43%** orta radar + fetal frontal orta.

Few-Shot 50 - Yenilik Algısı (cem cicek.pdf):
Muhafazakar tablo + fetal prefrontal düşük + yenilik yorum.

Few-Shot 51 - Şişmanlık/Alkol (Bekir Bahadır.pdf):
Orta gauge/bar + lifestyle öneri + fetal düşük RC bağımlılık.

Few-Shot 52 - Parmak Desenleri (bahar şişman.pdf):
El diyagramı varyasyon + per-finger fetal link + RC yorum.

Few-Shot 53 - Eğitim Türü (banu gençer.pdf):
**Fen 36%** düşük bar + doğa süreçleri yorum + fetal occipital düşük.

Few-Shot 54 - Sonuç varyasyon (ALPER AYDIN.pdf):
Çevre faktörü güçlü vurgu + motive kapanış + "Cevap senin genlerinde" + fetal genel yorum.

Few-Shot 55 - Eğitim Türü (Ayşe Sude Türkyılmaz.pdf):
**Matematik 70%** mantıksal bulmaca + bar dolgu + fetal frontal.

Few-Shot 56 - Meslek Alanları (arda yağız akkuş.pdf):
**ANALİZ 11%** düşük radar + yorum + fetal prefrontal düşük.

Few-Shot 57 - Mesleki Küreler (ceylin otuzoğlu.pdf):
**YENİLİKLER 30%** düşük radar + Apşeroni varyasyon + fetal prefrontal düşük.

Few-Shot 58 - Sağlık (bartuğ ogulcan.pdf):
**KALP 10%** düşük bar + uyarı + fetal düşük RC.

Few-Shot 59 - Spor (cemal ulvi berber.pdf):
**KOORDİNASYON 39%** düşük gauge + öneri + fetal occipital düşük.

Few-Shot 60 - Kendini Geliştirme (Burak Özdemir.pdf):
**MESLEKSEL 10%** düşük radar + fetal mesleksel düşük.

Few-Shot 61 - Eğitim Türü (Betül Serra Özcan.pdf):
**Genel 11%** düşük bar + tarihsel filmler yorum + fetal genel düşük.

Few-Shot 62 - Meslek Alanları (cemre gece.pdf):
**İLETİŞİM 97%** yüksek radar + quote varyasyon + fetal temporal yüksek.

Few-Shot 63 - Sağlık (bhr snc.pdf):
**DAMARLAR 13%** düşük bar + uyarı + fetal damar düşük.

Few-Shot 64 - Spor (Ayşegül biçer.pdf):
**HIZ 90%** gauge yüksek + koşu öneri + fetal parietal yüksek.

Few-Shot 65 - Kendini Geliştirme (büşranur turkyılmaz.pdf):
**YÖNETİMSEL 43%** orta radar + fetal frontal orta.

Few-Shot 66 - Yenilik Algısı (cem cicek.pdf):
Bireysel tablo + fetal yenilik prefrontal orta.

Few-Shot 67 - Şişmanlık/Alkol (Bekir Bahadır.pdf):
Orta gauge + öneri + fetal düşük RC bağımlılık orta.

Few-Shot 68 - Parmak Desenleri (bahar şişman.pdf):
El diyagramı + fetal bağlantı varyasyon.

Few-Shot 69 - Eğitim Türü (banu gençer.pdf):
**Dil 74%** yeşil bar + çevirmenlik + fetal temporal orta.

Few-Shot 70 - Sonuç varyasyon (ALPER AYDIN.pdf):
Çevre faktörü güçlü vurgu + motive kapanış + "Cevap senin genlerinde".

Few-Shot 71 - Eğitim Türü (Ayşe Sude Türkyılmaz.pdf):
**Sosyal-ekonomi 76%** mor bar + sosyoloji öneri + fetal temporal yüksek.

Few-Shot 72 - Meslek Alanları (arda yağız akkuş.pdf):
**UYGULAMA 35%** orta radar + pratik beceri + fetal parietal orta.

Few-Shot 73 - Sağlık (ceylin otuzoğlu.pdf):
**SİNİR SİSTEMİ 50%** orta bar + sinir yorumu + fetal TFRC orta.

Few-Shot 74 - Spor (bartuğ ogulcan.pdf):
**DAYANIKLILIK 62%** gauge orta + dayanıklılık öneri + fetal temporal orta.

Few-Shot 75 - Kendini Geliştirme (cemal ulvi berber.pdf):
**KURUMSAL 70%** radar yüksek + kurumsal yorum + fetal frontal orta.

Few-Shot 76 - Yenilik Algısı (Burak Özdemir.pdf):
Muhafazakar tablo + fetal prefrontal düşük + yenilik yorum.

Few-Shot 77 - Şişmanlık/Alkol (Betül Serra Özcan.pdf):
Orta gauge/bar + lifestyle öneri + fetal düşük RC orta.

Few-Shot 78 - Parmak Desenleri (cemre gece.pdf):
El diyagramı varyasyon + per-finger fetal link + RC yorum.

Few-Shot 79 - Eğitim Türü (bhr snc.pdf):
**Fen 36%** düşük bar + doğa süreçleri yorum + fetal occipital düşük.

Few-Shot 80 - Sonuç varyasyon (Ayşegül biçer.pdf):
Çevre faktörü vurgu + motive kapanış + "Cevap senin genlerinde" + fetal genel yorum.

Strictly follow 13 sections with fetal/ridge/personal/practical elements.
Use empathetic, encouraging language. Report depth 20 pages equivalent.
"""

    try:
        response = client.chat.completions.create(
            model=REASONING_MODEL,
            messages=[
                {"role": "system", "content": "You are the Nobel Koçluk Lead Genetic Analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=6000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Rapor Oluşturma Hatası: {str(e)}"
