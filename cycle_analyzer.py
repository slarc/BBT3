import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import statistics

class CycleAnalyzer:
    def __init__(self):
        self.phase_colors = {
            'Menstrual': '#FF6B6B',
            'Follicular': '#4ECDC4', 
            'Ovulatory': '#45B7D1',
            'Luteal': '#96CEB4'
        }
    
    def get_current_cycle_info(self, data: Dict) -> Optional[Dict]:
        """Get information about the current cycle"""
        if not data['cycle_starts']:
            return None
        
        today = date.today()
        
        # Find the most recent cycle start
        cycle_starts = [datetime.fromisoformat(cs).date() for cs in data['cycle_starts']]
        cycle_starts.sort(reverse=True)
        
        current_cycle_start = None
        for cycle_start in cycle_starts:
            if cycle_start <= today:
                current_cycle_start = cycle_start
                break
        
        if not current_cycle_start:
            return None
        
        cycle_day = (today - current_cycle_start).days + 1
        phase = self._determine_cycle_phase(cycle_day, data)
        
        return {
            'cycle_day': cycle_day,
            'phase': phase,
            'cycle_start': current_cycle_start
        }
    
    def _determine_cycle_phase(self, cycle_day: int, data: Dict) -> str:
        """Determine cycle phase based on cycle day and temperature data"""
        # Standard phase determination
        if cycle_day <= 5:
            return 'Menstrual'
        elif cycle_day <= 12:
            return 'Follicular'
        elif cycle_day <= 16:
            return 'Ovulatory'
        else:
            return 'Luteal'
    
    def calculate_temperature_shift(self, data: Dict) -> Optional[Dict]:
        """Calculate temperature shift from follicular to luteal phase"""
        if len(data['temperatures']) < 10:  # Need sufficient data
            return None
        
        try:
            # Get recent cycle data
            recent_temps = self._get_recent_cycle_temperatures(data)
            if len(recent_temps) < 10:
                return None
            
            # Separate follicular and luteal phase temperatures
            follicular_temps = []
            luteal_temps = []
            
            for temp_record in recent_temps:
                temp_date = datetime.fromisoformat(temp_record['datetime']).date()
                cycle_day = self._get_cycle_day_for_date(temp_date, data['cycle_starts'])
                
                if cycle_day:
                    if 6 <= cycle_day <= 12:  # Follicular phase
                        follicular_temps.append(temp_record['temperature_celsius'])
                    elif cycle_day >= 17:  # Luteal phase
                        luteal_temps.append(temp_record['temperature_celsius'])
            
            if len(follicular_temps) >= 3 and len(luteal_temps) >= 3:
                follicular_avg = statistics.mean(follicular_temps)
                luteal_avg = statistics.mean(luteal_temps)
                shift = luteal_avg - follicular_avg
                
                return {
                    'follicular_avg': follicular_avg,
                    'luteal_avg': luteal_avg,
                    'shift_celsius': shift,
                    'shift_fahrenheit': shift * 9/5
                }
        
        except Exception:
            pass
        
        return None
    
    def predict_cycle_events(self, data: Dict) -> Dict:
        """Predict next period and ovulation based on historical data"""
        predictions = {
            'next_period': None,
            'next_ovulation': None,
            'confidence': 'low'
        }
        
        if len(data['cycle_starts']) < 2:
            return predictions
        
        try:
            # Calculate average cycle length
            cycle_lengths = self._calculate_cycle_lengths(data['cycle_starts'])
            
            if cycle_lengths:
                avg_cycle_length = statistics.mean(cycle_lengths)
                
                # Get last cycle start
                last_cycle_start = max([datetime.fromisoformat(cs).date() 
                                      for cs in data['cycle_starts']])
                
                # Predict next period
                next_period = last_cycle_start + timedelta(days=int(avg_cycle_length))
                
                # Predict next ovulation (typically 12-16 days before next period)
                next_ovulation = next_period - timedelta(days=14)
                
                predictions['next_period'] = next_period
                predictions['next_ovulation'] = next_ovulation
                predictions['confidence'] = 'high' if len(cycle_lengths) >= 3 else 'medium'
        
        except Exception:
            pass
        
        return predictions
    
    def calculate_cycle_statistics(self, data: Dict) -> Optional[Dict]:
        """Calculate comprehensive cycle statistics"""
        if len(data['cycle_starts']) < 2:
            return None
        
        try:
            cycle_lengths = self._calculate_cycle_lengths(data['cycle_starts'])
            
            if not cycle_lengths:
                return None
            
            # Temperature shift data
            temp_shift = self.calculate_temperature_shift(data)
            
            stats = {
                'avg_cycle_length': statistics.mean(cycle_lengths),
                'cycle_length_std': statistics.stdev(cycle_lengths) if len(cycle_lengths) > 1 else 0,
                'min_cycle_length': min(cycle_lengths),
                'max_cycle_length': max(cycle_lengths),
                'avg_follicular_phase': 14,  # Standard approximation
                'avg_luteal_phase': 14,      # Standard approximation
                'avg_temp_shift': temp_shift['shift_celsius'] if temp_shift else 0
            }
            
            return stats
            
        except Exception:
            return None
    
    def calculate_temperature_statistics(self, data: Dict) -> Optional[Dict]:
        """Calculate temperature statistics"""
        if not data['temperatures']:
            return None
        
        try:
            temps = [temp['temperature_celsius'] for temp in data['temperatures']]
            
            return {
                'avg_temp': statistics.mean(temps),
                'min_temp': min(temps),
                'max_temp': max(temps),
                'temp_std': statistics.stdev(temps) if len(temps) > 1 else 0
            }
            
        except Exception:
            return None
    
    def get_phase_distribution(self, data: Dict) -> Optional[Dict]:
        """Get distribution of days spent in each phase"""
        if not data['temperatures'] or not data['cycle_starts']:
            return None
        
        try:
            phase_counts = {'Menstrual': 0, 'Follicular': 0, 'Ovulatory': 0, 'Luteal': 0}
            
            for temp_record in data['temperatures']:
                temp_date = datetime.fromisoformat(temp_record['datetime']).date()
                cycle_day = self._get_cycle_day_for_date(temp_date, data['cycle_starts'])
                
                if cycle_day:
                    phase = self._determine_cycle_phase(cycle_day, data)
                    phase_counts[phase] += 1
            
            return phase_counts
            
        except Exception:
            return None
    
    def analyze_temperature_trends(self, data: Dict) -> Optional[Dict]:
        """Analyze temperature trends and consistency"""
        if len(data['temperatures']) < 7:
            return None
        
        try:
            # Get recent temperatures
            recent_temps = sorted(data['temperatures'], 
                                key=lambda x: x['datetime'])[-30:]  # Last 30 readings
            
            temps = [temp['temperature_celsius'] for temp in recent_temps]
            
            # Calculate trend
            x = list(range(len(temps)))
            slope = np.polyfit(x, temps, 1)[0]
            
            if slope > 0.01:
                trend_direction = "Increasing"
            elif slope < -0.01:
                trend_direction = "Decreasing"
            else:
                trend_direction = "Stable"
            
            # Calculate consistency (lower standard deviation = higher consistency)
            consistency_score = max(0, 10 - (statistics.stdev(temps) * 10))
            
            # Generate analysis text
            if consistency_score >= 8:
                analysis = "Your temperature readings show excellent consistency."
            elif consistency_score >= 6:
                analysis = "Your temperature readings show good consistency."
            elif consistency_score >= 4:
                analysis = "Your temperature readings show moderate consistency."
            else:
                analysis = "Consider taking temperature at the same time daily for better consistency."
            
            return {
                'trend_direction': trend_direction,
                'consistency_score': consistency_score,
                'analysis_text': analysis
            }
            
        except Exception:
            return None
    
    def _calculate_cycle_lengths(self, cycle_starts: List[str]) -> List[int]:
        """Calculate lengths of completed cycles"""
        if len(cycle_starts) < 2:
            return []
        
        cycle_dates = [datetime.fromisoformat(cs).date() for cs in cycle_starts]
        cycle_dates.sort()
        
        lengths = []
        for i in range(len(cycle_dates) - 1):
            length = (cycle_dates[i + 1] - cycle_dates[i]).days
            if 15 <= length <= 45:  # Reasonable cycle length
                lengths.append(length)
        
        return lengths
    
    def _get_recent_cycle_temperatures(self, data: Dict, days: int = 35) -> List[Dict]:
        """Get temperature readings from recent cycle"""
        cutoff_date = date.today() - timedelta(days=days)
        
        return [temp for temp in data['temperatures']
                if datetime.fromisoformat(temp['datetime']).date() >= cutoff_date]
    
    def _get_cycle_day_for_date(self, target_date: date, cycle_starts: List[str]) -> Optional[int]:
        """Get cycle day for a specific date"""
        if not cycle_starts:
            return None
        
        cycle_dates = [datetime.fromisoformat(cs).date() for cs in cycle_starts]
        cycle_dates.sort()
        
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
