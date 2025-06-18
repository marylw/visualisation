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
from load_data import static_sensors, mobile_sensors, static_sensors_hour, static_sensors_min, mobile_sensors_hour, mobile_sensors_min

# Function to rename values to radiation categories
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



# Compare measurements of mobile and static sensors that are closeby
# Constants
earth_radius_km = 6371.0
distance_threshold_km = 0.2
distance_threshold_rad = distance_threshold_km / earth_radius_km
difference_threshold = 100  # in cpm

# Group static and mobile sensor data by minute
static_groups = static_sensors_min.groupby('Minute')
mobile_groups = mobile_sensors_min.groupby('Minute')

mismatched_sensors = []
mobile_with_proximity = set()  

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

# Build full summary
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