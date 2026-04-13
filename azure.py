# __init__.py (Azure Function)
import logging
import json
import requests
import os
from datetime import datetime
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.digitaltwins.core import DigitalTwinsClient

ADT_ENDPOINT = os.environ["ADT_SERVICE_URL"] 
MODEL_API_URL = os.environ["MODEL_PREDICT_URL"] # The URL of your FastAPI container

def main(event: func.EventHubEvent):
    try:
        # 1. Parse incoming IoT telemetry (JSON payload from physical sensors)
        message_body = event.get_body().decode('utf-8')
        telemetry = json.loads(message_body)
        twin_id = event.iothub_metadata.get('connection-device-id')
        
        # Determine time features dynamically based on current event time
        now = datetime.utcnow()

        # 2. Construct the payload exactly as your Notebook model expects
        # Note: In a true production environment, power_lag_24 would be queried 
        # from Azure Time Series Insights or a Redis cache of past twin states.
        payload = {
            "twin_id": twin_id,
            "power_lag_1": telemetry.get("Global_active_power"), # Simplified: using current as lag_1
            "power_lag_24": telemetry.get("power_24h_ago", 0.0), # Requires state caching
            "hour": now.hour,
            "dayofweek": now.weekday(),
            "month": now.month,
            "temperature_2m": telemetry.get("temperature_2m"),
            "relative_humidity_2m": telemetry.get("relative_humidity_2m"),
            "wind_speed_10m": telemetry.get("wind_speed_10m", 0.0),
            "wind_direction_10m": telemetry.get("wind_direction_10m", 0.0)
        }
        
        # 3. Request Prediction from your containerized model
        response = requests.post(MODEL_API_URL, json=payload)
        response.raise_for_status()
        predicted_power = response.json()["predicted_power_next_hour"]

        # 4. Update the Digital Twin Property
        credential = DefaultAzureCredential()
        client = DigitalTwinsClient(ADT_ENDPOINT, credential)

        patch = [
            {
                "op": "replace",
                "path": "/PredictedPowerNextHour",
                "value": predicted_power
            }
        ]

        client.update_digital_twin(twin_id, patch)
        logging.info(f"Twin {twin_id} updated: Next hour prediction is {predicted_power} kW.")

    except Exception as e:
        logging.error(f"Error processing telemetry: {e}")