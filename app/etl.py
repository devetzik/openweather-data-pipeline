import requests
import pandas as pd
from sqlalchemy import create_engine, text
import time
import os
import sys
from sqlalchemy.exc import IntegrityError

# Configuration
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
LATITUDE = os.getenv('LATITUDE')
LONGITUDE = os.getenv('LONGITUDE')

if not all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
    print("Error: Missing database credentials in environment variables.")
    sys.exit(1)

# Database Connection URI
DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}'


# Retry logic for database connection
def get_engine():
    while True:      
        try:
            engine = create_engine(DATABASE_URI)
            # Test connection
            with engine.connect() as conn:
                pass
            print("Connected to Database!")
            return engine
        except Exception as e:
            print(f"Database not ready yet. Retrying in 5 seconds... Error: {e}")
            time.sleep(5)


#Create the table if it doesn't exist
def init_db(engine):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS weather_data (
        timestamp TIMESTAMP PRIMARY KEY,
        latitude FLOAT,
        longitude FLOAT,
        temperature_c FLOAT,
        humidity INT,
        weather_code INT,
        apparent_temp_c FLOAT,
        wind_speed_kmh FLOAT,
        pressure_hpa FLOAT,
        precipitation_mm FLOAT,
        cloud_cover INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with engine.connect() as conn:
        conn.execute(text(create_table_query))
        conn.commit()
    print("Table initialized.")

def run_pipeline(engine):
    print("Running ETL job...")
    try:
        # 1. EXTRACT
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,cloud_cover,pressure_msl,wind_speed_10m",
            "timezone": "Europe/Athens"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data['current']
        
        # 2. TRANSFORM
        record = {
            "timestamp": pd.to_datetime(current['time']),
            "latitude": data['latitude'],
            "longitude": data['longitude'],
            "temperature_c": current['temperature_2m'],
            "humidity": current['relative_humidity_2m'],
            "weather_code": current['weather_code'],
            "apparent_temp_c": current['apparent_temperature'],
            "wind_speed_kmh": current['wind_speed_10m'],
            "pressure_hpa": current['pressure_msl'],
            "precipitation_mm": current['precipitation'],
            "cloud_cover": current['cloud_cover']
        }
        
        df = pd.DataFrame([record])
        
        # 3. LOAD (The Robust Way)
        try:
            df.to_sql('weather_data', engine, if_exists='append', index=False)
            print(f"SUCCESS: Loaded data for {record['timestamp']}")
        except IntegrityError:
            print(f"INFO: Data for {record['timestamp']} already exists. Skipping duplicate.")
        
    except Exception as e:
        print(f"FAILURE: Pipeline error: {e}")

if __name__ == "__main__":
    # Force prints to flush immediately to logs
    sys.stdout.reconfigure(line_buffering=True)
    
    # Get DB connection (will block until DB is ready)
    db_engine = get_engine()
    
    # Initialize Table
    init_db(db_engine)
    
    # Scheduler Loop
    while True:
        run_pipeline(db_engine)
        print("Sleeping for 15 minutes...")
        time.sleep(900)