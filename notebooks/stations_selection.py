# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 01:51:29 2026

@author: sakkari
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np


MOUNTAIN_DEPTS = ['04','05','06','09','15','26','31','38',
                  '43','48','64','65','66','67','68','73','74','88']

COASTAL_DEPTS  = ['06','11','13','14','17','22','29','30',
                  '33','34','40','44','50','56','76','80','83','85']

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))

def exclude_overseas(df):
    df = df[~df['department_id'].isin([96, 97, 98])]
    return df


def select_stations(df, max_stations_per_dept=2, difference_threshold=0.3):
    df = exclude_overseas(df)
    selected = []

    for dept, group in df.groupby('department_id'):
        group = group.copy()
        
        if len(group) == 1:
            selected.append(group)
            continue

        # Features that determine weather behavior
        features = group[['latitude', 'longitude', 'altitude']].values
        
        # Normalize so altitude doesn't dominate over lat/lon
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # Check how different the stations actually are
        # by looking at the variance in the scaled features
        variance = features_scaled.var(axis=0).mean()
        import pdb
        pdb.set_trace()
        if variance < difference_threshold:
            # stations are all very similar → just pick 1 closest to centroid
            centroid_lat = group['latitude'].mean()
            centroid_lon = group['longitude'].mean()
            group['dist'] = haversine(
                group['latitude'], group['longitude'],
                centroid_lat, centroid_lon
            )
            selected.append(group.nsmallest(1, 'dist'))

        else:
            # stations are meaningfully different → cluster into 2
            kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
            group['cluster'] = kmeans.fit_predict(features_scaled)
            
            # From each cluster pick the station closest to cluster center
            for cluster_id in range(2):
                cluster_group = group[group['cluster'] == cluster_id].copy()
                center = features_scaled[group['cluster'] == cluster_id].mean(axis=0)
                cluster_group['dist_to_center'] = np.linalg.norm(
                    scaler.transform(cluster_group[['latitude', 'longitude', 'altitude']]) - center,
                    axis=1
                )
                selected.append(cluster_group.nsmallest(1, 'dist_to_center'))

    result = pd.concat([s for s in selected if not s.empty])
    result = result.drop_duplicates(subset='station_id')
    return result

df = pd.read_csv("data/liste-stations-obs-metropole-om_completed.csv", delimiter = ";")
selected = select_stations(df, difference_threshold=0.1)
counts = selected.groupby('department_id').size()
print(f"Total stations: {len(selected)}")
print(f"Departments with 1 station: {(counts == 1).sum()}")
print(f"Departments with 2 stations: {(counts == 2).sum()}")



import folium
import pandas as pd

def visualize_stations(selected_df, all_df):
    m = folium.Map(location=[46.8, 2.3], zoom_start=6)
    
    # count stations per department
    counts = selected_df.groupby('department').size()
    
    for _, row in selected_df.iterrows():
        dept = row['department']
        n_stations = counts[dept]
        
        # green = 2 stations selected (diverse dept)
        # blue  = 1 station selected (homogeneous dept)
        color = 'green' if n_stations == 2 else 'blue'
        
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=6,
            color=color,
            fill=True,
            fill_opacity=0.8,
            popup=folium.Popup(
                f"""
                <b>Station:</b> {row['station_id']}<br>
                <b>Department:</b> {dept}<br>
                <b>Altitude:</b> {row['altitude']}m<br>
                <b>Lat:</b> {row['latitude']:.3f}<br>
                <b>Lon:</b> {row['longitude']:.3f}
                """,
                max_width=200
            )
        ).add_to(m)
    
    # add legend
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
                background-color: white; padding: 10px; border-radius: 5px;
                border: 2px solid grey;">
        <b>Stations selected</b><br>
        <i class="fa fa-circle" style="color:green"></i> 2 stations (diverse)<br>
        <i class="fa fa-circle" style="color:blue"></i>  1 station (homogeneous)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    m.save('stations_selection.html')
    print(f"Map saved to stations_selection.html")
    return m

m = visualize_stations(selected, df)
m  # displays inline in jupyter
```

**What to look for visually:**
```
Good signs ✓
├── Mountain departments (Alps, Pyrenees) → green (2 stations)
├── Coastal departments → green (2 stations)  
├── Flat departments (Beauce, Landes) → blue (1 station)
└── No obvious geographic gaps across France

Bad signs ✗
├── Alps or Pyrenees showing blue → threshold too strict, lower it
├── Flat northern France showing green → threshold too loose, raise it
└── Big geographic gaps with no stations → some departments missing