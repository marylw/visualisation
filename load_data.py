import pandas as pd
from PIL import Image
import os
import joblib

mobile_sensors = pd.read_csv("MC2\data\MobileSensorReadings.csv")
static_sensors = pd.read_csv("MC2\data\StaticSensorReadings.csv")
static_sensors_locations = pd.read_csv("MC2\data\StaticSensorLocations.csv")
img = Image.open("MC2\data\StHimarkNeighborhoodMap.png")
demographics = pd.read_csv("MC2\data\st_himark_neighborhood_data.csv")

static_sensors['Timestamp'] = pd.to_datetime(static_sensors['Timestamp'])
mobile_sensors['Timestamp'] = pd.to_datetime(mobile_sensors['Timestamp'])

static_sensors = pd.merge(static_sensors, static_sensors_locations, on='Sensor-id', how='left')

# Delete values below zero in static_sensors
static_sensors.loc[static_sensors['Value'] <= 0, 'Value'] = 0

# Delete extreme outlier in mobile_sensors
mobile_sensors.drop(index = mobile_sensors[mobile_sensors['Value'] == mobile_sensors['Value'].max()].index, inplace = True)

# Add minute and hour columns
static_sensors['Minute'] = static_sensors['Timestamp'].dt.floor('min')
static_sensors['Hour'] = static_sensors['Timestamp'].dt.floor('h')

# Take max value per min/hour to get smaller datasets
static_sensors_min = static_sensors.groupby(['Sensor-id', 'Minute'])['Value'].max().reset_index()
static_sensors_hour = static_sensors.groupby(['Sensor-id', 'Hour'])['Value'].max().reset_index()

# Add locations to static sensor data
static_sensors_hour = pd.merge(static_sensors_hour, static_sensors_locations, on='Sensor-id', how='left')
static_sensors_min = pd.merge(static_sensors_min, static_sensors_locations, on='Sensor-id', how='left')
static_sensors = pd.merge(static_sensors, static_sensors_locations, on='Sensor-id', how='left')

# Delete values below zero
static_sensors_hour.loc[static_sensors_hour['Value'] <= 0, 'Value'] = 0
static_sensors_min.loc[static_sensors_min['Value'] <= 0, 'Value'] = 0
static_sensors.loc[static_sensors['Value'] <= 0, 'Value'] = 0

# Do same for mobile sensers
mobile_sensors['Minute'] = mobile_sensors['Timestamp'].dt.floor('min')
mobile_sensors['Hour'] = mobile_sensors['Timestamp'].dt.floor('h')

mobile_sensors_min = mobile_sensors.groupby(['Sensor-id', 'Minute', 'Long', 'Lat'])['Value'].max().reset_index()
mobile_sensors_hour = mobile_sensors.groupby(['Sensor-id', 'Hour', 'Long', 'Lat'])['Value'].max().reset_index()


CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_load_or_compute(filename, compute_fn):
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        print(f"Loading cached {filename}")
        return joblib.load(path)
    else:
        print(f"Computing and caching {filename}")
        obj = compute_fn()
        joblib.dump(obj, path)
        return obj
