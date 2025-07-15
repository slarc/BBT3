import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import json
import os
from data_manager import DataManager
from sqlite_storage import SQLiteStorage
from cycle_analyzer import CycleAnalyzer
from graph_utils import GraphUtils

# Page configuration
st.set_page_config(
    page_title="TCW TempTrack",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize data manager and cycle analyzer
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = SQLiteStorage()
    
if 'cycle_analyzer' not in st.session_state:
    st.session_state.cycle_analyzer = CycleAnalyzer()

if 'graph_utils' not in st.session_state:
    st.session_state.graph_utils = GraphUtils()

# Initialize session state variables
if 'temp_unit' not in st.session_state:
    st.session_state.temp_unit = 'Celsius'

if 'graph_zoom_level' not in st.session_state:
    st.session_state.graph_zoom_level = 30  # days

if 'graph_offset' not in st.session_state:
    st.session_state.graph_offset = 0

def main():
    st.title("🌡️ TCW TempTrack")
    st.markdown("*Comprehensive Basal Body Temperature Tracking*")
    
    # Load existing data
    data = st.session_state.data_manager.load_data()
    
    # Show data persistence status
    data_size = st.session_state.data_manager.get_data_size()
    with st.sidebar:
        st.metric("📊 Data Points", 
                 f"{data_size['temperatures']} temps, {data_size['notes']} notes")
        
        # Data persistence indicator
        if os.path.exists("temptrack.db"):
            st.success("✅ Data saved in database")
        else:
            st.info("💾 Creating database...")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "➕ Add Entry", "📝 Notes", "📈 Analysis"])
    
    with tab1:
        show_dashboard(data)
    
    with tab2:
        show_temperature_input()
    
    with tab3:
        show_notes_section(data)
    
    with tab4:
        show_analysis_section(data)

