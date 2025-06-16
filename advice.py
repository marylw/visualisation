import joblib
import os

from load_data import demographics

try: 
    CACHE_DIR = "cache"
    static_filename = 'gdf_joined_static.pkl'
    mobile_filename = 'gdf_joined_mobile.pkl'
    static_path = os.path.join(CACHE_DIR, static_filename)
    mobile_path = os.path.join(CACHE_DIR, mobile_filename)
    static2_filename = 'static_sensors_clustered_minDB.pkl'
    mobile2_filename = 'mobile_sensors_clustered_minDB.pkl'
    static2_path = os.path.join(CACHE_DIR, static2_filename)
    mobile2_path = os.path.join(CACHE_DIR, mobile2_filename)
    print(f"Loading cached {static_filename}")
    gdf_joined_static = joblib.load(static_path)
    print(f"Loading cached {mobile_filename}")
    gdf_joined_mobile = joblib.load(mobile_path)
    print(f"Loading cached {mobile2_filename}")
    mobile_sensors_clustered_minDB = joblib.load(mobile2_path)
    print(f"Loading cached {static2_filename}")
    static_sensors_clustered_minDB = joblib.load(static2_path)
    
except:
    print('Running peaks_scatter.py')
    from peaks_scatter import gdf_joined_mobile, gdf_joined_static
    from map import static_sensors_clustered_minDB, mobile_sensors_clustered_minDB

def cluster_location(cluster_data, location_data):
    location_data['Minute'] = location_data['Timestamp'].dt.floor('min')
    location_data.groupby(['Sensor-id', 'Minute', 'Long', 'Lat'])['Value'].max().reset_index()
    joined = cluster_data.merge(location_data, on=['Sensor-id', 'Long', 'Lat', 'Minute', 'Value'], how='left')
    print(joined.head(10))
    print(cluster_data.head(10))
    print(location_data.head(10))
    
cluster_location(static_sensors_clustered_minDB, gdf_joined_static)

print('data is joined')

def analyze_neighborhood_data(df):
    results = {
        "sensors_needed": [],
        "neighborhoods_to_clean": [],
        "decontamination_needed": [],
        "shelter_suggestions": []
    }

    # Sensor placement: more static sensors where population is high and infrastructure is limited
    for _, row in df.iterrows():
        sensor_flag = False
        if row['Population'] > df['Population'].quantile(0.75):
            if row['Amount of hospitals'] == 0 or row['Fire stations'] == 0:
                results['sensors_needed'].append((row['Neighborhood'], 'static'))
                sensor_flag = True
        # Mobile sensors where animals are abundant or vehicle ownership is low
        if row['Amount of animals'] > df['Amount of animals'].mean() and not sensor_flag:
            results['sensors_needed'].append((row['Neighborhood'], 'mobile'))

    # Cleaning: low green space or many animals can indicate contamination
    for _, row in df.iterrows():
        if row['% green space'] < df['% green space'].quantile(0.25) or row['Amount of animals'] > df['Amount of animals'].quantile(0.75):
            results['neighborhoods_to_clean'].append(row['Neighborhood'])

    # Decontamination (level 3+): high elderly/children population near nuclear zone
    for _, row in df.iterrows():
        if row['Avg. dist. to nuclear (km)'] < df['Avg. dist. to nuclear (km)'].quantile(0.25):
            vulnerable_pop = row['Amount of children'] + row['Amount of elderly']
            if vulnerable_pop / row['Population'] > 0.3:
                results['decontamination_needed'].append(row['Neighborhood'])

    # Shelters: high population, low hospital/fire station, and far from nuclear zone
    for _, row in df.iterrows():
        if row['Population'] > df['Population'].quantile(0.75):
            if row['Amount of hospitals'] == 0 and row['Fire stations'] == 0:
                if row['Avg. dist. to nuclear (km)'] > df['Avg. dist. to nuclear (km)'].mean():
                    results['shelter_suggestions'].append(row['Neighborhood'])

    return results

# Example usage
if __name__ == "__main__":
    df = demographics
    decision = analyze_neighborhood_data(df)

    print("--- SENSOR PLACEMENT SUGGESTIONS ---")
    for nb, typ in decision['sensors_needed']:
        print(f"{nb}: {typ} sensor")

    print("\n--- NEIGHBORHOODS TO CLEAN ---")
    for nb in decision['neighborhoods_to_clean']:
        print(nb)

    print("\n--- DECONTAMINATION REQUIRED ---")
    for nb in decision['decontamination_needed']:
        print(nb)

    print("\n--- SHELTER RECOMMENDATIONS ---")
    for nb in decision['shelter_suggestions']:
        print(nb)
