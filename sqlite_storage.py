import sqlite3
import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional
import streamlit as st

class SQLiteStorage:
    """SQLite-based storage for better cloud persistence"""
    
    def __init__(self, db_file='temptrack.db'):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database and create tables"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Create temperatures table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temperatures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    datetime TEXT NOT NULL,
                    temperature_celsius REAL NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create notes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    note TEXT NOT NULL,
                    category TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create cycle_starts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cycle_starts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_temp_datetime ON temperatures(datetime)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_date ON notes(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cycle_date ON cycle_starts(start_date)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"Database initialization error: {e}")
    
    def load_data(self) -> Dict:
        """Load all data from SQLite database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Load temperatures
            cursor.execute('SELECT datetime, temperature_celsius FROM temperatures ORDER BY datetime')
            temperatures = [
                {
                    'datetime': row[0],
                    'temperature_celsius': row[1]
                }
                for row in cursor.fetchall()
            ]
            
            # Load notes
            cursor.execute('SELECT date, note, category FROM notes ORDER BY date')
            notes = [
                {
                    'date': row[0],
                    'note': row[1],
                    'category': row[2]
                }
                for row in cursor.fetchall()
            ]
            
            # Load cycle starts
            cursor.execute('SELECT start_date FROM cycle_starts ORDER BY start_date')
            cycle_starts = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'temperatures': temperatures,
                'notes': notes,
                'cycle_starts': cycle_starts
            }
            
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return {'temperatures': [], 'notes': [], 'cycle_starts': []}
    
    def save_data(self, data: Dict):
        """Save data to SQLite database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Clear existing data
            cursor.execute('DELETE FROM temperatures')
            cursor.execute('DELETE FROM notes')
            cursor.execute('DELETE FROM cycle_starts')
            
            # Insert temperatures
            for temp in data['temperatures']:
                cursor.execute(
                    'INSERT INTO temperatures (datetime, temperature_celsius) VALUES (?, ?)',
                    (temp['datetime'], temp['temperature_celsius'])
                )
            
            # Insert notes
            for note in data['notes']:
                cursor.execute(
                    'INSERT INTO notes (date, note, category) VALUES (?, ?, ?)',
                    (note['date'], note.get('note', note.get('text', '')), note['category'])
                )
            
            # Insert cycle starts
            for cycle_start in data['cycle_starts']:
                cursor.execute(
                    'INSERT INTO cycle_starts (start_date) VALUES (?)',
                    (cycle_start,)
                )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"Error saving data: {e}")
    
    def add_temperature(self, datetime_str: str, temperature_celsius: float):
        """Add a single temperature reading"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO temperatures (datetime, temperature_celsius) VALUES (?, ?)',
                (datetime_str, temperature_celsius)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Error adding temperature: {e}")
    
    def add_note(self, date_str: str, note: str, category: str):
        """Add a single note"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO notes (date, note, category) VALUES (?, ?, ?)',
                (date_str, note, category)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Error adding note: {e}")
    
    def add_cycle_start(self, start_date_str: str):
        """Add a single cycle start"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO cycle_starts (start_date) VALUES (?)',
                (start_date_str,)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Error adding cycle start: {e}")
    
    def delete_temperature(self, datetime_str: str):
        """Delete a temperature reading"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM temperatures WHERE datetime = ?', (datetime_str,))
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Error deleting temperature: {e}")
    
    def delete_note(self, date_str: str, note_text: str):
        """Delete a note"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM notes WHERE date = ? AND note = ?', (date_str, note_text))
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Error deleting note: {e}")
    
    def delete_cycle_start(self, start_date_str: str):
        """Delete a cycle start"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cycle_starts WHERE start_date = ?', (start_date_str,))
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Error deleting cycle start: {e}")
    
    def export_to_csv(self, data: Dict = None) -> str:
        """Export temperature data to CSV format"""
        if data is None:
            data = self.load_data()
            
        csv_data = "Date,Temperature (°C)\n"
        for temp in sorted(data['temperatures'], key=lambda x: x['datetime']):
            temp_date = datetime.fromisoformat(temp['datetime']).strftime('%Y-%m-%d')
            csv_data += f"{temp_date},{temp['temperature_celsius']}\n"
        
        return csv_data
    
    def get_data_size(self) -> Dict[str, int]:
        """Get information about data size"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM temperatures')
            temp_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM notes')
            note_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM cycle_starts')
            cycle_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'temperatures': temp_count,
                'notes': note_count,
                'cycle_starts': cycle_count
            }
        except Exception as e:
            st.error(f"Error getting data size: {e}")
            return {'temperatures': 0, 'notes': 0, 'cycle_starts': 0}