import pandas as pd
import joblib
from datetime import datetime
from scipy.signal import find_peaks

# Radiation classification
def classify_radiation(cpm):
    if cpm <= 100: return 1
    elif cpm <= 1000: return 2
    elif cpm <= 10000: return 3
    elif cpm <= 100000: return 4
    else: return 5

# Peak detection
def detect_peaks(gdf_data):
    sensors = gdf_data['Sensor-id'].unique()
    peaks_df = pd.DataFrame(columns=['Sensor-id', 'Timestamp', 'Value', 'Lat', 'Long', 'Nbrhood', 'Peak_Height'])
    for sensor in sensors:
        sensor_data = gdf_data[gdf_data['Sensor-id'] == sensor]
        peaks, properties = find_peaks(sensor_data['Value'], height=75)
        selected_peaks_df = sensor_data.iloc[peaks].copy()
        selected_peaks_df['Peak_Height'] = properties['peak_heights']
        peaks_df = pd.concat([peaks_df, selected_peaks_df], ignore_index=True)
    return peaks_df

# Main advisory logic 
def analyze_neighborhood_data(population_df, peaks_df, timestamp):
    results = {
        "sensors_needed": [],
        "neighborhoods_to_clean": [],
        "decontamination_needed": [],
        "shelter_suggestions": []
    }

    # Sensor placement
    for _, row in population_df.iterrows():
        if (row['Population'] > population_df['Population'].median() or row['Amount of hospitals'] >= 1) and row['Amount of sensors'] <= 2:
            results['sensors_needed'].append((row['Nbrhood'], 'static'))
        elif row['Amount of animals'] > population_df['Amount of animals'].mean() and row['Population'] < population_df['Population'].median():
            results['sensors_needed'].append((row['Nbrhood'], 'mobile'))

    # Filter peak data for the selected timestamp
    peaks_df['Minute'] = pd.to_datetime(peaks_df['Timestamp']).dt.floor('min')
    snapshot = peaks_df[peaks_df['Minute'] == pd.to_datetime(timestamp)]
    snapshot['Radiation_Level'] = snapshot['Peak_Height'].apply(classify_radiation)

    for _, row in snapshot.iterrows():
        results['neighborhoods_to_clean'] = list(
            snapshot[snapshot['Radiation_Level'] >= 2]['Nbrhood'].dropna().unique()
        )
        results['decontamination_needed'] = list(
            snapshot[snapshot['Radiation_Level'] >= 3]['Nbrhood'].dropna().unique()
        )

    # Shelter placement
    for _, row in population_df.iterrows():
        if row['Population'] > population_df['Population'].quantile(0.60):
            if row['Amount of hospitals'] == 0 and row['Fire stations'] == 0:
                results['shelter_suggestions'].append(row['Nbrhood'])

    return results

# Main execution
if __name__ == "__main__":
    # Load input data
    pop_df = pd.read_csv("st_himark_neighborhood_data.csv")
    pop_df.rename(columns={"Neighborhood": "Nbrhood"}, inplace=True)

    # Add dummy column if needed
    if 'Amount of sensors' not in pop_df.columns:
        pop_df['Amount of sensors'] = 0

    # Load spatially joined sensor data (preprocessed)
    gdf_joined_combined = joblib.load("cache/gdf_joined_combined.pkl")

    # Detect peaks
    peaks_df = detect_peaks(gdf_joined_combined)

    # Define timestamp of interest
    timestamp = "2020-04-07 01:40:00"  # Modify as needed

    # Analyze
    decision = analyze_neighborhood_data(pop_df, peaks_df, timestamp)

    # Print results
    print("Sensor Placement Suggestions:")
    for nb, typ in decision['sensors_needed']:
        print(f"{nb}: {typ} sensor")

    print("Neighborhoods to Clean Suggestions:")
    for nb in decision['neighborhoods_to_clean']:
        print(nb)

    print("Citizen Decontamination Suggestions:")
    for nb in decision['decontamination_needed']:
        print(nb)

    print("Neighborhoods to Build Shelters in Suggestions:")
    for nb in decision['shelter_suggestions']:
        print(nb)