def show_dashboard(data):
    """Display the main dashboard with temperature graph and cycle info"""
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Temperature Chart")
        
        # Graph controls
        control_col1, control_col2, control_col3, control_col4, control_col5, control_col6 = st.columns(6)
        
        with control_col1:
            if st.button("⬅️ Previous Week"):
                st.session_state.graph_offset -= 7
                st.rerun()
        
        with control_col2:
            if st.button("➡️ Next Week"):
                st.session_state.graph_offset += 7
                st.rerun()
        
        with control_col3:
            if st.button("🔍 Zoom In"):
                if st.session_state.graph_zoom_level > 7:
                    st.session_state.graph_zoom_level -= 7
                    st.rerun()
        
        with control_col4:
            if st.button("🔍 Zoom Out"):
                if st.session_state.graph_zoom_level < 90:
                    st.session_state.graph_zoom_level += 7
                    st.rerun()
        
        with control_col5:
            if st.button("📊 Last Week"):
                st.session_state.graph_zoom_level = 7
                st.session_state.graph_offset = -7
                st.rerun()
        
        with control_col6:
            if st.button("🏠 Today"):
                st.session_state.graph_offset = 0
                st.session_state.graph_zoom_level = 30
                st.rerun()
        
        # Display current view info
        end_date = date.today() + timedelta(days=st.session_state.graph_offset)
        start_date = end_date - timedelta(days=st.session_state.graph_zoom_level)
        st.caption(f"Showing {st.session_state.graph_zoom_level} days: {start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}")
        
        # Generate and display the temperature graph
        if data['temperatures']:
            fig = st.session_state.graph_utils.create_temperature_graph(
                data, 
                st.session_state.temp_unit,
                st.session_state.graph_zoom_level,
                st.session_state.graph_offset
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No temperature data available. Add your first temperature reading in the 'Add Entry' tab.")
    
    with col2:
        st.subheader("Cycle Information")
        
        # Current cycle info
        current_cycle = st.session_state.cycle_analyzer.get_current_cycle_info(data)
        
        if current_cycle:
            st.metric("Current Cycle Day", current_cycle['cycle_day'])
            st.metric("Current Phase", current_cycle['phase'])
            
            # Temperature shift info
            temp_shift = st.session_state.cycle_analyzer.calculate_temperature_shift(data)
            if temp_shift:
                shift_celsius = temp_shift['shift_celsius']
                if st.session_state.temp_unit == 'Fahrenheit':
                    shift_display = f"{shift_celsius * 9/5:.2f}°F"
                else:
                    shift_display = f"{shift_celsius:.2f}°C"
                st.metric("Temp Shift (Follicular → Luteal)", shift_display)
        
        # Predictions
        st.subheader("Predictions")
        predictions = st.session_state.cycle_analyzer.predict_cycle_events(data)
        
        if predictions['next_period']:
            days_until = (predictions['next_period'] - date.today()).days
            st.metric("Next Period", f"{days_until} days")
        
        if predictions['next_ovulation']:
            days_until = (predictions['next_ovulation'] - date.today()).days
            st.metric("Next Ovulation", f"{days_until} days")
        
        # Cycle Management
        st.subheader("Cycle Management")
        
        # Add new cycle button
        if st.button("🔴 Start New Cycle", type="primary"):
            today = date.today()
            data['cycle_starts'].append(today.isoformat())
            st.session_state.data_manager.save_data(data)
            st.success(f"New cycle started on {today.strftime('%d/%m/%Y')}")
            st.rerun()
        
        # Show existing cycle starts with delete option
        if data['cycle_starts']:
            st.write("**Recent Cycle Starts:**")
            cycle_starts = sorted(data['cycle_starts'], reverse=True)[:3]  # Show last 3
            
            for i, cycle_start in enumerate(cycle_starts):
                cycle_date = datetime.fromisoformat(cycle_start).date()
                col_cycle, col_delete = st.columns([4, 1])
                with col_cycle:
                    st.write(f"Day 1: {cycle_date.strftime('%d/%m/%Y')}")
                with col_delete:
                    if st.button("🗑️", key=f"delete_dashboard_cycle_{i}", help="Delete this cycle start"):
                        data['cycle_starts'].remove(cycle_start)
                        st.session_state.data_manager.save_data(data)
                        st.success("Cycle start deleted")
                        st.rerun()
        
        # Recent Temperature Readings
        st.subheader("Recent Readings")
        
        if data['temperatures']:
            # Show last 5 temperature readings
            recent_temps = sorted(data['temperatures'], key=lambda x: x['datetime'], reverse=True)[:5]
            
            for i, temp in enumerate(recent_temps):
                temp_date = datetime.fromisoformat(temp['datetime']).date()
                temp_display = temp['temperature_celsius']
                if st.session_state.temp_unit == 'Fahrenheit':
                    temp_display = temp_display * 9/5 + 32
                
                col_temp, col_delete = st.columns([4, 1])
                with col_temp:
                    st.write(f"{temp_date.strftime('%d/%m/%Y')}: {temp_display:.1f}°{st.session_state.temp_unit[0]}")
                with col_delete:
                    if st.button("🗑️", key=f"delete_temp_{i}", help="Delete this reading"):
                        data['temperatures'].remove(temp)
                        st.session_state.data_manager.save_data(data)
                        st.success("Temperature reading deleted")
                        st.rerun()
        else:
            st.info("No temperature readings yet")
        
        # Recent Notes
        st.subheader("Recent Notes")
        
        if data['notes']:
            # Show last 3 notes
            recent_notes = sorted(data['notes'], key=lambda x: x['date'], reverse=True)[:3]
            
            for i, note in enumerate(recent_notes):
                note_date = datetime.fromisoformat(note['date']).date()
                col_note, col_delete = st.columns([4, 1])
                with col_note:
                    # Category emoji mapping
                    category_emojis = {
                        'Symptoms': '🩺',
                        'Mood': '😊',
                        'Sex': '💕',
                        'Medication': '💊',
                        'Other': '📝'
                    }
                    emoji = category_emojis.get(note['category'], '📝')
                    note_text = note.get('note', note.get('text', 'No text'))
                    st.write(f"{emoji} {note_date.strftime('%d/%m/%Y')}: {note_text}")
                with col_delete:
                    if st.button("🗑️", key=f"delete_dashboard_note_{i}", help="Delete this note"):
                        data['notes'].remove(note)
                        st.session_state.data_manager.save_data(data)
                        st.success("Note deleted")
                        st.rerun()
        else:
            st.info("No notes yet")
        
        # Export functionality
        st.subheader("Export Data")
        if st.button("📥 Export CSV"):
            csv_data = st.session_state.data_manager.export_to_csv(data)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"temptrack_data_{date.today().isoformat()}.csv",
                mime="text/csv"
            )

def show_temperature_input():
    """Show temperature input form"""
    st.subheader("Add Temperature Reading")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Temperature unit toggle
        temp_unit = st.radio("Temperature Unit", ["Celsius", "Fahrenheit"], 
                           index=0 if st.session_state.temp_unit == 'Celsius' else 1)
        st.session_state.temp_unit = temp_unit
        
        # Temperature input
        if temp_unit == "Celsius":
            temp_value = st.number_input("Temperature (°C)", min_value=30.0, max_value=45.0, 
                                       value=36.5, step=0.1, format="%.1f")
        else:
            temp_value = st.number_input("Temperature (°F)", min_value=86.0, max_value=113.0, 
                                       value=97.7, step=0.1, format="%.1f")
    
    with col2:
        # Date input
        input_date = st.date_input("Date", value=date.today(), format="DD/MM/YYYY")
        
        # Time input (auto-set to current time)
        input_time = st.time_input("Time", value=datetime.now().time())
    
    # Combine date and time
    input_datetime = datetime.combine(input_date, input_time)
    
    if st.button("Add Temperature Reading", type="primary"):
        # Convert to Celsius for storage
        temp_celsius = temp_value if temp_unit == "Celsius" else (temp_value - 32) * 5/9
        
        data = st.session_state.data_manager.load_data()
        
        # Add temperature reading
        data['temperatures'].append({
            'date': input_date.isoformat(),
            'time': input_time.isoformat(),
            'temperature_celsius': temp_celsius,
            'datetime': input_datetime.isoformat()
        })
        
        # Sort by datetime
        data['temperatures'].sort(key=lambda x: x['datetime'])
        
        st.session_state.data_manager.save_data(data)
        st.success(f"Temperature reading added: {temp_value}°{temp_unit[0]} on {input_date.strftime('%d/%m/%Y')}")
        st.rerun()

