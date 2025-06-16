import pandas as pd

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
    df = pd.read_csv("st_himark_neighborhood_data.csv")
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
