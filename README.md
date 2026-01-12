# 🌦️ End-to-End Weather ETL Pipeline (Home Lab)

A robust, containerized ETL pipeline running on **TrueNAS Scale**. It extracts real-time meteorological data, transforms it for analytics, and loads it into a PostgreSQL data warehouse for visualization.

![Dashboard Preview](images/dashboard.png)
*(A view of the Metabase dashboard tracking temperature, pressure trends, and precipitation)*

## 🎯 Engineering Goal
To engineer a fault-tolerant data pipeline that overcomes the networking isolation limitations of **Docker Macvlan** on Linux hosts, enabling a full "Extract-Load-Visualize" lifecycle for local weather metrics.

## 🏗️ Architecture & Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Extract** | Python (Requests) | Fetches real-time data from Open-Meteo API. |
| **Transform** | Pandas | Normalizes timestamps, cleans data, and calculates rich metrics (Apparent Temp, Pressure). |
| **Load** | PostgreSQL 15 | Persistent storage with time-series data and idempotent insertion logic. |
| **Infrastructure** | Docker Compose | Multi-container orchestration. |
| **Networking** | Macvlan & Shim | **Custom Host Bridge** for bidirectional communication on TrueNAS. |
| **Visualization** | Metabase | Business Intelligence dashboarding and trend analysis. |

## ⚙️ Key Engineering Challenges

### 1. Network Bridging (The "Shim")
**The Problem:** I utilized the Docker `macvlan` driver to give my containers dedicated physical LAN IPs (`192.168.1.x`). However, by kernel design, Macvlan interfaces are isolated from the parent host, preventing the TrueNAS host (and the ETL worker) from accessing the database via its storage IP.

**The Solution:** Engineered a custom Shell script (`scripts/shim_setup.sh`) that:
1. Creates a virtual bridge interface (`shim0`) on the host.
2. Manually routes traffic destined for the container IPs through this bridge.
3. Establishes full bidirectional connectivity between the Host and the Macvlan containers.

### 2. Idempotency & Data Integrity
The pipeline is designed to be "crash-proof." It can be restarted multiple times without corrupting the dataset:
* **Duplicate Handling:** The ETL script catches `SQLAlchemy.exc.IntegrityError` (UniqueConstraint violations). If a record for a specific timestamp already exists, it is gracefully skipped.
* **Self-Healing Schema:** The `init_db` module checks for the table's existence on startup. If missing, it automatically generates the schema with all 10+ metric columns.
* **Smart Retries:** Implements connection backoff logic to wait for the database container to become ready before attempting execution.

## 🚀 Deployment

### 1. Prerequisites
* Docker & Docker Compose
* A Linux host (Debian/TrueNAS Scale recommended)
* Network interface availability (e.g., `br0` or `eth0`)

### 2. Installation
Clone the repository:
```bash
git clone [https://github.com/devetzik/weather-pipeline-homelab.git](https://github.com/devetzik/weather-pipeline-homelab.git)
cd weather-pipeline-homelab
```

### 3. Configuration
Create the environment file from the template:
```bash
cp env.example .env
```
Edit the .env file to match your network subnet and target location.

### 4. Launch
Build and run the stack:
```
docker compose up -d --build
```
### 5. Apply Network Shim (Linux/TrueNAS)
If you are running on a host that needs access to the containers, apply the bridge:
```
sudo ./scripts/shim_setup.sh
```

## 📊 Sample Analytics (SQL)
The data schema supports complex analytical queries.

Query: The "Comfort Gap" (Actual vs. RealFeel) Visualizes wind chill effects by comparing temperature_c with apparent_temp_c.
```
SELECT 
    timestamp, 
    temperature_c as "Actual", 
    apparent_temp_c as "Feels Like" 
FROM weather_data 
WHERE timestamp > NOW() - INTERVAL '48 hours'
ORDER BY timestamp ASC;
```

Query: Storm Prediction (Pressure Drop) Rapid drops in pressure_hpa indicate approaching storm fronts.
```
SELECT timestamp, pressure_hpa 
FROM weather_data 
WHERE timestamp > NOW() - INTERVAL '3 days';
```


