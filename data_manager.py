import json
import os
import pandas as pd
from datetime import datetime, date, timedelta
import streamlit as st

class DataManager:
    def __init__(self, data_file='temptrack_data.json'):
        self.data_file = data_file
        self.default_data = {
            'temperatures': [],
            'notes': [],
            'cycle_starts': [],
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    
    def load_data(self):
        """Load data from JSON file or return default structure"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    # Ensure all required keys exist
                    for key in self.default_data:
                        if key not in data:
                            data[key] = self.default_data[key]
                    return data
            else:
                return self.default_data.copy()
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return self.default_data.copy()
    
    def save_data(self, data):
        """Save data to JSON file"""
        try:
            data['last_updated'] = datetime.now().isoformat()
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            st.error(f"Error saving data: {e}")
            return False
    
    def export_to_csv(self, data):
        """Export temperature data to CSV format"""
        try:
            # Prepare temperature data
            temp_records = []
            for temp in data['temperatures']:
                temp_date = datetime.fromisoformat(temp['datetime']).date()
                temp_records.append({
                    'Date': temp_date.strftime('%d/%m/%Y'),
                    'Time': temp['time'],
                    'Temperature_Celsius': round(temp['temperature_celsius'], 2),
                    'Temperature_Fahrenheit': round(temp['temperature_celsius'] * 9/5 + 32, 2)
                })
            
            # Add cycle information
            for i, temp_record in enumerate(temp_records):
                temp_date = datetime.strptime(temp_record['Date'], '%d/%m/%Y').date()
                
                # Find cycle day
                cycle_day = self._get_cycle_day_for_date(temp_date, data['cycle_starts'])
                temp_record['Cycle_Day'] = cycle_day
                
                # Find notes for this date
                notes_for_date = [note for note in data['notes'] 
                                if datetime.fromisoformat(note['date']).date() == temp_date]
                
                temp_record['Notes'] = '; '.join([f"{note['category']}: {note['text']}" 
                                                for note in notes_for_date])
                
                # Check for sex notes
                has_sex = any(note['category'] == 'Sex' for note in notes_for_date)
                temp_record['Sex'] = 'Yes' if has_sex else 'No'
            
            # Convert to DataFrame and then to CSV
            df = pd.DataFrame(temp_records)
            return df.to_csv(index=False)
            
        except Exception as e:
            st.error(f"Error exporting data: {e}")
            return ""
    
    def _get_cycle_day_for_date(self, target_date, cycle_starts):
        """Calculate cycle day for a given date"""
        if not cycle_starts:
            return None
        
        # Convert cycle starts to date objects and sort
        cycle_dates = [datetime.fromisoformat(cs).date() for cs in cycle_starts]
        cycle_dates.sort()
        
        # Find the most recent cycle start before or on the target date
        current_cycle_start = None
        for cycle_date in cycle_dates:
            if cycle_date <= target_date:
                current_cycle_start = cycle_date
            else:
                break
        
        if current_cycle_start:
            return (target_date - current_cycle_start).days + 1
        else:
            return None
    
    def cleanup_old_data(self, data, retention_days=730):  # 2 years
        """Remove data older than retention period"""
        try:
            cutoff_date = datetime.now().date() - timedelta(days=retention_days)
            
            # Clean temperatures
            data['temperatures'] = [
                temp for temp in data['temperatures']
                if datetime.fromisoformat(temp['datetime']).date() >= cutoff_date
            ]
            
            # Clean notes
            data['notes'] = [
                note for note in data['notes']
                if datetime.fromisoformat(note['date']).date() >= cutoff_date
            ]
            
            # Clean cycle starts
            data['cycle_starts'] = [
                cs for cs in data['cycle_starts']
                if datetime.fromisoformat(cs).date() >= cutoff_date
            ]
            
            self.save_data(data)
            return True
            
        except Exception as e:
            st.error(f"Error cleaning up old data: {e}")
            return False
