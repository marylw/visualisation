import os
import joblib  # pip install joblib
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from scipy.signal import find_peaks
import plotly.express as px


from load_data import mobile_sensors, static_sensors, cache_load_or_compute
print('Data loaded')


# Create Point geometries from Lat/Long and convert to GeoDataFrame
static_geometry = cache_load_or_compute(
    "static_geometry.pkl",
    lambda: [Point(xy) for xy in zip(static_sensors["Long"], static_sensors["Lat"])]
)
gdf_static_sensors = cache_load_or_compute(
    "gdf_static_sensors.pkl",
    lambda: gpd.GeoDataFrame(static_sensors, geometry=static_geometry, crs="EPSG:4326")
)

mobile_geometry = cache_load_or_compute(
    "mobile_geometry.pkl",
    lambda: [Point(xy) for xy in zip(mobile_sensors["Long"], mobile_sensors["Lat"])]
)
gdf_mobile_sensors = cache_load_or_compute(
    "gdf_mobile_sensors.pkl",
    lambda: gpd.GeoDataFrame(mobile_sensors, geometry=mobile_geometry, crs="EPSG:4326")
)

gdf_neighborhoods = cache_load_or_compute(
    "gdf_neighborhoods.pkl",
    lambda: gpd.read_file("MC2\data\StHimarkNeighborhoodShapefile\StHimark.shp")
)
gdf_neighborhoods = gdf_neighborhoods.to_crs(gdf_static_sensors.crs)

gdf_joined_static = cache_load_or_compute(
    "gdf_joined_static.pkl",
    lambda: gpd.sjoin(gdf_static_sensors, gdf_neighborhoods, how="left", predicate="within")[['Timestamp', 'Sensor-id', 'Value', 'Lat', 'Long', 'Nbrhood']]
)
gdf_joined_mobile = cache_load_or_compute(
    "gdf_joined_mobile.pkl",
    lambda: gpd.sjoin(gdf_mobile_sensors, gdf_neighborhoods, how="left", predicate="within")[['Timestamp', 'Sensor-id', 'Value', 'Lat', 'Long', 'Nbrhood']]
)

gdf_joined_mobile['Sensor-id'] = gdf_joined_mobile['Sensor-id'] + 100
gdf_joined_combined = cache_load_or_compute(
    "gdf_joined_combined.pkl",
    lambda: pd.concat([gdf_joined_static, gdf_joined_mobile], ignore_index=True)
)
print('Part 1 done')

# Create a dataframe to hold the peaks
def peaks(gdf_data):
    sensors = gdf_data['Sensor-id'].unique()
    peaks_df = pd.DataFrame(columns=['Sensor-id', 'Timestamp', 'Value', 'Lat', 'Long', 'Nbrhood', 'Peak_Height'])
    for sensor in sensors:
        sensor_data = gdf_data[gdf_data['Sensor-id'] == sensor]
        peaks, properties = find_peaks(sensor_data['Value'], height=75) # Select all peaks that have a danger level >= 2
        selected_peaks_df = sensor_data.iloc[peaks].copy()
        selected_peaks_df['Peak_Height'] = properties['peak_heights']
        peaks_df = pd.concat([peaks_df, selected_peaks_df], ignore_index=True)
    return peaks_df
print('Part 2 done')

def compute_normalized_peaks(full_df): ### NOT CORRECT YET??? ###
    """
    Compute normalized peak counts per hour per neighborhood.
    Handles zero-peak and zero-sensor hours gracefully.

    Parameters:
        peaks_df: DataFrame with detected peaks (including 'Timestamp', 'Nbrhood', 'Sensor-id')
        full_df: Full sensor dataset with all readings

    Returns:
        merged DataFrame with columns: Nbrhood, Hour, Peak_Count, Sensor_Count, Peaks_per_Sensor
    """
    # Ensure datetime format
    peaks_df = peaks(full_df.copy())
    full_df = full_df.copy()
    peaks_df['Hour'] = peaks_df['Timestamp'].dt.floor('h')
    full_df['Hour'] = full_df['Timestamp'].dt.floor('h')

    # Get all hour-neighborhood combinations
    all_hours = pd.date_range(full_df['Hour'].min(), full_df['Hour'].max(), freq='H')
    all_nbrhoods = full_df['Nbrhood'].dropna().unique()
    full_index = pd.MultiIndex.from_product([all_nbrhoods, all_hours], names=['Nbrhood', 'Hour'])
    base = pd.DataFrame(index=full_index).reset_index()

    # Peak count per neighborhood-hour
    peak_counts = peaks_df.groupby(['Nbrhood', 'Hour']).size().reset_index(name='Peak_Count')

    # Active sensor count per neighborhood-hour
    sensor_counts = full_df.groupby(['Nbrhood', 'Hour'])['Sensor-id'].nunique().reset_index(name='Sensor_Count')

    # Merge
    merged = base.merge(peak_counts, on=['Nbrhood', 'Hour'], how='left')
    merged = merged.merge(sensor_counts, on=['Nbrhood', 'Hour'], how='left')

    # Fill missing values
    merged['Peak_Count'] = merged['Peak_Count'].fillna(0)
    merged['Sensor_Count'] = merged['Sensor_Count'].fillna(0)

    # Compute normalized peaks
    merged['Peaks_per_Sensor'] = merged.apply(
        lambda row: row['Peak_Count'] / row['Sensor_Count'] if row['Sensor_Count'] > 0 else 0,
        axis=1
    )

    return merged

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px  # Needed for color palettes