def show_notes_section(data):
    """Show notes management section"""
    st.subheader("Daily Notes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Add Note")
        note_date = st.date_input("Date for Note", value=date.today(), format="DD/MM/YYYY")
        note_category = st.selectbox("Category", ["Sex", "Cervical Mucus", "Menstrual", "Other"])
        note_text = st.text_area("Note", placeholder="Enter your note here...")
        
        if st.button("Add Note", type="primary"):
            if note_text.strip():
                data = st.session_state.data_manager.load_data()
                
                data['notes'].append({
                    'date': note_date.isoformat(),
                    'category': note_category,
                    'text': note_text.strip()
                })
                
                st.session_state.data_manager.save_data(data)
                st.success("Note added successfully!")
                st.rerun()
    
    with col2:
        st.markdown("#### Recent Notes")
        
        # Display recent notes
        if data['notes']:
            # Sort notes by date (most recent first)
            sorted_notes = sorted(data['notes'], key=lambda x: x['date'], reverse=True)
            
            for i, note in enumerate(sorted_notes[:10]):  # Show last 10 notes
                note_date_obj = datetime.fromisoformat(note['date']).date()
                
                with st.expander(f"📝 {note['category']} - {note_date_obj.strftime('%d/%m/%Y')}"):
                    st.write(note['text'])
                    if st.button(f"Delete", key=f"delete_notes_section_{i}"):
                        data['notes'].remove(note)
                        st.session_state.data_manager.save_data(data)
                        st.rerun()
        else:
            st.info("No notes added yet.")

def show_analysis_section(data):
    """Show detailed analysis and statistics"""
    st.subheader("Cycle Analysis")
    
    if not data['temperatures']:
        st.info("No temperature data available for analysis.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Cycle Statistics")
        
        # Calculate cycle statistics
        stats = st.session_state.cycle_analyzer.calculate_cycle_statistics(data)
        
        if stats:
            st.metric("Average Cycle Length", f"{stats['avg_cycle_length']:.1f} days")
            st.metric("Average Follicular Phase", f"{stats['avg_follicular_phase']:.1f} days")
            st.metric("Average Luteal Phase", f"{stats['avg_luteal_phase']:.1f} days")
            st.metric("Average Temperature Shift", f"{stats['avg_temp_shift']:.2f}°C")
        
        # Temperature shift analysis
        temp_shift = st.session_state.cycle_analyzer.calculate_temperature_shift(data)
        
        if temp_shift:
            unit_suffix = "°C" if st.session_state.temp_unit == "Celsius" else "°F"
            
            # Display follicular and luteal averages
            follicular_avg = temp_shift['follicular_avg']
            luteal_avg = temp_shift['luteal_avg']
            shift_celsius = temp_shift['shift_celsius']
            
            if st.session_state.temp_unit == "Fahrenheit":
                follicular_avg = follicular_avg * 9/5 + 32
                luteal_avg = luteal_avg * 9/5 + 32
                shift_display = shift_celsius * 9/5
            else:
                shift_display = shift_celsius
            
            st.metric("Follicular Phase Avg", f"{follicular_avg:.2f}{unit_suffix}")
            st.metric("Luteal Phase Avg", f"{luteal_avg:.2f}{unit_suffix}")
            st.metric("Temperature Step", f"+{shift_display:.2f}{unit_suffix}", 
                     delta="Follicular → Luteal shift")
        else:
            st.info("Need more cycle data to calculate temperature shift")
    
    with col2:
        st.markdown("#### Phase Distribution")
        
        # Create phase distribution chart
        phase_data = st.session_state.cycle_analyzer.get_phase_distribution(data)
        
        if phase_data:
            fig_pie = px.pie(
                values=list(phase_data.values()),
                names=list(phase_data.keys()),
                title="Time Spent in Each Phase",
                color_discrete_map={
                    'Menstrual': '#FF6B6B',
                    'Follicular': '#4ECDC4',
                    'Ovulatory': '#45B7D1',
                    'Luteal': '#96CEB4'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # Temperature trend analysis
    st.markdown("#### Temperature Trends")
    trend_analysis = st.session_state.cycle_analyzer.analyze_temperature_trends(data)
    
    if trend_analysis:
        st.write(f"**Trend Direction:** {trend_analysis['trend_direction']}")
        st.write(f"**Consistency Score:** {trend_analysis['consistency_score']:.2f}/10")
        st.write(f"**Analysis:** {trend_analysis['analysis_text']}")

if __name__ == "__main__":
    main()
