# -*- coding: utf-8 -*-
"""
Created on Thu Feb  5 22:37:17 2026

@author: YYYNÇİGGGİİÜÜÜÜĞĞĞ
"""

import sqlite3
import pandas as pd
from datetime import datetime

class DBManager:
    def __init__(self, db_name="dmit_system.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Öğrenci Tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT UNIQUE,
                age INTEGER,
                created_at DATETIME,
                status TEXT DEFAULT 'pending'
            )
        ''')
        # Parmak İzi ve Analiz Tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS fingerprints (
                student_id INTEGER,
                finger_code TEXT,
                pattern_type TEXT,
                ridge_count INTEGER,
                confidence TEXT,
                note TEXT,
                dmit_insight TEXT,
                image_data BLOB,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
        ''')
        self.conn.commit()

    def add_student(self, name, age):
        try:
            self.cursor.execute("INSERT INTO students (full_name, age, created_at) VALUES (?, ?, ?)", 
                                (name, age, datetime.now()))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_student_id(self, name):
        self.cursor.execute("SELECT id FROM students WHERE full_name = ?", (name,))
        res = self.cursor.fetchone()
        return res[0] if res else None

    def save_fingerprint_analysis(self, student_id, finger_code, analysis_data, img_bytes):
        # analysis_data: Grok'tan gelen JSON
        self.cursor.execute('''
            INSERT INTO fingerprints (student_id, finger_code, pattern_type, ridge_count, confidence, note, dmit_insight, image_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            student_id, 
            finger_code, 
            analysis_data.get('type', 'Unknown'), 
            analysis_data.get('rc', 0),
            analysis_data.get('confidence', 'Low'),
            analysis_data.get('note', ''),
            analysis_data.get('dmit_insight', ''),
            img_bytes
        ))
        self.conn.commit()

    def get_all_students(self):
        return pd.read_sql("SELECT * FROM students", self.conn)

    def get_student_data(self, student_id):
        return pd.read_sql("SELECT * FROM fingerprints WHERE student_id = ?", self.conn, params=(student_id,))
    
    def get_student_info(self, student_id):
        self.cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        return self.cursor.fetchone()