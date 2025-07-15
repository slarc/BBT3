import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import streamlit as st

class GraphUtils:
    def __init__(self):
        self.phase_colors = {
            'Menstrual': '#FF6B6B',
            'Follicular': '#4ECDC4',
            'Ovulatory': '#45B7D1', 
            'Luteal': '#96CEB4'
        }
    
    def create_temperature_graph(self, data: Dict, temp_unit: str, zoom_days: int, offset_days: int):
        """Create interactive temperature graph with cycle phases"""
        
        if not data['temperatures']:
            fig = go.Figure()
            fig.add_annotation(
                text="No temperature data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            return fig
        
        # Prepare data
        temp_df = self._prepare_temperature_dataframe(data, temp_unit)
        
        if temp_df.empty:
            return go.Figure()
        
        # Calculate date range for display
        end_date = date.today() + timedelta(days=offset_days)
        start_date = end_date - timedelta(days=zoom_days)
        
        # Filter data for display range
        display_df = temp_df[
            (temp_df['date'] >= start_date) & 
            (temp_df['date'] <= end_date)
        ].copy()
        
        # Create figure
        fig = go.Figure()
        
        # Add temperature line with phase colors
        if not display_df.empty:
            self._add_phase_colored_temperature_line(fig, display_df, data, temp_unit)
        
        # Add cycle phase backgrounds (temporarily disabled for stability)
        # self._add_phase_backgrounds(fig, data, start_date, end_date, display_df)
        
        # Add cycle start markers (temporarily disabled for stability)
        # self._add_cycle_markers(fig, data, start_date, end_date)
        
        # Add note indicators (temporarily disabled for stability)
        # self._add_note_indicators(fig, data, start_date, end_date, display_df)
        
        # Update layout for stable graph display
        y_range = [35.5, 38.0] if temp_unit == "Celsius" else [95.9, 100.4]
        
        fig.update_layout(
            title=dict(
                text=f"Basal Body Temperature ({temp_unit})",
                x=0.5,
                font=dict(size=18)
            ),
            xaxis=dict(
                title="Date",
                range=[start_date, end_date],
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                fixedrange=True,  # Prevents zooming/panning
                tickformat='%d/%m'
            ),
            yaxis=dict(
                title=f"Temperature (°{temp_unit[0]})",
                range=y_range,
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray',
                fixedrange=True,  # Prevents zooming/panning
                tickformat='.1f'
            ),
            hovermode='x unified',
            showlegend=True,
            height=500,
            margin=dict(l=60, r=50, t=60, b=50),
            plot_bgcolor='white',
            paper_bgcolor='white',
            dragmode=False  # Disables dragging
        )
        
        return fig
    
    def _prepare_temperature_dataframe(self, data: Dict, temp_unit: str) -> pd.DataFrame:
        """Prepare temperature data as a DataFrame"""
        if not data['temperatures']:
            return pd.DataFrame()
        
        temp_records = []
        for temp in data['temperatures']:
            temp_celsius = temp['temperature_celsius']
            temp_display = temp_celsius if temp_unit == 'Celsius' else (temp_celsius * 9/5 + 32)
            
            temp_records.append({
                'date': datetime.fromisoformat(temp['datetime']).date(),
                'datetime': datetime.fromisoformat(temp['datetime']),
                'temperature': temp_display,
                'temperature_celsius': temp_celsius
            })
        
        df = pd.DataFrame(temp_records)
        if not df.empty:
            df = df.sort_values('date')
        
        return df
    
    def _add_phase_colored_temperature_line(self, fig, display_df, data: Dict, temp_unit: str):
        """Add temperature line with different colors for each cycle phase"""
        if data['cycle_starts']:
            # Group data points by cycle phase
            phase_groups = {'Menstrual': [], 'Follicular': [], 'Ovulatory': [], 'Luteal': []}
            
            for _, row in display_df.iterrows():
                cycle_day = self._get_cycle_day_for_date(row['date'], 
                    [datetime.fromisoformat(cs).date() for cs in data['cycle_starts']])
                
                if cycle_day:
                    phase = self._determine_cycle_phase(cycle_day)
                    phase_groups[phase].append(row)
            
            # Add separate traces for each phase
            for phase, phase_data in phase_groups.items():
                if phase_data:
                    phase_df = pd.DataFrame(phase_data).sort_values('date')
                    fig.add_trace(go.Scatter(
                        x=phase_df['date'],
                        y=phase_df['temperature'],
                        mode='lines+markers',
                        name=f'{phase} Phase',
                        line=dict(color=self.phase_colors[phase], width=3),
                        marker=dict(size=6, color=self.phase_colors[phase], 
                                  line=dict(width=1, color='white')),
                        hovertemplate=f'%{{x}}<br>%{{y:.1f}}°{temp_unit[0]}<br>{phase} Phase<extra></extra>'
                    ))
        else:
            # No cycle data - use single color
            fig.add_trace(go.Scatter(
                x=display_df['date'],
                y=display_df['temperature'],
                mode='lines+markers',
                name='Temperature',
                line=dict(color='#2E86AB', width=3),
                marker=dict(size=6, color='#2E86AB', line=dict(width=1, color='white')),
                hovertemplate=f'%{{x}}<br>%{{y:.1f}}°{temp_unit[0]}<extra></extra>'
            ))
    
    def _add_phase_backgrounds(self, fig, data: Dict, start_date: date, end_date: date, temp_df):
        """Add colored backgrounds for cycle phases"""
        if not data['cycle_starts']:
            return
        
        cycle_starts = [datetime.fromisoformat(cs).date() for cs in data['cycle_starts']]
        cycle_starts.sort()
        
        # Add a future cycle start for visualization
        if cycle_starts:
            last_cycle = cycle_starts[-1]
            avg_cycle_length = 28  # Default assumption
            
            if len(cycle_starts) > 1:
                lengths = [(cycle_starts[i] - cycle_starts[i-1]).days 
                          for i in range(1, len(cycle_starts))]
                avg_cycle_length = sum(lengths) / len(lengths)
            
            next_cycle = last_cycle + timedelta(days=int(avg_cycle_length))
            cycle_starts.append(next_cycle)
        
        current_date = start_date
        while current_date <= end_date:
            cycle_day = self._get_cycle_day_for_date(current_date, cycle_starts)
            
            if cycle_day:
                phase = self._determine_cycle_phase(cycle_day)
                
                # Find the end of this phase or end of display period
                phase_end = current_date
                for i in range(1, 8):  # Check up to 7 days ahead
                    check_date = current_date + timedelta(days=i)
                    if check_date > end_date:
                        phase_end = end_date
                        break
                    
                    check_cycle_day = self._get_cycle_day_for_date(check_date, cycle_starts)
                    if not check_cycle_day or self._determine_cycle_phase(check_cycle_day) != phase:
                        phase_end = check_date - timedelta(days=1)
                        break
                    phase_end = check_date
                
                # Add phase background
                fig.add_vrect(
                    x0=current_date,
                    x1=phase_end + timedelta(days=1),
                    fillcolor=self.phase_colors[phase],
                    opacity=0.2,
                    layer="below",
                    line_width=0
                )
                
                current_date = phase_end + timedelta(days=1)
            else:
                current_date += timedelta(days=1)
    
    def _add_cycle_markers(self, fig, data: Dict, start_date: date, end_date: date):
        """Add markers for cycle starts"""
        if not data['cycle_starts']:
            return
        
        cycle_starts = [datetime.fromisoformat(cs).date() for cs in data['cycle_starts']]
        
        for cycle_start in cycle_starts:
            if start_date <= cycle_start <= end_date:
                fig.add_vline(
                    x=cycle_start,
                    line_width=3,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Day 1",
                    annotation_position="top"
                )
    
    def _add_note_indicators(self, fig, data: Dict, start_date: date, end_date: date, temp_df):
        """Add indicators for notes on the graph"""
        if not data['notes'] or temp_df.empty:
            return
        
        # Group notes by date
        notes_by_date = {}
        for note in data['notes']:
            note_date = datetime.fromisoformat(note['date']).date()
            if start_date <= note_date <= end_date:
                if note_date not in notes_by_date:
                    notes_by_date[note_date] = []
                notes_by_date[note_date].append(note)
        
        # Add indicators
        for note_date, notes in notes_by_date.items():
            # Find temperature for this date
            temp_row = temp_df[temp_df['date'] == note_date]
            if temp_row.empty:
                continue
            
            temp_value = temp_row.iloc[0]['temperature']
            
            # Check for sex notes
            has_sex = any(note['category'] == 'Sex' for note in notes)
            has_other_notes = len(notes) > (1 if has_sex else 0)
            
            # Add heart icon for sex
            if has_sex:
                fig.add_trace(go.Scatter(
                    x=[note_date],
                    y=[temp_value + 0.15],
                    mode='markers',
                    marker=dict(
                        symbol='heart',
                        size=16,
                        color='#FF1493',
                        line=dict(width=2, color='white')
                    ),
                    name='Sex',
                    showlegend=False,
                    hovertemplate=f'{note_date}<br>💕 Sex noted<extra></extra>'
                ))
            
            # Add star icon for other notes
            if has_other_notes:
                y_offset = 0.05 if not has_sex else -0.1
                fig.add_trace(go.Scatter(
                    x=[note_date],
                    y=[temp_value + y_offset],
                    mode='markers',
                    marker=dict(
                        symbol='star',
                        size=12,
                        color='#FFA500',
                        line=dict(width=1, color='white')
                    ),
                    name='Notes',
                    showlegend=False,
                    hovertemplate=f'{note_date}<br>⭐ Notes available<extra></extra>'
                ))
    
    def _determine_cycle_phase(self, cycle_day: int) -> str:
        """Determine cycle phase based on cycle day"""
        if cycle_day <= 5:
            return 'Menstrual'
        elif cycle_day <= 12:
            return 'Follicular'
        elif cycle_day <= 16:
            return 'Ovulatory'
        else:
            return 'Luteal'
    
    def _get_cycle_day_for_date(self, target_date: date, cycle_starts: List[date]) -> Optional[int]:
        """Get cycle day for a specific date"""
        if not cycle_starts:
            return None
        
        current_cycle_start = None
        for cycle_start in cycle_starts:
            if cycle_start <= target_date:
                current_cycle_start = cycle_start
            else:
                break
        
        if current_cycle_start:
            return (target_date - current_cycle_start).days + 1
        else:
            return None
