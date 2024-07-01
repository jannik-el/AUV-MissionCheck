import streamlit as st
import os
from dotenv import load_dotenv
import datetime
from pathlib import Path
import pandas as pd
import json
import folium
import plotly.express as px
from streamlit_folium import st_folium

load_dotenv()

from scripts.preprocessing import extract_waypoints
from scripts.mission_checks import validate_mission_devices, get_payloads, check_timeouts, check_max_depth

def main():
    st.header("NemoSens Mission Plan Validation")

    with st.sidebar:
        st.title("AUV Mission Check")
        st.write("Upload a JSON file to check and visualize the mission plan.")

        uploaded_file = st.file_uploader("Choose a file", type="json")
        max_depth = st.slider("Maximum Local Depth", 0, 40, 20)
        timeout_buffer = st.slider("Timeout Buffer. Default is 2x the minimum travel time (surface distance * velocity).", 0, 5, 2)
        

    if uploaded_file is not None:

        tab1, tab2, tab3, tab4 = st.tabs(["Mission Check", "View Mission Data", "Plot Mission", "Fix Mission"])
        data = json.load(uploaded_file)

        with tab1: 
            with st.spinner("Extracting Waypoints..."):
                waypoints_df = extract_waypoints(data)

            mission_info = {
                "Mission Name": data['mission']['name'],
                "Mission Timestamp": data['mission']['comment'],
                "SCM Serial No." : data["mission"]["devices"][0]["serialNumber"],
                "AUV Serial No." : data["mission"]["devices"][1]["serialNumber"],
                "Total Minimum Travel Time (minutes)": round(waypoints_df["minimum_timeout"].sum() / 60, 2),
                "Total Maximal Timeout Time (minutes)": round(waypoints_df["timeout"].sum() / 60, 2),
                "Total Distance Travelled (excluding start of mission) (meters)": round(waypoints_df["distance_to_last_wp_m"].sum(), 2),
                "3% Offset from Total Distance Travelled": round(waypoints_df["distance_to_last_wp_m"].sum() * 0.03, 2),
            }

            st.write(mission_info)

            st.write(f"When deploying stay within a radius of {waypoints_df["velocity"].iloc[0]*waypoints_df["timeout"].iloc[0]} meters of the start waypoint.")

            with st.status("Checking Mission Plan...", expanded=True):
                # Run the checks
                mission_devices_validation_dict = validate_mission_devices(str(data["mission"]["devices"]))

                if all(mission_devices_validation_dict.values()):
                    st.success("SCM and AUV are activated, and correct SN selected.")
                elif not any(mission_devices_validation_dict.values()):
                    st.error("SCM and/or AUV are either not activated or incorrect SN selected.")

                mission_payload_validation_dict = get_payloads(str(data["mission"]["store"]))
                if all(mission_payload_validation_dict.values()):
                    st.success("AUV AML Payload selected and enabled.")
                elif not any(mission_payload_validation_dict.values()):
                    st.error("AUV AML Payload not selected and/or not enabled.")

                timeouts_df = waypoints_df[waypoints_df["device_type"] == "DEVICE_DRONE"]
                timeout_pass = check_timeouts(timeouts_df)
                if timeout_pass:
                    st.success("Timeout Validation Passed")
                else:
                    st.error("Timeout Validation Failed")

                max_depth_pass = check_max_depth(waypoints_df, max_depth)
                print(max_depth_pass)
                if max_depth_pass:
                    st.success("Max Depth Validation Passed")
                else:
                    st.error("Max Depth Validation Failed")

        with tab2: 
            # tab for showing all the mission data
            st.write("Payload Info")
            st.write(data["mission"]["store"])
            st.write("Mission Waypoints:")
            st.dataframe(waypoints_df)

        with tab3: 
            df = waypoints_df
            # tab for plotting the mission
            map = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=13)

            # Plot the points
            points_layer = folium.FeatureGroup(name="Points")
            for i, row in df.iterrows():
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=row['name'],
                    icon=folium.Icon(color='blue', icon='circle', prefix='fa')
                ).add_to(points_layer)
                
                # Add name label
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=None,
                    icon=folium.DivIcon(
                        icon_size=(150,36),
                        icon_anchor=(0,0),
                        html=f'<div style="font-size: 12px; color: blue;">{row["name"]}</div>'
                    )
                ).add_to(points_layer)
            points_layer.add_to(map)

            # Plot the circles
            circles_layer = folium.FeatureGroup(name="Circles")
            for i, row in df.iterrows():
                if not pd.isna(row['radius']):
                    folium.Circle(
                        location=[row['latitude'], row['longitude']],
                        radius=row['radius_degrees'] * 111000,  # Convert degrees to meters
                        color='red',
                        fill=True,
                        fill_color='red',
                        fill_opacity=0.5
                    ).add_to(circles_layer)
            circles_layer.add_to(map)

            # Plot the dotted lines between waypoints with arrows
            nemo_route = df[df["device_type"] == "DEVICE_DRONE"]
            nemo_route = nemo_route.sort_values(by='waypoint_no').reset_index(drop=True)
            lines_layer = folium.FeatureGroup(name="Lines")
            for i, row in nemo_route.iterrows():
                if i > 0:
                    prev_row = nemo_route.iloc[i-1]
                    folium.PolyLine(
                        locations=[[prev_row['latitude'], prev_row['longitude']], [row['latitude'], row['longitude']]],
                        color='black',
                        weight=2,
                        opacity=0.5,
                        dash_array='5, 5'
                    ).add_to(lines_layer)
            lines_layer.add_to(map)

            # Add satellite background layer
            satellite_layer = folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Satellite'
            ).add_to(map)

            # Add layer control
            folium.LayerControl().add_to(map)

            map.fit_bounds(map.get_bounds())
            
            st.write("Mission Plan")
            st_data = st_folium(map, width=800, height=400)

            st.write("Mission Plan Cross-section")

if __name__ == "__main__":
    main()


