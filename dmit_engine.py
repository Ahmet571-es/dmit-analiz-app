# -*- coding: utf-8 -*-
"""
Created on Thu Feb  5 22:38:22 2026

@author: YYYNÇİGGGİİÜÜÜÜĞĞĞ
"""

import pandas as pd

class DMITEngine:
    def __init__(self, df_fingerprints):
        self.data = df_fingerprints
        self.results = self.run_full_analysis()

    def run_full_analysis(self):
        raw_scores = self._calculate_raw_scores()
        return {
            "lobes": self._calculate_lobes(raw_scores),
            "hemispheres": self._calculate_hemispheres(raw_scores),
            "tfrc": int(self.data['ridge_count'].sum()) if not self.data.empty else 0,
            "multiple_intelligences": self._calculate_multiple_intelligences(raw_scores),
            "learning_styles": self._calculate_learning_styles(raw_scores),
            "raw_scores": raw_scores
        }

    def _calculate_raw_scores(self):
        scores = {}
        # Ağırlıklar: Whorl (W)=10, S=9, RL=8, UL=7, AT=5, A=4
        weights = {"W": 10, "S": 9, "RL": 8, "UL": 7, "AT": 5, "A": 4, "Unknown": 4}

        for _, row in self.data.iterrows():
            code = row['finger_code']
            ptype = row['pattern_type']
            rc = row['ridge_count']
            
            # Formül: Desen Ağırlığı + (Sırt Sayısı * 0.5)
            # RC potansiyeli artırır.
            base_val = weights.get(ptype, 5)
            final_val = base_val + (rc * 0.5)
            scores[code] = final_val
            
        return scores

    def _calculate_lobes(self, s):
        # L1/R1: Prefrontal, L2/R2: Frontal, L3/R3: Parietal, L4/R4: Temporal, L5/R5: Occipital
        lobes = {
            "Prefrontal (Kişilik)": s.get('L1', 0) + s.get('R1', 0),
            "Frontal (Mantık)": s.get('L2', 0) + s.get('R2', 0),
            "Parietal (Kinestetik)": s.get('L3', 0) + s.get('R3', 0),
            "Temporal (İşitsel)": s.get('L4', 0) + s.get('R4', 0),
            "Occipital (Görsel)": s.get('L5', 0) + s.get('R5', 0)
        }
        total = sum(lobes.values()) or 1
        return {k: round((v/total)*100, 1) for k, v in lobes.items()}

    def _calculate_hemispheres(self, s):
        left_val = sum([v for k, v in s.items() if k.startswith('L')])
        right_val = sum([v for k, v in s.items() if k.startswith('R')])
        total = left_val + right_val or 1
        return {
            "Sol Beyin (Analitik)": round((right_val / total) * 100, 1), # Sağ el sol beyni yönetir
            "Sağ Beyin (Yaratıcı)": round((left_val / total) * 100, 1)   # Sol el sağ beyni yönetir
        }

    def _calculate_multiple_intelligences(self, s):
        # Simülasyon Ağırlıkları
        mi = {
            "İçsel (Intrapersonal)": s.get('L1', 0) * 1.2,
            "Sosyal (Interpersonal)": s.get('R1', 0) * 1.2,
            "Mantıksal": s.get('R2', 0) * 1.5,
            "Sözel/Dilsel": s.get('R4', 0) + s.get('L4', 0),
            "Görsel/Uzamsal": s.get('L2', 0) + s.get('R5', 0),
            "Müziksel": s.get('L4', 0) * 1.3,
            "Bedensel/Kinestetik": s.get('L3', 0) + s.get('R3', 0),
            "Doğasal": s.get('L5', 0) + s.get('R5', 0)
        }
        total = sum(mi.values()) or 1
        return {k: round((v/total)*100, 1) for k, v in mi.items()}

    def _calculate_learning_styles(self, s):
        # VAK Modeli
        visual = s.get('L5', 0) + s.get('R5', 0) + s.get('L2', 0)
        auditory = s.get('L4', 0) + s.get('R4', 0)
        kinesthetic = s.get('L3', 0) + s.get('R3', 0) + s.get('R2', 0)
        
        total = visual + auditory + kinesthetic or 1
        return {
            "Görsel (Visual)": round((visual/total)*100, 1),
            "İşitsel (Auditory)": round((auditory/total)*100, 1),
            "Kinestetik (Dokunsal)": round((kinesthetic/total)*100, 1)
        }