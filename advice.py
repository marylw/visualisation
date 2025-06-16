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

# Daily advisory logic
def analyze_neighborhood_data_daily(pop_df, peaks_df, selected_day):
    selected_day = pd.to_datetime(selected_day)
    peaks_df['Day'] = pd.to_datetime(peaks_df['Timestamp']).dt.floor('d')
    snapshot = peaks_df[peaks_df['Day'] == selected_day].copy()
    snapshot['Radiation_Level'] = snapshot['Peak_Height'].apply(classify_radiation)

    results = {
        "sensors_needed": [],
        "neighborhoods_to_clean": [],
        "decontamination_needed": [],
        "shelter_suggestions": []
    }

    for _, row in pop_df.iterrows():
        if (row['Population'] > pop_df['Population'].median() or row['Amount of hospitals'] >= 1) and row['Amount of sensors'] <= 2:
            results['sensors_needed'].append((row['Nbrhood'], 'static'))
        elif row['Amount of animals'] > pop_df['Amount of animals'].mean() and row['Population'] < pop_df['Population'].median():
            results['sensors_needed'].append((row['Nbrhood'], 'mobile'))

    results['neighborhoods_to_clean'] = list(snapshot[snapshot['Radiation_Level'] >= 2]['Nbrhood'].dropna().unique())
    results['decontamination_needed'] = list(snapshot[snapshot['Radiation_Level'] >= 3]['Nbrhood'].dropna().unique())

    for _, row in pop_df.iterrows():
        if row['Population'] > pop_df['Population'].quantile(0.75):
            if row['Amount of hospitals'] == 0:
                results['shelter_suggestions'].append(row['Nbrhood'])

    return results

# Main execution
if __name__ == "__main__":
    pop_df = pd.read_csv("st_himark_neighborhood_data.csv")
    pop_df.rename(columns={"Neighborhood": "Nbrhood"}, inplace=True)
    if 'Amount of sensors' not in pop_df.columns:
        pop_df['Amount of sensors'] = 0

    gdf_joined_combined = joblib.load("cache/gdf_joined_combined.pkl")
    peaks_df = detect_peaks(gdf_joined_combined)

    # Define day of interest
    day_of_interest = "2020-04-06"
    decision = analyze_neighborhood_data_daily(pop_df, peaks_df, day_of_interest)

    # Print results
    print(f"Advice Summary for {day_of_interest}:")
    print("Cleaning/Investigation Needed:", decision['neighborhoods_to_clean'])
    print("Decontamination Citizens Needed:", decision['decontamination_needed'])
    print("Shelter Needed:", decision['shelter_suggestions'])
    print("Sensor Recommendations:")
    for nb, typ in decision['sensors_needed']:
        print(f"  - {nb}: {typ} sensor")