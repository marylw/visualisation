import pandas as pd
from PIL import Image

mobile_sensors = pd.read_csv("MC2\data\MobileSensorReadings.csv")
static_sensors = pd.read_csv("MC2\data\StaticSensorReadings.csv")
static_sensors_locations = pd.read_csv("MC2\data\StaticSensorLocations.csv")
img = Image.open("MC2\data\StHimarkNeighborhoodMap.png")

static_sensors['Timestamp'] = pd.to_datetime(static_sensors['Timestamp'])
mobile_sensors['Timestamp'] = pd.to_datetime(mobile_sensors['Timestamp'])

static_sensors = pd.merge(static_sensors, static_sensors_locations, on='Sensor-id', how='left')

# Delete values below zero in static_sensors
static_sensors.loc[static_sensors['Value'] <= 0, 'Value'] = 0

# Delete extreme outlier in mobile_sensors
mobile_sensors.drop(index = mobile_sensors[mobile_sensors['Value'] == mobile_sensors['Value'].max()].index, inplace = True)

