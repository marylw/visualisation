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

# Make seperate dataframes to add dummy data (needed for legend in map)
static_sensors_hourD = static_sensors_hour.copy()
static_sensors_minD = static_sensors_min.copy()
static_sensorsD = static_sensors.copy()
mobile_sensors_hourD = mobile_sensors_hour.copy()
mobile_sensors_minD = mobile_sensors_min.copy()
mobile_sensorsD = mobile_sensors.copy()

# add column for color mapping (needed for legend in map)
static_sensors_hourD['DangerLevel'] = static_sensors_hourD['Radiation_Level'].astype(str)
static_sensors_minD['DangerLevel'] = static_sensors_minD['Radiation_Level'].astype(str)
static_sensorsD['DangerLevel'] = static_sensorsD['Radiation_Level'].astype(str)
mobile_sensors_hourD['DangerLevel'] = mobile_sensors_hourD['Radiation_Level'].astype(str)
mobile_sensors_minD['DangerLevel'] = mobile_sensors_minD['Radiation_Level'].astype(str)
mobile_sensorsD['DangerLevel'] = mobile_sensorsD['Radiation_Level'].astype(str)

# add dummy values so that the legend is visible
for i in range(5):
    temp = static_sensors_hourD.head(1).copy()
    temp.loc[0,'DangerLevel'] = str(int(i+1))
    temp.loc[0,'Lat'] = -200
    temp.loc[0,'Long'] = -200
    temp.loc[0,'Sensor-id'] = 0
    static_sensors_hourD = pd.concat([temp, static_sensors_hourD], ignore_index=True)

for i in range(5):
    temp = static_sensors_minD.head(1).copy()
    temp.loc[0,'DangerLevel'] = str(int(i+1))
    temp.loc[0,'Lat'] = -200
    temp.loc[0,'Long'] = -200
    temp.loc[0,'Sensor-id'] = 0
    static_sensors_minD = pd.concat([temp, static_sensors_minD], ignore_index=True)

for i in range(5):
    temp = static_sensorsD.head(1).copy()
    temp.loc[0,'DangerLevel'] = str(int(i+1))
    temp.loc[0,'Lat'] = -200
    temp.loc[0,'Long'] = -200
    temp.loc[0,'Sensor-id'] = 0
    static_sensorsD = pd.concat([temp, static_sensorsD], ignore_index=True)

for i in range(5):
    temp = mobile_sensors_hourD.head(1).copy()
    temp.loc[0,'DangerLevel'] = str(int(i+1))
    temp.loc[0,'Lat'] = -200
    temp.loc[0,'Long'] = -200
    temp.loc[0,'Sensor-id'] = 0
    mobile_sensors_hourD = pd.concat([temp, mobile_sensors_hourD], ignore_index=True)

for i in range(5):
    temp = mobile_sensors_minD.head(1).copy()
    temp.loc[0,'DangerLevel'] = str(int(i+1))
    temp.loc[0,'Lat'] = -200
    temp.loc[0,'Long'] = -200
    temp.loc[0,'Sensor-id'] = 0
    mobile_sensors_minD = pd.concat([temp, mobile_sensors_minD], ignore_index=True)

for i in range(5):
    temp = mobile_sensorsD.head(1).copy()
    temp.loc[0,'DangerLevel'] = str(int(i+1))
    temp.loc[0,'Lat'] = -200
    temp.loc[0,'Long'] = -200
    temp.loc[0,'Sensor-id'] = 0
    mobile_sensorsD = pd.concat([temp, mobile_sensorsD], ignore_index=True)

# CLUSTERING
# For static sensors, per minute
minute_groups = static_sensors_minD.groupby('Minute')
cluster_results = []

for minute, group in minute_groups:
    if group.shape[0] < 3: 
        continue

    X = group[['Lat', 'Long', 'Value']].copy()
    X_scaled = StandardScaler().fit_transform(X)

    # DBSCAN: tune eps and min_samples for your data
    dbscan = DBSCAN(eps=0.8, min_samples=2)
    labels = dbscan.fit_predict(X_scaled)

    group = group.copy()
    group['Cluster'] = labels
    group['Minute'] = minute
    cluster_results.append(group)

# Combine all clustered groups
static_sensors_clustered_minDB = pd.concat(cluster_results)

# For mobile sensors per minute
minute_groups_M = mobile_sensors_minD.groupby('Minute')
cluster_results_M = []

for minute, group in minute_groups_M:
    if group.shape[0] < 3: 
        continue

    X_M = group[['Lat', 'Long', 'Value']].copy()
    X_scaled_M = StandardScaler().fit_transform(X)

    # DBSCAN: tune eps and min_samples for your data
    dbscan_M = DBSCAN(eps=0.8, min_samples=2)
    labels_M = dbscan_M.fit_predict(X_scaled)

    group = group.copy()
    group['Cluster'] = labels_M
    group['Minute'] = minute
    cluster_results_M.append(group)

# Combine all clustered groups
static_sensors_clustered_minDB_M = pd.concat(cluster_results_M)

# PLOTTING
def animated_hotspot_map(data, timescale='Minute', scale=40):
    """
    Shows animated colored zones for DangerLevel 2–5 over time.
    `data` must include 'DangerLevel' (as string), 'Lat', 'Long', and 'Value'.
    """
    extent = [-120, -119.711751, 0, 0.238585]
    
    color_map = {
        "2": "yellow",
        "3": "orange",
        "4": "red",
        "5": "purple"
    }

    # Filter for danger levels of interest
    data = data[data['DangerLevel'].isin(["2", "3", "4", "5"])]

    # Create Plotly Express animated scatter
    fig = px.scatter(
        data,
        x="Long",
        y="Lat",
        animation_frame=timescale,
        animation_group="Sensor-id",
        color="DangerLevel",
        color_discrete_map=color_map,
        size=[30] * len(data),  # Circle size (adjust as needed)
        opacity=0.9,
        category_orders={"DangerLevel": ["2", "3", "4", "5"]},
        hover_name="Sensor-id"
    )

    # Add static sensor markers on top
    fig.add_trace(go.Scatter(
        x=static_sensors_locations['Long'],
        y=static_sensors_locations['Lat'],
        mode='markers',
        marker=dict(size=10, color='black', symbol='triangle-up'),
        name='Static Sensors',
        showlegend=True
    ))

    # Background map image
    fig.add_layout_image(
        dict(
            source=img,
            xref="x",
            yref="y",
            x=extent[0],
            y=extent[3],
            sizex=extent[1] - extent[0],
            sizey=extent[3] - extent[2],
            sizing="stretch",
            layer="below"
        )
    )

    # Layout
    fig.update_layout(
        title="Animated Hotspot Zones by Danger Level",
        xaxis=dict(range=[extent[0], extent[1]], title="Longitude", showgrid=False),
        yaxis=dict(range=[extent[2], extent[3]], title="Latitude", showgrid=False),
        width=19.9 * scale,
        height=16.45 * scale
    )

    fig.show()

animated_hotspot_map(static_sensors_clustered_minDB,'Minute')
animated_hotspot_map(static_sensors_clustered_minDB_M,'Minute')