import pandas as pd
import json
import math
import numpy as np
import re


def validate_mission_devices(mission_devices_text):
    # expects data["mission"]["devices"] as input

    mission_devices_validation_dict = {
        "SCM": 'DEVICE_SURFACE' in mission_devices_text,
        "SCM_SERIAL": 'SUSDA14_2302002' in mission_devices_text,
        "AUV": 'DEVICE_DRONE' in mission_devices_text,
        "AUV_SERIAL": 'NEMOSENS_2304001' in mission_devices_text
    }
    return mission_devices_validation_dict

def get_payloads(text):
    # expects data["mission"]["store"] as input
    
    payload_validation_dict = {
        "AML": "'aml'" in text,
        "AML-SERIAL": "'aml': {'info': {'optionEnable': True}" in text,
    }
    return payload_validation_dict

def check_timeouts(waypoints_df):

    waypoints_df["timeout_too_short"].iloc[0] = False
    timeout_too_short = waypoints_df["timeout_too_short"]
    
    if any(timeout_too_short):
        return False
    else:
        return True

def check_max_depth(waypoints_df, max_depth): 

    depth_df = waypoints_df[["depth"]].dropna()

    if any(depth_df["depth"]) > max_depth:
        print(depth_df["depth"])
        return False
    else:
        return True


