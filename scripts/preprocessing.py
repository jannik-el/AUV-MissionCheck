import pandas as pd
import json
import math
import numpy as np
import re

import warnings
#remove all warnings
warnings.filterwarnings("ignore")

EARTH_RADIUS = 6378137

def load_json(file_path):
    with open(file_path) as f:
        data = json.load(f)
    return data

def lat_lon_to_meters(latitude, longitude):
    # Convert latitude and longitude to radians
    lat_rad = math.radians(latitude)
    lon_rad = math.radians(longitude)

    # Latitude and longitude in meters
    lat_meters = lat_rad * EARTH_RADIUS
    lon_meters = lon_rad * EARTH_RADIUS * math.cos(lat_rad)

    return lat_meters, lon_meters

def extract_waypoints(data):
    waypoints = []
    waypoint_no = 0
    for device in data['mission']['devices']:
        device_type = device['type']
        if "paths" in device:
            for path in device['paths']:
                for stage in path['stages']:
                    waypoint_no += 1
                    waypoint = {
                        'device': device['name'],
                        'device_type': device_type,
                        'path': path['name'],
                        'name': stage['name'],
                        'waypoint_no': waypoint_no,
                        'latitude': stage['latitude'],
                        'longitude': stage['longitude'],
                        'velocity': stage['navigation'].get('velocity', None),
                        'altitude': stage['navigation'].get('altitude', None),
                        'depth': stage['navigation'].get('depth', None),
                    }
                    nav_data = list(stage['navigation'].keys())
                    # remove velocity and depth
                    if "velocity" in nav_data: nav_data.remove('velocity')
                    if "depth" in nav_data: nav_data.remove('depth')
                    if "altitude" in nav_data: nav_data.remove('altitude')
                    path_type = nav_data[0]

                    waypoint['path_type'] = path_type
                    waypoint['radius'] = stage['navigation'][path_type].get('radius', None)
                    waypoint['timeout'] = stage['navigation'][path_type].get('timeout', None)

                    waypoints.append(waypoint)

    waypoints_df = pd.DataFrame(waypoints)

    waypoints_df['radius_degrees'] = waypoints_df['radius'] / EARTH_RADIUS * (180 / np.pi)

    waypoints_df['latitude_m'], waypoints_df['longitude_m'] = zip(*waypoints_df.apply(lambda x: lat_lon_to_meters(x['latitude'], x['longitude']), axis=1))

    for i, row in waypoints_df.iterrows():
        if i == 0: 
            waypoints_df.at[i, 'distance_to_last_wp_m'] = 0
        if i > 0:
            next_lat = waypoints_df.iloc[i-1]['latitude_m']
            next_lon = waypoints_df.iloc[i-1]['longitude_m']*-1
            curr_lat = row['latitude_m']
            curr_lon = row['longitude_m']*-1
            distance = math.sqrt((next_lat - curr_lat)**2 + (next_lon - curr_lon)**2)
            waypoints_df.at[i, 'distance_to_last_wp_m'] = distance

    waypoints_df['total_distance_m'] = waypoints_df['distance_to_last_wp_m'].cumsum()

    waypoints_df["minimum_timeout"] = waypoints_df["distance_to_last_wp_m"] / waypoints_df["velocity"]
    waypoints_df["timeout_too_short"] = waypoints_df["timeout"] < waypoints_df["minimum_timeout"]

    return waypoints_df