def combined_peak_plot(gdf_joined, y_max=1500, combined=True):
    """
    Create a plot of:
    - Scatter plot of individual peak heights per timestamp
    - Line plot of normalized peak rate per sensor per hour
    If `combined` is True, both are shown in a single plot with dual y-axes.
    If `combined` is False, return the two plots separately.
    """

    normalized_df = compute_normalized_peaks(gdf_joined)
    peaks_df = peaks(gdf_joined)
    peaks_df['Hour'] = peaks_df['Timestamp'].dt.floor('h')

    neighborhoods = sorted(peaks_df['Nbrhood'].dropna().unique())
    colors = px.colors.qualitative.Set2
    color_map = {nbr: colors[i % len(colors)] for i, nbr in enumerate(neighborhoods)}

    if combined:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        for nbr in neighborhoods:
            df_nbr = peaks_df[peaks_df['Nbrhood'] == nbr]
            fig.add_trace(
                go.Scatter(
                    x=df_nbr['Timestamp'],
                    y=df_nbr['Peak_Height'],
                    mode='markers',
                    name=f'{nbr} - Peak Height',
                    marker=dict(color=color_map[nbr]),
                    legendgroup=nbr,
                    showlegend=True
                ),
                secondary_y=False
            )

        for nbr in neighborhoods:
            df_norm = normalized_df[normalized_df['Nbrhood'] == nbr]
            fig.add_trace(
                go.Scatter(
                    x=df_norm['Hour'],
                    y=df_norm['Peaks_per_Sensor'],
                    mode='lines+markers',
                    name=f'{nbr} - Peaks per Neighborhood',
                    marker=dict(color=color_map[nbr]),
                    legendgroup=nbr,
                ),
                secondary_y=True
            )

        # Add danger lines
        fig.add_hline(y=1000, line_dash='dash', line_color='red', annotation_text='Danger Level 3',
                      annotation_position='top left', opacity=0.5)
        fig.add_hline(y=100, line_dash='dash', line_color='orange', annotation_text='Danger Level 2',
                      annotation_position='top left', opacity=0.5)

        fig.update_yaxes(showgrid=False)
        fig.update_layout(
            title='Detected Peaks and Normalized Amount of Peaks per Neighborhood',
            xaxis_title='Time',
            yaxis_title='Peak Height',
            yaxis2_title='Peaks per Neighborhood',
            yaxis_range=[0, y_max],
            yaxis2_range=[0, normalized_df['Peaks_per_Sensor'].max() * 1.1],
            legend=dict(orientation="v", x=1.02, y=1),
            margin=dict(r=200),
            width=1000,
            height=600,
        )
        return fig

    else:
        # Create scatter plot
        scatter_fig = go.Figure()
        color_map = {nbr: px.colors.qualitative.Light24[i % len(px.colors.qualitative.Light24)] for i, nbr in enumerate(neighborhoods)}
        for nbr in neighborhoods:
            df_nbr = peaks_df[peaks_df['Nbrhood'] == nbr]
            scatter_fig.add_trace(
                go.Scatter(
                    x=df_nbr['Timestamp'],
                    y=df_nbr['Peak_Height'],
                    mode='markers',
                    name=f'{nbr} - Peak Height',
                    marker=dict(color=color_map[nbr]),
                    text='Sensor ID: ' + df_nbr['Sensor-id'].astype(str),
                    hoverinfo='text'
                )
            )

        scatter_fig.update_layout(
            title='Detected Peak Heights per Neighborhood',
            xaxis_title='Time',
            yaxis_title='Peak Height',
            yaxis_range=[0, y_max],
            width=1000,
            height=700,
            legend = dict(font=dict(size=10))
        )
        scatter_fig.add_hline(y=1000, line_dash='dash', line_color='red', annotation_text='Danger Level 3',
                      annotation_position='top left', opacity=0.5)
        scatter_fig.add_hline(y=100, line_dash='dash', line_color='orange', annotation_text='Danger Level 2',
                      annotation_position='top left', opacity=0.5)

        # Create line plot
        # line_fig = go.Figure()
        # for nbr in neighborhoods:
        #     df_norm = normalized_df[normalized_df['Nbrhood'] == nbr]
        #     line_fig.add_trace(
        #         go.Scatter(
        #             x=df_norm['Hour'],
        #             y=df_norm['Peaks_per_Sensor'],
        #             mode='lines+markers',
        #             name=f'{nbr} - Peaks per Neighborhood',
        #             marker=dict(color=color_map[nbr]),
        #         )
        #     )

        bar_fig = px.bar(normalized_df, x="Hour", y="Peaks_per_Sensor", color="Nbrhood", title="Average Amount of Peaks per Sensor per Hour",color_discrete_map=color_map) 
        bar_fig.update_layout(
            xaxis_title='Hour',
            yaxis_title='Average Amount of Peaks per Sensor',
            legend = dict(font=dict(size=10)),
            height = 500
            )


        # line_fig.update_layout(
        #     title='Normalized Peaks per Sensor per Neighborhood',
        #     xaxis_title='Hour',
        #     yaxis_title='Peaks per Sensor',
        #     yaxis_range=[0, normalized_df['Peaks_per_Sensor'].max() * 1.1],
        #     width=1000,
        #     height=500,
        # )

        return scatter_fig, bar_fig

scatter, bar = combined_peak_plot(gdf_joined_combined, combined=False)

normalized_df = peaks(gdf_joined_combined)
categorical_scatter = px.scatter(normalized_df, y="Nbrhood", x="Timestamp")
categorical_scatter.update_layout(
    title = 'Peaks per Neighborhood',
    xaxis_title='Time',
    yaxis_title='Neighborhood',
    )

