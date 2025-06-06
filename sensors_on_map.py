from load_data import static_sensors, mobile_sensors, static_sensors_locations, img
import pandas as pd
import pandas as pd
import plotly.express as px

### PREPROCESSING ###
static_sensors['Minute'] = static_sensors['Timestamp'].dt.floor('min')
static_sensors['Hour'] = static_sensors['Timestamp'].dt.floor('h')

# Maybe we should use a mean that gives less weight to outliers, as we cannot draw meaningful conclusions from the plot now
static_sensors_min = static_sensors.groupby(['Sensor-id', 'Minute'])['Value'].max().reset_index()
static_sensors_hour = static_sensors.groupby(['Sensor-id', 'Hour'])['Value'].max().reset_index()

# Delete values below zero
static_sensors_hour.loc[static_sensors_hour['Value'] <= 0, 'Value'] = 0
static_sensors_min.loc[static_sensors_min['Value'] <= 0, 'Value'] = 0
static_sensors.loc[static_sensors['Value'] <= 0, 'Value'] = 0


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
# def apply_classification(df):
#     df['Radiation_Level'] = df['Value'].apply(classify_radiation)
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
static_sensors_hourD['DangerLevel'] = static_sensors_hourD['Value'].astype(str)
static_sensors_minD['DangerLevel'] = static_sensors_minD['Value'].astype(str)
static_sensorsD['DangerLevel'] = static_sensorsD['Value'].astype(str)
mobile_sensors_hourD['DangerLevel'] = mobile_sensors_hourD['Value'].astype(str)
mobile_sensors_minD['DangerLevel'] = mobile_sensors_minD['Value'].astype(str)
mobile_sensorsD['DangerLevel'] = mobile_sensorsD['Value'].astype(str)

# add dummy values so that the legend is visible (MAKE ONE FUNCTION)
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

### CREATE THE PLOT ###

def sensor_map_data(data, timescale, scale = 40):
    """
    Timescale should be either 'Minute' or 'Hour'
    Scale is the size of the image"""    
    extent = [-120, -119.711751, 0, 0.238585]
    
    # Create triangle markers for static sensors
    fig = px.scatter(
        static_sensors_locations,
        x="Long",
        y="Lat",
        symbol_sequence=["triangle-up"],
        color_discrete_sequence=["black"],
    )
    
    # Add radiation data with different color scale
    fig2 = px.scatter(
        data_frame=data,
        x="Long",
        y="Lat",
        animation_frame=data[timescale],
        animation_group=data['Sensor-id'],
        size="Value",
        color="DangerLevel",
        color_discrete_map={
            "1": "green",
            "2": "yellow",
            "3": "orange",
            "4": "red",
            "5": "purple"
        },
        category_orders={"DangerLevel": ["1","2","3","4","5"]},
        hover_name=None, 
        range_x=None,
        range_y=None
    )

    # Add the background map image
    fig2.add_layout_image(
        dict(
            source=img,
            xref="x",
            yref="y",
            x=extent[0],
            y=extent[3],  # top-left corner
            sizex=extent[1] - extent[0],
            sizey=extent[3] - extent[2],
            sizing="stretch",
            layer="below"
        )
    )

    # Update layout
    fig2.update_layout(
        title=dict(text="Sensors Overlaid on Map",
                font=dict(size=20, color='black'),
                x=0.5,
                xanchor='center',
                yanchor='top'),
        xaxis=dict(range=[extent[0], extent[1]], title="Longitude", showgrid=False),
        yaxis=dict(range=[extent[2], extent[3]], title="Latitude", showgrid=False),
        width=19.9 * scale,
        height=16.45 * scale
    )
    fig2.add_traces(fig.data)
    fig2.show()


sensor_map_data(static_sensors_hourD, 'Hour')
# sensor_map_data(static_sensorsD, 'Timestamp')
# sensor_map_data(static_sensors_minD, 'Minute')
