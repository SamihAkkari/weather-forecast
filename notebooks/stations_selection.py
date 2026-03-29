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

def visualize_all_vs_selected(all_df, selected_df):
    m = folium.Map(location=[46.8, 2.3], zoom_start=6)
    
    selected_ids = set(selected_df['station_id'])
    
    # plot all stations in red (not selected)
    for _, row in all_df.iterrows():
        if row['station_id'] not in selected_ids:
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=3,
                color='red',
                fill=True,
                fill_opacity=0.4,
                popup=f"Station: {row['station_id']} | Alt: {row['altitude']}m"
            ).add_to(m)
    
    # plot selected stations in green (on top)
    for _, row in selected_df.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=6,
            color='green',
            fill=True,
            fill_opacity=0.9,
            popup=f"Station: {row['station_id']} | Dept: {row['department_id']} | Alt: {row['altitude']}m"
        ).add_to(m)

    # legend
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
                background-color: white; padding: 10px; border-radius: 5px;
                border: 2px solid grey; font-size: 14px;">
        <b>Stations</b><br>
        <span style="color:green;">●</span> Selected<br>
        <span style="color:red;">●</span> Not selected
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    m.save('stations_selection.html')
    return m

m = visualize_all_vs_selected(df, selected)
m