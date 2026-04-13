# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import xgboost as xgb
import pandas as pd
import joblib

app = FastAPI()

# Load the model and scaler trained in your notebook
model = xgb.XGBRegressor()
model.load_model("xgboost_power_model.json")
scaler = joblib.load("merged_data.pkl")

# Define the exact features your hybrid model expects
class TwinTelemetry(BaseModel):
    twin_id: str
    power_lag_1: float
    power_lag_24: float
    hour: int
    dayofweek: int
    month: int
    temperature_2m: float
    relative_humidity_2m: float
    wind_speed_10m: float
    wind_direction_10m: float

@app.post("/predict")
async def predict_power(data: TwinTelemetry):
    try:
        # 1. Format the incoming request into a DataFrame matching your notebook
        input_df = pd.DataFrame([{
            'power_lag_1': data.power_lag_1,
            'power_lag_24': data.power_lag_24,
            'hour': data.hour,
            'dayofweek': data.dayofweek,
            'month': data.month,
            'temperature_2m': data.temperature_2m,
            'relative_humidity_2m': data.relative_humidity_2m,
            'wind_speed_10m': data.wind_speed_10m,
            'wind_direction_10m': data.wind_direction_10m
        }])

        # 2. Scale the data using the scaler from your notebook
        # Note: In production, ensure you separate X and y scalers or slice appropriately 
        # based on how you fitted `scaler` in normalize_and_join()
        scaled_input = scaler.transform(input_df) 

        # 3. Predict using XGBoost
        scaled_prediction = model.predict(scaled_input)

        # 4. Inverse transform to get actual kW (Target Power)
        # Assuming target_power was the last column in your scaler
        dummy_array = [[0]*8 + [scaled_prediction[0]]] 
        actual_kw = scaler.inverse_transform(dummy_array)[0][-1]

        return {"predicted_power_next_hour": float(actual_kw)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))