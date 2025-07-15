# TCW TempTrack

A comprehensive basal body temperature tracking application for fertility awareness and personal health monitoring.

## Features

- **Temperature Tracking**: Daily basal body temperature logging with Celsius/Fahrenheit support
- **Cycle Management**: Track menstrual cycle starts and phases
- **Visual Analysis**: Interactive color-coded graphs showing cycle phases
- **Phase Tracking**: Automatic detection of Menstrual, Follicular, Ovulatory, and Luteal phases
- **Notes System**: Add categorized notes (Symptoms, Mood, Sex, Medication, Other)
- **Data Management**: Edit and delete entries, CSV export, 2-year data retention
- **Predictions**: Cycle length analysis and next period/ovulation predictions

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run app.py
```

## Deployment on Streamlit Cloud

This app is ready for deployment on Streamlit Cloud via GitHub.

## Data Storage

The application uses local JSON file storage (`temptrack_data.json`) for data persistence. Your data remains private and local to your deployment.

## Privacy

All temperature and cycle data is stored locally. No data is transmitted to external services.