import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from PIL import Image
import plotly.graph_objects as go
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from scipy.interpolate import griddata
import numpy as np
from geopy.distance import geodesic

# PREPROCESSING
mobile_sensors = pd.read_csv("Data\MobileSensorReadings.csv")
static_sensors = pd.read_csv("Data\StaticSensorReadings.csv")
static_sensors_locations = pd.read_csv("Data\StaticSensorLocations.csv")
img = Image.open("Data\StHimarkNeighborhoodMap.png")

# Fix timestamps in data
static_sensors['Timestamp'] = pd.to_datetime(static_sensors['Timestamp'])
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
mobile_sensors['Timestamp'] = pd.to_datetime(mobile_sensors['Timestamp'])
mobile_sensors['Minute'] = mobile_sensors['Timestamp'].dt.floor('min')
mobile_sensors['Hour'] = mobile_sensors['Timestamp'].dt.floor('h')

mobile_sensors_min = mobile_sensors.groupby(['Sensor-id', 'Minute', 'Long', 'Lat'])['Value'].max().reset_index()
mobile_sensors_hour = mobile_sensors.groupby(['Sensor-id', 'Hour', 'Long', 'Lat'])['Value'].max().reset_index()

# Function to rename values to danger categories
def classify_radiation(cpm):
    if cpm <= 100:
        return 1
    elif cpm <= 1000:
        return 2
    elif cpm <= 10000:
        return 3
    elif cpm <= 100000:
        return 4
    else:
        return 5

# Add radiation level 1 - 5 to data
static_sensors_hour['Radiation_Level'] = static_sensors_hour['Value'].apply(classify_radiation)
static_sensors_min['Radiation_Level'] = static_sensors_min['Value'].apply(classify_radiation)
static_sensors['Radiation_Level'] = static_sensors['Value'].apply(classify_radiation)
mobile_sensors_hour['Radiation_Level'] = mobile_sensors_hour['Value'].apply(classify_radiation)
mobile_sensors_min['Radiation_Level'] = mobile_sensors_min['Value'].apply(classify_radiation)
mobile_sensors['Radiation_Level'] = mobile_sensors['Value'].apply(classify_radiation)

# CHECK MEASUREMENTS MOBILE SENSORS AGAINST STATIC SENSORS
# Constants
earth_radius_km = 6371.0
distance_threshold_km = 0.2
distance_threshold_rad = distance_threshold_km / earth_radius_km
difference_threshold = 100  # in cpm

# Group static and mobile sensor data by minute
static_groups = static_sensors_min.groupby('Minute')
mobile_groups = mobile_sensors_min.groupby('Minute')

mismatched_sensors = []
mobile_with_proximity = set()  # track sensors near any static sensor

for minute, mobile_minute_df in mobile_groups:
    if minute not in static_groups.groups:
        continue

    static_minute_df = static_groups.get_group(minute)
    if static_minute_df.empty:
        continue

    # Coordinates in radians
    static_coords_rad = np.deg2rad(static_minute_df[['Lat', 'Long']].values)
    mobile_coords_rad = np.deg2rad(mobile_minute_df[['Lat', 'Long']].values)

    # Build BallTree
    tree = BallTree(static_coords_rad, metric='haversine')

    # Query radius
    neighbors_indices = tree.query_radius(mobile_coords_rad, r=distance_threshold_rad)

    for i, indices in enumerate(neighbors_indices):
        if len(indices) == 0:
            continue

        # Track sensor that was near any static sensor
        mobile_sensor_id = mobile_minute_df.iloc[i]['Sensor-id']
        mobile_with_proximity.add(mobile_sensor_id)

        # Compute difference
        mobile_val = mobile_minute_df.iloc[i]['Value']
        static_vals = static_minute_df.iloc[indices]['Value'].values
        mean_static = static_vals.mean()
        diff = abs(mean_static - mobile_val)

        if diff > difference_threshold:
            mismatched_sensors.append({
                'MobileSensorID': mobile_sensor_id,
                'Minute': minute,
                'Lat': mobile_minute_df.iloc[i]['Lat'],
                'Long': mobile_minute_df.iloc[i]['Long'],
                'MobileValue': mobile_val,
                'MeanStaticValue': mean_static,
                'Difference': diff
            })

# Final DataFrame of mismatches
mismatched_df = pd.DataFrame(mismatched_sensors)

# Show 0 for avg difference of  mobile sensors that did visit static sensor but had no notable difference, show nan for never having visited static sensor
# Summarize mismatching sensors
if not mismatched_df.empty:
    mismatch_summary = (
        mismatched_df
        .groupby('MobileSensorID')['Difference']
        .agg(NumMismatches='count', AvgDifference='mean')
        .reset_index()
    )
else:
    mismatch_summary = pd.DataFrame(columns=['MobileSensorID', 'NumMismatches', 'AvgDifference'])

# Get all mobile sensor IDs
all_mobile_ids = mobile_sensors_min['Sensor-id'].unique()

# At the top of your loop logic:
mobile_with_proximity = set()

# Inside the BallTree loop, after checking if len(indices) > 0:
mobile_with_proximity.add(mobile_minute_df.iloc[i]['Sensor-id'])

# Step 4: Build full summary
matched_ids = set(mismatch_summary['MobileSensorID'])
all_ids = set(all_mobile_ids)

# Sensors near static sensors but no mismatches
good_match_ids = mobile_with_proximity - matched_ids
good_matches = pd.DataFrame({
    'MobileSensorID': list(good_match_ids),
    'NumMismatches': 0,
    'AvgDifference': 0
})

# Sensors never near static sensors
never_near_ids = all_ids - mobile_with_proximity
never_near = pd.DataFrame({
    'MobileSensorID': list(never_near_ids),
    'NumMismatches': 0,
    'AvgDifference': np.nan
})

# Combine all summaries
sensor_summary_full = pd.concat([mismatch_summary, good_matches, never_near], ignore_index=True)
sensor_summary_full = sensor_summary_full.sort_values(by='MobileSensorID', ascending=True)

# Show result
print(sensor_summary_full)
print(mismatch_summary)