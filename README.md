# Open-Meteo Data Pipeline

A lightweight, containerized ETL (Extract, Transform, Load) pipeline that fetches real-time weather data from the Open-Meteo API and stores it in a local PostgreSQL database.

This project is built to run continuously as a background data job, pulling rich weather metrics for a specific geographic location every 15 minutes.

The database was tested, connected to pgAdmin4 for queries and administration and connected to Metabase for visualizing the data.

## Project Structure
```
open-meteo-data-pipeline/
├── app/
│   ├── Dockerfile            
│   ├── etl.py               # Main ETL script 
│   └── requirements.txt     # Python dependencies 
├── docker/
│   ├── compose.yaml         # Docker Compose configuration
│   └── env.example          # Template for environment variables
└── images/
    └── dashboard.png        # Example visualization of the data
```

## How it works
1. Database Initialization: On startup, the script connects to PostgreSQL and ensures the weather_data table exists.
2. Extraction: Polls the Open-Meteo API for current weather conditions at the configured coordinates.
3. Transformation: Uses Pandas to process the JSON response into a flat structure.
4. Loading: Inserts the data into PostgreSQL. It uses primary keys to ignore duplicate data points if the pipeline restarts or overlaps.
5. Scheduling: The script sleeps for 15 minutes before executing the next run. (Better orchestration coming soon)

## Idempotency & Data Integrity
The pipeline is designed to be "crash-proof." It can be restarted multiple times without corrupting the dataset:
* **Duplicate Handling:** The ETL script catches `SQLAlchemy.exc.IntegrityError` (UniqueConstraint violations). If a record for a specific timestamp already exists, it is gracefully skipped.
* **Self-Healing Schema:** The `init_db` module checks for the table's existence on startup. If missing, it automatically generates the schema with all 10+ metric columns.
* **Smart Retries:** Implements connection backoff logic to wait for the database container to become ready before attempting execution.

## Data Schema
The pipeline collects the following rich metrics:

* timestamp (Primary Key)
* latitude
* longitude
* temperature_c
* apparent_temp_c
* humidity
* wind_speed_kmh
* pressure_hpa
* precipitation_mm
* cloud_cover
* weather_code

## Deployment

### Prerequisites
* Docker & Docker Compose

### 1. Configure the environment
Clone the repository, navigate to the docker directory and copy the example environment file to create your own .env file:
```bash
git clone [https://github.com/devetzik/open-meteo-data-pipeline.git](https://github.com/devetzik/open-meteo-data-pipeline.git)
cd open-meteo-data-pipeline
cd docker
cp env.example .env
```
Open .env and configure your settings. You can set the target location by updating the decimal coordinates LATITUDE and LONGITUDE. Ensure the BUILD_PATH and VOLUME_PATH correctly point to ../app and ../postgres_data respectively.

### 2. Run the pipeline
Build and run the stack:
```
docker compose up -d --build
```
During the build phase, the Dockerfile will install the required Python packages cleanly to keep the image size small. The etl.py script will automatically start running.
